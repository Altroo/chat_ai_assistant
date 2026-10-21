"""Balanced ordinary-SFT admission checks, with no model or training execution."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import facturation_uniform_correction_training_v1 as subject
import facturation_semantic_correction_training_v2 as previous_recipe
import test_facturation_semantic_correction_training_v2 as previous
import test_facturation_semantic_training_v1 as historical


def training():
    report = previous.training()
    report["training_config"]["semantic_loss_weight"] = 1.0
    return report


def preflight():
    report = historical.preflight()
    for name, count, digest in (("train.jsonl", 128, subject.TRAIN_SHA256),
                                 ("valid.jsonl", 275, subject.VALID_SHA256)):
        row = report[name]
        for field in ("count", "round_trip_passed", "runtime_prefix_parity_passed",
                      "loss_boundary_passed", "semantic_alignment_passed", "output_budget_passed"):
            row[field] = count
        row["sha256"] = digest
        row["semantic_loss_weight"] = 1.0
    return report


def capacity():
    report = historical.capacity()
    report.update(dataset_sha256=subject.TRAIN_SHA256, learning_rate=0.00001,
                  semantic_loss_weight=1.0)
    return report


def validate(report):
    return subject.validate_training_report(report, historical.pins(),
        {"identity": "experimental"}, {"torch": "pinned"}, True)


class UniformCorrectiveAdmissionTests(unittest.TestCase):
    def test_only_numerical_command_change_is_token_weight(self):
        old = previous_recipe.training_command("python", "new-run", "parent125", True)
        expected = old.copy()
        expected[expected.index("--semantic-loss-weight") + 1] = "1"
        self.assertEqual(subject.training_command("python", "new-run", "parent125", True), expected)
        self.assertEqual(subject.EXPOSURE, previous_recipe.EXPOSURE)
        self.assertEqual(subject.SAVED_STEPS, (32, 64, 96, 128))
        self.assertEqual(subject.VALIDATION_STEPS, (0, 64, 128))
        self.assertEqual(subject.TRAIN_SHA256, previous_recipe.TRAIN_SHA256)
        self.assertEqual(subject.VALID_SHA256, previous_recipe.VALID_SHA256)
        self.assertLess(subject.TRAIN_TIMEOUT_SECONDS, subject.UNIT_TIMEOUT_SECONDS)

    def test_completion_is_not_acceptance_or_activation(self):
        report = training()
        before = deepcopy(report)
        result = validate(report)
        self.assertEqual(report, before)
        self.assertTrue(result["training_complete"])
        self.assertTrue(result["functional_evaluation_required"])
        self.assertFalse(result["model_accepted"])
        self.assertFalse(result["production_activation"])
        self.assertFalse(result["next_application_training_started"])

    def test_stale_weight_or_non_numeric_weight_is_rejected_in_all_stages(self):
        for value in (4, True, "1", float("nan"), float("inf"), 0):
            with self.subTest(value=value):
                report = preflight()
                report["train.jsonl"]["semantic_loss_weight"] = value
                with self.assertRaises(ValueError): subject.validate_preflight(report)
                report = capacity()
                report["semantic_loss_weight"] = value
                with self.assertRaises(ValueError):
                    subject.validate_capacity(report, historical.pins(), "experimental-parent", True, 7000, 40)
                report = training()
                report["training_config"]["semantic_loss_weight"] = value
                with self.assertRaises(ValueError): validate(report)

    def test_frozen_weighted_reports_remain_valid_only_for_the_old_recipe(self):
        self.assertTrue(previous.validate(previous.training())["training_complete"])
        with self.assertRaises(ValueError): validate(previous.training())
        with self.assertRaises(ValueError): previous.validate(training())

    def test_every_preflight_case_and_full_output_reserve_are_required(self):
        subject.validate_preflight(preflight())
        for field, value in (("round_trip_passed", 127), ("runtime_prefix_parity_passed", 127),
                              ("semantic_alignment_passed", 127), ("output_budget_passed", 127),
                              ("maximum_output_tokens", 1024), ("sha256", "changed")):
            report = preflight()
            report["train.jsonl"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.validate_preflight(report)

    def test_complete_capacity_updates_and_all_adapter_layers_are_required(self):
        subject.validate_capacity(capacity(), historical.pins(), "experimental-parent", True, 7000, 40)
        for mode in ("missing_step", "missing_layer", "wrong_source", "wrong_parent"):
            report = capacity()
            if mode == "missing_step": report["steps"].pop()
            elif mode == "missing_layer": report["steps"][1]["updated_layers"] = list(range(23))
            elif mode == "wrong_source": report["script_sha256"] = "changed"
            else: report["model_path"] = "another-parent"
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.validate_capacity(report, historical.pins(), "experimental-parent", True, 7000, 40)

    def test_partial_epoch_missing_retention_or_changed_provenance_is_rejected(self):
        for mode in ("missing_update", "duplicate_update", "nonfinite", "missing_retention",
                     "wrong_parent", "wrong_data", "wrong_source", "wrong_dependencies", "wrong_lr"):
            report = training()
            if mode == "missing_update": report["steps_metrics"].pop()
            elif mode == "duplicate_update": report["steps_metrics"][-1]["step"] = 127
            elif mode == "nonfinite": report["steps_metrics"][0]["loss"] = float("nan")
            elif mode == "missing_retention": report["application_exposure"]["design_workflow"]["unique_examples"] -= 1
            elif mode == "wrong_parent": report["base_artifacts"] = {}
            elif mode == "wrong_data": report["dataset_sha256"] = "changed"
            elif mode == "wrong_source": report["script"]["sha256"] = "changed"
            elif mode == "wrong_dependencies": report["dependency_versions"] = {}
            else: report["training_config"]["learning_rate"] = 0.0001
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(report)

    def test_ten_percent_memory_reserve_is_required(self):
        subject.memory_admission(64 * 1024**3, 50 * 1024**3, 40)
        with self.assertRaises(ValueError): subject.memory_admission(64 * 1024**3, 46 * 1024**3, 40)


if __name__ == "__main__":
    unittest.main()
