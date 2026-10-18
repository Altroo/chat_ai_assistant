"""Safety and semantics checks for synthetic native stock-profile transfer."""
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
    "stock_profiles", ROOT / "training/scripts/prepare_facturation_stock_profiles_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def bundle(broad=False):
    branches = []
    for resource in (*m.STOCK, "logistics_order") if broad else m.STOCK:
        branches.append({"type": "object", "properties": {
            "resource": {"const": resource}, "product_name": {"type": "string"},
            "location_name": {"type": "string"}, "date_from": {"type": "string"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 10}},
            "required": ["resource"], "additionalProperties": False})
    return [{"type": "function", "function": {
        "name": name, "description": "Synthetic test tool.",
        "parameters": {"type": "object", "oneOf": branches} if name == "search_operations"
        else {"type": "object", "properties": {
            "resource": {"enum": list(m.STOCK) + (["logistics_order"] if broad else [])}}}}}
        for name in m.TOOL_NAMES]


def row():
    return {"application": "facturation", "language": "en", "capability_profile": "member_read",
        "tools": bundle(True), "messages": [
            {"role": "system", "content": 'Rules. Trusted context: {"application":"facturation",'
             '"current_invoice_id":null,"previous_result_type":null,"current_resource":null}'},
            {"role": "user", "content": 'Earlier user messages (background only): ["Hello"]\n'
             "Current request: Show two balances of SYN-Product at SYN-Location since 2032-04-02."},
            {"role": "assistant", "content": None, "tool_calls": [{"type": "function",
              "function": {"name": "search_operations", "arguments": {
                  "resource": "stock_balance", "product_name": "SYN-Product",
                  "location_name": "SYN-Location", "date_from": "2032-04-02", "limit": 2}}}]}]}


class StockProfileTests(unittest.TestCase):
    def test_only_offered_bundle_and_profile_metadata_change(self):
        original = row()
        before = deepcopy(original)
        variant = m.profile_variant(original, bundle(), 17)
        self.assertEqual(variant["messages"], original["messages"])
        self.assertEqual(variant["tools"], bundle())
        self.assertEqual(variant["capability_profile"], "stock_only")
        self.assertEqual(variant["language"], original["language"])
        self.assertEqual(original, before)
        self.assertEqual(variant["augmentation"]["source_row_index"], 17)

    def test_original_target_and_input_are_bound(self):
        original = row()
        proof = m.profile_variant(original, bundle(), 19)["augmentation"]
        self.assertEqual(proof["source_input_sha256"],
                         m.prior.digest(m.prior.input_key(original).encode()))
        self.assertEqual(proof["source_target_sha256"], m.prior.digest(m.prior.encoded(
            original["messages"][-1]["tool_calls"][0]["function"]).encode()))

    def test_other_applications_are_skipped(self):
        original = row()
        original["application"] = "management_projet"
        self.assertIsNone(m.profile_variant(original, bundle(), 0))

    def test_logistics_targets_are_never_transferred_to_stock_only(self):
        original = row()
        original["messages"][-1]["tool_calls"][0]["function"]["arguments"]["resource"] = "logistics_order"
        self.assertIsNone(m.profile_variant(original, bundle(), 0))

    def test_nonoperation_tools_are_skipped(self):
        original = row()
        original["messages"][-1]["tool_calls"][0]["function"]["name"] = "financial_summary"
        self.assertIsNone(m.profile_variant(original, bundle(), 0))

    def test_existing_stock_only_bundle_is_not_duplicated(self):
        original = row()
        original["tools"] = bundle()
        self.assertIsNone(m.profile_variant(original, bundle(), 0))

    def test_foreign_page_or_result_context_is_not_claimed_as_stock_only(self):
        for patch in ({"current_invoice_id": 14}, {"current_resource": "invoice"},
                      {"previous_result_type": "payment"}, {"previous_result_type": "logistics_order"}):
            original = row()
            context = {"application": "facturation", **patch}
            original["messages"][0]["content"] = "Rules. Trusted context: " + json.dumps(context)
            with self.subTest(context=context):
                self.assertIsNone(m.profile_variant(original, bundle(), 0))

    def test_compatible_stock_context_is_preserved(self):
        original = row()
        original["messages"][0]["content"] = (
            'Rules. Trusted context: {"application":"facturation",'
            '"current_resource":"stock_receipt","current_identifier":21,'
            '"previous_result_type":"stock_balance","previous_result_count":3}')
        variant = m.profile_variant(original, bundle(), 0)
        self.assertEqual(variant["messages"], original["messages"])

    def test_schema_tampering_is_not_silently_accepted(self):
        tools = bundle()
        tools[0]["function"]["parameters"]["oneOf"][0]["properties"]["limit"]["maximum"] = 20
        with self.assertRaises(ValueError):
            m.profile_variant(row(), tools, 0)

    def test_invalid_arguments_fail_closed(self):
        original = row()
        original["messages"][-1]["tool_calls"][0]["function"]["arguments"]["supplier_name"] = "SYN-Supplier"
        with self.assertRaises(Exception) as error:
            m.profile_variant(original, bundle(), 0)
        self.assertEqual(type(error.exception).__name__, "ValidationError")

    def test_template_must_exist_and_have_a_single_exact_bundle(self):
        with self.assertRaises(ValueError):
            m.template([row()])
        first = row()
        first["tools"] = bundle()
        second = deepcopy(first)
        second["tools"][1]["function"]["description"] = "Changed."
        with self.assertRaises(ValueError):
            m.template([first, second])

    def test_history_and_mutable_metadata_are_not_shared(self):
        original = row()
        variant = m.profile_variant(original, bundle(), 0)
        variant["messages"][-2]["content"] = "Changed"
        variant["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = 9
        self.assertEqual(original, row())

    def test_existing_output_and_source_overwrite_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            source.mkdir()
            for destination in (source, source / "child", Path(temp)):
                with self.subTest(destination=destination), self.assertRaises(ValueError):
                    m.prepare(source, destination)


if __name__ == "__main__":
    unittest.main()
