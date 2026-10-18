"""Assemble reviewed TRAIN-only search contrasts with the exact prior schedule.

This prepares a new candidate corpus. It does not run training, edit frozen
evaluations, qualify a model or activate production.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import prepare_facturation_role_variants_v1 as prior

VERSION = "facturation-search-refinement-v1-en-fr"
CONTRASTS = {
    "profiles": ("5f539a4902e0e1163be53b412029f90706607638188fe9a097921ee1c73da210",
                 "14378b89b5ce62a310fb67a77592f295744b722e83427fe6bd82a1df0fa3f6f8"),
    "roles": ("68b7b32033ef8abe1ce37615d7e5ad6fd78608fc4805c9152b94015a31479ae6",
              "95d88af62759f2a3fb013e2a65223357b54ac44ee778be3f676101465162530a"),
    "natural": ("54e7668bcc8536696cc7133ee7442a726d743b1da036d154a3dc760fa7b1ea88", "3f06f930007f9519f00a92d98ee8ac6bc7137d086c8482c2835e7b1d1ecc2741"),
}


def target(row):
    calls = row["messages"][-1].get("tool_calls", [])
    if len(calls) != 1 or row["messages"][-1]["role"] != "assistant":
        raise ValueError("Exactly one supervised action is required")
    return calls[0]["function"]


PLAN_SHA256 = "d5d22fa5a49c6991190d7f249938c35e52db5c7cf2cc88edbdfa4c93024ba87a"


def retained(rows, plan_raw):
    """Reuse exactly the reviewed prior TRAIN schedule, never its adapter."""
    if prior.digest(plan_raw) != PLAN_SHA256:
        raise ValueError("Immutable retained TRAIN selection plan changed")
    plan = json.loads(plan_raw)
    selected = plan["audit"]["rehearsal"]
    indices = selected["row_indices"]
    if (len(rows) != 2975 or selected["count"] != 2283 or len(indices) != 2283
            or len(set(indices)) != 2283
            or any(type(i) is not int or not 0 <= i < len(rows) for i in indices)
            or plan["audit"]["input_sha256"]["train"] != prior.SOURCE_SHA256["train.jsonl"]
            or prior.digest(prior.encoded([rows[i] for i in indices]).encode()) != selected["selected_rows_sha256"]):
        raise ValueError("Prior training selection no longer matches its source")
    return indices


def validate_rows(rows, development):
    excluded = {prior.canonical_input_key(row) for row in development}
    seen = {}
    for row in rows:
        if row["application"] not in {"facturation", "management_projet", "design_workflow"}:
            raise ValueError("Unexpected application")
        if row.get("language") not in (None, "en", "fr"):
            raise ValueError("Unexpected language")
        function = target(row)
        tools = {tool["function"]["name"]: tool["function"]["parameters"] for tool in row["tools"]}
        if function["name"] not in tools:
            raise ValueError("Target tool is not offered")
        Draft202012Validator(tools[function["name"]]).validate(function["arguments"])
        if prior.canonical_input_key(row) in excluded:
            raise ValueError("Development-input overlap")
        key = prior.input_key(row)
        if key in seen:
            raise ValueError("Duplicate or conflicting candidate input")
        seen[key] = prior.encoded(function)


def prepare(original, profiles, natural, roles, selection_plan, output):
    original, profiles, natural, roles, selection_plan, output = map(
        lambda p: Path(p).resolve(), (original, profiles, natural, roles, selection_plan, output))
    if output.exists() or any(root == output or root in output.parents
                              for root in (original, profiles, natural, roles, selection_plan.parent)):
        raise ValueError("New isolated output required")
    raw = {name: (original / name).read_bytes() for name in prior.SOURCE_SHA256}
    if any(prior.digest(value) != prior.SOURCE_SHA256[name] for name, value in raw.items()):
        raise ValueError("Frozen original corpus changed")
    all_rows = [json.loads(line) for line in raw["train.jsonl"].splitlines()]
    valid = [json.loads(line) for line in raw["valid.jsonl"].splitlines()]
    if len(all_rows) != 2975 or len(valid) != 275:
        raise ValueError("Unexpected original corpus")
    selected = retained(all_rows, selection_plan.read_bytes())
    rows = [all_rows[index] for index in selected]
    provenance, pins = [], {}
    for kind, root in (("profiles", profiles), ("natural", natural), ("roles", roles)):
        manifest_raw, payload = (root / "manifest.json").read_bytes(), (root / "contrasts.jsonl").read_bytes()
        manifest_sha, payload_sha = map(prior.digest, (manifest_raw, payload))
        expected_manifest, expected_payload = CONTRASTS[kind]
        if (expected_manifest is not None and manifest_sha != expected_manifest) or payload_sha != expected_payload:
            raise ValueError("Reviewed contrast corpus changed")
        manifest = json.loads(manifest_raw)
        if (manifest.get("applications", [manifest.get("generated_application")]) != ["facturation"] or manifest["languages"] != ["en", "fr"]
                or manifest["files"]["contrasts.jsonl"] != payload_sha):
            raise ValueError("Contrast manifest mismatch")
        contrast_rows = [json.loads(line) for line in payload.splitlines()]
        expected_count = {"profiles": 268, "natural": 112, "roles": 440}[kind]
        if len(contrast_rows) != expected_count or manifest["count"] != expected_count:
            raise ValueError("Incomplete reviewed contrast corpus")
        if kind == "natural" and (
            manifest["source_profile_manifest_sha256"] != CONTRASTS["profiles"][0]
            or manifest["source_profile_contrast_sha256"] != CONTRASTS["profiles"][1]
            or manifest["generator_sha256"] != "4a1dc1fda931b9cd0f6f705aad67e73ffb6ae742eddbce33e6488963127f19ad"):
            raise ValueError("Natural contrast lineage changed")
        start = len(rows)
        rows.extend(contrast_rows)
        provenance.append({"kind": kind, "first_index": start, "count": len(contrast_rows)})
        pins[kind] = {"manifest_sha256": manifest_sha, "contrasts_sha256": payload_sha}
    validate_rows(rows, valid)
    train_raw = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                        for row in rows).encode()
    manifest = {
        "version": VERSION, "status": "PREPARED; server preflight and reviewed admission required",
        "applications": ["facturation", "management_projet", "design_workflow"],
        "languages": ["en", "fr"],
        "files": {"train.jsonl": prior.digest(train_raw), "valid.jsonl": prior.digest(raw["valid.jsonl"])},
        "source_files_sha256": prior.SOURCE_SHA256, "contrast_sources": pins,
        "count": len(rows), "by_application": dict(Counter(r["application"] for r in rows)),
        "retained": {"count": len(selected), "original_indices": selected,
                     "by_application": dict(Counter(all_rows[i]["application"] for i in selected)),
                     "selection_plan_sha256": PLAN_SHA256,
                     "policy": "Exact previously optimized 2283-row TRAIN schedule; no replacement sampler"},
        "added": provenance, "generator_sha256": prior.digest(Path(__file__).read_bytes()),
        "starting_model": {"selected_step": 600, "rejected_v3_adapter_allowed": False},
        "training_executed": False, "model_accepted": False, "production_activation": False,
        "limitations": [
            "The 2283 prior optimized rows are retained exactly; 692 other original TRAIN rows remain outside this schedule.",
            "The two natural wording families do not establish generalization.",
            "Role contrasts retain their original tool bundles; not every name, profile and phrasing combination is crossed.",
            "Passing four-family name probes did not establish naming as the source of failures.",
            "The original 275 development rows remain byte-identical; acceptance and fresh cases are not opened.",
            "The original checkpoint 600 and unchanged Colibri accuracy and regression gates remain mandatory.",
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "train.jsonl").write_bytes(train_raw)
    (output / "valid.jsonl").write_bytes(raw["valid.jsonl"])
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("original", "profiles", "natural", "roles", "selection-plan", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.original, args.profiles, args.natural, args.roles, args.selection_plan, args.output), indent=2))


if __name__ == "__main__":
    main()
