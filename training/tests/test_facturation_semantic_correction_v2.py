"""Semantic and isolation checks for the bounded corrective corpus, not accuracy."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_facturation_semantic_correction_v2 as subject
import prepare_facturation_semantic_contrasts_v2 as prior
from test_facturation_semantic_contrasts_v1 import fixture


def source_rows():
    parents = fixture()
    contrasts = prior.clarify_rows(subject.helper().generate(parents))
    return deepcopy(parents[:384]) + contrasts


class CorrectiveDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = source_rows()
        cls.generated = subject.generate(cls.rows)

    def family(self, name):
        return [r for r in self.generated if r["augmentation"]["family"] == name]

    def args(self, row):
        return subject.helper().target(row)["arguments"]

    def text(self, row):
        return subject.helper().helper().current_request(row["messages"][-2]["content"])[1]

    def test_pure_complete_balanced_generation(self):
        before = deepcopy(self.rows)
        self.assertEqual(subject.generate(self.rows), self.generated)
        self.assertEqual(self.rows, before)
        self.assertEqual(Counter(r["language"] for r in self.generated), {"en": 32, "fr": 32})
        self.assertEqual(len(self.generated), 64)

    def test_complete_literal_is_quoted_in_request_and_nested_in_change(self):
        values = set()
        for row in self.family("full_literal"):
            args = self.args(row)
            value = args["changes"]["remarque"]
            self.assertIn(json.dumps(value, ensure_ascii=False), self.text(row))
            self.assertEqual(args["operation"], "update")
            self.assertNotIn("remarque", args)
            self.assertEqual(set(args["changes"]), {"remarque", "date_echeance"})
            values.add(value)
        self.assertEqual(len(values), 4)
        self.assertTrue(any('"Approved"' in value for value in values))

    def test_optional_filters_are_absent_never_null_strings(self):
        for row in self.family("optional_filters"):
            args = self.args(row)
            factors = row["augmentation"]["factors"]
            expected = {"lower": {"date_from"}, "upper": {"date_to"},
                        "closed": {"date_from", "date_to"}}[factors["mode"]]
            self.assertEqual(set(args) & {"date_from", "date_to"}, expected)
            self.assertEqual("unpaid" in args, factors["unpaid"])
            self.assertNotIn(None, args.values())
            self.assertTrue(all(v not in ("None", "null") for v in args.values()))
            self.assertIn(args["client_name"], self.text(row))
            self.assertIn(args["product_name"], self.text(row))

    def test_real_calendar_endings_and_month_to_date(self):
        endings = {"2028-02-14": ("2028-02-29", "2028-01-31"),
                   "2031-02-11": ("2031-02-28", "2031-01-31"),
                   "2030-11-18": ("2030-11-30", "2030-10-31"),
                   "2031-01-21": ("2031-01-31", "2030-12-31")}
        for row in self.family("month_endings"):
            factors, args = row["augmentation"]["factors"], self.args(row)
            today, mode = factors["today"], factors["mode"]
            expected = (today if mode == "month_to_date" else
                        endings[today][1 if mode == "previous_full" else 0])
            self.assertEqual(args["date_to"], expected)
            context = subject.helper().trusted_context(row)
            self.assertEqual(context["today"], today)
            self.assertEqual(context, subject.calendar_context(context))

    def test_identity_permissions_history_preserved_with_only_declared_clock_change(self):
        for row in self.generated:
            parent = self.rows[row["augmentation"]["source_line"] - 1]
            self.assertEqual(row["tools"], parent["tools"])
            self.assertEqual(row.get("capability_profile"), parent.get("capability_profile"))
            self.assertEqual(row["messages"][1:-2], parent["messages"][1:-2])
            context = subject.helper().trusted_context(row)
            original = subject.helper().trusted_context(parent)
            if row["augmentation"]["family"] == "month_endings":
                for item in (context, original):
                    item.pop("today")
                    item.pop("calendar")
            self.assertEqual(context, original)

    def test_unoffered_update_tool_is_rejected_before_output(self):
        rows = deepcopy(self.rows)
        for row in rows[384:]:
            if row["augmentation"]["family"] == "verbatim_update_text":
                row["tools"] = [t for t in row["tools"] if t["function"]["name"] != "prepare_change"]
        with self.assertRaisesRegex(ValueError, "offered tools"):
            subject.generate(rows)

    def test_development_input_or_template_overlap_is_rejected(self):
        old = subject.helper()
        overlap = deepcopy(self.generated[0])
        with self.assertRaisesRegex(ValueError, "development"):
            old.validate_exclusions(self.rows, self.generated, [overlap])
        overlap["messages"][-2]["content"] += " "
        with self.assertRaisesRegex(ValueError, "development"):
            old.validate_exclusions(self.rows, self.generated, [overlap])

    def test_replay_preserves_source_bytes_and_generated_tool_key_order(self):
        source = b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in self.rows) + b"\n"
        kept = [self.rows[3], self.rows[20]]
        train, contrasts = subject.assemble(kept, self.generated, source)
        self.assertEqual(train.splitlines()[:2], [source.splitlines()[3], source.splitlines()[20]])
        generated_raw = json.dumps(self.generated[0], ensure_ascii=False, separators=(",", ":")).encode()
        self.assertEqual(contrasts.splitlines()[0], generated_raw)
        self.assertEqual(json.loads(train.splitlines()[0]), self.rows[3])
        with self.assertRaisesRegex(ValueError, "Duplicate source"):
            subject.assemble(kept, [], source + source.splitlines()[0] + b"\n")

    def test_calendar_change_is_rejected_before_import(self):
        with patch.object(subject, "CALENDAR_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "calendar implementation changed"):
                subject.calendar_context({"today": "2030-11-18"})

    def test_incomplete_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "500-row"):
            subject.generate(self.rows[:-1])

    def test_article_aliases_and_invoice_payment_shape_are_distinguished(self):
        for name, key in (("search_articles", "product_name"), ("search_articles", "query"),
                          ("search_payments", "invoice_number")):
            args = {key: "SYN-Only"}
            if name == "search_payments":
                args["limit"] = 2
            row = {"messages": [{"tool_calls": [{"function": {"name": name, "arguments": args}}]}],
                   "tools": [{"function": {"name": name, "parameters": {"properties": {}}}}]}
            tag = key if name == "search_articles" else "invoice_number_with_limit"
            self.assertIn(("critical_shape", name, tag), subject.features(row))

    def test_retention_quotas_are_deterministic_and_preserve_source(self):
        rows = deepcopy(self.rows)
        for i, row in enumerate(rows[:384]):
            row["application"] = ("facturation" if i < 200 else
                                  "management_projet" if i < 312 else "design_workflow")
        before = deepcopy(rows)
        kept = subject.retain(rows)
        self.assertEqual(Counter(r["application"] for r in kept), subject.QUOTAS)
        self.assertEqual(kept, subject.retain(rows))
        self.assertEqual(rows, before)
        self.assertTrue(all(r in rows for r in kept))
        fact = [r for r in kept if r["application"] == "facturation"]
        represented = {r.get("augmentation", {}).get("family") for r in fact}
        self.assertTrue(set(subject.helper().EXPECTED_FAMILIES) <= represented)
        for family, factor in (("users_collection_versus_detail", "collection"),
                               ("ambiguous_previous_result_selection", "explicit")):
            self.assertEqual({r["augmentation"]["factors"][factor] for r in fact
                              if r.get("augmentation", {}).get("family") == family}, {False, True})
        with self.assertRaisesRegex(ValueError, "Insufficient"):
            subject.retain([r for r in rows if r["application"] != "design_workflow"])


if __name__ == "__main__":
    unittest.main()
