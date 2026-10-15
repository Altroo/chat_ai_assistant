"""Append the reviewed coverage supplement without changing retained splits.

This is an unbound three-application preparation. It neither selects a base
model nor grants training, deployment or later-application acceptance.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from audit_training_inputs import checked_rows
from prepare_management_name_errata_v2 import check_labels
from prepare_coverage_contrasts_v1 import check_exclusions
from prepare_shared_v5r6 import current_request
from build_shared_v5r3 import key

ROOT = Path(__file__).resolve().parents[2]
PARENT = "shared-v5r9-en-fr"
PARENT_SHA = "74fb992ed98e326ff518cdd4302f36205230c41c3b41b34515ef0c823b2763e5"
SUPPLEMENT = "coverage-contrasts-v1-en-fr"
SUPPLEMENT_SHA = "a8f0f98964810756037b0b25b88275764570c0d78ab5ab6bce435238fa2a783c"
OUTPUT = "shared-v5r10-en-fr"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_bound(directory, expected):
    if sha(directory / "manifest.json") != expected:
        raise ValueError("Reviewed manifest changed")
    manifest = json.loads((directory / "manifest.json").read_text())
    for name, digest in manifest["files"].items():
        if sha(directory / name) != digest:
            raise ValueError("Reviewed dataset payload changed")
    for name, digest in manifest["helper_sha256"].items():
        if sha(ROOT / name) != digest:
            raise ValueError("Reviewed helper source changed")
    return manifest


def native_union(parent, supplement, roots):
    result = deepcopy(parent)
    if set(roots) != set(result) or set(supplement) != set(result):
        raise ValueError("Exactly the three reviewed applications are required")
    for app, files in supplement.items():
        for name, digest in files.items():
            if name in result[app] and result[app][name] != digest:
                raise ValueError("Conflicting native source identities")
            result[app][name] = digest
    for app, files in result.items():
        for name, digest in files.items():
            if sha(roots[app] / name) != digest:
                raise ValueError("Native source changed")
    return result


def assemble(roots):
    source = ROOT / "training/datasets" / PARENT
    extra = ROOT / "training/datasets" / SUPPLEMENT
    parent = read_bound(source, PARENT_SHA)
    supplement = read_bound(extra, SUPPLEMENT_SHA)
    native = native_union(parent["native_metadata"], supplement["native_metadata"], roots)
    retained = (source / "train.jsonl").read_bytes()
    additions = (extra / "train.jsonl").read_bytes()
    if not retained.endswith(b"\n") or not additions.endswith(b"\n"):
        raise ValueError("Complete newline-terminated records required")
    rows = checked_rows(retained, set(parent["applications"]))
    new = checked_rows(additions, set(parent["applications"]))
    if len(rows) != 2339 or len(new) != 80:
        raise ValueError("Unexpected reviewed curriculum size")
    check_exclusions(parent, new)
    existing = {key(r["application"], current_request(r)) for r in rows}
    if any(key(r["application"], current_request(r)) in existing for r in new):
        raise ValueError("Supplement repeats retained training")
    check_labels(rows + new)
    payloads = {"train.jsonl": retained + additions, "valid.jsonl": (source / "valid.jsonl").read_bytes()}
    valid = checked_rows(payloads["valid.jsonl"], set(parent["applications"]))
    manifest = deepcopy(parent)
    manifest.update(version=OUTPUT, status="PREPARATION ONLY; no base model bound or numerical rehearsal executed",
        parent_manifest_sha256=PARENT_SHA, generator_sha256=sha(Path(__file__)),
        helper_sha256={name: sha(ROOT / name) for name in (
            "training/scripts/audit_training_inputs.py", "training/scripts/training_schedule.py",
            "training/scripts/prepare_management_name_errata.py", "training/scripts/prepare_management_name_errata_v2.py",
            "training/scripts/prepare_coverage_contrasts_v1.py", "training/scripts/prepare_shared_v5r6.py",
            "training/scripts/prepare_shared_v5r8.py", "training/scripts/build_shared_v5r3.py")},
        source_manifest_sha256={**parent["source_manifest_sha256"], PARENT: PARENT_SHA, SUPPLEMENT: SUPPLEMENT_SHA},
        native_metadata=native,
        counts={"train": len(rows)+len(new), "valid": len(valid), "retained_parent_rows_byte_identical": len(rows),
                "added": len(new), "by_application": dict(Counter(r["application"] for r in rows+new)),
                "added_categories": supplement["counts"]["categories"]},
        files={name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()},
        inherited_preparation={"version": PARENT, "manifest_sha256": PARENT_SHA,
                               "counts": parent["counts"], "corrections": parent["corrections"]},
        supplement={"version": SUPPLEMENT, "manifest_sha256": SUPPLEMENT_SHA},
        training_policy="Retain every corrected R9 training byte and all validation/evaluation bytes. Append only the reviewed 80 synthetic training rows. Server numerical rehearsal and exact export checks precede any full continuation.",
        model_binding={"status": "UNBOUND; active R8 acceptance must finish before selecting a rehearsal base",
                       "later_stage_policy": "An accepted model and its actual complete curriculum must be bound before later application training."})
    return payloads, manifest


def prepare(roots, output=None):
    output = output or ROOT / "training/datasets" / OUTPUT
    if output.exists():
        raise ValueError("Never overwrite a versioned curriculum")
    payloads, manifest = assemble(roots)
    output.mkdir()
    for name, raw in payloads.items():
        with (output / name).open("xb") as stream:
            stream.write(raw)
    with (output / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for app in ("facturation", "management_projet", "design_workflow"):
        parser.add_argument("--" + app.replace("_", "-") + "-backend", type=Path, required=True)
    args = parser.parse_args()
    result = prepare({app: getattr(args, app + "_backend") for app in ("facturation", "management_projet", "design_workflow")})
    print(json.dumps({"version": result["version"], "counts": result["counts"],
                      "training_started": False, "model_bound": False}))
