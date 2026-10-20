"""Admission guards for the 128-update correction; no model is loaded."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import facturation_semantic_correction_training_v2 as subject
import test_facturation_semantic_training_v1 as historical


def training():
    report = historical.training()
    report["steps"] = report["training_config"]["steps"] = 128
    report["training_config"].update(learning_rate=0.00001, checkpoint_interval_steps=32,
                                     validation_interval_steps=64)
    report["training_config"]["optimizer"]["lr"] = 0.00001
    report["dataset_sha256"] = subject.TRAIN_SHA256
    report["steps_metrics"] = [dict(step=i, loss=.1, seconds=30) for i in range(1,129)]
    report["application_exposure"] = {app: {"steps": count, "unique_examples": count}
                                     for app, count in subject.EXPOSURE.items()}
    for entry, step in zip(report["validation_history"], subject.VALIDATION_STEPS):
        entry["step"] = step
    return report


def validate(report):
    return subject.validate_training_report(report, historical.pins(),
        {"identity": "experimental"}, {"torch": "pinned"}, True)


class CorrectiveAdmissionTests(unittest.TestCase):
    def test_command_uses_new_parent_fresh_epoch_and_checkpoints(self):
        command = subject.training_command("python", "new-run", "parent125", True)
        for flag, value in (("--model", "parent125"), ("--complete-epochs","1"),
                            ("--learning-rate", "0.00001"), ("--threads", "14"),
                            ("--checkpoint-interval", "32"), ("--validation-interval", "64")):
            self.assertEqual(command[command.index(flag)+1], value)
        self.assertNotIn("--resume", command)
        self.assertNotIn("--adapter", command)
        self.assertEqual(subject.SAVED_STEPS, (32,64,96,128))
        self.assertLess(subject.TRAIN_TIMEOUT_SECONDS, subject.UNIT_TIMEOUT_SECONDS)

    def test_full_epoch_is_not_model_acceptance(self):
        report = training()
        before = deepcopy(report)
        result = validate(report)
        self.assertEqual(report, before)
        self.assertTrue(result["training_complete"])
        self.assertFalse(result["model_accepted"])

    def test_old_500_run_cannot_be_accepted_as_new_run(self):
        with self.assertRaises(ValueError):
            validate(historical.training())

    def test_missing_duplicate_or_nonfinite_update_is_rejected(self):
        for mode in ("missing", "duplicate", "nonfinite"):
            report = training()
            if mode == "missing":
                report["steps_metrics"].pop()
            elif mode == "duplicate":
                report["steps_metrics"][-1]["step"] = 127
            else:
                report["steps_metrics"][0]["loss"] = float("nan")
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate(report)

    def test_missing_replay_or_validation_is_rejected(self):
        report = training()
        report["application_exposure"]["design_workflow"]["unique_examples"] -= 1
        with self.assertRaises(ValueError):
            validate(report)
        report = training()
        report["validation_history"][1]["step"] = 32
        with self.assertRaises(ValueError):
            validate(report)

    def test_recipe_or_parent_change_is_rejected(self):
        for mode in ("parent", "lr", "interval", "dataset", "source"):
            report = training()
            if mode == "parent": report["base_artifacts"] = {}
            elif mode == "lr": report["training_config"]["learning_rate"] = 0.000002
            elif mode == "interval": report["training_config"]["checkpoint_interval_steps"] = 125
            elif mode == "dataset": report["dataset_sha256"] = "wrong"
            else: report["script"]["sha256"] = "wrong"
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate(report)

    def test_exact_preflight_inventory_and_budget_are_required(self):
        report = historical.preflight()
        row = report["train.jsonl"]
        for field in ("count", "round_trip_passed", "runtime_prefix_parity_passed",
                      "loss_boundary_passed", "semantic_alignment_passed", "output_budget_passed"):
            row[field] = 128
        row["sha256"] = subject.TRAIN_SHA256
        subject.validate_preflight(report)
        for field, value in (("count",127), ("round_trip_passed",127),
                              ("maximum_output_tokens",1024), ("sha256","wrong")):
            invalid = deepcopy(report)
            invalid["train.jsonl"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.validate_preflight(invalid)

    def test_capacity_must_use_new_lr_data_and_all_layers(self):
        report = historical.capacity()
        report.update(dataset_sha256=subject.TRAIN_SHA256, learning_rate=0.00001)
        subject.validate_capacity(report, historical.pins(), "experimental-parent", True,7000,40)
        report["steps"][1]["updated_layers"] = list(range(23))
        with self.assertRaises(ValueError):
            subject.validate_capacity(report,historical.pins(),"experimental-parent",True,7000,40)


if __name__ == "__main__":
    unittest.main()
