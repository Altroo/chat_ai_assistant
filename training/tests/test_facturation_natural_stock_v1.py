"""Behavior checks for EN/FR natural compound stock question preparation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
spec = importlib.util.spec_from_file_location(
    "natural_stock", ROOT / "training/scripts/prepare_facturation_natural_stock_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(language="en", resource="stock_balance"):
    props = {"resource": {"const": resource}, "product_name": {"type": "string"},
             "location_name": {"type": "string"}, "date_from": {"type": "string"},
             "date_to": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 10}}
    return {"application": "facturation", "language": language,
        "messages": [{"role": "system", "content": 'Trusted context: {"interface_language":"fr"}'},
                     {"role": "user", "content": "Original request."},
                     {"role": "assistant", "content": None, "tool_calls": [{"type": "function",
                      "function": {"name": "search_operations", "arguments": {
                          "resource": resource, "product_name": "SYN-Product", "location_name": "SYN-Depot",
                          "date_from": "2032-04-02", "date_to": "2032-04-19", "limit": 3}}}]}],
        "tools": [{"type": "function", "function": {"name": "search_operations",
          "parameters": {"type": "object", "oneOf": [{"type": "object", "properties": props,
                                                    "required": ["resource"], "additionalProperties": False}]}}}]}


def args(value):
    return value["messages"][-1]["tool_calls"][0]["function"]["arguments"]


class NaturalStockTests(unittest.TestCase):
    def test_two_orderings_express_all_filters_without_mutating_source(self):
        original = row()
        before = deepcopy(original)
        output = m.questions(original)
        self.assertEqual(set(output), {"product_first", "location_first"})
        for text in output.values():
            for value in ("SYN-Product", "SYN-Depot", "2 April 2032", "19 April 2032", "3"):
                self.assertIn(value, text)
            self.assertIn("inclusive", text)
            self.assertIn("updated", text)
            for field in ("product_name", "location_name", "date_from", "date_to"):
                self.assertNotIn(field, text)
        self.assertEqual(original, before)

    def test_french_and_english_use_current_metadata_not_interface_language(self):
        for language, expected in (("en", "2 April 2032"), ("fr", "2 avril 2032")):
            with self.subTest(language=language):
                for text in m.questions(row(language)).values():
                    self.assertIn(expected, text)

    def test_balance_uses_update_event_and_other_resources_use_creation(self):
        for resource in m.NOUNS:
            for language in ("en", "fr"):
                output = " ".join(m.questions(row(language, resource)).values())
                with self.subTest(resource=resource, language=language):
                    expected = m.NOUNS[resource][2 if language == "en" else 3]
                    self.assertIn(expected, output)

    def test_lower_only_and_upper_only_dates_keep_inclusive_bounds(self):
        for language in ("en", "fr"):
            lower = row(language)
            del args(lower)["date_to"]
            upper = row(language)
            del args(upper)["date_from"]
            for text in m.questions(lower).values():
                self.assertIn("on or after" if language == "en" else "à partir du", text)
                self.assertNotIn("19 April" if language == "en" else "19 avril", text)
            for text in m.questions(upper).values():
                self.assertIn("on or before" if language == "en" else "au plus tard", text)
                self.assertNotIn("2 April" if language == "en" else "2 avril", text)

    def test_different_year_and_leap_day_are_not_hardcoded(self):
        original = row()
        args(original)["date_from"] = "2040-02-29"
        args(original)["date_to"] = "2040-03-04"
        for text in m.questions(original).values():
            self.assertIn("29 February 2040", text)
            self.assertIn("4 March 2040", text)
            self.assertNotIn("2032", text)

    def test_invalid_or_inverted_dates_fail_closed(self):
        for invalid in ("2032-02-30", "2032-4-02", "2032-05-01"):
            original = row()
            args(original)["date_from"] = invalid
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                m.questions(original)

    def test_additional_arguments_are_never_silently_dropped(self):
        for key, value in (("status", "draft"), ("reference", "SYN-REF"), ("supplier_name", "SYN-Supplier")):
            original = row()
            args(original)[key] = value
            with self.subTest(field=key):
                self.assertEqual(m.questions(original), {})

    def test_missing_required_filter_or_date_is_not_invented(self):
        for key in ("product_name", "location_name", "limit"):
            original = row()
            del args(original)[key]
            with self.subTest(key=key):
                self.assertEqual(m.questions(original), {})
        original = row()
        del args(original)["date_from"]
        del args(original)["date_to"]
        self.assertEqual(m.questions(original), {})

    def test_foreign_application_language_and_nonsynthetic_literals_are_excluded(self):
        for patch in ({"application": "contracts"}, {"language": "ar"}, {"language": "unknown"}):
            original = row()
            original.update(patch)
            self.assertEqual(m.questions(original), {})
        original = row()
        args(original)["product_name"] = "Private Customer"
        self.assertEqual(m.questions(original), {})

    def test_invalid_limit_is_not_coerced(self):
        for limit in (0, 11, "3"):
            original = row()
            args(original)["limit"] = limit
            with self.subTest(limit=limit), self.assertRaises(Exception) as error:
                m.questions(original)
            self.assertEqual(type(error.exception).__name__, "ValidationError")

    def test_output_cannot_overwrite_or_be_inside_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            base = Path(temp) / "base"
            source.mkdir()
            base.mkdir()
            development = base / "valid.jsonl"
            for output in (source, source / "child", base / "child"):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    m.prepare(source, development, output)

    def test_changed_source_is_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            source, base, output = Path(temp) / "source", Path(temp) / "base", Path(temp) / "output"
            source.mkdir()
            base.mkdir()
            (source / "manifest.json").write_text("{}")
            (source / "contrasts.jsonl").write_text("{}")
            development = base / "valid.jsonl"
            development.write_text("{}")
            with self.assertRaises(ValueError):
                m.prepare(source, development, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
