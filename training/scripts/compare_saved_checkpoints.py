"""Compare saved checkpoints using validation actions, never held-out outcomes."""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from prepare_shared_v5r5 import recover_rows, rebalance
from build_dialogue_v1 import reframe, encode
from model_acceptance import assess

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def prepare(report_path, output):
    """Freeze all validation inputs and selection rules before model inference."""
    if output.exists():
        raise ValueError("Never overwrite a checkpoint comparison")
    folders = [ROOT / "training/datasets" / v for v in
               ("shared-v5r3-en-fr", "shared-v5r4-en-fr", "shared-v5r5-en-fr")]
    manifests = [load(p / "manifest.json") for p in folders]
    for p, m in zip(folders, manifests):
        if digest(p / "valid.jsonl") != m["files"]["valid.jsonl"]:
            raise ValueError("Validation data changed")
    if (digest(folders[0] / "manifest.json") != manifests[1]["parent_manifest_sha256"]
            or digest(folders[1] / "manifest.json") != manifests[2]["parent_manifest_sha256"]):
        raise ValueError("Parent provenance changed")
    original, prior, rows = [
        [json.loads(line) for line in (p / "valid.jsonl").read_text().splitlines()]
        for p in folders]
    augmentation = manifests[1]["augmentation"]["valid"]
    reconstructed, _ = rebalance(recover_rows(original, prior, augmentation))
    reconstructed = [{**r, "messages": reframe(r["messages"])} for r in reconstructed]
    if reconstructed != rows:
        raise ValueError("Reconstructed validation differs from trained validation")
    groups = list(range(len(original))) + [a["source_index"] for a in augmentation]
    if len(groups) != len(rows):
        raise ValueError("Scenario provenance incomplete")
    training = load(report_path)
    if training["validation_sha256"] != digest(folders[2] / "valid.jsonl"):
        raise ValueError("Training used a different validation split")
    history = {r["step"]: r["loss"]["macro"] for r in training["validation_history"]}
    # Only saved interval checkpoints; exclude baseline and unscheduled final.
    candidates = sorted((s for s in history if s > 0 and s % 300 == 0),
                        key=lambda s: (history[s], s))[:3]
    if candidates != [600, 1200, 1800] or not all(math.isfinite(history[s]) for s in candidates):
        raise ValueError("Unexpected saved-checkpoint shortlist")
    evaluations = []
    for index, (r, group) in enumerate(zip(rows, groups)):
        final = r["messages"][-1]
        if final["role"] != "assistant" or len(final["tool_calls"]) != 1:
            raise ValueError("Validation row has no unique target")
        function = final["tool_calls"][0]["function"]
        evaluations.append({
            "id": f"validation-{index:03}",
            "category": r["application"],
            "language": "en_fr_unlabeled",
            "scenario_group": f"{r['application']}-{group:03}",
            "messages": r["messages"][:-1],
            "offered_tool_schemas": [t for t in r["tools"] if t["function"]["name"] != "clarify"],
            "expected": {"tool": function["name"], "arguments": function["arguments"]},
        })
    raw = encode(evaluations)
    policy = {
        "version": "shared-v5r5-functional-validation-v1",
        "source_validation_sha256": digest(folders[2] / "valid.jsonl"),
        "training_report_sha256": digest(report_path),
        "evaluation_sha256": hashlib.sha256(raw.encode()).hexdigest(),
        "script_sha256": digest(Path(__file__)),
        "rows": len(rows), "underlying_scenarios": len(original),
        "candidates": [{"step": s, "validation_macro_loss": history[s]} for s in candidates],
        "selection": ["highest application-macro action-match fraction",
                      "highest application-macro valid-structure fraction",
                      "lowest recorded validation macro loss", "lowest checkpoint step"],
        "scoring": "Unchanged evaluate_snapshot.py action matching, including clarification reason/language, knowledge nonempty query and existing optional-default normalization. Invalid outputs fail.",
        "evaluator_sha256": digest(ROOT / "training/scripts/evaluate_snapshot.py"),
        "acceptance_sha256": digest(ROOT / "training/scripts/model_acceptance.py"),
        "limitations": [
            "275 validation rows include 53 neutral-history variants of 222 scenarios.",
            "Application averaging does not remove correlated variants; scenario-grouped scores are reported separately.",
            "Source rows lack per-language labels; no inferred per-language accuracy is claimed.",
            "Selection is validation only, not acceptance. The 438 frozen regressions are repeatedly inspected and are not fresh blind certification.",
            "No business tools execute. No model activation follows selection.",
        ],
    }
    output.mkdir(parents=True)
    (output / "validation.eval.jsonl").write_text(raw)
    (output / "policy.json").write_text(json.dumps(policy, indent=2) + "\n")
    return policy


def score(rows, cases):
    """Use exact fractions for deterministic selection and reject incomplete runs."""
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids) or len(cases) != len(ids) or set(cases) != set(ids):
        raise ValueError("Incomplete or duplicate validation results")
    assessed = assess(rows, [cases[i] for i in ids])
    failed = {item["id"] for item in assessed["failures"]}
    by_app, by_group = defaultdict(list), defaultdict(list)
    for row in rows:
        case = cases[row["id"]]
        if case["expected"] != row["expected"]:
            raise ValueError("Result target changed")
        if case["category"] != row["category"] or case["language"] != row["language"]:
            raise ValueError("Result metadata changed")
        for key in ("tool_correct", "arguments_correct", "structured_valid"):
            if not isinstance(case[key], bool):
                raise ValueError("Non-boolean result")
        action = case.get("action", {})
        actual_tool = case["structured_valid"] and action.get("tool") == row["expected"]["tool"]
        actual_match = row["id"] not in failed
        if case["tool_correct"] != actual_tool or case["arguments_correct"] != actual_match:
            raise ValueError("Cached correctness disagrees with actual action")
        by_app[row["category"]].append(case)
        by_group[row["scenario_group"]].append(case)
    macro = sum((Fraction(sum(c["arguments_correct"] for c in v), len(v))
                 for v in by_app.values()), Fraction()) / len(by_app)
    valid = sum((Fraction(sum(c["structured_valid"] for c in v), len(v))
                 for v in by_app.values()), Fraction()) / len(by_app)
    grouped = defaultdict(list)
    for name, values in by_group.items():
        app = name.rsplit("-", 1)[0]
        grouped[app].append(Fraction(sum(c["arguments_correct"] for c in values), len(values)))
    grouped_macro = sum((sum(v, Fraction()) / len(v) for v in grouped.values()), Fraction()) / len(grouped)
    report = {
        "count": len(rows),
        "action_matches": sum(c["arguments_correct"] for c in cases.values()),
        "application_macro_action_percent": float(macro * 100),
        "application_macro_valid_percent": float(valid * 100),
        "scenario_grouped_application_macro_action_percent": float(grouped_macro * 100),
        "by_application": {app: {"count": len(v), "action_matches": sum(c["arguments_correct"] for c in v),
                                  "valid_structures": sum(c["structured_valid"] for c in v)}
                           for app, v in by_app.items()},
    }
    return macro, valid, report


def select(policy, rows, results):
    if hashlib.sha256(encode(rows).encode()).hexdigest() != policy["evaluation_sha256"]:
        raise ValueError("Validation rows differ from frozen policy")
    steps = {c["step"] for c in policy["candidates"]}
    if set(results) != steps:
        raise ValueError("Every shortlisted candidate must complete")
    ranked, reports = [], []
    for candidate in policy["candidates"]:
        step = candidate["step"]
        action, valid, report = score(rows, results[step])
        ranked.append((action, valid, -candidate["validation_macro_loss"], -step))
        reports.append({"step": step, **report})
    return {"selected_step": -max(ranked)[-1], "candidates": reports,
            "status": "VALIDATION SELECTION ONLY; ACCEPTANCE NOT ESTABLISHED"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--training-report", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(prepare(args.training_report, args.output), indent=2))
