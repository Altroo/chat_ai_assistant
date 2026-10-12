"""Functional checkpoint selection cannot use missing or changed validation results."""
from copy import deepcopy
from pathlib import Path
import sys
import hashlib
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_saved_checkpoints import score, select, encode
from model_acceptance import clarification_message


def fixtures():
    rows = [{"id": str(i), "category": app, "language": "en_fr_unlabeled",
             "scenario_group": f"{app}-{group}", "expected": {"tool": "lookup", "arguments": {"id": i}}}
            for i, (app, group) in enumerate([("a", 0), ("a", 0), ("a", 1), ("b", 2)])]
    cases = {r["id"]: {k: r[k] for k in ("expected", "category", "language")} |
             {"id": r["id"], "action": {"tool": "lookup", "arguments": {"id": int(r["id"])}},
              "tool_correct": True, "arguments_correct": True, "structured_valid": True}
             for r in rows}
    policy = {"candidates": [{"step": 600, "validation_macro_loss": .07},
                              {"step": 1200, "validation_macro_loss": .08},
                              {"step": 1800, "validation_macro_loss": .09}]}
    policy["evaluation_sha256"] = hashlib.sha256(encode(rows).encode()).hexdigest()
    return rows, cases, policy


class FunctionalSelectionTests(unittest.TestCase):
    def test_action_accuracy_wins_over_loss_and_application_imbalance(self):
        rows, cases, policy = fixtures()
        results = {step: deepcopy(cases) for step in (600, 1200, 1800)}
        # Missing the smaller application is worse than one failure in the larger.
        results[600]["3"]["arguments_correct"] = False
        results[600]["3"]["action"]["arguments"]["id"] = 99
        results[1200]["0"]["arguments_correct"] = False
        results[1200]["0"]["action"]["arguments"]["id"] = 99
        results[1800]["0"]["arguments_correct"] = False
        results[1800]["0"]["action"]["arguments"]["id"] = 99
        results[1800]["1"]["arguments_correct"] = False
        results[1800]["1"]["action"]["arguments"]["id"] = 99
        self.assertEqual(select(policy, rows, results)["selected_step"], 1200)

    def test_validity_breaks_action_tie_before_loss(self):
        rows, cases, policy = fixtures()
        results = {step: deepcopy(cases) for step in (600, 1200, 1800)}
        for result in results.values():
            result["0"]["arguments_correct"] = False
            result["0"]["action"]["arguments"]["id"] = 99
        results[600]["0"].update(structured_valid=False, tool_correct=False)
        self.assertEqual(select(policy, rows, results)["selected_step"], 1200)

    def test_loss_then_step_break_final_ties(self):
        rows, cases, policy = fixtures()
        results = {step: deepcopy(cases) for step in (600, 1200, 1800)}
        self.assertEqual(select(policy, rows, results)["selected_step"], 600)
        for candidate in policy["candidates"]:
            candidate["validation_macro_loss"] = .1
        self.assertEqual(select(policy, rows, results)["selected_step"], 600)

    def test_missing_extra_changed_targets_and_nonboolean_results_reject(self):
        rows, cases, policy = fixtures()
        for mutation in ("missing", "extra", "target", "flag", "invalid_pass"):
            bad = deepcopy(cases)
            if mutation == "missing": del bad["0"]
            if mutation == "extra": bad["extra"] = deepcopy(bad["0"])
            if mutation == "target": bad["0"]["expected"]["arguments"]["id"] = 99
            if mutation == "flag": bad["0"]["arguments_correct"] = 1
            if mutation == "invalid_pass": bad["0"]["structured_valid"] = False
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                score(rows, bad)
        with self.assertRaises(ValueError):
            select(policy, rows, {600: cases})

    def test_grouped_score_does_not_count_a_variant_as_independent(self):
        rows, cases, _ = fixtures()
        cases["0"]["arguments_correct"] = False
        cases["1"]["arguments_correct"] = False
        cases["0"]["action"]["arguments"]["id"] = 99
        cases["1"]["action"]["arguments"]["id"] = 99
        action, valid, report = score(rows, cases)
        self.assertAlmostEqual(float(action), 2 / 3)
        self.assertEqual(report["scenario_grouped_application_macro_action_percent"], 75)
        self.assertEqual(valid, 1)


    def test_wrong_action_cannot_reuse_success_flags(self):
        for action in ({"tool": "prepare_change", "arguments": {"id": 0}},
                       {"tool": "lookup", "arguments": {"id": 99}}):
            rows, cases, _ = fixtures()
            cases["0"]["action"] = action
            with self.subTest(action=action), self.assertRaises(ValueError):
                score(rows, cases)

    def test_clarification_reason_language_and_knowledge_scoring(self):
        rows, cases, _ = fixtures()
        rows[0]["expected"] = {"tool": "clarify", "arguments": {"reason": "missing_details", "language": "en"}}
        cases["0"]["expected"] = deepcopy(rows[0]["expected"])
        cases["0"]["action"] = {"tool": "clarify", "message": clarification_message("missing_details", "en")}
        score(rows, cases)
        for reason, language in (("unsupported", "en"), ("missing_details", "fr")):
            cases["0"]["action"]["message"] = clarification_message(reason, language)
            with self.assertRaises(ValueError):
                score(rows, cases)
        rows[0]["expected"] = {"tool": "knowledge", "arguments": {"query": "workflow"}}
        cases["0"]["expected"] = deepcopy(rows[0]["expected"])
        cases["0"]["action"] = {"tool": "knowledge", "arguments": {"query": "another nonempty query"}}
        score(rows, cases)
        cases["0"]["action"]["arguments"]["query"] = ""
        with self.assertRaises(ValueError):
            score(rows, cases)

    def test_changed_prompt_rejected_by_frozen_policy(self):
        rows, cases, policy = fixtures()
        rows[0]["messages"] = [{"role": "user", "content": "changed"}]
        with self.assertRaises(ValueError):
            select(policy, rows, {step: deepcopy(cases) for step in (600, 1200, 1800)})


if __name__ == "__main__":
    unittest.main()
