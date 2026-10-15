"""Retained curriculum and frozen evaluations must survive coverage assembly."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_shared_v5r10 as m


class SharedV5R10Tests(unittest.TestCase):
    def test_exact_retention_and_frozen_evaluations(self):
        source = m.ROOT / "training/datasets" / m.PARENT
        extra = m.ROOT / "training/datasets" / m.SUPPLEMENT
        parent = json.loads((source / "manifest.json").read_text())
        with patch.object(m, "native_union", return_value=parent["native_metadata"]):
            payloads, manifest = m.assemble({})
        self.assertEqual(payloads["train.jsonl"], (source / "train.jsonl").read_bytes() + (extra / "train.jsonl").read_bytes())
        self.assertEqual(payloads["valid.jsonl"], (source / "valid.jsonl").read_bytes())
        for field in ("held_out", "historical_regression_held_out", "fresh_controls", "corrections"):
            self.assertEqual(manifest[field], parent[field])
        self.assertEqual(manifest["counts"]["train"], 2419)
        self.assertEqual(manifest["counts"]["retained_parent_rows_byte_identical"], 2339)
        self.assertIn("UNBOUND", manifest["model_binding"]["status"])

    def test_native_metadata_conflict_is_rejected(self):
        parent = {"facturation": {"chat_ai/tools.py": "a"}}
        supplement = {"facturation": {"chat_ai/tools.py": "b"}}
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            m.native_union(parent, supplement, {"facturation": Path(".")})

    def test_missing_application_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "three"):
            m.native_union({"facturation": {}}, {}, {"facturation": Path(".")})

    def test_changed_supplement_payload_is_rejected_before_use(self):
        folder = m.ROOT / "training/datasets" / m.SUPPLEMENT
        original = m.sha
        with patch.object(m, "sha", side_effect=lambda p: "0"*64 if p == folder / "train.jsonl" else original(p)):
            with self.assertRaisesRegex(ValueError, "payload"):
                m.read_bound(folder, m.SUPPLEMENT_SHA)


if __name__ == "__main__":
    unittest.main()
