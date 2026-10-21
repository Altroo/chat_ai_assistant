"""Real-baseline replay and synthetic candidate guards, never predicted accuracy."""
from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import select_qwen35_4b_pilot_v1 as subject


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reference = subject.references()
        cls.rows = [json.loads(line) for line in reference["facturation_primary_v1.eval.jsonl"].splitlines()]
        cls.baseline = json.loads(reference["qwen35_4b_primary_baseline_v1.json"])
        cls.cached = {case["id"]: case for case in cls.baseline["cases"]}
        cls.clarify = staticmethod(runpy.run_path(str(ROOT / "training/references/clarifications_v1.py"))["clarification_message"])
        cls.ordinary = [row["id"] for row in cls.rows if row["expected"]["tool"]
                        not in ("clarify", "knowledge", "prepare_change")]
        cls.critical = next(row["id"] for row in cls.rows if row["expected"]["tool"] == "clarify")

    def fixtures(self, perfect=False):
        candidates = {step: deepcopy(self.cached) for step in subject.STEPS}
        if perfect:
            for step in subject.STEPS[1:]:
                candidates[step] = self.perfect()
        return subject.prepare_policy(), deepcopy(self.rows), candidates

    def perfect(self):
        cases = {}
        for row in self.rows:
            expected = deepcopy(row["expected"])
            action = deepcopy(expected)
            if expected["tool"] == "clarify":
                action = {"tool": "clarify", "message": self.clarify(**expected["arguments"])}
            cases[row["id"]] = {name: deepcopy(row[name]) for name in
                                ("id", "category", "language", "expected")}
            cases[row["id"]].update(action=action, tool_correct=True,
                                    arguments_correct=True, structured_valid=True)
        return cases

    def fail(self, cases, key, invalid=False):
        case = cases[key]
        case["arguments_correct"] = False
        if case["expected"]["tool"] == "clarify":
            case["action"]["message"] = "Wrong clarification"
        else:
            case["action"]["arguments"]["_fixture_wrong"] = True
        if invalid:
            case.update(structured_valid=False, tool_correct=False)

    def test_actual_baseline_replay_stays_rejected(self):
        policy, rows, results = self.fixtures()
        report = subject.select(policy, rows, results)
        self.assertEqual(report["selected_step"], 0)
        self.assertEqual(report["eligible_development_steps"], [])
        for candidate in report["candidates"]:
            self.assertEqual(candidate["action_matches"], 77)
            self.assertEqual(candidate["eligible_exact_arguments"], {"passed": 71, "count": 111, "percent": 63.96})
            self.assertEqual(candidate["clarification_actions"], 0)
            self.assertEqual(candidate["critical_actions"], 6)
        self.assertFalse(report["model_accepted"])

    def test_each_scheduled_trained_candidate_can_win(self):
        for best in subject.STEPS[1:]:
            policy, rows, results = self.fixtures()
            results[best] = self.perfect()
            with self.subTest(best=best):
                report = subject.select(policy, rows, results)
                self.assertEqual(report["selected_step"], best)
                self.assertEqual(report["eligible_development_steps"], [best])
                self.assertTrue(report["selected_development_targets_passed"])
                self.assertFalse(report["model_accepted"])
                self.assertFalse(report["production_activation"])
                self.assertFalse(report["next_application_training_started"])

    def test_critical_failure_cannot_beat_eligible_candidate(self):
        policy, rows, results = self.fixtures()
        results[158] = self.perfect()
        self.fail(results[158], self.critical)
        results[316] = self.perfect()
        for key in self.ordinary[:3]:
            self.fail(results[316], key)
        report = subject.select(policy, rows, results)
        self.assertEqual(report["selected_step"], 316)
        self.assertNotIn(158, report["eligible_development_steps"])

    def test_structure_breaks_action_tie_then_lowest_step(self):
        policy, rows, results = self.fixtures(perfect=True)
        for step in subject.STEPS[1:]:
            self.fail(results[step], self.ordinary[0], invalid=step == 158)
        report = subject.select(policy, rows, results)
        self.assertEqual(report["selected_step"], 316)

    def test_all_candidates_and_all_cases_are_mandatory(self):
        for mutation in ("candidate", "extra", "boolean", "case"):
            policy, rows, results = self.fixtures()
            if mutation == "candidate":
                del results[474]
            elif mutation == "extra":
                results[999] = deepcopy(self.cached)
            elif mutation == "boolean":
                results[False] = results.pop(0)
            else:
                del results[158][self.ordinary[0]]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                subject.select(policy, rows, results)

    def test_baseline_labels_flags_and_primary_inputs_cannot_change(self):
        for mutation in ("baseline", "label", "flag", "input", "policy"):
            policy, rows, results = self.fixtures(perfect=True)
            if mutation == "baseline":
                results[0] = self.perfect()
            elif mutation == "label":
                results[158][self.ordinary[0]]["expected"]["arguments"]["_changed"] = True
            elif mutation == "flag":
                results[158][self.ordinary[0]]["arguments_correct"] = 1
            elif mutation == "input":
                rows[0]["messages"][-1]["content"] += " Changed input"
            else:
                policy["selection"] += ["lowest loss"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                subject.select(policy, rows, results)

    def test_candidate_order_and_extra_loss_fields_do_not_affect_selection(self):
        policy, rows, results = self.fixtures(perfect=True)
        before = deepcopy((policy, rows, results))
        expected = subject.select(policy, rows, results)
        for step in subject.STEPS[1:]:
            for case in results[step].values():
                case["validation_macro_loss"] = -step
        actual = subject.select(policy, rows, dict(reversed(list(results.items()))))
        self.assertEqual(expected, actual)
        self.assertFalse(actual["validation_loss_used_for_ranking"])
        self.assertEqual(before[0], policy)
        self.assertEqual(before[1], rows)

    def test_changed_scorer_bytes_reject_before_execution(self):
        original = Path.read_bytes
        helper = Path(subject.__file__).with_name("select_facturation_argument_coverage_v2.py")
        def altered(path):
            return b'raise RuntimeError("unverified source executed")' if path == helper else original(path)
        with patch.object(Path, "read_bytes", altered):
            with self.assertRaisesRegex(ValueError, "Frozen scorer loader changed"):
                subject.verified_scorer()

    def test_shadowed_module_cannot_supply_the_scorer(self):
        def unverified():
            raise RuntimeError("shadow module executed")
        shadow = SimpleNamespace(frozen_scorer=unverified)
        with patch.dict(sys.modules, {"select_facturation_argument_coverage_v2": shadow}):
            policy, rows, results = self.fixtures()
            report = subject.select(policy, rows, results)
            self.assertEqual(report["selected_step"], 0)
            self.assertEqual(report["candidates"][0]["action_matches"], 77)

    def test_freeze_copies_exact_references_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "comparison"
            policy = subject.freeze(output)
            self.assertEqual(json.loads((output / "policy.json").read_text()), policy)
            for name, raw in subject.references().items():
                self.assertEqual((output / name).read_bytes(), raw)
            with self.assertRaises(ValueError):
                subject.freeze(output)


if __name__ == "__main__":
    unittest.main()
