"""Prepare a conditional corrective corpus. Never load or train a model.

The existing 216-row preparation is reproduced unchanged as a reference.
Only 40 additional, approved Management Projet TRAIN rows are selected.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import prepare_facturation_entity_pilot_v1 as original

VERSION = "facturation-entity-pilot-v2-corrective-preparation"
REFERENCE_SHA256 = {
    "manifest.json": "e45463a270e61db770ca2bf6503f990fa3be82b2c890add9b257bb89a2df6baa",
    "train.jsonl": "de28c9ce947c4310f22b8df3460944d3ee1d3b653e559633b919849f4c92676a",
    "valid.jsonl": "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487",
    "retained-plan.json": "eadeb3af47d9179cdead8b1660fd4f053c989f2fd54017b8f437d9d87906cc6f",
}
HELPER_SHA256 = {
    "prepare_facturation_entity_pilot_v1.py":
        "c2371315efdfcdd49a3fcb0802ba5b23059fb1280f9a10a92a3e950a1b687289",
    "prepare_facturation_entity_spans_v1.py":
        "978cd1341754b480f29a20ab929adaefd3d0fb2b94aa2d41a71c988caa86aded",
    "prepare_facturation_role_variants_v1.py":
        "2a654ed769d246e314803587b9cfa8e7177cf299dcb47b127b65be204557f84e",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare(source, supplement, output):
    source, supplement, output = [Path(p).resolve() for p in (source, supplement, output)]
    if (output.exists() or any(output == p or p in output.parents
                               for p in (source, supplement))):
        raise ValueError("A new isolated output directory is required")
    if not output.parent.is_dir():
        raise ValueError("Output parent must already exist")
    helper_hashes = {Path(module.__file__).name: sha(Path(module.__file__).read_bytes())
                     for module in (original, original.entity, original.prior)}
    if helper_hashes != HELPER_SHA256:
        raise ValueError("Approved preparation helper identity changed")
    with TemporaryDirectory(prefix="entity-v2-reference-", dir=output.parent) as temporary:
        reference = Path(temporary) / "reference"
        old_manifest = original.prepare(source, supplement, reference)
        if any(sha((reference / name).read_bytes()) != expected
               for name, expected in REFERENCE_SHA256.items()):
            raise ValueError("Approved original pilot reference identity changed")
        old_lines = (reference / "train.jsonl").read_bytes().splitlines()
        old_plan = json.loads((reference / "retained-plan.json").read_text())
        raw_source = (source / "train.jsonl").read_bytes()
        if sha(raw_source) != old_manifest["source_sha256"]["train.jsonl"]:
            raise ValueError("Approved TRAIN source changed during preparation")
        source_lines = raw_source.splitlines()
        rows = [json.loads(line) for line in source_lines]
        indices, management = original.retained(rows, "management_projet", 112)
        for item in management["selected"]:
            item["source_row_sha256"] = sha(source_lines[item["source_line"] - 1])
        management_lines = [source_lines[index] for index in indices]
        if (management_lines[:72] != old_lines[72:144] or
                management["selected"][:72] != old_plan["applications"]["management_projet"]["selected"]):
            raise ValueError("The original retained Management Projet prefix changed")
        plans = {"management_projet": management,
                 "design_workflow": old_plan["applications"]["design_workflow"]}
        if any(len(plan["by_tool"]) != 9 or
               any(info["uncovered"] for info in plan["feature_coverage"].values())
               for plan in plans.values()):
            raise ValueError("Every retained tool and measured shape/enum must be covered")
        lines = old_lines[:72] + management_lines + old_lines[144:]
        selected = [json.loads(line) for line in lines]
        validation_raw = (reference / "valid.jsonl").read_bytes()
        validation = [json.loads(line) for line in validation_raw.splitlines()]
        excluded = {original.prior.canonical_input_key(row) for row in validation}
        seen = set()
        for row in selected:
            original.target(row)
            key = original.prior.canonical_input_key(row)
            if key in seen or key in excluded:
                raise ValueError("Duplicate candidate or development input overlap")
            seen.add(key)
        counts = Counter(row["application"] for row in selected)
        if counts != Counter(facturation=72, management_projet=112, design_workflow=72):
            raise ValueError("Unexpected corrective corpus counts")
        plan = {
            "version": VERSION, "source_sha256": old_plan["source_sha256"],
            "method": old_plan["method"], "applications": plans,
            "evaluation_outcomes_used_for_selection": False,
            "reference_v1_manifest_sha256": sha((reference / "manifest.json").read_bytes()),
            "reference_v1_train_sha256": old_manifest["files"]["train.jsonl"],
        }
        files = {
            "train.jsonl": b"\n".join(lines) + b"\n",
            "valid.jsonl": validation_raw,
            "retained-plan.json": (json.dumps(plan, sort_keys=True, indent=2) + "\n").encode(),
        }
        manifest = {
            "version": VERSION, "status": "PREPARED; NO MODEL BOUND; NOT TRAINED OR ACCEPTED",
            "applications": list(original.APPLICATIONS), "languages": ["en", "fr"],
            "count": len(selected), "by_application": dict(counts),
            "files": {name: sha(raw) for name, raw in files.items()},
            "source_sha256": old_manifest["source_sha256"],
            "supplement_sha256": old_manifest["supplement_sha256"],
            "preparation_source_sha256": helper_hashes,
            "approved_reference_sha256": REFERENCE_SHA256,
            "generator_sha256": sha(Path(__file__).read_bytes()),
            "requested_experimental_parent": {
                "selected_step": 2048, "accepted": False, "actual_model_sha256": None,
            },
            "original_regression_reference_step": 600,
            "current_pilot_failure_evidence_sha256": None,
            "complete_epochs_requested": 1, "updates_requested": 256,
            "numerical_admission": False, "training_executed": False,
            "model_accepted": False, "production_activation": False,
            "next_application_training_started": False,
            "required_before_training": [
                "The current pilot comparison must finish unsuccessfully.",
                "Freshly attest the experimental merged FP32 parent and retained reference.",
                "Use a new optimizer and adapter; never apply the old adapter twice.",
                "Review new versioned numerical and evaluation bindings before any launch.",
                "Preserve all frozen cases, thresholds and earlier-app regression protection.",
            ],
            "limitations": [
                "Shape/enum coverage is not semantic retention or model accuracy.",
                "The first 72 Management Projet rows, all 72 Design Workflow rows and all "
                "72 Facturation rows are preserved from the original preparation.",
                "Development bytes stay unchanged; their input keys only exclude collisions.",
                "Missing retained language labels remain missing.",
                "Changing the parent and replay together would test their combined recipe.",
                "No inference, training, parity probe or accepted predecessor is established.",
            ],
        }
    output.mkdir()
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "supplement", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.supplement, args.output), indent=2))


if __name__ == "__main__":
    main()
