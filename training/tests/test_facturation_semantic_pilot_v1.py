"""Verify byte-preserved subset assembly and fail-closed source checks."""
import hashlib,json,sys,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import prepare_facturation_semantic_pilot_v1 as subject

def fixture():
    rows=[]
    for app,count in (("facturation",200),("management_projet",112),("design_workflow",72)):
        rows.extend(json.dumps({"application":app,"id":len(rows)+i}).encode() for i in range(count))
    contrasts=[json.dumps({"application":"facturation","contrast":i}).encode() for i in range(116)]
    filler=[json.dumps({"application":"facturation","other":i}).encode() for i in range(320)]
    pack=lambda lines:b"\n".join(lines)+b"\n"
    return ({"train.jsonl":pack(rows)},{"train.jsonl":pack(rows+filler+contrasts),
              "contrasts.jsonl":pack(contrasts)},pack(rows+contrasts))

class PilotAssemblyTests(unittest.TestCase):
    def test_complete_subset_is_byte_preserved(self):
        replay,semantic,expected=fixture()
        with patch.object(subject,"TRAIN_SHA256",subject.sha(expected)):
            self.assertEqual(subject.assemble(replay,semantic),expected)

    def test_dropped_or_duplicate_replay_is_rejected(self):
        for kind in ("drop","duplicate"):
            replay,semantic,_=fixture();rows=replay["train.jsonl"].splitlines()
            if kind=="drop":rows.pop()
            else:rows[-1]=rows[0]
            replay["train.jsonl"]=b"\n".join(rows)+b"\n"
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                subject.assemble(replay,semantic)

    def test_modified_or_missing_contrasts_are_rejected(self):
        for kind in ("modify","drop"):
            replay,semantic,_=fixture()
            semantic["contrasts.jsonl"]=(semantic["contrasts.jsonl"].replace(b'"contrast": 0',b'"contrast": 9')
                if kind=="modify" else b"\n".join(semantic["contrasts.jsonl"].splitlines()[:-1])+b"\n")
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                subject.assemble(replay,semantic)

    def test_real_identity_is_required_even_when_counts_match(self):
        replay,semantic,_=fixture()
        with self.assertRaisesRegex(ValueError,"identity"):
            subject.assemble(replay,semantic)

if __name__=="__main__": unittest.main()
