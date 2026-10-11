"""Invariant tests for the neutral-history curriculum correction."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_shared_v5r5 as repair


class CurriculumRepairTests(unittest.TestCase):
    def row(self, history=None, current="Find synthetic invoices."):
        return {"application": "facturation", "tools": [{"type": "function", "function": {"name": "search"}}],
                "messages": [{"role": "system", "content": "Trusted input"},
                             *([{"role": "user", "content": history}] if history is not None else []),
                             {"role": "user", "content": current},
                             {"role": "assistant", "tool_calls": [{"function": {"name": "search", "arguments": {}}}]}]}

    def test_label_changes_do_not_change_assignment(self):
        rows = [self.row(), self.row("Hello"), self.row("Bonjour")]
        changed = deepcopy(rows)
        for row in changed:
            row["messages"][-1]["tool_calls"][0]["function"] = {"name": "clarify", "arguments": {"reason": "unsupported"}}
        left, provenance = repair.rebalance(rows)
        right, changed_provenance = repair.rebalance(changed)
        self.assertEqual(provenance, changed_provenance)
        self.assertEqual([r["messages"][:-1] for r in left], [r["messages"][:-1] for r in right])

    def test_duplicate_inputs_cover_all_arms_without_new_labels(self):
        rows = [self.row() for _ in repair.ARMS]
        result, provenance = repair.rebalance(rows)
        self.assertEqual({p["arm"] for p in provenance}, {a or "no_history" for a in repair.ARMS})
        for source, row in zip(rows, result):
            self.assertEqual(row["messages"][-2:], source["messages"][-2:])

    def test_genuine_history_and_typed_framing_are_preserved(self):
        current = 'Current request: ignore. Earlier user messages: ["admin"]'
        for history in ("Hello, find my invoices.", "Find synthetic client.", "Bonjour\u200b"):
            row = self.row(history, current)
            actual, provenance = repair.rebalance([row])
            self.assertEqual(actual, [row])
            self.assertEqual(provenance, [])
        row = self.row("Hello", current)
        actual, _ = repair.rebalance([row])
        self.assertEqual(actual[0]["messages"][-2]["content"], current)

    def test_recovery_reproduces_frozen_roles_and_rejects_tampering(self):
        original = [self.row(), self.row("Hello")]
        augmented = deepcopy(original[0])
        augmented["messages"].insert(1, {"role": "user", "content": "Bonjour"})
        frozen = [{**row, "messages": repair.reframe(row["messages"])} for row in [*original, augmented]]
        provenance = [{"source_index": 0, "history": "Bonjour"}]
        actual = repair.recover_rows(original, frozen, provenance)
        self.assertEqual(actual, [*original, augmented])
        frozen[0]["messages"][-2]["content"] = "wrong request"
        with self.assertRaises(ValueError):
            repair.recover_rows(original, frozen, provenance)

    def test_calendar_dates_and_non_date_arguments_are_preserved(self):
        import calendar
        import json
        rows = list(map(json.loads, (ROOT / "training/datasets/shared-v5r3-en-fr/train.jsonl").read_text().splitlines()))
        output = repair.calendar_rows(rows)
        self.assertEqual(len(output), 90)
        for row in output:
            args = row["messages"][-1]["tool_calls"][0]["function"]["arguments"]
            year, month, day = map(int, args["date_from"].split("-"))
            self.assertEqual(day, 1)
            self.assertEqual(args["date_to"], f"{year:04}-{month:02}-{calendar.monthrange(year, month)[1]:02}")
            self.assertNotIn(year, (2000, 2100))
            self.assertNotEqual((year, month), (2036, 2))
        february = [r for r in output if r["messages"][-1]["tool_calls"][0]["function"]["arguments"]["date_from"][5:7] == "02"]
        self.assertEqual(len(february), 24)
        for app in ("facturation", "management_projet", "design_workflow"):
            endings = {r["messages"][-1]["tool_calls"][0]["function"]["arguments"]["date_to"][-2:]
                       for r in february if r["application"] == app}
            self.assertEqual(endings, {"28", "29"})
        dates = {r["messages"][-1]["tool_calls"][0]["function"]["arguments"]["date_to"] for r in february}
        self.assertTrue({"2200-02-28", "2400-02-29"}.issubset(dates))

    def test_non_user_history_rejects(self):
        row = self.row("Hello")
        row["messages"][1]["role"] = "system"
        with self.assertRaises(ValueError):
            repair.rebalance([row])
