"""Synthetic selection fixtures never establish model accuracy or admission."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import select_facturation_argument_coverage_v2 as subject
from compare_saved_checkpoints import encode


def fixtures():
    rows = [{"id": f"validation-{i:03}", "category": "facturation",
             "language": "en_fr_unlabeled", "scenario_group": f"facturation-{i:03}",
             "messages": [{"role": "user", "content": f"Synthetic lookup{i}"}],
             "expected": {"tool": "lookup", "arguments": {"id": i}}}
            for i in range(133)]
    cases = {r["id"]: {k: deepcopy(r[k]) for k in ("id", "category", "language", "expected")} |
             {"action": deepcopy(r["expected"]), "tool_correct": True,
              "arguments_correct": True, "structured_valid": True} for r in rows}
    results = {step: deepcopy(cases) for step in subject.STEPS}
    policy = {"version": subject.VERSION, "application": "facturation", "rows": 133,
              "candidate_steps": list(subject.STEPS), "selection": subject.RANKING[:],
              "validation_loss_used_for_ranking": False,
              "evaluation_sha256": hashlib.sha256(encode(rows).encode()).hexdigest(),
              "baseline": {"candidate_step": 0, "source_checkpoint": 32,
                           "accepted": False, "fp32_sha256": "1" * 64},
              "regression_reference": {"checkpoint": 600, "fp32_sha256": "2" * 64}}
    return policy, rows, results


def fail(result, index, invalid=False):
    case = result[f"validation-{index:03}"]
    case["arguments_correct"] = False
    case["action"]["arguments"]["id"] = -1
    if invalid:
        case.update(structured_valid=False, tool_correct=False)


class CorrectiveSelectionTests(unittest.TestCase):
    def test_every_checkpoint_can_win_without_any_recorded_loss(self):
        for best in subject.STEPS:
            policy, rows, results = fixtures()
            for step, cases in results.items():
                if step != best:
                    fail(cases, 0)
            with self.subTest(best=best):
                selected = subject.select(policy, rows, results)
                self.assertEqual(selected["selected_step"], best)
                self.assertFalse(selected["validation_loss_used_for_ranking"])

    def test_valid_structure_breaks_action_tie_then_lowest_step(self):
        policy, rows, results = fixtures()
        for cases in results.values():
            fail(cases, 0)
        fail(results[0], 0, invalid=True)
        self.assertEqual(subject.select(policy, rows, results)["selected_step"], 64)

    def test_action_accuracy_precedes_structure(self):
        policy, rows, results = fixtures()
        for step, cases in results.items():
            fail(cases, 0, invalid=step == 256)
            if step != 256:
                fail(cases, 1)
        self.assertEqual(subject.select(policy, rows, results)["selected_step"], 256)

    def test_baseline_is_actual_parent_and_selection_never_grants_acceptance(self):
        policy, rows, results = fixtures()
        report = subject.select(policy, rows, results)
        self.assertEqual(report["selected_step"], 0)
        self.assertEqual(report["baseline_source_checkpoint"], 32)
        self.assertEqual(report["original_regression_reference"], 600)
        for name in ("model_accepted", "production_activation", "next_application_training_started"):
            self.assertFalse(report[name])
        self.assertNotIn("validation_macro_loss", str(report))

    def test_incomplete_extra_and_noninteger_candidate_keys_reject(self):
        for kind in ("missing", "extra", "boolean", "float"):
            policy, rows, results = fixtures()
            if kind == "missing":
                del results[192]
            elif kind == "extra":
                results[999] = deepcopy(results[0])
            else:
                baseline = results.pop(0)
                results[False if kind == "boolean" else 0.0] = baseline
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "Every scheduled"):
                subject.select(policy, rows, results)

    def test_incomplete_cases_changed_labels_and_false_cached_flags_reject(self):
        for kind in ("missing", "label", "flag", "invalid_pass"):
            policy, rows, results = fixtures()
            result = results[64]
            if kind == "missing":
                del result["validation-000"]
            elif kind == "label":
                result["validation-000"]["expected"]["arguments"]["id"] = 999
            elif kind == "flag":
                result["validation-000"]["arguments_correct"] = 1
            else:
                result["validation-000"]["structured_valid"] = False
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                subject.select(policy, rows, results)

    def test_policy_cannot_silently_change_ranking_or_schedule(self):
        mutations = [
            {"version": "old"}, {"application": "management_projet"},
            {"candidate_steps": [0, 64, 128, 256]},
            {"candidate_steps": [False, 64, 128, 192, 256]},
            {"selection": subject.RANKING + ["lowest loss"]},
            {"validation_loss_used_for_ranking": True},
            {"rows": 132}, {"rows": 133.0}]
        for mutation in mutations:
            policy, rows, results = fixtures()
            policy.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(ValueError, "policy"):
                subject.select(policy, rows, results)

    def test_unbound_wrong_or_accepted_parent_and_reference_reject(self):
        for target, change in (
                ("baseline", {"source_checkpoint": 600}),
                ("baseline", {"accepted": True}),
                ("baseline", {"candidate_step": False}),
                ("baseline", {"fp32_sha256": None}),
                ("baseline", {"fp32_sha256": "not-a-hash"}),
                ("regression_reference", {"checkpoint": 32}),
                ("regression_reference", {"fp32_sha256": "1" * 64})):
            policy, rows, results = fixtures()
            policy[target].update(change)
            with self.subTest(target=target, change=change), self.assertRaisesRegex(
                    ValueError, "parent or original reference"):
                subject.select(policy, rows, results)

    def test_changed_prompt_and_missing_or_mixed_scope_cannot_be_ranked(self):
        for kind in ("prompt", "scope", "size"):
            policy, rows, results = fixtures()
            if kind == "prompt":
                rows[0]["messages"][0]["content"] = "changed"
            elif kind == "scope":
                rows[0]["category"] = "held_out"
            else:
                rows.pop()
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                subject.select(policy, rows, results)

    def test_wrong_source_identity_is_rejected_before_scoring(self):
        policy, rows, results = fixtures()
        for name in subject.FROZEN:
            with self.subTest(source=name), patch.dict(subject.FROZEN, {name: "0" * 64}), \
                    self.assertRaisesRegex(ValueError, "Frozen scoring source"):
                subject.select(policy, rows, results)

    def test_critical_failure_cannot_beat_a_fully_eligible_candidate(self):
        policy, rows, results = fixtures()
        rows[0]["expected"]["tool"] = "prepare_change"
        for cases in results.values():
            cases["validation-000"]["expected"] = deepcopy(rows[0]["expected"])
            cases["validation-000"]["action"] = deepcopy(rows[0]["expected"])
        policy["evaluation_sha256"] = hashlib.sha256(encode(rows).encode()).hexdigest()
        fail(results[64], 0)
        for index in (1, 2):
            fail(results[128], index)
        for step in (0, 192, 256):
            for index in range(1, 6):
                fail(results[step], index)
        report = subject.select(policy, rows, results)
        self.assertEqual(report["selected_step"], 128)
        self.assertNotIn(64, report["eligible_development_steps"])
        self.assertTrue(report["selected_development_targets_passed"])

    def test_full_action_gate_remains_required_when_other_targets_pass(self):
        policy, rows, results = fixtures()
        for index in range(6):
            key = f"validation-{index:03}"
            rows[index]["expected"] = {"tool": "knowledge", "arguments": {"query": "workflow"}}
            for cases in results.values():
                cases[key]["expected"] = deepcopy(rows[index]["expected"])
                cases[key]["action"] = deepcopy(rows[index]["expected"])
            results[64][key].update(action={"tool": "lookup", "arguments": {}},
                                     tool_correct=False, arguments_correct=False)
        for index in range(6, 11):
            fail(results[64], index)
        policy["evaluation_sha256"] = hashlib.sha256(encode(rows).encode()).hexdigest()
        report = subject.select(policy, rows, results)
        candidate = next(r for r in report["candidates"] if r["step"] == 64)
        targets = candidate["development_targets"]
        self.assertFalse(targets["full_action_accuracy"])
        self.assertTrue(all(value for name, value in targets.items()
                            if name != "full_action_accuracy"))
        self.assertNotIn(64, report["eligible_development_steps"])

    def test_no_eligible_candidate_still_reports_failure_without_acceptance(self):
        policy, rows, results = fixtures()
        for cases in results.values():
            for index in range(12):
                fail(cases, index)
        report = subject.select(policy, rows, results)
        self.assertEqual(report["selected_step"], 0)
        self.assertFalse(report["selected_development_targets_passed"])
        self.assertEqual(report["eligible_development_steps"], [])
        self.assertFalse(report["model_accepted"])

    def test_malformed_policy_and_reference_shapes_reject_safely(self):
        policy, rows, results = fixtures()
        for inputs in ((None, rows, results), (policy, None, results), (policy, rows, None)):
            with self.subTest(inputs=type(inputs[0])), self.assertRaises(ValueError):
                subject.select(*inputs)
        for key, value in (("baseline", None), ("regression_reference", [])):
            malformed = deepcopy(policy)
            malformed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                subject.select(malformed, rows, results)

    def test_unbound_current_policy_cannot_be_used_for_selection(self):
        policy, rows, results = fixtures()
        policy["baseline"]["fp32_sha256"] = None
        policy["regression_reference"]["fp32_sha256"] = None
        with self.assertRaisesRegex(ValueError, "parent or original reference"):
            subject.select(policy, rows, results)

    def test_saved_english_and_french_clarification_wording_uses_frozen_scorer(self):
        examples = [
            ("en", "Please specify the document, customer, product, or reporting period (including the year)."),
            ("fr", "Précisez le document, le client, le produit ou la période recherchée (avec l’année)."),
        ]
        for language, message in examples:
            policy, rows, results = fixtures()
            rows[0]["expected"] = {"tool": "clarify", "arguments": {
                "reason": "missing_details", "language": language}}
            for cases in results.values():
                case = cases["validation-000"]
                case["expected"] = deepcopy(rows[0]["expected"])
                case["action"] = {"tool": "clarify", "message": message}
            policy["evaluation_sha256"] = hashlib.sha256(encode(rows).encode()).hexdigest()
            with self.subTest(language=language):
                report = subject.select(policy, rows, results)
                self.assertTrue(report["selected_development_targets_passed"])
                self.assertTrue(all(c["action_matches"] == 133 for c in report["candidates"]))


    def test_inputs_are_immutable_and_result_order_does_not_change_ranking(self):
        policy, rows, results = fixtures()
        before = deepcopy((policy, rows, results))
        first = subject.select(policy, rows, results)
        second = subject.select(policy, rows, dict(reversed(list(results.items()))))
        self.assertEqual(first, second)
        self.assertEqual((policy, rows, results), before)

    def test_frozen_default_argument_normalization_is_preserved(self):
        policy, rows, results = fixtures()
        for cases in results.values():
            cases["validation-000"]["action"]["arguments"]["offset"] = 0
        report = subject.select(policy, rows, results)
        self.assertTrue(all(row["action_matches"] == 133 for row in report["candidates"]))


if __name__ == "__main__":
    unittest.main()
