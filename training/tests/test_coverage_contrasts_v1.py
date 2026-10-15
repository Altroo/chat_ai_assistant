"""Coverage preparation must preserve business meaning and exclude frozen prompts."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_coverage_contrasts_v1 as m


class CoverageContrastsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.parent = m.parent_rows()
        cls.rows = m.additions(cls.parent)

    def test_custom_finance_has_real_bounds_and_separate_currencies(self):
        rows = [r for r in self.rows if r["curriculum_category"] == "custom_currency_summary"]
        combinations = set()
        for row in rows:
            args = m.function(row)["arguments"]
            self.assertEqual(args["period"], "custom")
            self.assertLess(m.date.fromisoformat(args["date_from"]), m.date.fromisoformat(args["date_to"]))
            request = m.current_request(row)
            for key in ("date_from", "date_to", "currency"):
                self.assertIn(args[key], request)
            combinations.add((args["metric"], args["currency"], row["language"]))
        self.assertEqual(combinations, {(metric, currency, language)
            for metric in ("invoiced_net_ttc", "collected")
            for currency in ("MAD", "EUR", "USD") for language in ("en", "fr")})

    def test_product_and_place_remain_separate_without_invented_upper_bound(self):
        rows = [r for r in self.rows if r["curriculum_category"] == "natural_product_location"]
        self.assertEqual({m.function(r)["arguments"]["resource"] for r in rows},
                         {"stock_balance", "stock_movement", "stock_receipt", "stock_inventory", "logistics_order"})
        for row in rows:
            args = m.function(row)["arguments"]
            self.assertNotEqual(args["product_name"], args["location_name"])
            self.assertNotIn("date_to", args)
            self.assertNotIn("supplier_name", args)
            for name in ("product_name", "location_name", "date_from"):
                self.assertIn(args[name], m.current_request(row))
            if args["resource"] == "stock_balance":
                self.assertTrue("updated" in m.current_request(row) or "mises à jour" in m.current_request(row))

    def test_status_is_resource_specific(self):
        rows = [r for r in self.rows if r["curriculum_category"] == "resource_completion_status"]
        for row in rows:
            args = m.function(row)["arguments"]
            self.assertEqual(args["status"], {"task": "done", "project": "completed"}[args["resource"]])

    def test_full_remark_and_selected_identifier_are_retained(self):
        rows = [r for r in self.rows if r["curriculum_category"] == "verbatim_remark"]
        for row in rows:
            args = m.function(row)["arguments"]
            self.assertIn(args["changes"]["remarque"], m.current_request(row))
            self.assertGreater(len(args["changes"]["remarque"].split()), 2)
            self.assertEqual(m.context(row)["previous_result_identifiers"], [args["identifier"]])

    def test_unchosen_record_never_defaults_to_first(self):
        rows = [r for r in self.rows if r["curriculum_category"] == "unchosen_invoice"]
        for row in rows:
            target = m.function(row)
            self.assertEqual(target["name"], "clarify")
            self.assertEqual(target["arguments"], {"reason": "missing_details", "language": row["language"]})
            self.assertEqual(m.context(row)["previous_result_count"], 3)

    def test_current_language_is_independent_of_prior_greeting(self):
        for row in self.rows:
            self.assertNotEqual(row["language"], m.context(row)["interface_language"])
            self.assertIn(row["language"], ("en", "fr"))

    def test_exclusion_checks_reject_frozen_or_duplicate_requests(self):
        m.check_exclusions(self.manifest, self.rows)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            m.check_exclusions(self.manifest, self.rows + [copy.deepcopy(self.rows[0])])
        valid = m.json.loads((m.PARENT / "valid.jsonl").read_text().splitlines()[0])
        poisoned = copy.deepcopy(self.rows)
        poisoned[0]["application"] = valid["application"]
        poisoned[0]["messages"][-2] = valid["messages"][-2]
        with self.assertRaisesRegex(ValueError, "Frozen"):
            m.check_exclusions(self.manifest, poisoned)
        parent = {m.key(r["application"], m.current_request(r)) for r in self.parent}
        self.assertFalse(parent & {m.key(r["application"], m.current_request(r)) for r in self.rows})


if __name__ == "__main__":
    unittest.main()
