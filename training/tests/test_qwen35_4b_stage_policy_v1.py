"""Synthetic policy/control tests, not measured model accuracy."""
from copy import deepcopy
import json
from pathlib import Path
import runpy
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import qwen35_4b_stage_policy_v1 as subject


class StagePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = subject.prepare_policy()
        cls.primary = [json.loads(line) for line in
                       (ROOT / "training/references/facturation_primary_v1.eval.jsonl").read_bytes().splitlines()]
        baseline = json.loads((ROOT / "training/references/qwen35_4b_primary_baseline_v1.json").read_bytes())
        cls.baseline = {case["id"]: case for case in baseline["cases"]}
        cls.clarify = staticmethod(runpy.run_path(str(ROOT / "training/references/clarifications_v1.py"))["clarification_message"])
        cls.receipt = "e" * 64
        cls.original = {}
        for phase, paths in (
            ("development", {"development": None}),
            ("regression", {name: ROOT / "training/datasets/shared-dialogue-v2-en-fr" / name
                            for name in cls.policy["regression"]["files"]}),
            ("additional_controls", {"controls": ROOT / "training/datasets/shared-v5r8-fresh-en-fr/controls.eval.jsonl"}),
        ):
            cls.original[phase] = {"selected_step": 158, "export_receipt_sha256": cls.receipt, "datasets": {}}
            for name, path in paths.items():
                raw = subject.development_source() if path is None else path.read_bytes()
                cls.original[phase]["datasets"][name] = {
                    "source": raw, "events": cls.perfect([json.loads(line) for line in raw.splitlines()])}

    @classmethod
    def perfect(cls, rows):
        result = []
        for row in rows:
            expected = deepcopy(row["expected"])
            action = deepcopy(expected)
            if expected["tool"] == "clarify":
                action = {"tool": "clarify", "message": cls.clarify(**expected["arguments"])}
            event = {name: deepcopy(row[name]) for name in ("id", "category", "language", "expected")}
            event.update(action=action, structured_valid=True, tool_correct=True, arguments_correct=True)
            result.append(event)
        return result

    def fixtures(self):
        candidates = {step: deepcopy(self.baseline) for step in (0, 158, 316, 474, 632)}
        candidates[158] = {event["id"]: event for event in self.perfect(self.primary)}
        return deepcopy(self.policy), deepcopy(self.primary), candidates, deepcopy(self.original), self.receipt

    def check(self, values=None):
        return subject.assess_facturation(*(values or self.fixtures()))

    def test_public_sealed_policy_matches_reviewed_sources_and_original_thresholds(self):
        sealed = json.loads((ROOT / "training/references/qwen35_4b_sequential_stage_policy_v1.json").read_bytes())
        self.assertEqual(subject.prepare_policy(), sealed)
        self.assertEqual(sealed["primary_policy"]["candidate_steps"], [0, 158, 316, 474, 632])
        self.assertEqual(sealed["primary_policy"]["broader_checks_required"], [275, 438, 48])
        self.assertEqual(sealed["stage_order"], list(subject.ORDER))

    def test_committed_inputs_reproduce_the_exact_historical_development_bytes(self):
        raw = subject.development_source()
        self.assertEqual(subject.digest(raw), subject.DEVELOPMENT_SHA)
        self.assertEqual(len(raw.splitlines()), 275)

    def test_complete_synthetic_success_is_only_a_focused_model_gate(self):
        result = self.check()
        self.assertTrue(result["focused_model_targets_passed"])
        self.assertEqual(result["retained_predecessor_applications"], [])
        self.assertEqual(result["applications_not_measured"], ["contrat", "gestion_magasin", "reservation"])
        for key in ("next_application_training_authorized", "model_accepted",
                    "all_six_apps_accepted", "production_activation",
                    "model_provenance_independently_verified", "later_stage_retention_verified"):
            self.assertFalse(result[key])
        for key in ("native_backend_security_verified", "integrated_behavior_verified", "latency_requirement_verified"):
            self.assertIsNone(result[key])
        self.assertEqual(len(result["regression_subsets"]), 15)

    def test_untrained_application_failures_are_preserved_without_false_retention(self):
        values = list(self.fixtures())
        for phase, suite in values[3].items():
            for name, part in suite["datasets"].items():
                rows = [json.loads(line) for line in part["source"].splitlines()]
                for row, event in zip(rows, part["events"]):
                    app = (row["category"] if phase == "development" else
                           row["trusted_context"]["application"] if phase == "additional_controls" else
                           next(app for app in subject.ORDER[:3] if app.replace("_", "-") in name))
                    if app != "facturation":
                        event.update(action={}, structured_valid=False)
        result = self.check(values)
        self.assertTrue(result["focused_model_targets_passed"])
        self.assertEqual(result["untrained_application_diagnostics"],
                         {"management_projet": False, "design_workflow": False})
        self.assertFalse(result["all_six_apps_accepted"])

    def test_current_application_failure_is_not_hidden_by_other_passes(self):
        values = list(self.fixtures())
        event = values[3]["additional_controls"]["datasets"]["controls"]["events"][0]
        event.update(action={}, structured_valid=False)
        result = self.check(values)
        self.assertFalse(result["focused_model_targets_passed"])
        self.assertFalse(result["broader_targets_by_application"]["facturation"])
        self.assertTrue(result["broader_targets_by_application"]["management_projet"])

    def test_each_original_subset_remains_mandatory(self):
        values = list(self.fixtures())
        datasets = values[3]["regression"]["datasets"]
        name = next(name for name in datasets if "facturation-refinement-v1" in name)
        datasets[name]["events"][0].update(action={}, structured_valid=True)
        result = self.check(values)
        self.assertFalse(result["focused_model_targets_passed"])
        self.assertFalse(next(row["passed"] for row in result["regression_subsets"] if row["dataset"] == name))

    def test_primary_failure_cannot_be_rescued_by_perfect_broader_suites(self):
        values = list(self.fixtures())
        critical = next(row["id"] for row in values[1] if row["expected"]["tool"] == "clarify")
        values[2][158][critical]["action"]["message"] = "Wrong clarification"
        values[2][158][critical]["arguments_correct"] = False
        self.assertFalse(self.check(values)["focused_model_targets_passed"])

    def test_all_primary_candidates_still_required(self):
        values = list(self.fixtures())
        del values[2][632]
        with self.assertRaisesRegex(ValueError, "Every predeclared"):
            self.check(values)

    def test_baseline_cannot_become_trained_stage(self):
        values = list(self.fixtures())
        values[2][158] = deepcopy(self.baseline)
        with self.assertRaisesRegex(ValueError, "Untrained baseline"):
            self.check(values)

    def test_missing_broader_phase_or_dataset_rejected(self):
        for mutation in ("phase", "dataset"):
            values = list(self.fixtures())
            if mutation == "phase":
                del values[3]["additional_controls"]
            else:
                values[3]["regression"]["datasets"].pop(next(iter(values[3]["regression"]["datasets"])))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.check(values)

    def test_mixed_export_or_checkpoint_rejected(self):
        for phase in self.original:
            for key, value in (("export_receipt_sha256", "a"*64), ("selected_step", 316)):
                values = list(self.fixtures())
                values[3][phase][key] = value
                with self.subTest(phase=phase, key=key), self.assertRaises(ValueError):
                    self.check(values)

    def test_changed_input_label_missing_reordered_or_recategorized_case_rejected(self):
        for mutation in ("source", "label", "missing", "order", "category", "verdict"):
            values = list(self.fixtures())
            part = values[3]["development"]["datasets"]["development"]
            if mutation == "source":
                part["source"] += b"\n"
            elif mutation == "label":
                part["events"][0]["expected"]["arguments"]["_changed"] = True
            elif mutation == "missing":
                part["events"].pop()
            elif mutation == "order":
                part["events"].reverse()
            elif mutation == "category":
                part["events"][0]["category"] = "management_projet"
            else:
                part["events"][0]["structured_valid"] = 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.check(values)

    def test_changed_policy_or_absent_receipt_rejected(self):
        values = list(self.fixtures())
        values[0]["stage_order"].reverse()
        with self.assertRaisesRegex(ValueError, "policy changed"):
            self.check(values)
        for receipt in (None, "", "e"*63, "z"*64):
            values = list(self.fixtures())
            values[4] = receipt
            with self.subTest(receipt=receipt), self.assertRaisesRegex(ValueError, "receipt hash"):
                self.check(values)

    def test_exact_integer_thresholds_still_apply(self):
        scorer = subject.selector()["verified_scorer"]()
        rows = self.primary
        for misses, expected_pass in ((6, True), (7, False)):
            events = self.perfect(rows)
            ordinary = [e for e in events if e["expected"]["tool"] not in ("clarify", "prepare_change", "knowledge")]
            for event in ordinary[:misses]:
                event["action"]["tool"] = "wrong_fixture_tool"
            assessment = scorer.assess(rows, events)
            # 95% full-action boundary: 127/133 passes, 126/133 fails.
            full_action_gate = 100 * assessment["metrics"]["counts"]["action_matches"] >= 95 * len(rows)
            self.assertEqual(full_action_gate, expected_pass)
        events = self.perfect(rows)
        ordinary = [e for e in events if e["expected"]["tool"] not in ("clarify", "prepare_change", "knowledge")]
        ordinary[0]["structured_valid"] = False
        self.assertTrue(scorer.assess(rows, events)["targets"]["structured_output"])
        ordinary[1]["structured_valid"] = False
        self.assertFalse(scorer.assess(rows, events)["targets"]["structured_output"])

    def test_input_evidence_is_not_mutated(self):
        values = self.fixtures()
        before = deepcopy(values)
        self.check(values)
        self.assertEqual(values, before)


if __name__ == "__main__":
    unittest.main()
