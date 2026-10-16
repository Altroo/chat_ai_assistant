"""Focused training must retain scope and labels while varying independent inputs."""
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, timedelta
import calendar
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_facturation_focus_v1 as m


class FacturationFocusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.payloads, cls.parents = m.retained()
        cls.rows = m.additions(cls.parents["train"])

    def test_retains_all_facturation_rows_and_no_other_app(self):
        for split, count in (("train", 931), ("valid", 133)):
            raw = (m.PARENT / (split + ".jsonl")).read_bytes()
            expected = b"".join(line for line in raw.splitlines(keepends=True)
                                if json.loads(line)["application"] == "facturation")
            self.assertEqual(self.payloads[split + ".jsonl"], expected)
            self.assertEqual(len(self.parents[split]), count)
        self.assertEqual({r["application"] for r in self.rows}, {"facturation"})

    def test_rejects_changed_parent_before_generation(self):
        with mock.patch.object(m, "sha", return_value="changed"):
            with self.assertRaisesRegex(ValueError, "manifest changed"):
                m.retained()

    def test_modified_helpers_and_exclusion_input_reject(self):
        actual = m.sha
        helper = next(iter(self.manifest["helper_sha256"]))
        with mock.patch.object(m, "sha", side_effect=lambda p: "changed" if p == ROOT / helper else actual(p)):
            with self.assertRaisesRegex(ValueError, "helper changed"):
                m.helpers(self.manifest)
        for changed in (m.PARENT / "valid.jsonl", m.EXCLUSION_PARENT / "valid.jsonl"):
            with self.subTest(source=changed.parent.name):
                with mock.patch.object(m, "sha", side_effect=lambda p: "changed" if p == changed else actual(p)):
                    with self.assertRaisesRegex(ValueError, "exclusion input changed"):
                        m.check_exclusions(self.manifest, self.rows)

    def test_date_operators_have_exact_inclusive_native_bounds(self):
        dated = [r for r in self.rows if "literal_date" in r["contrast"]]
        seen = defaultdict(set)
        for row in dated:
            target = m.function(row)
            args, meta = target["arguments"], row["contrast"]
            day = date.fromisoformat(meta["literal_date"])
            operator = meta["operator"]
            expected = {}
            if operator in ("lower", "day"):
                expected["date_from"] = day.isoformat()
            if operator in ("upper", "day"):
                expected["date_to"] = day.isoformat()
            if operator == "after":
                expected["date_from"] = (day + timedelta(days=1)).isoformat()
            if operator == "before":
                expected["date_to"] = (day - timedelta(days=1)).isoformat()
            if operator == "month":
                expected = {"date_from": day.replace(day=1).isoformat(),
                            "date_to": day.replace(day=calendar.monthrange(day.year, day.month)[1]).isoformat()}
            self.assertEqual({k: v for k, v in args.items() if k in ("date_from", "date_to")}, expected)
            seen[(target["name"], args.get("resource"))].add(day)
        self.assertTrue(all(len(days) >= 3 for days in seen.values()))
        self.assertGreaterEqual(len({date.fromisoformat(r["contrast"]["literal_date"]).day
                                     for r in dated if date.fromisoformat(r["contrast"]["literal_date"]).day < 10}), 5)

    def test_optional_filters_and_literals_are_independent(self):
        variants = defaultdict(set)
        for row in self.rows:
            target, text = m.function(row), m.current_request(row)
            args = target["arguments"]
            if row["curriculum_category"] == "operation_filter_contrast":
                variants[args["resource"]].add(("product_name" in args, "location_name" in args))
                self.assertNotIn("supplier_name", args)
            for field in ("client_name", "product_name", "location_name"):
                if field in args:
                    self.assertIn(args[field], text)
        self.assertEqual(set(variants), {"stock_balance", "stock_movement", "stock_receipt", "stock_inventory", "logistics_order"})
        for combinations in variants.values():
            self.assertEqual(combinations, {(True, False), (False, True), (True, True)})

    def test_list_and_detail_targets_are_distinct(self):
        lists = [r for r in self.rows if r["curriculum_category"] == "user_list"]
        details = [r for r in self.rows if r["curriculum_category"] == "user_detail"]
        self.assertEqual((len(lists), len(details)), (6, 6))
        for row in lists:
            self.assertEqual(m.function(row)["arguments"], {"resource": "users"})
        for row in details:
            args = m.function(row)["arguments"]
            self.assertEqual(args["resource"], "user")
            self.assertIn(str(args["identifier"]), m.current_request(row))
            self.assertEqual(m.context(row)["previous_result_identifiers"], [args["identifier"]])
            self.assertEqual(row["capability_profile"], "staff_read")

    def test_verbatim_edits_and_unselected_records(self):
        for row in self.rows:
            args = m.function(row)["arguments"]
            if row["curriculum_category"] == "verbatim_remark":
                self.assertIn(args["changes"]["remarque"], m.current_request(row))
                self.assertGreater(len(args["changes"]["remarque"].split()), 4)
                self.assertEqual(m.context(row)["previous_result_identifiers"], [args["identifier"]])
            if row["curriculum_category"] == "unselected_record":
                self.assertEqual(m.function(row)["name"], "clarify")
                self.assertEqual(args, {"reason": "missing_details", "language": row["language"]})
                self.assertGreater(m.context(row)["previous_result_count"], 1)

    def test_small_bilingual_supplement_has_unique_requests(self):
        self.assertEqual(len(self.rows), 116)
        self.assertEqual(Counter(r["language"] for r in self.rows), {"en": 58, "fr": 58})
        keys = {m.key("facturation", m.current_request(r)) for r in self.rows}
        self.assertEqual(len(keys), len(self.rows))
        self.assertFalse(keys & {m.key("facturation", m.current_request(r)) for r in self.parents["train"]})
        for row in self.rows:
            self.assertNotEqual(row["language"], m.context(row)["interface_language"])

    def test_validation_and_acceptance_requests_cannot_enter_supplement(self):
        # Only compare exclusion keys; evaluation targets never inform generated rows.
        candidate = deepcopy(self.rows)
        candidate[0]["messages"][-2] = deepcopy(self.parents["valid"][0]["messages"][-2])
        with self.assertRaisesRegex(ValueError, "Frozen"):
            m.check_exclusions(self.manifest, candidate)


if __name__ == "__main__":
    unittest.main()
