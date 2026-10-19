"""Verify numerical recipe admission without loading or training a model."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import facturation_corrective_training_v1 as subject


def pins():
    names = ("train_cpu.py", "training_schedule.py", "text_lora.py", "semantic_loss.py",
             "validation_selection.py", "probe_cpu_capacity.py")
    return {name: str(index) * 64 for index, name in enumerate(names, 1)}


def preflight():
    result = {}
    for name, count, digest in (("train.jsonl", 704, subject.TRAIN_SHA256),
                                 ("valid.jsonl", 275, subject.VALID_SHA256)):
        result[name] = {key: count for key in (
            "count", "round_trip_passed", "runtime_prefix_parity_passed",
            "loss_boundary_passed", "semantic_alignment_passed", "output_budget_passed")}
        result[name].update(sha256=digest, semantic_loss_weight=4, maximum_tokens=7000,
                            maximum_output_tokens=512, maximum_target_tokens=80,
                            minimum_output_budget=512, output_budget_contract="conservative-target-v1")
    return result


def capacity(checkpointing=True):
    result = dict(passed=True, model_path="experimental-parent", dataset_sha256=subject.TRAIN_SHA256,
                  threads=14, dtype="bfloat16", attention="sdpa", lora_layers=24,
                  lora_rank=16, lora_alpha=32, semantic_loss_weight=4, learning_rate=0.00001,
                  gradient_checkpointing="nonreentrant" if checkpointing else False,
                  sequence_tokens=7000, script_sha256=pins()["probe_cpu_capacity.py"],
                  lora_setup_sha256=pins()["text_lora.py"],
                  semantic_loss_sha256=pins()["semantic_loss.py"], peak_rss_kib=8*1024**2)
    result["steps"] = [dict(step=index, loss=.1, unweighted_loss=.05, gradient_norm=.3,
                           seconds=35, gradient_layers=list(range(24)),
                           nonzero_gradient_layers=list(range(24)), updated_layers=list(range(24)),
                           optimizer_state_entries=192, optimizer_state_bytes=1000000)
                       for index in (1, 2)]
    return result


def training(checkpointing=True):
    config = dict(steps=704, complete_epochs=1, threads=14, interop_threads=1,
                  max_seq_length=8192, learning_rate=0.00001, seed=17, device="cpu",
                  dtype="bfloat16", attention_implementation="sdpa", batch_size=1,
                  gradient_accumulation_steps=1, gradient_clip_norm=1.0,
                  checkpoint_interval_steps=176, validation_interval_steps=352,
                  thinking=False, gradient_checkpointing="nonreentrant" if checkpointing else False,
                  semantic_loss_weight=4, lora=dict(r=16, alpha=32, layers=24, dropout=0),
                  optimizer={"class": "torch.optim.AdamW", "lr": .00001, "weight_decay": 0})
    report = dict(steps=704, training_config=config, dataset_sha256=subject.TRAIN_SHA256,
                  validation_sha256=subject.VALID_SHA256, base_artifacts={"identity": "experimental"},
                  dependency_versions={"torch": "pinned"}, application_exposure={
                      app: {"steps": count, "unique_examples": count}
                      for app, count in subject.EXPOSURE.items()},
                  steps_metrics=[dict(step=i, loss=.1, seconds=30) for i in range(1, 705)],
                  validation_history=[{"step": i, "loss": {
                      "micro": .1, "macro": .1, "by_application": {
                          app: .1 for app in subject.EXPOSURE}}} for i in (0, 352, 704)])
    for key, filename in (
            ("script", "train_cpu.py"), ("schedule_script", "training_schedule.py"),
            ("lora_setup_script", "text_lora.py"), ("semantic_loss_script", "semantic_loss.py"),
            ("validation_selection_script", "validation_selection.py")):
        report[key] = {"sha256": pins()[filename]}
    return report


class CorrectiveTrainingContractTests(unittest.TestCase):
    def validate_training(self, report, checkpointing=True):
        return subject.validate_training_report(
            report, pins(), {"identity": "experimental"}, {"torch": "pinned"}, checkpointing)

    def test_command_uses_one_complete_epoch_all_checkpoints_and_distinct_validation_schedule(self):
        command = subject.training_command("python", "run", "experimental-parent", True)
        self.assertEqual(command[command.index("--model")+1], "experimental-parent")
        for name, value in (("--complete-epochs", "1"), ("--threads", "14"),
                            ("--checkpoint-interval", "176"), ("--validation-interval", "352"),
                            ("--max-seq-length", "8192"), ("--semantic-loss-weight", "4")):
            self.assertEqual(command[command.index(name)+1], value)
        self.assertNotIn("--adapter", command)
        self.assertNotIn("--resume", command)
        self.assertNotIn("--steps", command)
        self.assertIn("--gradient-checkpointing", command)
        self.assertNotIn("--gradient-checkpointing",
                         subject.training_command("python", "run", "experimental-parent", False))
        with self.assertRaises(ValueError):
            subject.training_command("python", "run", "parent", None)

    def test_larger_run_does_not_reuse_six_hour_child_timeout(self):
        self.assertEqual(subject.TRAIN_TIMEOUT_SECONDS, 43200)
        self.assertEqual(subject.UNIT_TIMEOUT_SECONDS, 50400)
        self.assertGreater(subject.UNIT_TIMEOUT_SECONDS, subject.TRAIN_TIMEOUT_SECONDS)

    def test_memory_ceiling_preserves_ten_percent_host_ram(self):
        subject.memory_admission(62*1024**3, 50*1024**3, 40)
        for values in ((62*1024**3, 45*1024**3, 40),
                       (62*1024**3, 60*1024**3, 41),
                       (62*1024**3, 63*1024**3, 40),
                       (62*1024**3, 50*1024**3, True)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                subject.memory_admission(*values)

    def test_every_actual_preflight_check_is_required(self):
        subject.validate_preflight(preflight())
        for field in ("count", "round_trip_passed", "runtime_prefix_parity_passed",
                      "loss_boundary_passed", "semantic_alignment_passed", "output_budget_passed"):
            report = preflight()
            report["train.jsonl"][field] = 703
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.validate_preflight(report)

    def test_preflight_rejects_context_output_or_data_changes(self):
        for field, value in (("maximum_tokens", 8193), ("maximum_output_tokens", 1024),
                             ("maximum_target_tokens", 513), ("sha256", "changed"),
                             ("semantic_loss_weight", 1)):
            report = preflight()
            report["valid.jsonl"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.validate_preflight(report)

    def test_capacity_requires_actual_new_parent_and_selected_mode(self):
        for mode in (True, False):
            report = capacity(mode)
            subject.validate_capacity(report, pins(), "experimental-parent", mode, 7000, 40)
            for field, value in (("model_path", "old-reference"), ("dataset_sha256", "changed"),
                                 ("sequence_tokens", 6999), ("gradient_checkpointing", "wrong"),
                                 ("passed", False), ("script_sha256", "changed"),
                                 ("peak_rss_kib", 41*1024**2)):
                invalid = deepcopy(report)
                invalid[field] = value
                with self.subTest(mode=mode, field=field), self.assertRaises(ValueError):
                    subject.validate_capacity(invalid, pins(), "experimental-parent", mode, 7000, 40)

    def test_capacity_requires_finite_updates_all_layers_and_optimizer(self):
        for field, value in (("loss", float("nan")), ("seconds", float("inf")),
                             ("gradient_layers", list(range(23))),
                             ("nonzero_gradient_layers", []), ("updated_layers", []),
                             ("optimizer_state_entries", 0), ("optimizer_state_bytes", 0)):
            report = capacity()
            report["steps"][1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                subject.validate_capacity(report, pins(), "experimental-parent", True, 7000, 40)

    def test_valid_complete_training_is_not_model_acceptance(self):
        for mode in (True, False):
            report = training(mode)
            before = deepcopy(report)
            result = self.validate_training(report, mode)
            self.assertTrue(result["training_complete"])
            self.assertTrue(result["functional_evaluation_required"])
            for key in ("model_accepted", "production_activation", "next_application_training_started"):
                self.assertFalse(result[key])
            self.assertEqual(report, before)

    def test_training_rejects_wrong_parent_environment_or_source(self):
        for field, value in (("base_artifacts", {"identity": "old-reference"}),
                             ("dependency_versions", {"torch": "changed"}),
                             ("dataset_sha256", "changed"), ("validation_sha256", "changed"),
                             ("script", {"sha256": "changed"})):
            report = training()
            report[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate_training(report)

    def test_training_requires_complete_replay_and_finite_contiguous_updates(self):
        for kind in ("missing", "duplicate", "nan", "exposure", "validation"):
            report = training()
            if kind == "missing":
                report["steps_metrics"].pop()
            elif kind == "duplicate":
                report["steps_metrics"][-1]["step"] = 703
            elif kind == "nan":
                report["steps_metrics"][0]["loss"] = float("nan")
            elif kind == "exposure":
                report["application_exposure"]["facturation"]["unique_examples"] -= 1
            else:
                report["validation_history"].pop(1)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.validate_training(report)

    def test_training_rejects_changed_recipe(self):
        for field, value in (("complete_epochs", 2), ("gradient_checkpointing", False),
                             ("validation_interval_steps", 176), ("checkpoint_interval_steps", 352),
                             ("threads", 16), ("semantic_loss_weight", 1),
                             ("thinking", True), ("max_seq_length", 4096)):
            report = training()
            report["training_config"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate_training(report)

    def test_validation_losses_must_be_finite_for_every_retained_application(self):
        report = training()
        report["validation_history"][1]["loss"]["by_application"]["management_projet"] = float("inf")
        with self.assertRaises(ValueError):
            self.validate_training(report)


if __name__ == "__main__":
    unittest.main()
