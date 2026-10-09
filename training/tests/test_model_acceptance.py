import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
from model_acceptance import assess, clarification_message


def scenario(identifier, tool="search_records", arguments=None, language="en", category="test"):
    expected = {"tool": tool, "arguments": arguments if arguments is not None else {"resource": "project"}}
    row = {"id": identifier, "category": category, "language": language, "expected": expected}
    action = {"tool": tool, "arguments": copy.deepcopy(expected["arguments"])}
    if tool == "clarify":
        action = {"tool": tool, "message": clarification_message(**expected["arguments"])}
    event = {**row, "action": action, "structured_valid": True}
    return row, event


class ModelAcceptanceTests(unittest.TestCase):
    def test_wrong_clarifications_cannot_hide_behind_perfect_aggregate_scores(self):
        pairs = [scenario("ordinary-" + str(i)) for i in range(26)]
        for i in range(6):
            row, event = scenario("clarify-" + str(i), "clarify", {"reason": "unsupported", "language": "en"})
            event["action"]["message"] = clarification_message("missing_details", "en")
            pairs.append((row, event))
        report = assess([pair[0] for pair in pairs], [pair[1] for pair in pairs])
        self.assertEqual(report["metrics"]["percent"]["tool_correct"], 100)
        self.assertEqual(report["metrics"]["exact_arguments"]["percent"], 100)
        self.assertFalse(report["model_targets_passed"])
        self.assertEqual(report["clarifications"]["counts"]["action_matches"], 0)

    def test_wrong_proposed_change_fails_even_when_exact_arguments_reach_99_percent(self):
        pairs = [scenario("ordinary-" + str(i)) for i in range(99)]
        row, event = scenario("change", "prepare_change", {"resource": "client", "identifier": 12, "operation": "update", "changes": {"ville": "Oujda"}})
        event["action"]["arguments"]["identifier"] = 13
        pairs.append((row, event))
        report = assess([pair[0] for pair in pairs], [pair[1] for pair in pairs])
        self.assertEqual(report["metrics"]["exact_arguments"]["percent"], 99)
        self.assertFalse(report["targets"]["critical_model_cases"])
        self.assertFalse(report["model_targets_passed"])

    def test_unrequested_change_is_critical_even_during_an_expected_read(self):
        pairs = [scenario("read-" + str(i)) for i in range(100)]
        pairs[0][1]["action"] = {"tool": "prepare_change", "arguments": {"resource": "project", "identifier": 12, "operation": "archive"}}
        report = assess([pair[0] for pair in pairs], [pair[1] for pair in pairs])
        self.assertEqual(report["metrics"]["percent"]["tool_correct"], 99)
        self.assertEqual(report["metrics"]["exact_arguments"]["percent"], 99)
        self.assertEqual(report["critical_model_cases"]["count"], 1)
        self.assertFalse(report["model_targets_passed"])

    def test_rounding_cannot_turn_under_target_structure_into_a_pass(self):
        pairs = [scenario("row-" + str(i)) for i in range(499)]
        for pair in pairs[:5]:
            pair[1]["structured_valid"] = False
            pair[1].pop("action")
        report = assess([pair[0] for pair in pairs], [pair[1] for pair in pairs])
        self.assertEqual(report["metrics"]["percent"]["structured_valid"], 99)
        self.assertFalse(report["targets"]["structured_output"])
        self.assertFalse(report["model_targets_passed"])

    def test_missing_duplicate_and_relabeled_events_are_rejected(self):
        row, event = scenario("one")
        with self.assertRaises(ValueError):
            assess([row], [])
        with self.assertRaises(ValueError):
            assess([row], [event, event])
        changed = copy.deepcopy(event)
        changed["expected"]["arguments"]["resource"] = "supplier"
        with self.assertRaises(ValueError):
            assess([row], [changed])

    def test_bilingual_scenarios_and_security_groups_are_reported_without_relabeling(self):
        pairs = [scenario("management-projet-v3-en-fr-audit-denied-" + language, "clarify", {"reason": "unsupported", "language": language}, language, "audit") for language in ["fr", "en"]]
        snapshot = [pair[0] for pair in pairs]
        before = copy.deepcopy(snapshot)
        report = assess(snapshot, [pair[1] for pair in pairs])
        self.assertEqual(snapshot, before)
        self.assertEqual(report["distinct_bilingual_scenario_ids"], 1)
        self.assertEqual(report["by_reporting_group"]["permission_denial"]["count"], 2)
        self.assertIsNone(report["native_backend_security_verified"])


if __name__ == "__main__":
    unittest.main()
