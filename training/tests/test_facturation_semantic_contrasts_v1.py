"""Synthetic semantic guards for contrast data, not model-accuracy tests."""
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_facturation_semantic_contrasts_v1 as subject


def fixture():
    properties = {
        "resource": {"type": "string"}, "identifier": {"type": "integer", "minimum": 1},
        "operation": {"enum": ["open", "update", "delete"]}, "index": {"type": "integer", "minimum": 1},
        "reason": {"enum": ["unsupported", "missing_details"]}, "language": {"enum": ["en", "fr"]},
        "date_from": {"type": "string"}, "date_to": {"type": "string"},
        "product_name": {"type": "string"}, "client_name": {"type": "string"},
        "supplier_name": {"type": "string"}, "location_name": {"type": "string"},
        "status": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 10},
        "unpaid": {"type": "boolean"}, "changes": {
            "type": "object", "properties": {
                "remarque": {"type": "string"}, "date_echeance": {"type": "string"}},
            "additionalProperties": False},
    }
    schema = {"type": "object", "properties": properties, "additionalProperties": False}
    def row(index):
        context = {
            "application": "facturation", "today": "2027-11-18",
            "interface_language": "en", "current_identifier": None, "current_invoice_id": None,
            "previous_result_count": 0, "previous_result_identifiers": [],
            "calendar": {"current_month_first_day": "2027-11-01",
                         "previous_month_first_day": "2027-10-01",
                         "previous_month_last_day": "2027-10-31"},
        }
        return {
            "application": "facturation",
            "messages": [
                {"role": "system", "content": "Synthetic verified context.\nTrusted context: " + json.dumps(context)},
                {"role": "user", "content": f'Earlier user messages (background only): ["Hello"]\nCurrent request: Synthetic parent {index}'},
                {"role": "assistant", "tool_calls": [{"function": {
                    "name": "list_payments", "arguments": {}}}]},
            ],
            "tools": [{"type": "function", "function": {
                "name": name, "description": "Synthetic fixture tool", "parameters": deepcopy(schema)}}
                for name in ("list_payments", "navigate", "search_operations", "prepare_change",
                             "search_invoices", "previous_results", "clarify", "search_quotes")],
        }
    rows = [row(i) for i in range(1, 488)]
    targets = {
        81: ("prepare_change", {"resource": "proforma", "identifier": 72081, "operation": "update",
                               "changes": {"remarque": "SYN-Old note 301", "date_echeance": "2034-09-13"}}),
        169: ("prepare_change", {"resource": "quote", "identifier": 72080, "operation": "update",
                                "changes": {"remarque": "SYN-Old note 300", "date_echeance": "2034-09-12"}}),
        86: ("search_invoices", {"limit": 2, "client_name": "SYN-Customer-A", "product_name": "SYN-Product-B",
                                "unpaid": True, "date_from": "2032-03-01", "date_to": "2032-03-01"}),
        250: ("search_invoices", {"limit": 1, "client_name": "SYN-Customer-C", "product_name": "SYN-Product-D",
                                 "unpaid": True, "date_from": "2023-01-09"}),
        91: ("search_operations", {"resource": "logistics_order", "client_name": "SYN-Client",
                                  "supplier_name": "SYN-Supplier", "product_name": "SYN-Product",
                                  "status": "Transit"}),
        330: ("search_operations", {"resource": "logistics_order", "product_name": "SYN-Product",
                                   "location_name": "SYN-Location"}),
        487: ("search_operations", {"resource": "logistics_order", "client_name": "SYN-Client",
                                   "product_name": "SYN-Product"}),
        97: ("navigate", {"resource": "user", "identifier": 98127}),
        111: ("navigate", {"resource": "users"}),
        178: ("clarify", {"reason": "missing_details", "language": "fr"}),
        192: ("clarify", {"reason": "missing_details", "language": "en"}),
        177: ("clarify", {"reason": "unsupported", "language": "en"}),
        194: ("clarify", {"reason": "unsupported", "language": "fr"}),
        281: ("search_quotes", {"limit": 3}),
    }
    for n, (tool, arguments) in targets.items():
        rows[n - 1]["messages"][-1]["tool_calls"][0]["function"] = {
            "name": tool, "arguments": arguments}
    for n, resource, identifiers in (
        (97, "user", [98127]), (178, "invoice", [76008, 76003, 76091]),
        (192, "quote", [98461, 98403]),
    ):
        r = rows[n - 1]
        context = subject.trusted_context(r)
        context.update(previous_result_type=resource, previous_result_count=len(identifiers),
                       previous_result_identifiers=identifiers)
        r["messages"][0]["content"] = "Synthetic verified context.\nTrusted context: " + json.dumps(context)
    return rows


def args(row):
    return subject.target(row)["arguments"]


class SemanticContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parents = fixture()
        cls.generated = subject.generate(cls.parents)

    def family(self, name):
        return [row for row in self.generated if row["augmentation"]["family"] == name]

    def text(self, row):
        return subject.helper().current_request(row["messages"][-2]["content"])[1]

    def test_generation_is_pure_and_balanced(self):
        source = fixture()
        before = deepcopy(source)
        generated = subject.generate(source)
        self.assertEqual(source, before)
        self.assertEqual(generated, self.generated)
        self.assertEqual(Counter(r["language"] for r in generated), {"en": 58, "fr": 58})

    def test_context_history_and_permission_schemas_never_change(self):
        for row in self.generated:
            parent = self.parents[row["augmentation"]["source_line"] - 1]
            self.assertEqual(row["tools"], parent["tools"])
            self.assertEqual(row["messages"][:-2], parent["messages"][:-2])
            self.assertEqual(subject.helper().current_request(row["messages"][-2]["content"])[0],
                             subject.helper().current_request(parent["messages"][-2]["content"])[0])

    def test_generated_rows_drop_obsolete_parent_annotations(self):
        parents = deepcopy(self.parents)
        for n in subject.PARENTS:
            parents[n - 1].update(
                capability_profile="synthetic_unchanged_access",
                contrast={"mode": "none", "literal_date": "2044-04-05"},
                contrast_family="obsolete-parent-family",
                curriculum_category="obsolete-parent-category",
                augmentation={"version": "obsolete-parent-version"})
        generated = subject.generate(parents)
        for row in generated:
            self.assertNotIn("contrast", row)
            self.assertNotIn("contrast_family", row)
            self.assertEqual(row["capability_profile"], "synthetic_unchanged_access")
            self.assertEqual(row["curriculum_category"], row["augmentation"]["family"])
            self.assertEqual(row["augmentation"]["version"], subject.VERSION)

    def test_payment_upper_bounds_include_or_exclude_anchor_correctly(self):
        selected = {(r["augmentation"]["factors"].get("anchor"),
                     r["augmentation"]["factors"]["mode"], r["language"]): args(r)
                    for r in self.family("date_boundaries")}
        self.assertEqual(selected[("2032-02-29", "upper_inclusive", "fr")], {"date_to": "2032-02-29"})
        self.assertEqual(selected[("2032-02-29", "upper_exclusive", "fr")], {"date_to": "2032-02-28"})
        self.assertEqual(selected[("2031-12-31", "lower_exclusive", "en")], {"date_from": "2032-01-01"})
        self.assertEqual(selected[("2032-02-29", "lower_exclusive", "en")], {"date_from": "2032-03-01"})

    def test_unbounded_payment_omits_both_date_keys(self):
        rows = [r for r in self.family("date_boundaries")
                if r["augmentation"]["factors"]["mode"] == "unbounded"]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(args(r) == {} for r in rows))

    def test_users_collection_has_no_identifier_and_detail_uses_authorized_id(self):
        for row in self.family("users_collection_versus_detail"):
            if row["augmentation"]["factors"]["collection"]:
                self.assertEqual(args(row), {"resource": "users"})
            else:
                self.assertEqual(args(row), {"resource": "user", "identifier": 98127})
                self.assertIn(98127, subject.trusted_context(row)["previous_result_identifiers"])

    def test_unverified_detail_id_is_rejected(self):
        rows = deepcopy(self.parents)
        rows[96]["messages"][-1]["tool_calls"][0]["function"]["arguments"]["identifier"] = 999
        with self.assertRaisesRegex(ValueError, "already be authorized"):
            subject.generate(rows)

    def test_logistics_literals_have_explicit_correct_role_cues(self):
        for row in self.family("logistics_entity_roles"):
            labels = ({"client_name": "customer", "product_name": "product",
                       "supplier_name": "supplier", "location_name": "location"} if row["language"] == "en"
                      else {"client_name": "client", "product_name": "produit",
                            "supplier_name": "fournisseur", "location_name": "emplacement"})
            for field, label in labels.items():
                if field in args(row):
                    self.assertIn(label + " " + args(row)[field], self.text(row))
            self.assertEqual(args(row)["resource"], "logistics_order")
            if row["augmentation"]["source_line"] == 91:
                self.assertEqual(args(row)["status"], "Transit")
                self.assertIn("Transit", self.text(row))

    def test_logistics_rejects_filter_not_represented_in_generated_request(self):
        rows = deepcopy(self.parents)
        rows[329]["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = 2
        with self.assertRaisesRegex(ValueError, "unhandled filters"):
            subject.generate(rows)

    def test_remarks_copy_complete_punctuation_and_keep_identifier_and_due_date(self):
        for row in self.family("verbatim_update_text"):
            parent = self.parents[row["augmentation"]["source_line"] - 1]
            original = args(parent)
            self.assertEqual({k: v for k, v in args(row).items() if k != "changes"},
                             {k: v for k, v in original.items() if k != "changes"})
            self.assertEqual(args(row)["changes"]["date_echeance"], original["changes"]["date_echeance"])
            self.assertIn(args(row)["changes"]["remarque"], self.text(row))
            self.assertGreater(len(args(row)["changes"]["remarque"].split()), 2)
            self.assertIn(original["changes"]["date_echeance"], self.text(row))

    def test_unpaid_counterparts_keep_every_other_filter(self):
        pairs = defaultdict(dict)
        for row in self.family("unpaid_with_other_filters"):
            meta = row["augmentation"]
            pairs[(meta["source_line"], row["language"], meta["factors"]["paraphrase"])][meta["factors"]["unpaid"]] = row
        self.assertEqual(len(pairs), 12)
        for pair in pairs.values():
            unrestricted, unpaid = pair[False], pair[True]
            expected = dict(args(unpaid))
            self.assertIs(expected.pop("unpaid"), True)
            self.assertNotIn("unpaid", args(unrestricted))
            self.assertEqual(args(unrestricted), expected)
            self.assertEqual(unpaid["tools"], unrestricted["tools"])
            self.assertEqual(unpaid["messages"][:-2], unrestricted["messages"][:-2])
            self.assertIn(args(unpaid)["client_name"], self.text(unpaid))
            self.assertIn(args(unpaid)["product_name"], self.text(unpaid))

    def test_explicit_second_result_and_ambiguous_choice_have_different_tools(self):
        for row in self.family("ambiguous_previous_result_selection"):
            if row["augmentation"]["factors"]["explicit"]:
                self.assertEqual(subject.target(row)["name"], "previous_results")
                self.assertEqual(args(row), {"operation": "open", "index": 2})
            else:
                self.assertEqual(subject.target(row)["name"], "clarify")
                self.assertEqual(args(row), {"reason": "missing_details", "language": row["language"]})

    def test_selection_requires_two_real_previous_results(self):
        rows = deepcopy(self.parents)
        r = rows[177]
        context = subject.trusted_context(r)
        context["previous_result_count"] = 1
        context["previous_result_identifiers"] = [76008]
        r["messages"][0]["content"] = "Trusted context: " + json.dumps(context)
        with self.assertRaisesRegex(ValueError, "two unresolved"):
            subject.generate(rows)

    def test_missing_offered_tool_is_rejected(self):
        rows = deepcopy(self.parents)
        rows[177]["tools"] = [t for t in rows[177]["tools"] if t["function"]["name"] != "previous_results"]
        with self.assertRaisesRegex(ValueError, "offered tools"):
            subject.generate(rows)

    def test_relative_months_end_on_real_last_day_and_keep_result_limit(self):
        for row in self.family("relative_quote_month"):
            previous = row["augmentation"]["factors"]["previous"]
            self.assertEqual(args(row), {
                "limit": 3, "date_from": "2027-10-01" if previous else "2027-11-01",
                "date_to": "2027-10-31" if previous else "2027-11-30"})
        self.assertEqual(subject.month_bounds("2028-02-15"), ("2028-02-01", "2028-02-29"))
        self.assertEqual(subject.month_bounds("2032-01-10", True), ("2031-12-01", "2031-12-31"))

    def test_inconsistent_trusted_calendar_is_rejected(self):
        rows = deepcopy(self.parents)
        r = rows[280]
        context = subject.trusted_context(r)
        context["calendar"]["previous_month_last_day"] = "2027-10-30"
        r["messages"][0]["content"] = "Trusted context: " + json.dumps(context)
        with self.assertRaisesRegex(ValueError, "month end disagrees"):
            subject.generate(rows)

    def test_clarification_language_follows_current_message(self):
        rows = self.family("unsupported_current_language")
        self.assertEqual(len(rows), 8)
        for row in rows:
            self.assertEqual(subject.target(row)["name"], "clarify")
            self.assertEqual(args(row), {"reason": "unsupported", "language": row["language"]})
        self.assertTrue(any(r["language"] == "fr" and subject.trusted_context(r)["interface_language"] == "en"
                            for r in rows))

    def test_permission_filtered_financial_context_must_not_offer_reporting(self):
        rows = deepcopy(self.parents)
        fake = deepcopy(rows[193]["tools"][0])
        fake["function"]["name"] = "financial_summary"
        rows[193]["tools"].append(fake)
        with self.assertRaisesRegex(ValueError, "must not offer reporting"):
            subject.generate(rows)

    def test_development_labels_are_not_needed_for_exclusion(self):
        selected = self.generated[0]
        development = deepcopy(selected)
        development["messages"][-1] = {"role": "assistant", "content": "INVALID GOLD"}
        with self.assertRaisesRegex(ValueError, "overlap"):
            subject.validate_exclusions([], [selected], [development])

    def test_value_only_development_template_overlap_is_rejected(self):
        selected = deepcopy(self.generated[0])
        development = deepcopy(selected)
        development["messages"][-2]["content"] = development["messages"][-2]["content"].replace("2031-12-31", "2042-10-17")
        with self.assertRaisesRegex(ValueError, "overlap"):
            subject.validate_exclusions([], [selected], [development])

    def test_generated_input_duplicate_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            subject.validate_exclusions([], [self.generated[0], self.generated[0]], [])

    def test_sensitive_generated_text_and_unoffered_argument_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            subject.make(self.parents[197], 198, "test", "en", "api_key=ABC", {})
        with self.assertRaises(Exception):
            subject.make(self.parents[197], 198, "test", "en", "Show payments.", {"arbitrary_code": "bad"})

    def test_changed_helper_is_rejected_before_import(self):
        with patch.object(subject, "HELPER_SHA256", "0" * 64):
            with self.assertRaisesRegex(ValueError, "helper changed"):
                subject.helper()

    def test_existing_output_and_modified_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            with self.assertRaisesRegex(ValueError, "new isolated"):
                subject.prepare(source, root / "native", source)
            for name in subject.SOURCE_SHA256:
                (source / name).write_text("changed")
            with self.assertRaisesRegex(ValueError, "source changed"):
                subject.prepare(source, root / "native", root / "output")
            self.assertFalse((root / "output").exists())

    def test_prepare_preserves_replay_and_matches_existing_cli_manifest_contracts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, native, output = root / "source", root / "native", root / "prepared"
            source.mkdir()
            native.mkdir()
            training = fixture()
            while len(training) < 704:
                row = deepcopy(training[0])
                row["messages"][-2]["content"] = f"Unique synthetic replay input {len(training)}"
                training.append(row)
            for index, row in enumerate(training):
                row["application"] = ("facturation" if index < 520 else
                                      "management_projet" if index < 632 else "design_workflow")
            validation = deepcopy(training[:273] + training[520:521] + training[632:633])
            for index, row in enumerate(validation):
                row["messages"][-2]["content"] = f"Unique development exclusion input {index}"
            train_raw = ("".join(json.dumps(r) + "\n" for r in training)).encode()
            valid_raw = ("".join(json.dumps(r) + "\n" for r in validation)).encode()
            payloads = {"train.jsonl": train_raw, "valid.jsonl": valid_raw, "manifest.json": b"{}"}
            pins = {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()}
            for name, raw in payloads.items():
                (source / name).write_bytes(raw)
            native_pins = {}
            for name in subject.NATIVE_SHA256:
                file = native / name
                file.parent.mkdir(exist_ok=True)
                file.write_bytes(b"synthetic native pin")
                native_pins[name] = hashlib.sha256(file.read_bytes()).hexdigest()
            with patch.object(subject, "SOURCE_SHA256", pins), patch.object(subject, "NATIVE_SHA256", native_pins):
                manifest = subject.prepare(source, native, output)
            self.assertEqual(set(manifest["languages"]), {"en", "fr"})
            declared = set(manifest["applications"])
            for split in ("train.jsonl", "valid.jsonl"):
                data = (output / split).read_bytes()
                self.assertEqual({r["application"] for r in map(json.loads, data.splitlines())}, declared)
                self.assertEqual(hashlib.sha256(data).hexdigest(), manifest["files"][split])
            self.assertEqual((output / "valid.jsonl").read_bytes(), valid_raw)
            self.assertEqual((output / "train.jsonl").read_bytes(),
                             train_raw + (output / "contrasts.jsonl").read_bytes())
            self.assertEqual(manifest["combined_rows"], 820)
            with self.assertRaisesRegex(ValueError, "new isolated"):
                subject.prepare(source, native, output)

    def test_changed_native_contract_prevents_any_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, native = root / "source", root / "native"
            source.mkdir()
            native.mkdir()
            data = b"synthetic"
            pins = {name: hashlib.sha256(data).hexdigest() for name in subject.SOURCE_SHA256}
            for name in pins:
                (source / name).write_bytes(data)
            for name in subject.NATIVE_SHA256:
                file = native / name
                file.parent.mkdir(exist_ok=True)
                file.write_text("changed native contract")
            with patch.object(subject, "SOURCE_SHA256", pins):
                with self.assertRaisesRegex(ValueError, "native business contracts changed"):
                    subject.prepare(source, native, root / "output")
            self.assertFalse((root / "output").exists())


if __name__ == "__main__":
    unittest.main()
