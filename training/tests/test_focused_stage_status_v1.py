"""Synthetic reporting gates are not model performance measurements."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import report_focused_stage_v1 as report


def fixture(*, focused=True, retained=True, other_pass=False, six=False):
    apps = report.APPLICATIONS if six else (
        "facturation", "management_projet", "design_workflow")
    per_app = {app: focused if app == "facturation" else other_pass for app in apps}
    retention = {app: retained for app in apps if app != "facturation"}
    binding = {"policy": {"application": "facturation"}}
    selection = {"selected_step": 72}
    state = {
        "phase": "finished", "accepted": all(per_app.values()),
        "facturation_accepted": all(per_app.values()),
        "by_application": per_app, "production_activation": False,
    }
    gates = {
        "selected_step": 72, "by_application": per_app,
        "retained_no_decline": retention, "production_activation": False,
    }
    development = {"selected_step": 72, "retained_no_decline": retention}
    return copy.deepcopy((binding, selection, state, gates, development))


class FocusedStageReportTests(unittest.TestCase):
    def test_focused_pass_is_visible_when_later_apps_fail(self):
        result = report.status(*fixture(), "facturation")
        self.assertTrue(result["focused_application_recorded_gate_passed"])
        self.assertFalse(result["all_evaluated_application_gates_passed"])
        self.assertTrue(result["retained_development_not_regressed"])
        self.assertTrue(result["legacy_focused_flag_differs"])
        self.assertFalse(result["all_six_apps_accepted"])
        self.assertIsNone(result["native_backend_security_verified"])

    def test_retention_failure_does_not_erase_or_admit_focused_result(self):
        result = report.status(*fixture(retained=False), "facturation")
        self.assertTrue(result["focused_application_recorded_gate_passed"])
        self.assertFalse(result["retained_development_not_regressed"])
        self.assertFalse(result["next_application_training_authorized"])
        self.assertFalse(result["production_activation"])

    def test_failure_stays_failed_even_when_other_apps_pass(self):
        result = report.status(*fixture(focused=False, other_pass=True), "facturation")
        self.assertFalse(result["focused_application_recorded_gate_passed"])
        self.assertFalse(result["all_evaluated_application_gates_passed"])

    def test_three_app_pass_cannot_become_six_app_acceptance(self):
        result = report.status(*fixture(other_pass=True), "facturation")
        self.assertTrue(result["all_evaluated_application_gates_passed"])
        self.assertFalse(result["all_six_recorded_model_gates_passed"])
        self.assertEqual(set(result["applications_not_evaluated"]),
                         {"contrat", "reservation", "gestion_magasin"})

    def test_all_six_model_gates_do_not_prove_native_security_or_admit_work(self):
        result = report.status(*fixture(other_pass=True, six=True), "facturation")
        self.assertTrue(result["all_six_recorded_model_gates_passed"])
        self.assertFalse(result["all_six_apps_accepted"])
        self.assertIsNone(result["native_backend_security_verified"])
        self.assertFalse(result["next_application_training_authorized"])
        self.assertFalse(result["production_activation"])

    def test_rejects_running_or_wrong_checkpoint_or_scope(self):
        for index, key, value in (
            (2, "phase", "evaluating_acceptance"),
            (1, "selected_step", 144),
            (4, "selected_step", 144),
            (0, "policy", {"application": "management_projet"}),
            (2, "production_activation", True),
            (3, "production_activation", True),
            (2, "accepted", True),
            (2, "by_application", {"facturation": False}),
            (3, "by_application", {"facturation": "true"}),
            (3, "retained_no_decline", {"management_projet": True}),
            (4, "retained_no_decline", {"management_projet": False, "design_workflow": True}),
        ):
            with self.subTest(index=index, key=key, value=value):
                data = list(fixture())
                data[index][key] = value
                with self.assertRaises(ValueError):
                    report.status(*data, "facturation")

    def test_build_preserves_inputs_and_records_exact_evidence_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            raw = {}
            for name, value in zip(report.INPUTS, fixture()):
                raw[name] = json.dumps(value).encode()
                (root / name).write_bytes(raw[name])
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = report.build(root, "facturation")
            self.assertEqual(result["evidence_sha256"], {
                name: hashlib.sha256(value).hexdigest() for name, value in raw.items()})
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_changed_evidence_during_reporting_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name, value in zip(report.INPUTS, fixture()):
                (root / name).write_text(json.dumps(value))
            original = report.status

            def changed(*args):
                result = original(*args)
                (root / "selection.json").write_text('{"selected_step":144}')
                return result

            with patch.object(report, "status", side_effect=changed):
                with self.assertRaisesRegex(ValueError, "evidence changed"):
                    report.build(root, "facturation")


if __name__ == "__main__":
    unittest.main()
