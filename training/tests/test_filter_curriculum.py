"""Regression checks for explicit-filter training labels and frozen split retention."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from prepare_shared_v5r6 import ROOT, additions, current_request, function, make_row, key
from jsonschema import ValidationError

class FilterCurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = ROOT/"training/datasets/shared-v5r5-en-fr"
        cls.child = ROOT/"training/datasets/shared-v5r6-en-fr"
        cls.rows = [json.loads(x) for x in (cls.parent/"train.jsonl").read_text().splitlines()]
        cls.extra, cls.categories, _ = additions(cls.rows)

    def test_exact_parent_retention_and_deterministic_regeneration(self):
        self.assertEqual((self.child/"valid.jsonl").read_bytes(), (self.parent/"valid.jsonl").read_bytes())
        raw=(self.child/"train.jsonl").read_bytes()
        self.assertTrue(raw.startswith((self.parent/"train.jsonl").read_bytes()))
        generated=[json.loads(x) for x in raw.splitlines()][len(self.rows):]
        self.assertEqual(generated,self.extra)
        self.assertEqual(len(self.extra),166)

    def test_open_bounds_do_not_invent_a_second_boundary(self):
        for row,category in zip(self.extra,self.categories):
            if category not in ("date_lower","date_upper","date_day"):continue
            a=function(row)["arguments"]
            with self.subTest(request=current_request(row)):
                bounds=set(a)&{"date_from","date_to"}
                self.assertEqual(bounds,{"date_from"} if category=="date_lower" else
                                 {"date_to"} if category=="date_upper" else {"date_from","date_to"})
                if category=="date_day":self.assertEqual(a["date_from"],a["date_to"])
                for bound in bounds:
                    d=date.fromisoformat(a[bound])
                    self.assertGreater(d.day,1)
                    self.assertLess(d.day,28)
                self.assertIn(str(a["limit"]),current_request(row))

    def test_combined_filters_and_exact_quoted_values_are_preserved(self):
        for row,category in zip(self.extra,self.categories):
            a=function(row)["arguments"];request=current_request(row)
            if category=="combined_unpaid_filters":
                self.assertTrue(a["unpaid"])
                self.assertIn(a["client_name"],request)
                self.assertIn(a["product_name"],request)
                self.assertEqual(len(set(a)&{"date_from","date_to"}),1)
            if category=="literal_multifield":
                self.assertEqual(set(a["changes"]),{"adresse","ville"})
            if category in ("literal_multifield","literal_text"):
                for value in a["changes"].values():self.assertIn(value,request)

    def test_current_page_labels_have_matching_trusted_context(self):
        for row,category in zip(self.extra,self.categories):
            if category!="current_page":continue
            context=json.loads(row["messages"][0]["content"].split("Trusted context: ",1)[1])
            a=function(row)["arguments"]
            self.assertEqual(a,{"resource":context["current_resource"]})
            self.assertTrue(context["current_identifier"])

    def test_new_requests_do_not_overlap_existing_splits_or_each_other(self):
        frozen={key(row["application"],current_request(row)) for row in self.rows}
        frozen.update(key(row["application"],current_request(row)) for row in
                      map(json.loads,(self.parent/"valid.jsonl").read_text().splitlines()))
        seen=set()
        for row in self.extra:
            identity=key(row["application"],current_request(row))
            self.assertNotIn(identity,frozen|seen);seen.add(identity)

    def test_unoffered_tool_and_invalid_arguments_are_rejected(self):
        row=next(r for r in self.rows if function(r)["name"]=="search_invoices")
        original=deepcopy(row)
        with self.assertRaises(ValueError):make_row(row,"Example","run_sql",{"query":"SELECT 1"})
        with self.assertRaises(ValidationError):make_row(row,"Example","search_invoices",{"limit":999999})
        self.assertEqual(row,original)

if __name__=="__main__":unittest.main()
