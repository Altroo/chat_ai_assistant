"""Prospective Facturation selection without validation-loss tie breaking.

Only completed, fixed development results are consumed. The old selector,
scorer and acceptance gates are unchanged. Selection never authorizes training,
production activation, or another application's rollout.
"""
import hashlib
import ast
from collections import defaultdict
from fractions import Fraction
from types import SimpleNamespace
import json
from pathlib import Path
import re

VERSION = "facturation-entity-pilot-v2-functional-selection"
STEPS = (0, 176, 352, 528, 704)
ROWS = 133
RANKING = ["all primary Facturation development targets met",
           "highest Facturation development full-action fraction",
           "highest Facturation development valid-structure fraction",
           "lowest checkpoint step"]
FROZEN = {
    "compare_saved_checkpoints.py":
        "d5952e6aa77a0bc23319f046fe83f870bc527d58359b17aa51a6b0ef774bedd1",
    "model_acceptance.py":
        "c9efde5b48a32d2900ed581477e65e677865a875b08400fe67fe70a521fcaebc",
    "../references/clarifications_v1.py":
        "e5cb817facdb8e440538cc0ed9b252ff127f6d8e470bb630574e5530e7a31a7d",
}


def frozen_scorer():
    """Load pinned scoring and historical clarification text in isolated globals."""
    folder = Path(__file__).resolve().parent
    sources = {}
    for name, expected in FROZEN.items():
        raw = (folder / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Frozen scoring source changed")
        sources[name] = raw
    frozen_name = "../references/clarifications_v1.py"
    clarifications = {"__name__": "frozen_corrective_clarifications"}
    exec(compile(sources[frozen_name], str(folder / frozen_name), "exec"), clarifications)
    acceptance_path = folder / "model_acceptance.py"
    acceptance_tree = ast.parse(sources["model_acceptance.py"])
    removed = [node for node in acceptance_tree.body
               if isinstance(node, ast.ImportFrom)
               and node.module == "chat_ai_assistant.clarifications"]
    if len(removed) != 1:
        raise ValueError("Frozen clarification import structure changed")
    acceptance_tree.body = [node for node in acceptance_tree.body if node not in removed]
    acceptance = {"__file__": str(acceptance_path), "__name__": "frozen_corrective_acceptance",
                  "clarification_message": clarifications["clarification_message"]}
    exec(compile(acceptance_tree, str(acceptance_path), "exec"), acceptance)
    score_tree = ast.parse(sources["compare_saved_checkpoints.py"])
    functions = [node for node in score_tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == "score"]
    if len(functions) != 1:
        raise ValueError("Frozen scoring function structure changed")
    namespace = {"assess": acceptance["assess"], "Fraction": Fraction,
                 "defaultdict": defaultdict}
    exec(compile(ast.Module(body=functions, type_ignores=[]), "frozen_corrective_score",
                 "exec"), namespace)

    def encode(rows):
        return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)

    return SimpleNamespace(score=namespace["score"], assess=acceptance["assess"], encode=encode)


def select(policy, rows, results):
    """Prioritize primary gates, then exact fractions; never invent losses.

    Fingerprint declarations are checked, not independently attested here.
    Actual artifact provenance belongs to the separate numerical admission.
    """
    if not isinstance(policy, dict) or not isinstance(rows, list) or not isinstance(results, dict):
        raise ValueError("Policy, development rows and results must have valid shapes")
    if (policy.get("version") != VERSION or policy.get("application") != "facturation"
            or policy.get("candidate_steps") != list(STEPS)
            or any(type(step) is not int for step in policy["candidate_steps"])
            or policy.get("rows") != ROWS or type(policy["rows"]) is not int
            or policy.get("selection") != RANKING
            or policy.get("validation_loss_used_for_ranking") is not False):
        raise ValueError("Unexpected prospective selection policy")
    baseline = policy.get("baseline", {})
    reference = policy.get("regression_reference", {})
    if not isinstance(baseline, dict) or not isinstance(reference, dict):
        raise ValueError("Experimental parent or original reference is unbound")
    if (baseline.get("candidate_step") != 0 or type(baseline["candidate_step"]) is not int
            or baseline.get("source_checkpoint") != 2048
            or type(baseline["source_checkpoint"]) is not int
            or baseline.get("accepted") is not False
            or reference.get("checkpoint") != 600 or type(reference["checkpoint"]) is not int
            or any(not isinstance(v, str) or re.fullmatch("[0-9a-f]{64}", v) is None
                   for v in (baseline.get("fp32_sha256"), reference.get("fp32_sha256")))
            or baseline["fp32_sha256"] == reference["fp32_sha256"]):
        raise ValueError("Experimental parent or original reference is unbound")
    if len(rows) != ROWS or any(not isinstance(row, dict) or row.get("category") != "facturation" for row in rows):
        raise ValueError("All133 frozen Facturation development cases are required")
    if set(results) != set(STEPS) or any(type(step) is not int for step in results):
        raise ValueError("Every scheduled development candidate must complete")
    scorer = frozen_scorer()
    if hashlib.sha256(scorer.encode(rows).encode()).hexdigest() != policy.get("evaluation_sha256"):
        raise ValueError("Development inputs differ from the prospective frozen policy")
    ranked, reports = [], []
    for step in STEPS:
        action, valid, report = scorer.score(rows, results[step])
        assessment = scorer.assess(rows, [results[step][row["id"]] for row in rows])
        targets = dict(assessment["targets"])
        targets["full_action_accuracy"] = 100 * report["action_matches"] >= 95 * ROWS
        eligible = all(targets.values())
        ranked.append((eligible, action, valid, -step))
        reports.append({"step": step, **report, "development_targets": targets,
                        "development_targets_passed": eligible})
    policy_sha256 = hashlib.sha256(json.dumps(
        policy, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {
        "version": VERSION, "selected_step": -max(ranked)[-1],
        "baseline_source_checkpoint": 2048, "original_regression_reference": 600,
        "candidates": reports, "policy_sha256": policy_sha256,
        "validation_loss_used_for_ranking": False,
        "eligible_development_steps": [r["step"] for r in reports
                                       if r["development_targets_passed"]],
        "selected_development_targets_passed": any(
            r["development_targets_passed"] for r in reports),
        "status": "DEVELOPMENT SELECTION ONLY; ACCEPTANCE NOT ESTABLISHED",
        "model_accepted": False, "production_activation": False,
        "next_application_training_started": False,
    }
