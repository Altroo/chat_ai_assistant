"""Verify unambiguous recency/calendar TRAIN changes; no model is loaded."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import prepare_facturation_semantic_contrasts_v2 as subject
from test_facturation_semantic_contrasts_v1 import fixture

class ClarifiedTrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v1=subject.prior()
        cls.original=cls.v1.generate(fixture())
        cls.clarified=subject.clarify_rows(cls.original)

    def text(self,row):
        return self.v1.helper().current_request(row["messages"][-2]["content"])[1]

    def test_complete_inventory_and_original_are_preserved(self):
        original=deepcopy(self.original)
        self.assertEqual(subject.clarify_rows(self.original),self.clarified)
        self.assertEqual(original,self.original)
        self.assertEqual(len(self.clarified),116)
        self.assertTrue(all(r["augmentation"]["version"]==subject.VERSION for r in self.clarified))

    def test_bounded_payments_explicitly_request_latest_and_keep_arguments(self):
        bounded=0
        for source,row in zip(self.original,self.clarified):
            meta=row["augmentation"]
            if meta["family"]=="date_boundaries" and meta["factors"]["mode"]!="unbounded":
                self.assertIn("most recent" if row["language"]=="en" else "plus récents",self.text(row))
                self.assertEqual(self.v1.target(source),self.v1.target(row))
                bounded+=1
        self.assertEqual(bounded,20)

    def test_only_two_month_to_date_targets_end_today(self):
        count=0
        for row in self.clarified:
            meta=row["augmentation"]
            if meta["family"]=="relative_quote_month" and meta["factors"]["period_end"]=="today":
                self.assertFalse(meta["factors"]["previous"])
                args=self.v1.target(row)["arguments"]
                self.assertEqual(args,{"limit":3,"date_from":"2027-11-01","date_to":"2027-11-18"})
                self.assertIn("through today" if row["language"]=="en" else "aujourd’hui",self.text(row))
                count+=1
        self.assertEqual(count,2)

    def test_calendar_month_targets_are_explicit_and_cover_real_last_day(self):
        count=0
        for row in self.clarified:
            meta=row["augmentation"]
            if meta["family"]=="relative_quote_month" and meta["factors"]["period_end"]=="calendar_last_day":
                args=self.v1.target(row)["arguments"]
                previous=meta["factors"]["previous"]
                self.assertEqual(args,{"limit":3,"date_from":"2027-10-01" if previous else "2027-11-01",
                                       "date_to":"2027-10-31" if previous else "2027-11-30"})
                text=self.text(row)
                self.assertTrue(any(word in text for word in ("entire","full","complete calendar","first through the last","calendaire","premier au dernier")))
                count+=1
        self.assertEqual(count,10)

    def test_native_context_history_schemas_and_access_metadata_unchanged(self):
        for source,row in zip(self.original,self.clarified):
            self.assertEqual(source["messages"][:-2],row["messages"][:-2])
            self.assertEqual(source["tools"],row["tools"])
            self.assertEqual(source.get("capability_profile"),row.get("capability_profile"))
            self.assertEqual(self.v1.helper().current_request(source["messages"][-2]["content"])[0],
                             self.v1.helper().current_request(row["messages"][-2]["content"])[0])

    def test_non_date_non_month_requests_and_targets_are_unchanged(self):
        for source,row in zip(self.original,self.clarified):
            if row["augmentation"]["family"] not in ("date_boundaries","relative_quote_month"):
                self.assertEqual(source["messages"],row["messages"])
                self.assertEqual(self.v1.target(source),self.v1.target(row))

    def test_remark_targets_keep_nested_required_operation_and_complete_literal(self):
        for row in self.clarified:
            if row["augmentation"]["family"]=="verbatim_update_text":
                args=self.v1.target(row)["arguments"]
                self.assertEqual(args["operation"],"update")
                self.assertNotIn("remarque",args)
                self.assertNotIn("date_echeance",args)
                self.assertIn(args["changes"]["remarque"],self.text(row))
                self.assertIn(args["changes"]["date_echeance"],self.text(row))

    def test_reference_wording_change_is_rejected(self):
        rows=deepcopy(self.original)
        row=next(r for r in rows if r["augmentation"]["family"]=="date_boundaries")
        row["messages"][-2]["content"]="Some other payment query."
        with self.assertRaisesRegex(ValueError,"wording changed"):
            subject.clarify_rows(rows)

    def test_incomplete_inventory_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"inventory"):
            subject.clarify_rows(self.original[:-1])

    def test_prior_generator_change_is_rejected_before_import(self):
        with patch.object(subject,"PRIOR_SHA256","0"*64):
            with self.assertRaisesRegex(ValueError,"identity changed"):
                subject.prior()

    def test_existing_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaisesRegex(ValueError,"new isolated"):
                subject.prepare(root,root,root)

if __name__=="__main__":
    unittest.main()
