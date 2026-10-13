"""Integrity checks for assembling reviewed corrections, without model inference."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_shared_v5r7 as m

class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = m.load_sources(m.ROOT)
        parent, _ = cls.sources["shared-v5r6-en-fr"]
        errata, info = cls.sources["training-scope-errata-v1-en-fr"]
        cls.original = (parent / "train.jsonl").read_text().splitlines(keepends=True)
        cls.replacements = (errata / "train.replacements.jsonl").read_text().splitlines(keepends=True)
        cls.provenance = info["provenance"]

    def test_assembled_counts_retention_and_validation(self):
        payloads, counts, held = m.assemble(self.sources)
        rows = payloads["train.jsonl"].splitlines(keepends=True)
        self.assertEqual(counts["train"], 2065)
        self.assertEqual(counts["valid"], 275)
        self.assertEqual(sum(a == b for a,b in zip(self.original,rows)), 1957)
        self.assertEqual(payloads["valid.jsonl"], (self.sources["shared-validation-v2-en-fr"][0]/"valid.jsonl").read_text())
        self.assertEqual(set(held), {"shared-dialogue-v1-en-fr", "shared-dialogue-v2-en-fr"})
        self.assertEqual([sum(v["count"] for v in group.values()) for group in held.values()], [438,438])

    def test_changed_source_hash_rejected(self):
        with patch.object(m, "sha", return_value="0"*64), self.assertRaisesRegex(ValueError,"manifest changed"):
            m.load_sources(m.ROOT)

    def test_target_mutation_rejected(self):
        replacement = self.replacements.copy()
        row = json.loads(replacement[0]);row["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = 3
        replacement[0] = json.dumps(row)+"\n"
        with self.assertRaisesRegex(ValueError,"more than"):
            m.replace_rows(self.original,replacement,self.provenance,96)

    def test_history_mutation_rejected(self):
        replacement = self.replacements.copy()
        row = json.loads(replacement[0]);row["messages"][-2]["content"] = "Earlier user messages (background only): BAD\nCurrent request: " + self.provenance[0]["new_request"]
        replacement[0] = json.dumps(row)+"\n"
        with self.assertRaisesRegex(ValueError,"history"):
            m.replace_rows(self.original,replacement,self.provenance,96)

    def test_duplicate_index_rejected(self):
        provenance = copy.deepcopy(self.provenance);provenance[1]["source_index"] = provenance[0]["source_index"]
        with self.assertRaisesRegex(ValueError,"Duplicate replacement"):
            m.replace_rows(self.original,self.replacements,provenance,96)

    def test_no_append_instead_of_replacement(self):
        with self.assertRaisesRegex(ValueError,"counts differ"):
            m.replace_rows(self.original+self.replacements,self.replacements,self.provenance,96)

if __name__ == "__main__": unittest.main()
