"""Synthetic recipe mutations; no model loading, training, or measured accuracy."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import facturation_factor_coverage_training_v1 as subject
import facturation_uniform_correction_training_v1 as previous_recipe
import test_facturation_uniform_correction_training_v1 as previous
import test_facturation_semantic_training_v1 as historical


def training():
    report = previous.training()
    report["steps"] = 176
    config = report["training_config"]
    config.update(steps=176, learning_rate=0.000002, checkpoint_interval_steps=44,
                  validation_interval_steps=88)
    config["optimizer"]["lr"] = 0.000002
    report["dataset_sha256"] = subject.TRAIN_SHA256
    report["application_exposure"] = {
        app: {"steps": count, "unique_examples": count} for app, count in subject.EXPOSURE.items()}
    metric = report["steps_metrics"][0]
    report["steps_metrics"] = [dict(deepcopy(metric), step=i) for i in range(1, 177)]
    validation = report["validation_history"][0]
    report["validation_history"] = [dict(deepcopy(validation), step=i)
                                    for i in subject.VALIDATION_STEPS]
    return report


def preflight():
    report = previous.preflight()
    row = report["train.jsonl"]
    for field in ("count", "round_trip_passed", "runtime_prefix_parity_passed",
                  "loss_boundary_passed", "semantic_alignment_passed", "output_budget_passed"):
        row[field] = 176
    row["sha256"] = subject.TRAIN_SHA256
    return report


def capacity():
    report = previous.capacity()
    report.update(dataset_sha256=subject.TRAIN_SHA256, learning_rate=0.000002)
    return report


def validate(report):
    return subject.validate_training_report(report, historical.pins(),
        {"identity": "experimental"}, {"torch": "pinned"}, True)


class CoverageAdmissionTests(unittest.TestCase):
    def test_fresh_recipe_command_has_no_resume_or_adapter_reapplication(self):
        command = subject.training_command("python", "isolated-run", "selected-merged-parent", True)
        expected = previous_recipe.training_command("python", "isolated-run", "selected-merged-parent", True)
        for key, value in (("--learning-rate", "0.000002"), ("--checkpoint-interval", "44"),
                           ("--validation-interval", "88")):
            expected[expected.index(key) + 1] = value
        self.assertEqual(command, expected)
        self.assertFalse(any("resume" in part or "adapter" in part for part in command))
        self.assertEqual(subject.EXPOSURE, {"facturation": 144, "management_projet": 16, "design_workflow": 16})
        self.assertEqual(subject.SAVED_STEPS, (44, 88, 132, 176))
        self.assertEqual(subject.VALIDATION_STEPS, (0, 88, 176))
        self.assertLess(subject.TRAIN_TIMEOUT_SECONDS, subject.UNIT_TIMEOUT_SECONDS)

    def test_full_epoch_completion_is_never_accuracy_or_activation(self):
        report = training()
        before = deepcopy(report)
        result = validate(report)
        self.assertEqual(report, before)
        self.assertTrue(result["training_complete"])
        self.assertTrue(result["functional_evaluation_required"])
        self.assertFalse(result["model_accepted"])
        self.assertFalse(result["production_activation"])
        self.assertFalse(result["next_application_training_started"])

    def test_old_recipe_reports_are_not_admitted_as_new_measurements(self):
        self.assertTrue(previous.validate(previous.training())["training_complete"])
        with self.assertRaises(ValueError): validate(previous.training())
        with self.assertRaises(ValueError): previous.validate(training())
        with self.assertRaises(ValueError): subject.validate_preflight(previous.preflight())
        with self.assertRaises(ValueError):
            subject.validate_capacity(previous.capacity(), historical.pins(), "experimental-parent", True, 7000, 40)

    def test_uniform_weight_is_required_at_every_stage(self):
        for value in (4, True, "1", float("nan"), float("inf"), 0):
            with self.subTest(value=value):
                report = preflight(); report["train.jsonl"]["semantic_loss_weight"] = value
                with self.assertRaises(ValueError): subject.validate_preflight(report)
                report = capacity(); report["semantic_loss_weight"] = value
                with self.assertRaises(ValueError):
                    subject.validate_capacity(report, historical.pins(), "experimental-parent", True, 7000, 40)
                report = training(); report["training_config"]["semantic_loss_weight"] = value
                with self.assertRaises(ValueError): validate(report)

    def test_every_case_and_exact_output_reserve_are_required(self):
        subject.validate_preflight(preflight())
        for field, value in (("count", 128), ("round_trip_passed", 175),
                             ("runtime_prefix_parity_passed", 175), ("loss_boundary_passed", 175),
                             ("semantic_alignment_passed", 175), ("output_budget_passed", 175),
                             ("maximum_output_tokens", 1024), ("sha256", "stale")):
            report = preflight(); report["train.jsonl"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.validate_preflight(report)

    def test_complete_capacity_updates_use_the_new_lr_parent_and_all_layers(self):
        subject.validate_capacity(capacity(), historical.pins(), "experimental-parent", True, 7000, 40)
        for mode in ("missing_step", "missing_layer", "wrong_source", "wrong_parent", "old_lr", "wrong_tokens"):
            report = capacity()
            if mode == "missing_step": report["steps"].pop()
            elif mode == "missing_layer": report["steps"][1]["updated_layers"] = list(range(23))
            elif mode == "wrong_source": report["script_sha256"] = "changed"
            elif mode == "wrong_parent": report["model_path"] = "another-parent"
            elif mode == "old_lr": report["learning_rate"] = 0.00001
            else: report["sequence_tokens"] = 7001
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.validate_capacity(report, historical.pins(), "experimental-parent", True, 7000, 40)

    def test_epoch_retention_parent_sources_and_optimizer_are_bound(self):
        for mode in ("missing_update", "duplicate_update", "nonfinite", "missing_retention", "wrong_parent",
                     "wrong_data", "wrong_source", "wrong_dependencies", "old_lr", "old_optimizer_lr",
                     "old_checkpoint_interval", "old_validation", "partial_epoch"):
            report = training()
            if mode == "missing_update": report["steps_metrics"].pop()
            elif mode == "duplicate_update": report["steps_metrics"][-1]["step"] = 175
            elif mode == "nonfinite": report["steps_metrics"][0]["loss"] = float("nan")
            elif mode == "missing_retention": report["application_exposure"]["design_workflow"]["unique_examples"] -= 1
            elif mode == "wrong_parent": report["base_artifacts"] = {}
            elif mode == "wrong_data": report["dataset_sha256"] = "changed"
            elif mode == "wrong_source": report["script"]["sha256"] = "changed"
            elif mode == "wrong_dependencies": report["dependency_versions"] = {}
            elif mode == "old_lr": report["training_config"]["learning_rate"] = 0.00001
            elif mode == "old_optimizer_lr": report["training_config"]["optimizer"]["lr"] = 0.00001
            elif mode == "old_checkpoint_interval": report["training_config"]["checkpoint_interval_steps"] = 32
            elif mode == "old_validation": report["validation_history"][1]["step"] = 64
            else: report["steps"] = 128
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(report)

    def test_ten_percent_host_memory_reserve_is_required(self):
        subject.memory_admission(64 * 1024**3, 50 * 1024**3, 40)
        with self.assertRaises(ValueError):
            subject.memory_admission(64 * 1024**3, 46 * 1024**3, 40)


if __name__ == "__main__":
    unittest.main()
