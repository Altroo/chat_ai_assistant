"""Prepare source-verified contrast blocks and explicit shared-model replay.

This performs metadata/schema checks only. It creates no labels, loads no model
weights and cannot authorize numerical training or deployment.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path

HELPER_SHA256 = {
    "audit_training_inputs.py": "4a15488a8dd60dd38b710acb10d47c1c08c5828b2e7501045ef889f3ab5afcba",
    "facturation_focus_v2_admission.py": "0bb94397282cf3c27f93ef17bd96c1bd92c056e44d7afa9167d04670bf970c99",
    "training_schedule.py": "0df6692fa360c6ee0f194275941908e89c62496bdc0627fd6d0731e829b7bb83",
}
# Bind the reviewed metadata helpers before importing their code.
for _name, _expected in HELPER_SHA256.items():
    if hashlib.sha256(Path(__file__).with_name(_name).read_bytes()).hexdigest() != _expected:
        raise ValueError("Reviewed helper changed: " + _name)

import audit_training_inputs as base
import facturation_focus_v2_admission as prior
from training_schedule import complete_epoch_order

ROOT = Path(__file__).resolve().parents[2]
SHARED = "shared-v5r11-en-fr"
FOCUS = "facturation-focus-v2-en-fr"
SHARED_SHA256 = "02f2addad85051fd20a180b29c01239f67f8ceeb8265ace8b054d09f1f81ccdc"
FOCUS_SHA256 = "b5e9850bd8bcd7a2090f618b60e9d5bdc0a4f1e015a5f744fafdb64305c1cc8b"
APPLICATIONS = ("facturation", "management_projet", "design_workflow")
VERSION = "facturation-replay-v1-en-fr"
MATRIX = {"date_optional_document", "date_optional_operation"}
STATES = {"none", "first", "second", "limit"}
HELPERS = ("audit_training_inputs.py", "facturation_focus_v2_admission.py", "training_schedule.py")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def source(name, expected):
    path = ROOT / "training/datasets" / name
    raw = (path / "manifest.json").read_bytes()
    if sha(raw) != expected:
        raise ValueError("Reviewed source manifest changed: " + name)
    manifest = json.loads(raw)
    payloads = {s: (path / (s + ".jsonl")).read_bytes() for s in ("train", "valid")}
    if any(sha(value) != manifest["files"][s + ".jsonl"] for s, value in payloads.items()):
        raise ValueError("Reviewed source split changed: " + name)
    if any(not line.endswith(b"\n") for value in payloads.values() for line in value.splitlines(keepends=True)):
        raise ValueError("Source requires complete newline-terminated records")
    rows = {s: [json.loads(line) for line in value.splitlines()] for s, value in payloads.items()}
    return manifest, payloads, rows


def combined():
    shared, shared_bytes, shared_rows = source(SHARED, SHARED_SHA256)
    focus, focus_bytes, focus_rows = source(FOCUS, FOCUS_SHA256)
    if Counter(r["application"] for r in shared_rows["train"]) != Counter(
            facturation=931, management_projet=1012, design_workflow=476):
        raise ValueError("Reviewed cumulative training scope changed")
    if len(focus_rows["train"]) != 1487 or {r["application"] for r in focus_rows["train"]} != {"facturation"}:
        raise ValueError("Reviewed focused training scope changed")
    if {base.model_input_key(r) for r in shared_rows["valid"] if r["application"] == "facturation"} != {
            base.model_input_key(r) for r in focus_rows["valid"]}:
        raise ValueError("Focused development inputs differ from cumulative development")
    # Preserve all cumulative source bytes. Append only genuinely new focused
    # model inputs, using their original source bytes and targets unchanged.
    rows = list(shared_rows["train"])
    lines = shared_bytes["train"].splitlines(keepends=True)
    indexed = {}
    for index, row in enumerate(rows):
        indexed.setdefault(base.model_input_key(row), index)
    focus_indices = []
    for row, line in zip(focus_rows["train"], focus_bytes["train"].splitlines(keepends=True)):
        key = base.model_input_key(row)
        if key in indexed:
            index = indexed[key]
            if base.encoded(base.target(rows[index])) != base.encoded(base.target(row)):
                raise ValueError("Source model input has contradictory targets")
        else:
            index = len(rows)
            rows.append(row)
            lines.append(line)
            indexed[key] = index
        focus_indices.append(index)
    if len(rows) != 2975 or len(set(focus_indices)) != 1487:
        raise ValueError("Unexpected cumulative/focused source overlap")
    return shared, focus, rows, b"".join(lines), shared_bytes["valid"], focus_indices


def retention_features(row):
    """Cover each old tool, supplied/omitted fields and declared finite intents.

    This is marginal replay coverage, not every argument combination.
    """
    result = set(base.features(row))
    action = base.target(row)
    app, tool, args = row["application"], action["name"], action["arguments"]
    schema = next(t["function"]["parameters"] for t in row["tools"] if t["function"]["name"] == tool)
    for name in schema.get("properties", {}):
        result.add((app, "argument_presence", tool, name, str(name in args)))
    for name in ("resource", "metric", "period", "status", "unpaid"):
        if name in args:
            result.add((app, "finite_intent", tool, name, base.encoded(args[name])))
    return result


def contrast_blocks(rows, indices):
    grouped = defaultdict(list)
    for index in indices:
        row = rows[index]
        if row.get("curriculum_category") in MATRIX:
            key = (row["curriculum_category"], row["contrast_family"], row["language"])
        else:
            key = ("singleton", str(index))
        grouped[key].append(index)
    blocks = []
    for key in sorted(grouped):
        selected = grouped[key]
        if key[0] in MATRIX:
            variants = {rows[i]["contrast"]["optional_state"]: i for i in selected}
            if len(selected) != 4 or set(variants) != STATES:
                raise ValueError("Every matrix block requires all four optional states")
            baseline = base.target(rows[variants["none"]])
            for state, index in variants.items():
                action = deepcopy(base.target(rows[index]))
                optional = ({"first": "client_name", "second": "product_name", "limit": "limit"}
                            if key[0] == "date_optional_document" else
                            {"first": "product_name", "second": "location_name", "limit": "limit"})
                if state != "none":
                    if optional[state] not in action["arguments"]:
                        raise ValueError("Matched contrast lacks its declared optional field")
                    del action["arguments"][optional[state]]
                if action != baseline:
                    raise ValueError("Matched contrast changes more than its declared optional field")
        blocks.append(selected)
    return blocks


def greedy_units(rows, units, features, required):
    candidates = sorted(units, key=lambda unit: sha(base.encoded(
        [base.model_input_key(rows[i]) for i in sorted(unit)]).encode()))
    pending, selected = set(required), []
    while pending:
        if not candidates:
            raise ValueError("Training selection cannot cover required features")
        # Cost-aware cover selects whole contrast blocks, never a single
        # optional-state variant from an admitted matrix family/language.
        best = max(candidates, key=lambda unit: len(set().union(*(features[i] for i in unit)) & pending) / len(unit))
        covered = set().union(*(features[i] for i in best))
        if not covered & pending:
            raise ValueError("Training selection cannot cover required features")
        selected.extend(best)
        pending -= covered
        candidates.remove(best)
    return selected


def selection(rows, focus_indices, maximum=320):
    if type(maximum) is not int or not 1 <= maximum <= 320:
        raise ValueError("Positive bounded selection budget up to 320 required")
    if len(rows) != 2975 or len(focus_indices) != 1487:
        raise ValueError("Reviewed source dimensions required")
    added = focus_indices[1047:]
    axes = {i: prior.axis_features(rows[i]) for i in added}
    required_axes = set().union(*axes.values())
    new = greedy_units(rows, contrast_blocks(rows, added), axes, required_axes)
    # Replay is independently required even if new examples cover the same
    # tool names. Only the original cumulative TRAINING prefix is eligible.
    retained = {i: retention_features(rows[i]) for i in range(2419)}
    required_retention = set().union(*retained.values())
    replay = greedy_units(rows, [[i] for i in range(2419)], retained, required_retention)
    chosen = new + replay
    if len(chosen) > maximum or len(chosen) != len(set(chosen)):
        raise ValueError("Selection budget cannot cover contrasts and explicit replay")
    if len({base.model_input_key(rows[i]) for i in chosen}) != len(chosen):
        raise ValueError("Selection has duplicate model inputs")
    def bucket(index):
        return "new_facturation" if index >= 2419 else "retained_" + rows[index]["application"]
    # Schedule-only buckets are never written into trusted application context.
    buckets = [{"application": bucket(i)} for i in chosen]
    ordered = [chosen[i] for i in complete_epoch_order(buckets)]
    windows = [{"first_step": start + 1, "last_step": min(start + 32, len(ordered)),
                "by_source_bucket": dict(Counter(bucket(i) for i in ordered[start:start + 32]))}
               for start in range(0, len(ordered), 32)]
    return {
        "contract": "complete-contrast-blocks-with-independent-training-replay",
        "row_indices": ordered, "count": len(ordered),
        "new_training_rows": sorted(new), "retained_training_rows": sorted(replay),
        "by_source_bucket": dict(Counter(bucket(i) for i in ordered)),
        "covered_axes": [list(v) for v in sorted(required_axes)],
        "retention_features": [list(v) for v in sorted(required_retention)],
        "schedule_windows": windows,
        "selected_rows_sha256": sha(base.encoded([rows[i] for i in ordered]).encode()),
        "limitations": [
            "Whole selected optional-state groups and marginal replay coverage, not all Cartesian combinations.",
            "Uses only existing training inputs and metadata; no outcome-based selection.",
            "Replay and static checks do not predict retention or 95 percent model accuracy.",
        ],
    }


def capture_plan(rows, valid_rows, chosen):
    def capture_order(indices, values):
        return sorted(indices, key=lambda i: sha(base.model_input_key(values[i]).encode()))[:2]
    train_captures = []
    for bucket in chosen["by_source_bucket"]:
        eligible = [i for i in chosen["row_indices"]
                    if ("new_facturation" if i >= 2419 else "retained_" + rows[i]["application"]) == bucket]
        if len(eligible) < 2:
            raise ValueError("Each source bucket requires two diagnostic captures")
        train_captures.extend(capture_order(eligible, rows))
    valid_captures = []
    for app in APPLICATIONS:
        eligible = [i for i, row in enumerate(valid_rows) if row["application"] == app]
        valid_captures.extend(capture_order(eligible, valid_rows))
    return {"train": train_captures, "valid": valid_captures}


def admit_prepared(data, expected_manifest_sha256):
    """Verify an already reviewed/materialized dataset before numerical loading.

    The numerical caller must pin its independently reviewed expected hash.
    Source generation and numerical optimization remain separate operations.
    """
    data = Path(data)
    manifest_raw = (data / "manifest.json").read_bytes()
    if sha(manifest_raw) != expected_manifest_sha256:
        raise ValueError("Reviewed preparation manifest changed")
    manifest = json.loads(manifest_raw)
    if (manifest["version"] != VERSION or manifest["applications"] != list(APPLICATIONS)
            or manifest["languages"] != ["en", "fr"]
            or manifest["source_manifests"] != {SHARED: SHARED_SHA256, FOCUS: FOCUS_SHA256}):
        raise ValueError("Reviewed preparation scope changed")
    if manifest["generator_sha256"] != sha(Path(__file__).read_bytes()):
        raise ValueError("Prepared generator identity differs")
    expected_helpers = {"training/scripts/" + name: expected for name, expected in HELPER_SHA256.items()}
    if manifest["helper_sha256"] != expected_helpers:
        raise ValueError("Prepared helper identities differ")
    audit = base.audit(data)
    payloads = {s: (data / (s + ".jsonl")).read_bytes() for s in ("train", "valid")}
    rows = {s: [json.loads(line) for line in value.splitlines()] for s, value in payloads.items()}
    if len(rows["train"]) != 2975 or len(rows["valid"]) != 275:
        raise ValueError("Reviewed preparation dimensions changed")
    indices = manifest["focus_row_indices"]
    if (len(indices) != 1487 or len(set(indices)) != 1487
            or any(type(i) is not int or not 0 <= i < 2975 for i in indices)
            or set(indices[:931]) != {i for i in range(2419) if rows["train"][i]["application"] == "facturation"}
            or indices[931:] != list(range(2419, 2975))
            or any(rows["train"][i]["application"] != "facturation" for i in indices)):
        raise ValueError("Reviewed focused source mapping changed")
    chosen = selection(rows["train"], indices)
    audit["rehearsal"] = chosen
    captures = capture_plan(rows["train"], rows["valid"], chosen)
    if len(captures["train"]) != 8 or len(captures["valid"]) != 6:
        raise ValueError("Bounded diagnostic capture dimensions changed")
    if (data / "manifest.json").read_bytes() != manifest_raw or any(
            sha(value) != audit["input_sha256"][s] or (data / (s + ".jsonl")).read_bytes() != value
            for s, value in payloads.items()):
        raise ValueError("Prepared data changed during admission")
    lineage = {
        "application": "facturation", "retained_applications": ["management_projet", "design_workflow"],
        "manifest_sha256": expected_manifest_sha256,
        "source_manifests": manifest["source_manifests"],
        "model_acceptance_verified": False, "longer_training_admitted": False,
        "actual_model_binding_required_before_numerical_work": True,
        "disposable_adapter_must_not_be_used": True,
    }
    return audit, rows, captures, lineage


def control_metadata(shared, focus):
    """Preserve existing evaluation identities/policies without reading cases."""
    result = {}
    for name in ("held_out", "historical_regression_held_out"):
        merged = dict(shared[name])
        for key, value in focus[name].items():
            if key in merged and merged[key] != value:
                raise ValueError("Held-out registry identity conflict")
            merged[key] = value
        result[name] = merged
    if ("fresh_controls" not in shared or "fresh_controls" not in focus
            or shared["fresh_controls"] != focus["fresh_controls"]):
        raise ValueError("Parent fresh-controls identities or scoring policies disagree")
    result["fresh_controls"] = deepcopy(shared["fresh_controls"])
    for name in ("evaluation_manifest_sha256", "historical_evaluation_manifest_sha256", "held_out_count"):
        if name in focus and focus[name] != shared[name]:
            raise ValueError("Parent evaluation identity disagreement: " + name)
        result[name] = deepcopy(shared[name])
    return result


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError("Never overwrite existing preparation")
    shared, focus, rows, train_bytes, valid_bytes, focus_indices = combined()
    chosen = selection(rows, focus_indices)
    generator_sha = sha(Path(__file__).read_bytes())
    for name, expected in HELPER_SHA256.items():
        if sha(Path(__file__).with_name(name).read_bytes()) != expected:
            raise ValueError("Reviewed helper changed: " + name)
    # Carry both file identities and separate-scoring policy, never case contents.
    controls = control_metadata(shared, focus)
    native = deepcopy(shared["native_metadata"])
    native["facturation"] = focus["native_metadata"]["facturation"]
    manifest = {
        "version": VERSION, "applications": list(APPLICATIONS), "languages": ["en", "fr"],
        "status": "PREPARATION ONLY; no numerical work or accuracy claim",
        "generator_sha256": generator_sha,
        "helper_sha256": {"training/scripts/" + name: sha(Path(__file__).with_name(name).read_bytes()) for name in HELPERS},
        "source_manifests": {SHARED: SHARED_SHA256, FOCUS: FOCUS_SHA256},
        "focus_row_indices": focus_indices,
        "counts": {"train": 2975, "valid": 275, "retained_cumulative_training_prefix": 2419,
                   "new_focused_inputs": 556, "by_application": dict(Counter(r["application"] for r in rows))},
        "files": {"train.jsonl": sha(train_bytes), "valid.jsonl": sha(valid_bytes)},
        "native_metadata": native, **controls,
        "starting_model": {"required_predecessor_selected_step": 600,
            "required_predecessor_report_sha256": "388e6dfd0fe915cb13f85deb9e85aaf16df7272c8f2306ee0e3dd54290fcc258",
            "actual_model_binding_required_before_numerical_work": True,
            "disposable_adapter_must_not_be_used": True},
        "training_executed": False, "model_accepted": False, "full_training_authorized": False,
        "production_activation": False,
    }
    output.mkdir(parents=True)
    (output / "train.jsonl").write_bytes(train_bytes)
    (output / "valid.jsonl").write_bytes(valid_bytes)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    audit, admitted_rows, captures, lineage = admit_prepared(output, sha((output / "manifest.json").read_bytes()))
    # Detect concurrent source/helper changes, while leaving incomplete artifacts
    # unaccepted for inspection rather than silently overwriting or retrying.
    source(SHARED, SHARED_SHA256)
    source(FOCUS, FOCUS_SHA256)
    if sha(Path(__file__).read_bytes()) != generator_sha:
        raise ValueError("Generator changed during preparation")
    for name, expected in HELPER_SHA256.items():
        if sha(Path(__file__).with_name(name).read_bytes()) != expected:
            raise ValueError("Reviewed helper changed during preparation: " + name)
    report = {"version": VERSION, "manifest_sha256": sha((output / "manifest.json").read_bytes()),
              "audit": audit, "selection": chosen,
              "captures": {**captures, "total": 14,
                           "scope": "Eight training and six development diagnostics; not acceptance"},
              "lineage": lineage,
              "training_executed": False, "accuracy_estimated": False,
              "model_accepted": False, "production_activation": False}
    (output / "preparation.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.output)
    print(json.dumps({"rows_checked": report["audit"]["rows_checked"],
                      "selected_updates": report["selection"]["count"],
                      "by_source_bucket": report["selection"]["by_source_bucket"],
                      "training_executed": False, "accuracy_estimated": False}))


if __name__ == "__main__":
    main()
