"""Check real contrast coverage, literal labels and immutable data boundaries."""
import calendar
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "training/scripts"))
import prepare_facturation_focus_v2 as m


class FacturationFocusV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, cls.payloads, cls.parents = m.retained()
        cls.rows = m.additions(cls.parents["train"])

    def test_parent_bytes_scope_counts_and_languages(self):
        for split, count in (("train", 1047), ("valid", 133)):
            self.assertEqual(self.payloads[split + ".jsonl"], (m.PARENT / (split + ".jsonl")).read_bytes())
            self.assertEqual(len(self.parents[split]), count)
        self.assertEqual(len(self.rows), 440)
        self.assertEqual(Counter(row["language"] for row in self.rows), {"en": 220, "fr": 220})
        self.assertEqual({row["application"] for row in self.rows}, {"facturation"})
        self.assertIsNone(m.SECRET.search(m.encode(self.rows)))
        for row in self.rows:
            self.assertNotEqual(row["language"], m.context(row)["interface_language"])

    def test_changed_parent_is_rejected(self):
        with mock.patch.object(m, "sha", return_value="changed"):
            with self.assertRaisesRegex(ValueError, "parent manifest changed"):
                m.retained()

    def test_parent_generator_mutation_is_rejected_before_helpers(self):
        actual = m.sha
        with mock.patch.object(m, "sha", side_effect=lambda path: "changed" if path == Path(m.prior.__file__) else actual(path)):
            with mock.patch.object(m.prior, "helpers") as helpers:
                with self.assertRaisesRegex(ValueError, "parent generator changed"):
                    m.checked_helpers(self.manifest)
                helpers.assert_not_called()
        self.assertEqual(m.checked_helpers(self.manifest)["training/scripts/prepare_facturation_focus_v1.py"],
                         self.manifest["generator_sha256"])

    def test_native_update_is_exact_and_cannot_admit_other_changes(self):
        expected = m.native_expectations(self.manifest)
        source = self.manifest["native_metadata"]["facturation"]
        self.assertEqual({name for name in source if expected[name] != source[name]}, {"chat_ai/operations.py"})
        self.assertEqual(expected["chat_ai/operations.py"], m.NATIVE_UPDATES["chat_ai/operations.py"]["current_sha256"])
        changed = deepcopy(self.manifest)
        changed["native_metadata"]["facturation"]["chat_ai/operations.py"] = "unreviewed"
        with self.assertRaisesRegex(ValueError, "transition no longer matches parent"):
            m.native_expectations(changed)

    def test_exact_cartesian_optional_coverage_and_fixed_context(self):
        definitions = (
            ("date_optional_document", m.DOCUMENT_MODES,
             {(tool, resource) for tool, resource, *_ in m.DOCUMENTS},
             ("client_name", "product_name")),
            ("date_optional_operation", m.OPERATION_MODES,
             {("search_operations", resource) for resource, *_ in m.OPERATIONS},
             ("product_name", "location_name")),
        )
        for category, modes, resources, fields in definitions:
            selected = [row for row in self.rows if row["curriculum_category"] == category]
            cells, families = Counter(), defaultdict(list)
            for row in selected:
                target, details = m.function(row), row["contrast"]
                args = target["arguments"]
                cells[(target["name"], args.get("resource"), details["mode"],
                       details["optional_state"], row["language"])] += 1
                families[(row["contrast_family"], row["language"])].append(row)
                extras = set(args) - {"resource", "date_from", "date_to"}
                expected = {"none": set(), "first": {fields[0]}, "second": {fields[1]}, "limit": {"limit"}}[details["optional_state"]]
                self.assertEqual(extras, expected)
            expected = {(tool, resource, mode, state, language): 1
                        for tool, resource in resources for mode in modes
                        for state in m.OPTIONAL_STATES for language in ("en", "fr")}
            self.assertEqual(dict(cells), expected)
            for variants in families.values():
                self.assertEqual(len(variants), 4)
                self.assertEqual(len({row["messages"][0]["content"] for row in variants}), 1)
                self.assertEqual(len({row["messages"][-2]["content"].split("Current request: ", 1)[0]
                                      if "Current request: " in row["messages"][-2]["content"] else ""
                                      for row in variants}), 1)
                self.assertEqual(len({row["contrast"]["literal_date"] for row in variants}), 1)

    def test_date_literals_are_not_determined_by_mode(self):
        for category in ("date_optional_document", "date_optional_operation"):
            by_mode = defaultdict(set)
            for row in self.rows:
                if row["curriculum_category"] == category:
                    by_mode[row["contrast"]["mode"]].add(row["contrast"]["literal_date"])
            for dates in by_mode.values():
                self.assertEqual({date.fromisoformat(value).year for value in dates}, {2041, 2044, 2047, 2050, 2053})
                self.assertEqual({date.fromisoformat(value).day for value in dates}, {2, 5, 8, 14, 23})

    def test_every_date_label_matches_declared_inclusive_semantics(self):
        for row in self.rows:
            meta = row["contrast"]
            if "mode" not in meta or "literal_date" not in meta:
                continue
            day, mode = date.fromisoformat(meta["literal_date"]), meta["mode"]
            expected = {}
            if mode in ("lower", "day"):
                expected["date_from"] = day.isoformat()
            if mode in ("upper", "day"):
                expected["date_to"] = day.isoformat()
            if mode == "after":
                expected["date_from"] = (day + timedelta(days=1)).isoformat()
            if mode == "before":
                expected["date_to"] = (day - timedelta(days=1)).isoformat()
            if mode == "month":
                expected = {"date_from": day.replace(day=1).isoformat(),
                            "date_to": day.replace(day=calendar.monthrange(day.year, day.month)[1]).isoformat()}
            actual = {k: v for k, v in m.function(row)["arguments"].items() if k in ("date_from", "date_to")}
            self.assertEqual(actual, expected, (row["contrast_family"], row["language"]))

    def test_calendar_edges_have_independent_known_answers(self):
        examples = (
            (date(2048, 3, 1), "before", {"date_to": "2048-02-29"}),
            (date(2047, 1, 1), "before", {"date_to": "2046-12-31"}),
            (date(2044, 2, 29), "after", {"date_from": "2044-03-01"}),
            (date(2047, 12, 31), "after", {"date_from": "2048-01-01"}),
            (date(2044, 2, 5), "month", {"date_from": "2044-02-01", "date_to": "2044-02-29"}),
            (date(2041, 2, 5), "month", {"date_from": "2041-02-01", "date_to": "2041-02-28"}),
        )
        for day, mode, expected in examples:
            self.assertEqual(m.bounds(day, mode), expected)
        with self.assertRaises(ValueError):
            m.bounds(date(2041, 1, 1), "guess")

    def test_unpaid_is_optional_not_paid_only_and_crosses_limits(self):
        selected = [row for row in self.rows if row["curriculum_category"] == "unpaid_optional_filters"]
        cells = Counter()
        for row in selected:
            args, meta = m.function(row)["arguments"], row["contrast"]
            self.assertNotIn(False, [value for key, value in args.items() if key == "unpaid"])
            self.assertEqual("unpaid" in args, meta["unpaid_present"])
            self.assertEqual("limit" in args, meta["limit_present"])
            self.assertIn("client_name", args)
            self.assertIn("product_name", args)
            cells[(meta["mode"], meta["limit_present"], meta["unpaid_present"], row["language"])] += 1
        self.assertEqual(dict(cells), {(mode, limited, unpaid, language): 1
                                     for mode in m.DOCUMENT_MODES for limited in (False, True)
                                     for unpaid in (False, True) for language in ("en", "fr")})

    def test_remarks_preserve_full_delimited_literal_and_optional_due_date(self):
        selected = [row for row in self.rows if row["curriculum_category"] == "literal_field_copy"]
        self.assertEqual(len(selected), 12)
        for row in selected:
            args, meta, request = m.function(row)["arguments"], row["contrast"], m.current_request(row)
            changes = args["changes"]
            expected = {"remark_only": {"remarque"}, "due_only": {"date_echeance"},
                        "both": {"remarque", "date_echeance"}}[meta["fields"]]
            self.assertEqual(set(changes), expected)
            self.assertIn(args["identifier"], m.context(row)["previous_result_identifiers"])
            self.assertEqual(row["capability_profile"], "member_edit")
            if "remarque" in changes:
                self.assertEqual(changes["remarque"], meta["literal"])
                self.assertGreater(len(changes["remarque"].split()), 4)
                label = "Remarque : " if row["language"] == "fr" else "Remark: "
                line = next(line[len(label):] for line in request.splitlines() if line.startswith(label))
                self.assertEqual(line, '"' + meta["literal"] + '"' if meta["quoted"] else meta["literal"])
            if "date_echeance" in changes:
                self.assertEqual(changes["date_echeance"], meta["due_date"])

    def test_navigation_and_choice_use_trusted_selection(self):
        for row in self.rows:
            target, meta = m.function(row), row["contrast"]
            args, ctx = target["arguments"], m.context(row)
            if row["curriculum_category"] == "account_navigation":
                self.assertEqual(row["capability_profile"], "staff_read")
                if meta["target"] == "list":
                    self.assertEqual(args, {"resource": "users"})
                else:
                    self.assertEqual(args["resource"], "user")
                    self.assertIn(args["identifier"], ctx["previous_result_identifiers"])
            if row["curriculum_category"] == "explicit_result_choice":
                self.assertEqual(ctx["previous_result_count"], 2)
                if meta["selection"] == "unspecified":
                    self.assertEqual(target["name"], "clarify")
                    self.assertEqual(args, {"reason": "missing_details", "language": row["language"]})
                else:
                    self.assertEqual(target["name"], "previous_results")
                    self.assertEqual(args, {"operation": "open", "index": 2})

    def test_unique_requests_and_held_out_exclusion(self):
        keys = [m.key("facturation", m.current_request(row)) for row in self.rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertFalse(set(keys) & {m.key("facturation", m.current_request(row)) for row in self.parents["train"]})
        manifest, _, _ = m.prior.retained()
        m.prior.check_exclusions(manifest, self.rows)
        contaminated = deepcopy(self.rows[:1])
        contaminated[0]["messages"][-2] = deepcopy(self.parents["valid"][0]["messages"][-2])
        with self.assertRaisesRegex(ValueError, "Frozen"):
            m.prior.check_exclusions(manifest, contaminated)

    def test_operation_date_wording_matches_native_date_field(self):
        for row in self.rows:
            if row["curriculum_category"] != "date_optional_operation" or row["contrast"]["mode"] == "none":
                continue
            resource = m.function(row)["arguments"]["resource"]
            request = m.current_request(row)
            if resource == "stock_balance":
                self.assertIn("mises à jour" if row["language"] == "fr" else "updated", request)
            else:
                self.assertIn("créé" if row["language"] == "fr" else "created", request)


if __name__ == "__main__":
    unittest.main()
