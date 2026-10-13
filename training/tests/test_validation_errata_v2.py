"""Future validation corrections must not alter historical inputs or targets."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_validation_errata_v2 import ROOT, SOURCE, OUTPUT, EDITS, sha, request, correct, prepare
from build_shared_v5r3 import key
from jsonschema import validate


class ValidationErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = list(map(json.loads, (SOURCE / "valid.jsonl").read_text().splitlines()))
        cls.rows = list(map(json.loads, (OUTPUT / "valid.jsonl").read_text().splitlines()))
        cls.manifest = json.loads((OUTPUT / "manifest.json").read_text())

    def test_reconstruction_and_hash_binding(self):
        rows, changes = correct(self.original)
        self.assertEqual(rows, self.rows)
        self.assertEqual(changes, self.manifest["changes"])
        self.assertEqual(sha(SOURCE / "manifest.json"), self.manifest["parent_manifest_sha256"])
        self.assertEqual(sha(SOURCE / "valid.jsonl"), self.manifest["parent_validation_sha256"])
        self.assertEqual(sha(SOURCE / "train.jsonl"), self.manifest["unchanged_training_sha256"])
        self.assertEqual(sha(ROOT / "training/scripts/prepare_validation_errata_v2.py"), self.manifest["generator_sha256"])
        self.assertEqual(sha(OUTPUT / "valid.jsonl"), self.manifest["files"]["valid.jsonl"])

    def test_only_current_request_changes_and_every_target_validates(self):
        for old, new in zip(self.original, self.rows):
            copy = deepcopy(new)
            copy["messages"][-2]["content"] = old["messages"][-2]["content"]
            self.assertEqual(copy, old)
            before = old["messages"][-2]["content"].removesuffix(request(old))
            after = new["messages"][-2]["content"].removesuffix(request(new))
            self.assertEqual(before, after)
            fn = new["messages"][-1]["tool_calls"][0]["function"]
            offered = {t["function"]["name"]:t["function"]["parameters"] for t in new["tools"]}
            validate(fn["arguments"], offered[fn["name"]])

    def test_all_history_variants_and_unchanged_bytes(self):
        amendments = {request(self.original[i]): request(self.rows[i]) for i in EDITS}
        changed = 0
        raw_old = (SOURCE / "valid.jsonl").read_bytes().splitlines(keepends=True)
        raw_new = (OUTPUT / "valid.jsonl").read_bytes().splitlines(keepends=True)
        for i, (old, new) in enumerate(zip(self.original, self.rows)):
            if request(old) in amendments:
                self.assertEqual(request(new), amendments[request(old)])
                changed += 1
            else:
                self.assertEqual(raw_old[i], raw_new[i])
        self.assertEqual((len(amendments), changed), (39, 47))
        self.assertEqual(self.manifest["unchanged_count"], 228)

    def test_native_filter_scope_is_explicit(self):
        self.assertIn("article records", request(self.rows[22]))
        self.assertIn("reference or designation", request(self.rows[22]))
        self.assertIn("référence ou désignation", request(self.rows[23]))
        self.assertIn("stage, description or notes", request(self.rows[139]))
        self.assertIn("l’étape, la description ou les notes", request(self.rows[138]))
        self.assertIn("fournisseur", request(self.rows[164]))
        self.assertIn("supplier", request(self.rows[165]))

    def test_changed_requests_excluded_from_training_and_held_out(self):
        excluded = set()
        for folder in ("shared-v5r6-en-fr", "selection-contrasts-v1-en-fr"):
            for row in map(json.loads, (ROOT / "training/datasets" / folder / "train.jsonl").read_text().splitlines()):
                excluded.add(key(row["application"], request(row)))
        for version in (1, 2):
            folder = ROOT / "training/datasets" / f"shared-dialogue-v{version}-en-fr"
            manifest = json.loads((folder / "manifest.json").read_text())
            for name in manifest["inputs"]:
                for row in map(json.loads, (folder / name).read_text().splitlines()):
                    app = json.loads(row["messages"][0]["content"].split("Trusted context: ", 1)[1])["application"]
                    text = row["messages"][-1]["content"].split("\nCurrent request: ", 1)[-1]
                    excluded.add(key(app, text))
        for proof in self.manifest["changes"]:
            row = self.rows[proof["index"]]
            self.assertNotIn(key(row["application"], request(row)), excluded)

    def test_refuses_changed_source_and_existing_output(self):
        rows = deepcopy(self.original)
        rows[2]["messages"][-2]["content"] = "Unreviewed request."
        with self.assertRaises(ValueError):
            correct(rows)
        with self.assertRaises(ValueError):
            prepare()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "manifest.json").write_text('{"version":"shared-v5r6-en-fr"}')
            with self.assertRaisesRegex(ValueError, "Parent manifest changed"):
                prepare(source, Path(directory) / "new")


if __name__ == "__main__":
    unittest.main()
