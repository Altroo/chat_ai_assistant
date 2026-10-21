"""Adversarial tests for terminal execution identity, without systemd or models."""
from copy import deepcopy
from pathlib import Path
import importlib.util
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts/verify_terminal_execution.py"
SPEC = importlib.util.spec_from_file_location("terminal_execution_under_test", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def records():
    prefix = ("{ path=/srv/example/venv/bin/python ; "
              "argv[]=/srv/example/venv/bin/python -B /srv/example/controller.py "
              "--binding-sha256 " + "a" * 64 + " --admission-sha256 " + "b" * 64 +
              " ; ignore_errors=no ; ")
    original = prefix + ("start_time=[Wed 2026-07-01 12:00:00 CEST] ; "
                        "stop_time=[Wed 2026-07-01 12:01:00 CEST] ; "
                        "pid=1239 ; code=exited ; status=0 }")
    cleared = prefix + ("start_time=[n/a] ; stop_time=[n/a] ; "
                       "pid=0 ; code=(null) ; status=0/0 }")
    unit = {"MainPID": "0", "SubState": "exited", "Result": "success",
            "ExecMainStatus": "0", "InvocationID": "c" * 32, "ExecStart": original,
            "CPUQuotaPerSecUSec": "14s", "MemoryMax": "10737418240",
            "MemorySwapMax": "0", "KillMode": "control-group", "User": "operator",
            "RuntimeMaxUSec": "5h"}
    execution = {"InvocationID": "c" * 32, "ExecMainPID": "1239", "ExecMainCode": "1",
                 "ExecMainStatus": "0", "NRestarts": "0",
                 "ExecMainStartTimestamp": "Wed 2026-07-01 10:00:00 UTC",
                 "ExecMainExitTimestamp": "Wed 2026-07-01 10:01:00 UTC",
                 "ExecMainStartTimestampMonotonic": "100000000",
                 "ExecMainExitTimestampMonotonic": "160000000"}
    return unit, {**unit, "ExecStart": cleared}, execution


class TerminalExecutionTests(unittest.TestCase):
    def verify(self, original, current, execution):
        return MODULE.verify_terminal_execution(original, current, execution)

    def test_original_presentation_is_valid(self):
        original, _, execution = records()
        self.assertFalse(self.verify(original, deepcopy(original), execution)["execstart_presentation_cleared"])

    def test_cleared_presentation_requires_original_main_identity(self):
        original, current, execution = records()
        result = self.verify(original, current, execution)
        self.assertTrue(result["verified"])
        self.assertTrue(result["execstart_presentation_cleared"])
        self.assertEqual(result["original_controller_pid"], 1239)

    def test_timezone_equivalent_populated_presentation_is_valid(self):
        original, _, execution = records()
        current = deepcopy(original)
        current["ExecStart"] = current["ExecStart"].replace("12:00:00 CEST", "10:00:00 UTC").replace("12:01:00 CEST", "10:01:00 UTC")
        self.assertTrue(self.verify(original, current, execution)["verified"])

    def test_every_stable_unit_field_is_enforced(self):
        for key in MODULE.UNIT_FIELDS - {"ExecStart"}:
            with self.subTest(key=key):
                original, current, execution = records()
                current[key] += "-changed"
                with self.assertRaises(ValueError):
                    self.verify(original, current, execution)

    def test_missing_or_extra_unit_fields_are_rejected(self):
        for side in ("original", "current"):
            for mode in ("missing", "extra", "wrong_type"):
                with self.subTest(side=side, mode=mode):
                    original, current, execution = records()
                    selected = original if side == "original" else current
                    if mode == "missing":
                        selected.pop("User")
                    elif mode == "extra":
                        selected["other"] = "value"
                    else:
                        selected["MainPID"] = 0
                    with self.assertRaises(ValueError):
                        self.verify(original, current, execution)

    def test_configured_command_changes_are_rejected(self):
        for before, after in (
                ("/srv/example/venv/bin/python", "/srv/other/bin/python"),
                ("a" * 64, "d" * 64), ("b" * 64, "e" * 64),
                ("ignore_errors=no", "ignore_errors=yes")):
            with self.subTest(before=before):
                original, current, execution = records()
                current["ExecStart"] = current["ExecStart"].replace(before, after)
                with self.assertRaises(ValueError):
                    self.verify(original, current, execution)

    def test_multiple_commands_are_rejected(self):
        original, current, execution = records()
        current["ExecStart"] += current["ExecStart"]
        with self.assertRaises(ValueError):
            self.verify(original, current, execution)

    def test_cleared_original_is_not_completion_evidence(self):
        original, current, execution = records()
        original["ExecStart"] = current["ExecStart"]
        with self.assertRaises(ValueError):
            self.verify(original, current, execution)

    def test_partially_cleared_metadata_is_rejected(self):
        for before, after in (("pid=0", "pid=1239"), ("code=(null)", "code=exited"),
                              ("status=0/0", "status=0")):
            with self.subTest(before=before):
                original, current, execution = records()
                current["ExecStart"] = current["ExecStart"].replace(before, after)
                with self.assertRaises(ValueError):
                    self.verify(original, current, execution)

    def test_changed_actual_execution_identity_is_rejected(self):
        mutations = {"InvocationID": "d" * 32, "ExecMainPID": "1240", "ExecMainCode": "2",
                     "ExecMainStatus": "1", "NRestarts": "1",
                     "ExecMainStartTimestamp": "Wed 2026-07-01 09:59:59 UTC",
                     "ExecMainExitTimestamp": "Wed 2026-07-01 10:01:01 UTC",
                     "ExecMainStartTimestampMonotonic": "0",
                     "ExecMainExitTimestampMonotonic": "90000000"}
        for key, value in mutations.items():
            with self.subTest(key=key):
                original, current, execution = records()
                execution[key] = value
                with self.assertRaises(ValueError):
                    self.verify(original, current, execution)

    def test_missing_execution_identity_is_rejected(self):
        for key in MODULE.EXECUTION_FIELDS:
            with self.subTest(key=key):
                original, current, execution = records()
                del execution[key]
                with self.assertRaises(ValueError):
                    self.verify(original, current, execution)

    def test_invalid_timezone_calendar_and_weekday_are_rejected(self):
        for text in ("Wed 2026-07-01 10:00:00 UNKNOWN", "Wed 2026-02-31 10:00:00 UTC",
                     "Thu 2026-07-01 10:00:00 UTC"):
            with self.subTest(text=text):
                original, current, execution = records()
                execution["ExecMainStartTimestamp"] = text
                with self.assertRaises(ValueError):
                    self.verify(original, current, execution)

    def test_inconsistent_monotonic_duration_is_rejected(self):
        original, current, execution = records()
        execution["ExecMainExitTimestampMonotonic"] = "170000000"
        with self.assertRaises(ValueError):
            self.verify(original, current, execution)


if __name__ == "__main__":
    unittest.main()
