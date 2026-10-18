"""Frozen TRAIN schedule and candidate corpus isolation checks."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
spec = importlib.util.spec_from_file_location("refinement", ROOT / "training/scripts/prepare_facturation_search_refinement_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(text="Find stock.", language="en"):
    return {"application": "facturation", "language": language, "messages": [
        {"role": "system", "content": 'Trusted context: {}'},
        {"role": "user", "content": text},
        {"role": "assistant", "tool_calls": [{"function": {"name": "search",
            "arguments": {"resource": "stock_balance"}}}]}],
        "tools": [{"function": {"name": "search", "parameters": {
            "type": "object", "properties": {"resource": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1}}, "required": ["resource"],
            "additionalProperties": False}}}]}


def selection():
    rows = [row(f"Question {index}") for index in range(2975)]
    indices = list(range(2283))
    plan = {"audit": {"input_sha256": {"train": m.prior.SOURCE_SHA256["train.jsonl"]},
        "rehearsal": {"count": 2283, "row_indices": indices,
        "selected_rows_sha256": m.prior.digest(m.prior.encoded(rows[:2283]).encode())}}}
    return rows, plan


class RefinementTests(unittest.TestCase):
    def test_exact_prior_schedule_preserved_including_row_order(self):
        rows, plan = selection()
        raw = json.dumps(plan).encode()
        before = deepcopy(rows)
        with patch.object(m, "PLAN_SHA256", hashlib.sha256(raw).hexdigest()):
            self.assertEqual(m.retained(rows, raw), list(range(2283)))
        self.assertEqual(rows, before)

    def test_changed_plan_and_changed_selected_row_rejected(self):
        rows, plan = selection()
        raw = json.dumps(plan).encode()
        with self.assertRaises(ValueError): m.retained(rows, raw)
        with patch.object(m, "PLAN_SHA256", hashlib.sha256(raw).hexdigest()):
            rows[3]["messages"][-2]["content"] = "Changed"
            with self.assertRaises(ValueError): m.retained(rows, raw)

    def test_duplicate_and_out_of_range_indices_rejected_even_if_plan_rebound(self):
        for bad in (0, 2975, True):
            rows, plan = selection()
            plan["audit"]["rehearsal"]["row_indices"][-1] = bad
            raw = json.dumps(plan).encode()
            with patch.object(m, "PLAN_SHA256", hashlib.sha256(raw).hexdigest()):
                with self.subTest(index=bad), self.assertRaises(ValueError): m.retained(rows, raw)

    def test_valid_schema_passes_and_wrong_argument_type_fails(self):
        m.validate_rows([row()], [])
        invalid = row()
        invalid["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = "two"
        with self.assertRaises(Exception) as error: m.validate_rows([invalid], [])
        self.assertEqual(type(error.exception).__name__, "ValidationError")

    def test_unoffered_target_fails(self):
        invalid = row()
        invalid["tools"] = []
        with self.assertRaises(ValueError): m.validate_rows([invalid], [])

    def test_duplicates_and_conflicting_targets_fail(self):
        first, second = row(), row()
        with self.assertRaises(ValueError): m.validate_rows([first, second], [])
        second["messages"][-1]["tool_calls"][0]["function"]["arguments"]["resource"] = "stock_receipt"
        with self.assertRaises(ValueError): m.validate_rows([first, second], [])

    def test_development_overlap_including_neutral_wrapper_fails(self):
        variant = row()
        variant["messages"][-2]["content"] = 'Earlier user messages (background only): ["Hello"]\nCurrent request: Find stock.'
        with self.assertRaises(ValueError): m.validate_rows([variant], [row()])

    def test_unapproved_app_and_language_fail(self):
        for field, value in (("application", "contracts"), ("language", "ar"), ("language", "ary")):
            invalid = row()
            invalid[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                m.validate_rows([invalid], [])

    def test_existing_or_nested_output_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = [root / name for name in ("original", "profiles", "natural", "roles")]
            for directory in roots: directory.mkdir()
            plan = root / "selection" / "plan.json"
            for output in [*roots, *(p / "child" for p in roots), plan.parent / "child"]:
                with self.subTest(output=output), self.assertRaises(ValueError):
                    m.prepare(*roots, plan, output)

    def test_changed_original_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = [root / name for name in ("original", "profiles", "natural", "roles")]
            roots[0].mkdir()
            for name in m.prior.SOURCE_SHA256: (roots[0] / name).write_text("{}")
            output = root / "candidate"
            with self.assertRaises(ValueError): m.prepare(*roots, root / "selection/plan.json", output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
