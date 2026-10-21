"""Select all declared 4B primary candidates with the unchanged frozen scorer.

Preparation and scoring only. This never loads a model, changes labels, or grants
application acceptance, production activation, or next-application training.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = "qwen35-4b-pilot-primary-selection-v1"
STEPS = (0, 158, 316, 474, 632)
RANKING = [
    "all primary Facturation development targets met",
    "highest Facturation development full-action fraction",
    "highest Facturation development valid-structure fraction",
    "lowest checkpoint step",
]
REFERENCES = {
    "facturation_primary_v1.eval.jsonl": "ac1b70e353fc9ec632b21afd4d69de9743db24e07e865cb9f4b804d22b32ce58",
    "qwen35_4b_primary_baseline_v1.json": "aefc7ae52ae04243d5b4afe42ca11e78e979d7cbdba4d1dbc36edf65ea9724fd",
    "qwen35_4b_pilot_policy_v1.json": "5e53d0d7bc1b76120478b592b8c573e447ccf448c5ddfa86039b88114af9ebda",
}
SCORER_HELPER_SHA = "574165322a5fc6312244ddb0b86f33621ad903587bd432084950a9494cd603b8"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def references():
    result = {}
    for name, expected in REFERENCES.items():
        raw = (ROOT / "training/references" / name).read_bytes()
        if digest(raw) != expected:
            raise ValueError("Frozen 4B comparison reference changed: " + name)
        result[name] = raw
    helper = Path(__file__).with_name("select_facturation_argument_coverage_v2.py")
    if digest(helper.read_bytes()) != SCORER_HELPER_SHA:
        raise ValueError("Frozen scorer loader changed")
    return result


def verified_scorer():
    helper = Path(__file__).with_name("select_facturation_argument_coverage_v2.py")
    raw = helper.read_bytes()
    if digest(raw) != SCORER_HELPER_SHA:
        raise ValueError("Frozen scorer loader changed")
    namespace = {"__name__": "qwen35_4b_verified_scorer", "__file__": str(helper)}
    exec(compile(raw, str(helper), "exec"), namespace)
    return namespace["frozen_scorer"]()


def prepare_policy():
    raw = references()
    recipe = json.loads(raw["qwen35_4b_pilot_policy_v1.json"])
    if recipe["functional_candidates"] != list(STEPS):
        raise ValueError("Predeclared candidate schedule changed")
    baseline = json.loads(raw["qwen35_4b_primary_baseline_v1.json"])
    if (baseline["source_result_sha256"] != recipe["cached_base_result_sha256"]
            or baseline["revision"] != recipe["base_revision"]
            or baseline["model_id"] != "Qwen/Qwen3.5-4B"):
        raise ValueError("Actual baseline and training base are not coupled")
    return {
        "version": VERSION, "application": "facturation", "rows": 133,
        "candidate_steps": list(STEPS), "selection": RANKING[:],
        "primary_sha256": REFERENCES["facturation_primary_v1.eval.jsonl"],
        "cached_baseline_sha256": REFERENCES["qwen35_4b_primary_baseline_v1.json"],
        "source_baseline_result_sha256": baseline["source_result_sha256"],
        "training_policy_sha256": REFERENCES["qwen35_4b_pilot_policy_v1.json"],
        "selector_sha256": digest(Path(__file__).read_bytes()),
        "frozen_scorer_loader_sha256": SCORER_HELPER_SHA,
        "validation_loss_used_for_ranking": False,
        "broader_checks_required": [275, 438, 48],
        "limitations": [
            "Previously inspected correlated development cases, not new blind certification.",
            "A primary pass is necessary and does not establish broader or native-security acceptance.",
            "Actual completed-training, model/adapter/export/runtime and worker evidence is required separately.",
            "All declared candidates must complete; invalid model outputs remain failures.",
        ],
    }


def select(policy, rows, results):
    if not isinstance(policy, dict) or not isinstance(rows, list) or not isinstance(results, dict):
        raise ValueError("Policy, primary rows and candidate results must have valid shapes")
    if policy != prepare_policy():
        raise ValueError("Frozen 4B comparison policy changed")
    scorer = verified_scorer()
    if (len(rows) != 133 or any(r.get("category") != "facturation" for r in rows)
            or digest(scorer.encode(rows).encode()) != policy["primary_sha256"]):
        raise ValueError("All 133 unchanged Facturation primary inputs are required")
    if set(results) != set(STEPS) or any(type(step) is not int for step in results):
        raise ValueError("Every predeclared candidate must complete")
    baseline = json.loads(references()["qwen35_4b_primary_baseline_v1.json"])
    cached = {case["id"]: case for case in baseline["cases"]}
    if len(cached) != 133 or results[0] != cached:
        raise ValueError("Logical zero must reuse the exact actual untrained baseline")
    reports, ranking = [], []
    for step in STEPS:
        action, valid, summary = scorer.score(rows, results[step])
        assessed = scorer.assess(rows, [results[step][row["id"]] for row in rows])
        targets = dict(assessed["targets"])
        targets["full_action_accuracy"] = 100 * summary["action_matches"] >= 95 * len(rows)
        eligible = all(targets.values())
        ranking.append((eligible, action, valid, -step))
        reports.append({
            "step": step, **summary, "development_targets": targets,
            "development_targets_passed": eligible,
            "eligible_exact_arguments": assessed["metrics"]["exact_arguments"],
            "clarification_actions": assessed["clarifications"]["counts"]["action_matches"],
            "critical_actions": assessed["critical_model_cases"]["counts"]["action_matches"],
        })
    return {
        "version": VERSION, "selected_step": -max(ranking)[-1], "candidates": reports,
        "eligible_development_steps": [r["step"] for r in reports if r["development_targets_passed"]],
        "selected_development_targets_passed": any(r["development_targets_passed"] for r in reports),
        "policy_sha256": digest(json.dumps(policy, sort_keys=True, separators=(",", ":")).encode()),
        "baseline_reuse": "Actual untrained 4B responses, unchanged; no new inference",
        "validation_loss_used_for_ranking": False,
        "status": "PRIMARY DEVELOPMENT SELECTION ONLY; ACCEPTANCE NOT ESTABLISHED",
        "model_accepted": False, "production_activation": False,
        "next_application_training_started": False,
    }


def freeze(output):
    if output.exists() or not output.parent.is_dir():
        raise ValueError("New isolated comparison directory required")
    policy = prepare_policy()
    raw = references()
    output.mkdir()
    (output / "policy.json").write_text(json.dumps(policy, indent=2) + "\n")
    for name, payload in raw.items():
        (output / name).write_bytes(payload)
    return policy


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.output), indent=2))
