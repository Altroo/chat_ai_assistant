"""Synthetic evidence fixtures reject training-record inconsistencies, with no model."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_facturation_uniform_correction_v1 as subject
from test_verify_facturation_semantic_correction_v2 import fixture as weighted_fixture
from test_facturation_semantic_training_v1 import pins as historical_pins


def fixture(values=(.4, .2, .3), uniform=True):
    packet = weighted_fixture(values)
    report = packet[0]
    report["model_path"] = "parent125"
    report["training_config"].update(semantic_loss_weight=1.0, model_path="parent125",
                                     data_path="run/data", output_path="run/training")
    history = report["validation_history"]
    if uniform:
        for entry in history:
            plain = deepcopy(entry["loss"]["unweighted"])
            entry["loss"] = {**plain, "unweighted": deepcopy(plain)}
    selected_step = report["checkpoint_selection"]["step"]
    selected_loss = next(entry["loss"] for entry in history if entry["step"] == selected_step)
    report["checkpoint_selection"]["validation"] = deepcopy(selected_loss)
    for prefix, loss in (("baseline", history[0]["loss"]), ("final", history[-1]["loss"])):
        report[prefix + "_validation_by_application"] = deepcopy(loss)
        report[prefix + "_validation_loss"] = loss["micro"]
        report[prefix + "_validation_unweighted_loss"] = loss["unweighted"]["micro"]
    provenance = {key: deepcopy(report[key]) for key in subject.records.PROVENANCE_KEYS}
    saved = deepcopy(packet[3]); saved["validation"] = deepcopy(selected_loss)
    events = [{"baseline_validation_loss": history[0]["loss"]},
              *deepcopy(report["steps_metrics"][:64]), {"validation_checkpoint": history[1]},
              *deepcopy(report["steps_metrics"][64:]), {"validation_checkpoint": history[2]}]
    log = "Synthetic metadata fixture; not a measured training run\n" + "\n".join(json.dumps(v) for v in events)
    return [report, provenance, deepcopy(history), saved, log, packet[5], packet[6]]


def validate(packet):
    pins = historical_pins()
    pins["validation_selection.py"] = packet[6]
    return subject.verify(*packet, pins=pins, parent_artifacts={"identity": "experimental"},
        dependency_versions={"torch": "pinned"}, model_path="parent125",
        data_path="run/data", output_path="run/training")


class UniformTerminalEvidenceTests(unittest.TestCase):
    def test_verified_metadata_is_not_model_acceptance(self):
        for values, selected in (((.1,.2,.3),0), ((.4,.2,.3),64), ((.4,.3,.2),128)):
            packet = fixture(values)
            before = deepcopy(packet)
            result = validate(packet)
            self.assertEqual(packet, before)
            self.assertTrue(result["verified"])
            self.assertEqual(result["optimizer_updates"], 128)
            self.assertEqual(result["loss_selected_step"], selected)
            self.assertTrue(result["uniform_weighted_unweighted_consistent"])
            self.assertTrue(result["binding_paths_verified"])
            self.assertFalse(result["model_accepted"])
            self.assertFalse(result["production_activation"])

    def test_consistent_weighted_records_do_not_masquerade_as_uniform(self):
        packet = fixture(uniform=False)
        self.assertTrue(subject.records.verify(*packet)["verified"])
        with self.assertRaisesRegex(ValueError, "Uniform weighted/unweighted"):
            validate(packet)

    def test_wrong_top_level_or_coupled_config_paths_are_rejected(self):
        for mode in ("top_model", "model", "data", "output"):
            packet = fixture()
            if mode == "top_model": packet[0]["model_path"] = "wrong-parent"
            else:
                key = {"model": "model_path", "data": "data_path", "output": "output_path"}[mode]
                for record in packet[:2]: record["training_config"][key] = "wrong-location"
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "trusted binding"):
                validate(packet)

    def test_forged_report_or_saved_selection_is_rejected(self):
        for mode in ("report", "saved"):
            packet = fixture()
            if mode == "report": packet[0]["checkpoint_selection"]["step"] = 128
            else: packet[3]["selected_step"] = 128
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(packet)

    def test_nan_unweighted_loss_or_altered_summary_is_rejected(self):
        for mode in ("nan", "summary"):
            packet = fixture()
            if mode == "nan":
                packet[0]["validation_history"][1]["loss"]["unweighted"]["micro"] = float("nan")
                packet[2] = deepcopy(packet[0]["validation_history"])
            else: packet[0]["final_validation_loss"] += 1
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(packet)

    def test_changed_or_missing_raw_updates_are_rejected(self):
        for mode in ("missing", "duplicate", "changed"):
            packet = fixture(); lines = packet[4].splitlines()
            if mode == "missing": lines.pop(2)
            elif mode == "duplicate": lines.append(lines[2])
            else:
                row = json.loads(lines[2]); row["loss"] = 999; lines[2] = json.dumps(row)
            packet[4] = "\n".join(lines)
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(packet)

    def test_selector_source_provenance_and_history_remain_coupled(self):
        for mode in ("source", "provenance", "history"):
            packet = fixture()
            if mode == "source": packet[6] = "0" * 64
            elif mode == "provenance": packet[1]["training_config"]["learning_rate"] = .5
            else: packet[2][1]["selected_step"] = 128
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(packet)


if __name__ == "__main__":
    unittest.main()
