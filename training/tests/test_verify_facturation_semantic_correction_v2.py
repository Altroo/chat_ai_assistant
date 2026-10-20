"""Reject inconsistent terminal evidence without loading model weights."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_facturation_semantic_correction_v2 as subject
from validation_selection import ValidationSelection
from test_facturation_semantic_correction_training_v2 import training

SOURCE = (Path(__file__).resolve().parents[1] / "scripts/validation_selection.py").read_bytes()
DIGEST = hashlib.sha256(SOURCE).hexdigest()


def fixture(values=(.4, .2, .3)):
    report = training()
    history = []
    def loss(value):
        return {"micro": value, "macro": value,
                "by_application": {app: value for app in report["application_exposure"]},
                "unweighted": {"micro": value/2, "macro": value/2,
                              "by_application": {app: value/2 for app in report["application_exposure"]}}}
    history.append({"step": 0, "loss": loss(values[0])})
    state = ValidationSelection(history[0]["loss"], report["application_exposure"])
    adapter = None
    for step, value in zip((64, 128), values[1:]):
        measured = loss(value)
        improved = state.observe(step, measured)
        if improved:
            adapter = "selected-" + str(step)
        history.append({"step": step, "loss": measured, "improved": improved,
                        "selected_step": state.best_step})
    report["validation_history"] = history
    report["checkpoint_selection"] = {"metric": "validation application-macro semantic loss",
        "step": state.best_step, "adapter": adapter, "validation": state.best}
    for prefix, measured in (("baseline", history[0]["loss"]), ("final", history[-1]["loss"])):
        report[prefix+"_validation_by_application"] = measured
        report[prefix+"_validation_loss"] = measured["micro"]
        report[prefix+"_validation_unweighted_loss"] = measured["unweighted"]["micro"]
    for metric in report["steps_metrics"]:
        metric["rss_bytes"] = 1000000
    report["validation_selection_script"] = {"sha256": DIGEST}
    provenance = {key: deepcopy(report.get(key, "synthetic")) for key in subject.PROVENANCE_KEYS}
    provenance["provenance_version"] = 1
    report.update(deepcopy(provenance))
    saved = {"metric": "validation application-macro semantic loss",
             "selected_step": state.best_step, "selected_adapter": adapter,
             "validation": state.best,
             "policy": "Baseline remains selected unless validation improves. This is not model acceptance."}
    events = [{"baseline_validation_loss": history[0]["loss"]},
              *deepcopy(report["steps_metrics"]),
              *[{"validation_checkpoint": entry} for entry in history[1:]]]
    log = "Loading synthetic fixture\n" + "\n".join(json.dumps(event) for event in events)
    return [report, provenance, deepcopy(history), saved, log, SOURCE, DIGEST]


class TerminalEvidenceTests(unittest.TestCase):
    def test_replays_baseline_midpoint_and_final_choices_without_acceptance(self):
        for values, selected in (((.1,.2,.3),0), ((.4,.2,.3),64), ((.4,.3,.2),128)):
            packet = fixture(values)
            before = deepcopy(packet)
            result = subject.verify(*packet)
            self.assertEqual(packet, before)
            self.assertEqual(result["loss_selected_step"], selected)
            self.assertFalse(result["model_accepted"])

    def test_false_weighted_or_unweighted_macro_is_rejected(self):
        for mode in ("weighted", "unweighted"):
            packet = fixture()
            loss = packet[0]["validation_history"][1]["loss"]
            if mode == "unweighted":
                loss = loss["unweighted"]
            loss["macro"] += .01
            packet[2] = deepcopy(packet[0]["validation_history"])
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.verify(*packet)

    def test_report_and_saved_selection_cannot_lie(self):
        for index, field in ((0, "checkpoint_selection"), (3, None)):
            packet = fixture()
            if field: packet[index][field]["step"] = 128
            else: packet[index]["selected_step"] = 128
            with self.subTest(index=index), self.assertRaises(ValueError):
                subject.verify(*packet)

    def test_raw_history_must_match_report(self):
        packet = fixture(); packet[2][1]["selected_step"] = 128
        with self.assertRaises(ValueError): subject.verify(*packet)

    def test_provenance_cannot_be_empty_or_disagree(self):
        for mode in ("empty", "changed"):
            packet = fixture()
            if mode == "empty": packet[1] = {}
            else: packet[1]["training_config"]["learning_rate"] = .5
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.verify(*packet)

    def test_missing_duplicate_or_forged_printed_updates_are_rejected(self):
        for mode in ("missing", "duplicate", "changed"):
            packet = fixture(); lines = packet[4].splitlines()
            if mode == "missing": lines.pop(2)
            elif mode == "duplicate": lines.append(lines[2])
            else:
                event = json.loads(lines[2]); event["loss"] = 99; lines[2] = json.dumps(event)
            packet[4] = "\n".join(lines)
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                subject.verify(*packet)

    def test_baseline_and_validation_log_events_are_required(self):
        for needle in ('"baseline_validation_loss"', '"validation_checkpoint"'):
            packet = fixture()
            packet[4] = "\n".join(line for line in packet[4].splitlines() if needle not in line)
            with self.subTest(needle=needle), self.assertRaises(ValueError):
                subject.verify(*packet)

    def test_summary_and_selector_source_are_coupled(self):
        packet = fixture(); packet[0]["final_validation_loss"] = 99
        with self.assertRaises(ValueError): subject.verify(*packet)
        packet = fixture(); packet[-1] = "0"*64
        with self.assertRaisesRegex(ValueError, "source changed"): subject.verify(*packet)


if __name__ == "__main__":
    unittest.main()
