"""Training corrections must replace exact source rows without changing actions."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_training_scope_errata import ROOT,SOURCE,OUTPUT,CHANGES,sha,request,replacements,prepare
from build_shared_v5r3 import key

class TrainingScopeErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=list(map(json.loads,(SOURCE/"train.jsonl").read_text().splitlines()))
        cls.rows=list(map(json.loads,(OUTPUT/"train.replacements.jsonl").read_text().splitlines()))
        cls.manifest=json.loads((OUTPUT/"manifest.json").read_text())

    def test_exact_reconstruction_and_source_hashes(self):
        values,proof=replacements(self.source)
        self.assertEqual(values,self.rows)
        self.assertEqual(proof,self.manifest["provenance"])
        self.assertEqual(sha(SOURCE/"manifest.json"),self.manifest["parent_manifest_sha256"])
        self.assertEqual(sha(SOURCE/"train.jsonl"),self.manifest["parent_training_sha256"])
        self.assertEqual(sha(SOURCE/"valid.jsonl"),self.manifest["unchanged_validation_sha256"])
        self.assertEqual(sha(ROOT/"training/scripts/prepare_training_scope_errata.py"),self.manifest["generator_sha256"])
        self.assertEqual(sha(OUTPUT/"train.replacements.jsonl"),self.manifest["files"]["train.replacements.jsonl"])

    def test_replacements_preserve_targets_context_history_and_size(self):
        replaced=deepcopy(self.source)
        for row,proof in zip(self.rows,self.manifest["provenance"]):
            index=proof["source_index"]
            old=self.source[index]
            copy=deepcopy(row)
            copy["messages"][-2]["content"]=old["messages"][-2]["content"]
            self.assertEqual(copy,old)
            self.assertEqual(old["messages"][-2]["content"].removesuffix(request(old)),
                             row["messages"][-2]["content"].removesuffix(request(row)))
            replaced[index]=row
        self.assertEqual(len(replaced),1969)
        self.assertEqual(sum(a!=b for a,b in zip(self.source,replaced)),12)
        self.assertEqual(self.manifest["unchanged_rows"],1957)

    def test_new_requests_excluded_from_validation_and_evaluations(self):
        excluded=set()
        for version in ("shared-v5r6-en-fr","shared-validation-v2-en-fr"):
            for row in map(json.loads,(ROOT/"training/datasets"/version/"valid.jsonl").read_text().splitlines()):
                excluded.add(key(row["application"],request(row)))
        for version in (1,2):
            folder=ROOT/"training/datasets"/f"shared-dialogue-v{version}-en-fr"
            manifest=json.loads((folder/"manifest.json").read_text())
            for name in manifest["inputs"]:
                for row in map(json.loads,(folder/name).read_text().splitlines()):
                    app=json.loads(row["messages"][0]["content"].split("Trusted context: ",1)[1])["application"]
                    text=row["messages"][-1]["content"].split("\nCurrent request: ",1)[-1]
                    excluded.add(key(app,text))
        changed=set()
        for row in self.rows:
            identity=key(row["application"],request(row))
            self.assertNotIn(identity,excluded)
            self.assertNotIn(identity,changed)
            changed.add(identity)

    def test_refuses_source_drift_and_existing_version(self):
        source=deepcopy(self.source)
        source[72]["messages"][-2]["content"]="Unreviewed request."
        with self.assertRaises(ValueError):replacements(source)
        with self.assertRaises(ValueError):replacements(self.source[:-1])
        with self.assertRaises(ValueError):prepare()

if __name__=="__main__":unittest.main()
