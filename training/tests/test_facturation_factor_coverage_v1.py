"""Portable synthetic data guards, not model accuracy or real-corpus results."""
from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
from test_facturation_semantic_correction_v2 import source_rows

spec=importlib.util.spec_from_file_location("factor_generator",ROOT/"training/scripts/prepare_facturation_factor_coverage_v1.py")
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)

def fixture_row(template, request, application="facturation"):
    row=deepcopy(template)
    row["application"]=application
    row["language"]="en"
    row["messages"][-2]["content"]='Earlier user messages (background only): ["Hello"]\nCurrent request: '+request
    context=json.loads(row["messages"][0]["content"].split("Trusted context: ",1)[1])
    context["application"]=application
    row["messages"][0]["content"]="Synthetic verified context.\nTrusted context: "+json.dumps(context)
    return row


class DataGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory(prefix="factor-data-fixture-")
        cls.root=Path(cls.workspace.name)
        cls.base=cls.root/"base";cls.base.mkdir()
        cls.approved=cls.root/"approved";cls.approved.mkdir()
        cls.native=cls.root/"native";cls.native.mkdir()
        cls.source=source_rows()
        cls.source[96]["language"]="en"
        cls.source[110]["messages"][-2]["content"]='Earlier user messages (background only): ["Hello"]\nCurrent request: Amène-moi à la page de liste des utilisateurs.'
        cls.source_raw=b"".join(g.encode(row) for row in cls.source)
        cls.original=[deepcopy(cls.source[n-1]) for n in (390,401,410,414)]
        for app,count in (("facturation",92),("management_projet",16),("design_workflow",16)):
            cls.original.extend(fixture_row(cls.source[0],f"Synthetic retained baseline {app} {i}",app)
                                for i in range(count))
        cls.base_raw=b"".join(g.encode(row) for row in cls.original)
        cls.valid_raw=b"".join(g.encode(fixture_row(cls.source[0],f"Synthetic excluded validation {i}"))
                              for i in range(275))
        (cls.base/"train.jsonl").write_bytes(cls.base_raw)
        (cls.approved/"train.jsonl").write_bytes(cls.source_raw)
        for folder in (cls.base,cls.approved):(folder/"valid.jsonl").write_bytes(cls.valid_raw)
        cls.excluded=[]
        for label,count in (("primary",133),("regression",438),("controls",48)):
            path=cls.root/(label+".jsonl")
            path.write_bytes(b"".join(g.encode(fixture_row(cls.source[0],f"Synthetic excluded {label} {i}"))
                                      for i in range(count)))
            cls.excluded.append(path)
        cls.old=g.helper()
        cls.native_hashes={}
        for name in cls.old.NATIVE_SHA256:
            path=cls.native/name;path.parent.mkdir(parents=True,exist_ok=True)
            payload=("# Synthetic native contract fixture "+name+"\n").encode()
            path.write_bytes(payload);cls.native_hashes[name]=g.sha(payload)
    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()
    def fixture_pins(self):
        stack=ExitStack()
        stack.enter_context(patch.multiple(g,BASE_SHA=g.sha(self.base_raw),
                             SOURCE_SHA=g.sha(self.source_raw),VALID_SHA=g.sha(self.valid_raw)))
        stack.enter_context(patch.object(self.old,"NATIVE_SHA256",self.native_hashes))
        stack.enter_context(patch.object(g,"helper",return_value=self.old))
        return stack
    def data(self):
        generated=g.generated_remarks(self.source)
        copied,_,_=g.copies(self.source,self.source_raw.splitlines())
        return self.original+generated+copied,generated,copied
    def temporary(self):
        return tempfile.TemporaryDirectory(prefix="factor-data-test-")

    def test_whole_corpus_retains_all128_bytes_and_frozen_validation(self):
        with self.temporary() as directory, self.fixture_pins():
            out=Path(directory)/"data"
            m=g.prepare(self.base,self.approved,self.native,out,self.excluded)
            self.assertTrue((out/"train.jsonl").read_bytes().startswith(self.base_raw))
            self.assertEqual((out/"valid.jsonl").read_bytes(),self.valid_raw)
            self.assertEqual(len(g.rows((out/"train.jsonl").read_bytes())),176)
            self.assertEqual(m["by_application"],{"facturation":144,"management_projet":16,"design_workflow":16})
            self.assertEqual(m["exclusion_input_rows_checked"],894)
            self.assertEqual(m["sensitive_supervised_rows_checked"],176)
            self.assertFalse(m["training_executed"])

    def test_all_requested_change_fields_and_context_are_preserved(self):
        for row in g.generated_remarks(self.source):
            meta=row["augmentation"];parent=self.source[meta["source_line"]-1]
            expected=deepcopy(g.helper().target(parent)["arguments"])
            expected["changes"]["remarque"]=meta["factors"]["literal"]
            self.assertEqual(g.helper().target(row)["arguments"],expected)
            self.assertEqual(row["tools"],parent["tools"])
            self.assertEqual(row["messages"][:-2],parent["messages"][:-2])
            self.assertEqual(g.helper().helper().current_request(row["messages"][-2]["content"])[0],
                             g.helper().helper().current_request(parent["messages"][-2]["content"])[0])

    def test_complete_language_action_quote_length_calendar_coverage(self):
        all_rows,new,_=self.data()
        self.assertTrue(g.coverage(all_rows,new)["all_factor_cells_verified"])
        self.assertEqual(len(new),16)
        self.assertEqual({x["augmentation"]["factors"]["literal_words"] for x in new},{2,6})

    def test_missing_navigation_cell_is_rejected(self):
        all_rows,new,_=self.data()
        pruned=[r for r in all_rows if not (g.helper().target(r)["name"]=="navigate"
                and g.helper().target(r)["arguments"].get("resource")=="users"
                and r.get("language")=="fr")]
        with self.assertRaisesRegex(ValueError,"coverage"):g.coverage(pruned,new)

    def test_unquoted_or_mislabeled_literal_is_rejected(self):
        all_rows,new,_=self.data()
        for key,value in (("quoted",True),("literal_words",99)):
            with self.subTest(key=key):
                selected=deepcopy(new)
                index=next(i for i,r in enumerate(selected) if not r["augmentation"]["factors"]["quoted"])
                selected[index]["augmentation"]["factors"][key]=value
                with self.assertRaises(ValueError):g.coverage(all_rows,selected)

    def test_wrong_date_boundary_label_is_rejected(self):
        all_rows,new,_=self.data();all_rows=deepcopy(all_rows)
        row=next(r for r in all_rows if r.get("augmentation",{}).get("family")=="date_boundaries"
                 and r["augmentation"]["factors"]["mode"]=="upper_exclusive")
        row["messages"][-1]["tool_calls"][0]["function"]["arguments"]["date_to"]="2032-03-01"
        with self.assertRaisesRegex(ValueError,"calendar"):g.coverage(all_rows,new)

    def test_copies_change_only_reviewed_language_metadata(self):
        copied,payloads,provenance=g.copies(self.source,self.source_raw.splitlines())
        self.assertEqual(len(copied),32)
        for row,payload,item in zip(copied,payloads,provenance):
            original=deepcopy(self.source[item["source_line"]-1])
            if item["source_line"]==111:original["language"]="fr"
            self.assertEqual(row,original)
            self.assertEqual(json.loads(payload),row)

    def test_wrong_language_annotation_is_rejected(self):
        source=deepcopy(self.source)
        source[110]["messages"][-2]["content"]="Open the user list."
        with self.assertRaisesRegex(ValueError,"French"):g.copies(source,self.source_raw.splitlines())

    def test_evaluation_answers_are_never_copied_or_consulted(self):
        class Forbidden:
            def __deepcopy__(self,memo):raise AssertionError("Evaluation answer accessed")
        row={"messages":[{"role":"system","content":"context"},{"role":"user","content":"request"},
                         {"role":"assistant","content":Forbidden()}],
             "tools":[],"expected":Forbidden()}
        result=g.exclusion_envelope(row)
        self.assertEqual(result["messages"][-1],{"role":"assistant","content":None})
        self.assertEqual(result["messages"][-2]["content"],"request")

    def test_generated_evaluation_input_or_pattern_overlap_is_rejected(self):
        _,new,copied=self.data()
        envelope={"messages":new[0]["messages"][:-1],"offered_tool_schemas":new[0]["tools"],"expected":{}}
        excluded=[g.exclusion_envelope(envelope)]
        with self.assertRaisesRegex(ValueError,"overlap"):
            g.helper().validate_exclusions(self.original+copied,new,excluded)

    def test_credentials_are_rejected_in_supervised_text(self):
        all_rows,_,_=self.data();all_rows=deepcopy(all_rows)
        all_rows[0]["messages"][-2]["content"]="password=SYN-fake-fixture"
        with self.assertRaisesRegex(ValueError,"credential"):g.sensitive_checks(all_rows)

    def test_changed_base_and_existing_output_are_rejected(self):
        with self.temporary() as directory, self.fixture_pins():
            base=Path(directory)/"base";base.mkdir()
            (base/"train.jsonl").write_bytes(self.base_raw+b"\n")
            (base/"valid.jsonl").write_bytes(self.valid_raw)
            out=Path(directory)/"out"
            with self.assertRaisesRegex(ValueError,"Pinned"):g.prepare(base,self.approved,self.native,out)
            self.assertFalse(out.exists())
            out.mkdir()
            with self.assertRaisesRegex(ValueError,"isolated"):g.prepare(self.base,self.approved,self.native,out)

    def test_changed_native_contract_is_rejected_before_output(self):
        with self.temporary() as directory, self.fixture_pins():
            native=Path(directory)/"native"
            for name in self.native_hashes:
                destination=native/name;destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes((self.native/name).read_bytes())
            (native/next(iter(self.native_hashes))).write_text("# Changed fixture contract\n")
            out=Path(directory)/"out"
            with self.assertRaisesRegex(ValueError,"Native business contracts"):
                g.prepare(self.base,self.approved,native,out,self.excluded)
            self.assertFalse(out.exists())

    def test_unoffered_update_tool_is_rejected(self):
        source=deepcopy(self.source)
        for n in g.REMARKS:
            source[n-1]["tools"]=[t for t in source[n-1]["tools"]
                                   if t["function"]["name"]!="prepare_change"]
        with self.assertRaisesRegex(ValueError,"offered tools"):
            g.generated_remarks(source)

if __name__=="__main__":unittest.main()
