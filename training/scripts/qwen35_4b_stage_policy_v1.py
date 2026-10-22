"""Prospective first-stage 4B model gates; never a numerical admission.

Consume every declared primary candidate and all unchanged broader suites.
Other applications are measured separately, not certified by Facturation.
Later stages need a newly bound accepted predecessor and retention evidence.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
VERSION = "qwen35-4b-sequential-stage-v1"
ORDER = ("facturation", "management_projet", "design_workflow", "contrat",
         "gestion_magasin", "reservation")
SELECTOR_SHA = "10a49e4e2ce913b27bc7f6098f231c6fe905effcd3cde2983a70c2adad6841dd"
DEVELOPMENT_SHA = "b007326c32de9ede8424218ad4196a663324b1ad516df87a69df957f1b846a8b"
REGRESSION_MANIFEST_SHA = "6e8df0592ddcde75fd2d4c1277aaf789545cd7f1ca9224fc756787abe22e73f3"
FRESH_SHA = "5ef26e7d320a9360dcb3defee37c4a60bea807c3f17fb664c2c78c381eb3bff8"
FRESH_MANIFEST_SHA = "3c67453ad50eff5883a8c58fb0d2c208ac813dcc700c9680401e1cabc5bd3d7a"
DEVELOPMENT_COUNTS = dict(zip(ORDER[:3], (133, 78, 64)))
REGRESSION_COUNTS = dict(zip(ORDER[:3], (108, 200, 130)))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def selector():
    path = Path(__file__).with_name("select_qwen35_4b_pilot_v1.py")
    raw = path.read_bytes()
    if digest(raw) != SELECTOR_SHA:
        raise ValueError("Frozen primary selector changed")
    scope = {"__name__": "verified_primary_selector", "__file__": str(path)}
    exec(compile(raw, str(path), "exec"), scope)
    return scope


def regression_manifest():
    path = ROOT / "training/datasets/shared-dialogue-v2-en-fr/manifest.json"
    raw = path.read_bytes()
    if digest(raw) != REGRESSION_MANIFEST_SHA:
        raise ValueError("Frozen regression manifest changed")
    return json.loads(raw)


def development_source():
    """Reconstruct exact historical envelopes using committed synthetic inputs."""
    base = ROOT / "training/datasets"
    training = [json.loads(line) for line in
                (base / "shared-v5r11-en-fr/valid.jsonl").read_bytes().splitlines()]
    original_count = len((base / "shared-v5r3-en-fr/valid.jsonl").read_bytes().splitlines())
    augmentation = json.loads((base / "shared-v5r4-en-fr/manifest.json").read_bytes())["augmentation"]["valid"]
    groups = list(range(original_count)) + [row["source_index"] for row in augmentation]
    if len(training) != 275 or len(groups) != 275:
        raise ValueError("Complete historical development sources required")
    rows = []
    for index, (source, group) in enumerate(zip(training, groups)):
        target = source["messages"][-1]["tool_calls"][0]["function"]
        rows.append({
            "id": f"validation-{index:03}", "category": source["application"],
            "language": "en_fr_unlabeled", "scenario_group": f"{source['application']}-{group:03}",
            "messages": source["messages"][:-1],
            "offered_tool_schemas": [tool for tool in source["tools"] if tool["function"]["name"] != "clarify"],
            "expected": {"tool": target["name"], "arguments": target["arguments"]},
        })
    raw = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    if digest(raw) != DEVELOPMENT_SHA:
        raise ValueError("Reconstructed development inputs differ from frozen historical bytes")
    return raw


def prepare_policy():
    primary = selector()["prepare_policy"]()
    regression = regression_manifest()
    return {
        "version": VERSION, "base_model": "Qwen/Qwen3.5-4B",
        "base_revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        "stage_order": list(ORDER), "implemented_stage": "facturation",
        "primary_policy": primary,
        "development": {"sha256": DEVELOPMENT_SHA, "count": 275,
                        "by_application": DEVELOPMENT_COUNTS},
        "regression": {"manifest_sha256": REGRESSION_MANIFEST_SHA,
                       "count": 438, "by_application": REGRESSION_COUNTS,
                       "files": {name: regression["files"][name] for name in regression["inputs"]}},
        "additional_controls": {"manifest_sha256": FRESH_MANIFEST_SHA,
                                "sha256": FRESH_SHA, "count": 48,
                                "by_application": {app: 16 for app in ORDER[:3]}},
        "stage_rules": [
            "Run every declared primary candidate before selection; do not change scoring or labels.",
            "Run all 275 development, 438 regression and 48 additional controls for the selected model.",
            "Current application must pass every own grouped suite and each own regression subset.",
            "Report every measured untrained-application failure; it is not a previously qualified retention gate.",
            "Stage one has no accepted predecessor in this new 4B lineage; the old model is not its predecessor.",
            "Before each later stage, seal its datasets and actual accepted 4B predecessor model/report hashes.",
            "Retain all previously qualified applications on the candidate: all original gates plus no decline in tool, action, structure and eligible argument counts on identical cases.",
            "No stage skipping. Later-stage implementation/admission is separate and not supplied by this first-stage helper.",
            "Final six-application model qualification requires all six current evaluations on the same shared model.",
            "Native security, integrated behavior and latency remain separate requirements; model scores do not prove them.",
            "Numerical admission and production activation are separate; this helper authorizes neither.",
        ],
        "helper_sha256": digest(Path(__file__).read_bytes()),
    }


def passed(assessment):
    metrics = assessment["metrics"]
    return (assessment["model_targets_passed"] and metrics["count"] > 0
            and 100 * metrics["counts"]["action_matches"] >= 95 * metrics["count"])


def dataset(raw, expected_sha, events, scorer):
    if not isinstance(raw, bytes) or digest(raw) != expected_sha:
        raise ValueError("Frozen broader dataset changed")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if (not isinstance(events, list) or [e.get("id") for e in events] != [r["id"] for r in rows]
            or any(e.get("category") != r["category"] for r, e in zip(rows, events))):
        raise ValueError("Complete ordered result cases and original categories required")
    # The frozen scorer recomputes tool/argument correctness from model actions.
    scorer.assess(rows, events)
    return rows


def assess_facturation(policy, primary_rows, primary_results, broader, export_receipt_sha256):
    """Re-score supplied events only; provenance/numerical admission stay external."""
    if policy != prepare_policy():
        raise ValueError("Prospective stage policy changed")
    if not isinstance(export_receipt_sha256, str) or not re.fullmatch("[0-9a-f]{64}", export_receipt_sha256):
        raise ValueError("Selected exported-model receipt hash required")
    selected = selector()["select"](policy["primary_policy"], primary_rows, primary_results)
    if selected["selected_step"] == 0:
        raise ValueError("Untrained baseline is not a trained-stage candidate")
    if not isinstance(broader, dict) or set(broader) != {"development", "regression", "additional_controls"}:
        raise ValueError("All three complete broader suites required")
    scorer = selector()["verified_scorer"]()
    all_groups, subsets = {}, {}
    for phase, spec in (
        ("development", {"development": DEVELOPMENT_SHA}),
        ("regression", policy["regression"]["files"]),
        ("additional_controls", {"controls": FRESH_SHA}),
    ):
        suite = broader[phase]
        if (suite.get("export_receipt_sha256") != export_receipt_sha256
                or suite.get("selected_step") != selected["selected_step"]
                or set(suite.get("datasets", {})) != set(spec)):
            raise ValueError("Broader results must bind the selected export, step and every dataset")
        grouped = {app: ([], []) for app in ORDER[:3]}
        per_set = []
        for name, expected_sha in spec.items():
            part = suite["datasets"][name]
            events = part["events"]
            rows = dataset(part["source"], expected_sha, events, scorer)
            apps = set()
            for row, event in zip(rows, events):
                if phase == "development":
                    app = row["category"]
                elif phase == "additional_controls":
                    app = row["trusted_context"]["application"]
                else:
                    matches = [app for app in ORDER[:3] if app.replace("_", "-") in name]
                    if len(matches) != 1:
                        raise ValueError("Ambiguous regression application")
                    app = matches[0]
                    if row.get("trusted_context", {}).get("application", app) != app:
                        raise ValueError("Regression application mismatch")
                if app not in grouped:
                    raise ValueError("Unexpected application in frozen suite")
                grouped[app][0].append(row)
                grouped[app][1].append(event)
                apps.add(app)
            if phase == "regression":
                assessment = scorer.assess(rows, events)
                per_set.append({"dataset": name, "application": next(iter(apps)),
                                "assessment": assessment, "passed": passed(assessment)})
        expected_counts = (DEVELOPMENT_COUNTS if phase == "development" else
                           REGRESSION_COUNTS if phase == "regression" else
                           {app: 16 for app in ORDER[:3]})
        if {app: len(pair[0]) for app, pair in grouped.items()} != expected_counts:
            raise ValueError("Original per-application counts required")
        all_groups[phase] = {}
        for app, (rows, events) in grouped.items():
            assessment = scorer.assess(rows, events)
            all_groups[phase][app] = {"assessment": assessment, "passed": passed(assessment)}
        subsets[phase] = per_set
    gates = {
        app: all(groups[app]["passed"] for groups in all_groups.values())
             and all(s["passed"] for s in subsets["regression"] if s["application"] == app)
        for app in ORDER[:3]
    }
    return {
        "version": VERSION, "policy_sha256": digest(json.dumps(policy, sort_keys=True).encode()),
        "selected_step": selected["selected_step"], "export_receipt_sha256": export_receipt_sha256,
        "primary_selection": selected, "by_suite": all_groups,
        "regression_subsets": subsets["regression"], "broader_targets_by_application": gates,
        "focused_model_targets_passed": selected["selected_development_targets_passed"] and gates["facturation"],
        "retained_predecessor_applications": [],
        "untrained_application_diagnostics": {app: gates[app] for app in ORDER[1:3]},
        "applications_not_measured": list(ORDER[3:]),
        "model_provenance_independently_verified": False,
        "native_backend_security_verified": None, "integrated_behavior_verified": None,
        "latency_requirement_verified": None, "later_stage_retention_verified": False,
        "next_application_training_authorized": False, "model_accepted": False,
        "all_six_apps_accepted": False, "production_activation": False,
    }
