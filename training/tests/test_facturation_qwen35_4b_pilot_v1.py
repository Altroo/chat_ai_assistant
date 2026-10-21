"""Coverage and immutable-source checks for the bounded 4B training pilot."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_facturation_qwen35_4b_pilot_v1 as pilot


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (pilot.PARENT / "train.jsonl").read_bytes()
        cls.rows = [json.loads(line) for line in cls.raw.splitlines()]
        cls.manifest = json.loads((pilot.PARENT / "manifest.json").read_text())
        cls.prior, cls.pins = pilot.helpers(cls.manifest)
        cls.plan = pilot.select(cls.rows, cls.prior)
        cls.output = ROOT / "training/datasets" / pilot.VERSION

    def test_actual_projection_and_native_tools_are_preserved(self):
        self.assertEqual(self.plan["count"], 632)
        self.assertEqual(len(self.plan["by_tool"]), 18)
        self.assertEqual(self.plan["projected_features_available"], 1551)
        self.assertEqual(self.plan["projected_features_selected"], 1551)
        self.assertEqual(self.plan["uncovered_projected_features"], [])
        self.assertTrue(self.plan["mandatory_rows_present"])
        self.assertFalse(self.plan["evaluation_outcomes_used"])

    def test_selected_rows_and_validation_are_byte_identical(self):
        lines = self.raw.splitlines(keepends=True)
        expected = b"".join(lines[i] for i in self.plan["source_indices_zero_based"])
        self.assertEqual((self.output / "train.jsonl").read_bytes(), expected)
        self.assertEqual((self.output / "valid.jsonl").read_bytes(),
                         (pilot.PARENT / "valid.jsonl").read_bytes())
        manifest = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual(manifest["files"]["train.jsonl"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(manifest["helper_sha256"], self.pins)

    def test_budget_cannot_silently_drop_required_axes(self):
        with self.assertRaisesRegex(ValueError, "cannot preserve declared coverage"):
            pilot.select(self.rows, self.prior, maximum=631)

    def test_argument_omission_and_false_are_distinct(self):
        original = deepcopy(next(r for r in self.rows if
            r["messages"][-1]["tool_calls"][0]["function"]["name"] == "search_invoices"))
        missing = deepcopy(original)
        false = deepcopy(original)
        missing["messages"][-1]["tool_calls"][0]["function"]["arguments"].pop("unpaid", None)
        false["messages"][-1]["tool_calls"][0]["function"]["arguments"]["unpaid"] = False
        absent_features = pilot.features(missing, "en", self.prior)
        false_features = pilot.features(false, "en", self.prior)
        self.assertIn(("argument_presence", "search_invoices", "en", "unpaid", "False"), absent_features)
        self.assertIn(("argument_presence", "search_invoices", "en", "unpaid", "True"), false_features)
        self.assertNotEqual(absent_features, false_features)

    def test_unknown_metadata_is_disclosed_without_ui_inference(self):
        self.assertEqual(self.plan["source_unknown_language_rows"], 136)
        self.assertEqual(self.plan["by_request_language"], {"en": 299, "fr": 301, "unknown": 32})
        self.assertEqual(sum(self.plan["by_request_language"].values()), 632)

    def test_incomplete_parent_and_existing_output_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Complete reviewed corpus"):
            pilot.select(self.rows[:-1], self.prior)
        with self.assertRaisesRegex(ValueError, "New isolated output"):
            pilot.prepare(self.output)


if __name__ == "__main__":
    unittest.main()
