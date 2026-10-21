"""Synthetic176-update terminal records, never measured model-accuracy results."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_facturation_factor_coverage_v1 as subject
from test_verify_facturation_uniform_correction_v1 import fixture as previous_fixture
from test_facturation_factor_coverage_training_v1 import training as recipe_fixture
from test_facturation_semantic_training_v1 import pins as historical_pins


def fixture(values=(.4, .2, .3), uniform=True):
    old = previous_fixture(values, uniform)
    report = old[0]
    template = recipe_fixture()
    for key in ("steps", "dataset_sha256", "application_exposure"):
        report[key] = deepcopy(template[key])
    report["model_path"] = "parent32"
    report["training_config"].update(template["training_config"])
    report["training_config"].update(model_path="parent32", data_path="run/data", output_path="run/training")
    history = report["validation_history"]
    translate = {0: 0, 64: 88, 128: 176}
    for entry in history:
        entry["step"] = translate[entry["step"]]
        if "selected_step" in entry:
            entry["selected_step"] = translate[entry["selected_step"]]
    selected = report["checkpoint_selection"]
    selected["step"] = translate[selected["step"]]
    selected["adapter"] = "selected-"+str(selected["step"]) if selected["step"] else None
    metric = deepcopy(report["steps_metrics"][0])
    report["steps_metrics"] = [dict(deepcopy(metric), step=i) for i in range(1, 177)]
    provenance = {key: deepcopy(report[key]) for key in subject.PROVENANCE_KEYS}
    saved = deepcopy(old[3])
    saved.update(selected_step=selected["step"], selected_adapter=selected["adapter"])
    events = [{"baseline_validation_loss": history[0]["loss"]},
              *deepcopy(report["steps_metrics"][:88]), {"validation_checkpoint": history[1]},
              *deepcopy(report["steps_metrics"][88:]), {"validation_checkpoint": history[2]}]
    log = "Synthetic metadata fixture; not a measured run\n" + "\n".join(json.dumps(v) for v in events)
    return [report, provenance, deepcopy(history), saved, log, old[5], old[6]]


def validate(packet):
    pins = historical_pins()
    pins["validation_selection.py"] = packet[6]
    return subject.verify(*packet, pins=pins, parent_artifacts={"identity": "experimental"},
        dependency_versions={"torch": "pinned"}, model_path="parent32",
        data_path="run/data", output_path="run/training")


class CoverageTerminalEvidenceTests(unittest.TestCase):
    def test_verified_metadata_is_not_model_acceptance(self):
        for values, selected in (((.1,.2,.3),0), ((.4,.2,.3),88), ((.4,.3,.2),176)):
            packet = fixture(values)
            before = deepcopy(packet)
            result = validate(packet)
            self.assertEqual(packet, before)
            self.assertTrue(result["verified"])
            self.assertEqual(result["optimizer_updates"], 176)
            self.assertEqual(result["loss_selected_step"], selected)
            self.assertTrue(result["uniform_weighted_unweighted_consistent"])
            self.assertTrue(result["binding_paths_verified"])
            self.assertFalse(result["model_accepted"])
            self.assertFalse(result["production_activation"])

    def test_consistent_weighted_records_do_not_masquerade_as_uniform(self):
        packet = fixture(uniform=False)
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
            if mode == "report": packet[0]["checkpoint_selection"]["step"] = 176
            else: packet[3]["selected_step"] = 176
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
            else: packet[2][1]["selected_step"] = 176
            with self.subTest(mode=mode), self.assertRaises(ValueError): validate(packet)


    def test_unpinned_selector_is_rejected_before_ast_execution(self):
        packet = fixture()
        pinned_digest = packet[6]
        packet[5] = b'class ValidationSelection:\n    raise AssertionError("Untrusted class executed")\n'
        packet[6] = hashlib.sha256(packet[5]).hexdigest()
        pins = historical_pins()
        pins["validation_selection.py"] = pinned_digest
        with patch.object(subject.ast, "parse", side_effect=AssertionError("Untrusted AST parsed")):
            with self.assertRaisesRegex(ValueError, "pinned source"):
                subject.verify(*packet, pins=pins, parent_artifacts={"identity": "experimental"},
                    dependency_versions={"torch": "pinned"}, model_path="parent32",
                    data_path="run/data", output_path="run/training")

    def test_raw_log_events_must_follow_the_actual_training_order(self):
        for mode in ("early_validation", "late_baseline", "early_final_validation"):
            packet = fixture()
            lines = packet[4].splitlines()
            if mode == "early_validation":
                event = lines.pop(90)
                lines.insert(2, event)
            elif mode == "late_baseline":
                event = lines.pop(1)
                lines.append(event)
            else:
                event = lines.pop()
                lines.insert(-1, event)
            packet[4] = "\n".join(lines)
            with self.subTest(mode=mode), self.assertRaisesRegex(ValueError, "out of order"):
                validate(packet)

if __name__ == "__main__":
    unittest.main()
