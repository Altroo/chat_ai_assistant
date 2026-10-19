"""Prepare a conditional corrective corpus. Never load or train a model.

The existing 216-row preparation is reproduced unchanged as a reference.
The default adds 40 approved Management Projet TRAIN rows. Optional Facturation
replay covers its native tools and measured shapes without loading a model.
"""
import argparse
from collections import Counter, defaultdict
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


def facturation_retained(rows, count):
    """Cover TRAIN marginals and critical/lookup conjunctions before diversity."""
    candidates = {original.prior.canonical_input_key(row) for row in rows
                  if row["application"] == "facturation"}
    indices, _ = original.retained(rows, "facturation", len(candidates))
    if type(count) is not int or not 18 <= count <= len(indices):
        raise ValueError("Facturation replay budget must cover 18 tools without repeats")
    pool, available, conjunctions = {}, defaultdict(set), defaultdict(set)
    priority, bundles = set(), set()
    for index in indices:
        function, schema = original.target(rows[index])
        tool, arguments = function["name"], function["arguments"]
        features = original.features(arguments, schema)
        # Resource/operation are business codes even where schemas use plain strings.
        for key in ("resource", "operation"):
            if key in arguments and "enum" not in schema.get("properties", {}).get(key, {}):
                features.add("/" + key + ":business-code=" +
                             original.prior.encoded(arguments[key]))
        # Other free text and numeric values never enter a selection signature.
        conjunction = original.prior.encoded(sorted(features))
        required = set()
        if (tool == "prepare_change" or
                set(arguments) & {"identifier", "invoice_number", "reference"}):
            required.add((tool, conjunction))
        bundle = sha(original.prior.encoded(sorted(
            rows[index]["tools"], key=lambda item: item["function"]["name"])).encode())
        identity = sha(original.prior.encoded(rows[index]).encode())
        pool[index] = (tool, features, identity, conjunction, required, bundle)
        available[tool].update(features)
        conjunctions[tool].add(conjunction)
        priority.update(required)
        bundles.add(bundle)
    if len(available) != 18:
        raise ValueError("Approved Facturation replay must retain all 18 native tools")
    covered, joint_covered = defaultdict(set), defaultdict(set)
    priority_covered, bundle_covered = set(), set()
    counts, selected = Counter(), []

    def take(index):
        tool, features, _, conjunction, required, bundle = pool.pop(index)
        selected.append(index)
        counts[tool] += 1
        covered[tool].update(features)
        joint_covered[tool].add(conjunction)
        priority_covered.update(required)
        bundle_covered.add(bundle)

    for tool in sorted(available):
        take(min((i for i, item in pool.items() if item[0] == tool),
                 key=lambda i: (-len(pool[i][1]), pool[i][2])))
    while any(covered[tool] != features for tool, features in available.items()):
        if len(selected) == count:
            raise ValueError("Facturation replay budget cannot cover every measured shape/enum")
        index = min(pool, key=lambda i: (
            -len(pool[i][1] - covered[pool[i][0]]), counts[pool[i][0]], pool[i][2]))
        if not pool[index][1] - covered[pool[index][0]]:
            raise ValueError("Missing Facturation feature coverage")
        take(index)
    first_full = len(selected)
    while priority_covered != priority:
        if len(selected) == count:
            raise ValueError("Facturation replay budget cannot cover critical or exact-lookup conjunctions")
        take(min(pool, key=lambda i: (
            -len(pool[i][4] - priority_covered), counts[pool[i][0]], pool[i][2])))
    first_priority = len(selected)
    while len(selected) < count:
        take(min(pool, key=lambda i: (
            -(pool[i][5] not in bundle_covered),
            -(pool[i][3] not in joint_covered[pool[i][0]]),
            counts[pool[i][0]], pool[i][2])))
    plan = {
        "count": len(selected), "by_tool": dict(counts),
        "method": "One maximum-feature TRAIN row per tool; greedy marginal coverage; "
                  "all prepare_change and top-level identifier/invoice_number/reference "
                  "conjunctions; unseen offered-tool bundles and full conjunctions; "
                  "tool-count/hash ties.",
        "signature_definition": "Tool plus the sorted full set of argument path/types "
                                "and schema-enum/top-level resource/operation codes; "
                                "no other free-text or numeric values.",
        "first_full_feature_coverage_at": first_full,
        "first_full_priority_conjunction_coverage_at": first_priority,
        "canonical_source_candidates": len(indices),
        "language_metadata": dict(Counter(
            rows[i].get("language") or "unspecified" for i in selected)),
        "feature_coverage": {tool: {
            "selected": len(covered[tool]), "available": len(features),
            "uncovered": sorted(features - covered[tool]),
        } for tool, features in sorted(available.items())},
        "conjunction_coverage": {tool: {
            "selected": len(joint_covered[tool]), "available": len(signatures),
            "uncovered": sorted(signatures - joint_covered[tool]),
        } for tool, signatures in sorted(conjunctions.items())},
        "priority_conjunction_coverage": {
            "selected": len(priority_covered), "available": len(priority),
            "uncovered": sorted(priority - priority_covered),
        },
        "offered_tool_bundle_definition": "SHA256 of canonical sorted complete tool schemas.",
        "offered_tool_bundle_coverage": {
            "selected": len(bundle_covered), "available": len(bundles),
            "uncovered": sorted(bundles - bundle_covered),
        },
        "selected": [{"source_line": i + 1,
                      "canonical_input_sha256": sha(
                          original.prior.canonical_input_key(rows[i]).encode())}
                     for i in selected],
    }
    return selected, plan


def prepare(source, supplement, output, *, facturation_replay_rows=0):
    if type(facturation_replay_rows) is not int or facturation_replay_rows < 0:
        raise ValueError("Facturation replay rows must be a non-negative integer")
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
        facturation_lines = []
        if facturation_replay_rows:
            facturation_indices, facturation = facturation_retained(
                rows, facturation_replay_rows)
            for item in facturation["selected"]:
                item["source_row_sha256"] = sha(source_lines[item["source_line"] - 1])
            facturation_lines = [source_lines[i] for i in facturation_indices]
            plans["facturation"] = facturation
        if any(len(plan["by_tool"]) != (18 if app == "facturation" else 9) or
               any(info["uncovered"] for info in plan["feature_coverage"].values())
               for app, plan in plans.items()):
            raise ValueError("Every retained tool and measured shape/enum must be covered")
        lines = old_lines[:72] + facturation_lines + management_lines + old_lines[144:]
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
        if counts != Counter(facturation=72 + facturation_replay_rows,
                             management_projet=112, design_workflow=72):
            raise ValueError("Unexpected corrective corpus counts")
        plan = {
            "version": VERSION, "source_sha256": old_plan["source_sha256"],
            "method": old_plan["method"], "applications": plans,
            "evaluation_outcomes_used_for_selection": False,
            "reference_v1_manifest_sha256": sha((reference / "manifest.json").read_bytes()),
            "reference_v1_train_sha256": old_manifest["files"]["train.jsonl"],
        }
        if facturation_replay_rows:
            plan["variant"] = "facturation-native-tool-replay"
            plan["method"] = (
                "Facturation: marginal/priority/bundle/conjunction TRAIN replay; "
                "Management Projet and Design Workflow: " + old_plan["method"])
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
            "complete_epochs_requested": 1, "updates_requested": len(selected),
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
        if facturation_replay_rows:
            manifest["variant"] = "facturation-native-tool-replay"
            manifest["facturation_replay_rows"] = facturation_replay_rows
            manifest["limitations"].append(
                "Facturation replay coverage is limited to the recorded TRAIN inventory in its "
                "retained plan. Even complete structural coverage does not establish every "
                "wording, value combination, tool-selection behavior or model accuracy.")
    output.mkdir()
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "supplement", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--facturation-replay-rows", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.supplement, args.output,
                             facturation_replay_rows=args.facturation_replay_rows), indent=2))


if __name__ == "__main__":
    main()
