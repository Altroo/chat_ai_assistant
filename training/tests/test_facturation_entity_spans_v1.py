from copy import deepcopy
import sys
from pathlib import Path
import unittest
from jsonschema import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_facturation_entity_spans_v1 as subject


def row(tool="search_payments", text="Find payments for customer SYN-Rose and article SYN-PIN.",
        args=None, language="en"):
    args = args if args is not None else {
        "client_name": "SYN-Rose", "product_name": "SYN-PIN",
        "status": "Valide", "date_from": "2031-02-04", "limit": 3}
    properties = {k: {"type": "string"} for k in
                  ("client_name", "product_name", "query", "reference", "invoice_number", "status", "date_from")}
    properties["limit"] = {"type": "integer", "minimum": 1, "maximum": 10}
    return {"application": "facturation", "language": language,
            "messages": [{"role": "system", "content": "Trusted calendar: 2031-02-04."},
                         {"role": "user", "content": text},
                         {"role": "assistant", "tool_calls": [{"id": "call_test", "type": "function",
                          "function": {"name": tool, "arguments": deepcopy(args)}}]}],
            "tools": [{"type": "function", "function": {"name": tool,
                       "parameters": {"type": "object", "properties": properties,
                                      "additionalProperties": False}}}]}


class EntitySpanTests(unittest.TestCase):
    def test_payment_preserves_every_nonentity_filter_and_source(self):
        source = row(); original = deepcopy(source)
        value = subject.variant(source, ["client_name", "product_name"], "en", 2, 2)
        args = value["messages"][-1]["tool_calls"][0]["function"]["arguments"]
        self.assertEqual({k: args[k] for k in ("status", "date_from", "limit")},
                         {"status": "Valide", "date_from": "2031-02-04", "limit": 3})
        self.assertEqual(value["tools"], source["tools"])
        self.assertEqual(value["messages"][0], source["messages"][0])
        self.assertEqual(source, original)
        self.assertIn(args["client_name"], value["messages"][-2]["content"])
        self.assertIn(args["product_name"], value["messages"][-2]["content"])

    def test_payment_query_remains_invoice_customer_query(self):
        source = row(text="Search payment invoice numbers or customer names for SYN-PAY.",
                     args={"query": "SYN-PAY", "status": "Valide"})
        value = subject.variant(source, ["query"], "en", 3, 1)
        self.assertEqual(set(value["messages"][-1]["tool_calls"][0]["function"]["arguments"]),
                         {"query", "status"})

    def test_payment_product_query_intent_rejected(self):
        with self.assertRaisesRegex(ValueError, "invoice/customer"):
            subject.variant(row(text="Search payment product lines for SYN-PAY.",
                                args={"query": "SYN-PAY"}), ["query"], "en", 0, 0)

    def test_article_alias_key_is_never_normalized(self):
        for field in ("query", "product_name"):
            source = row("search_articles", "Search reference or designation for SYN-FIN.",
                         {field: "SYN-FIN"})
            value = subject.variant(source, [field], "en", 1, 0)
            self.assertEqual(set(value["messages"][-1]["tool_calls"][0]["function"]["arguments"]),
                             {field})

    def test_reference_remains_reference(self):
        source = row("search_articles", "Find article reference SYN-REF-21.",
                     {"reference": "SYN-REF-21"})
        value = subject.variant(source, ["reference"], "en", 2, 3)
        self.assertIn("reference", value["messages"][-1]["tool_calls"][0]["function"]["arguments"])

    def test_client_first_and_last_name_remain_person_name(self):
        source = row("search_clients", "Trouve un client dont le prénom et le nom sont SYN-Ana SYN-Mer.",
                     {"query": "SYN-Ana SYN-Mer"}, "fr")
        value = subject.variant(source, ["query"], "fr", 2, 0)
        self.assertEqual(len(value["messages"][-1]["tool_calls"][0]["function"]["arguments"]["query"].split()), 2)

    def test_company_or_code_parent_rejected(self):
        for word in ("company", "code", "société"):
            with self.assertRaisesRegex(ValueError, "company/code"):
                subject.variant(row("search_clients", f"Find client {word} SYN-CO.",
                                    {"query": "SYN-CO"}), ["query"], "en", 0, 0)

    def test_real_history_and_context_are_not_rewritten(self):
        for context in ("system", "history"):
            source = row()
            if context == "system":
                source["messages"][0]["content"] += " Customer SYN-Rose."
            else:
                source["messages"][-2]["content"] = (
                    'Earlier user messages (background only): ["Find SYN-Rose"]\nCurrent request: '
                    + source["messages"][-2]["content"])
            with self.assertRaisesRegex(ValueError, "History"):
                subject.variant(source, ["client_name", "product_name"], "en", 0, 0)

    def test_neutral_history_preserved_byte_for_byte(self):
        source = row()
        prefix = 'Earlier user messages (background only): ["Bonjour"]\nCurrent request: '
        source["messages"][-2]["content"] = prefix + source["messages"][-2]["content"]
        value = subject.variant(source, ["client_name", "product_name"], "en", 0, 0)
        self.assertTrue(value["messages"][-2]["content"].startswith(prefix))

    def test_ambiguous_roles_rejected(self):
        source = row(text="Find payments SYN-Rose and SYN-PIN.")
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            subject.variant(source, ["client_name", "product_name"], "en", 0, 0)

    def test_missing_grounding_and_substring_match_rejected(self):
        source = row(text="Find payments for SYN-Rosewood and article SYN-PIN.")
        with self.assertRaises(ValueError):
            subject.variant(source, ["client_name", "product_name"], "en", 0, 0)

    def test_unchanged_argument_link_rejected(self):
        source = row(); source["messages"][-1]["tool_calls"][0]["function"]["arguments"]["invoice_number"] = "SYN-Rose"
        with self.assertRaises(ValueError):
            subject.variant(source, ["client_name", "product_name"], "en", 0, 0)

    def test_unoffered_tool_and_unsupported_write_rejected(self):
        source = row(); source["tools"] = []
        with self.assertRaisesRegex(ValueError, "not offered"):
            subject.variant(source, ["client_name", "product_name"], "en", 0, 0)
        source = row(); source["messages"][-1]["tool_calls"][0]["function"]["name"] = "delete_invoice"
        with self.assertRaisesRegex(ValueError, "native search"):
            subject.variant(source, ["client_name", "product_name"], "en", 0, 0)

    def test_invalid_retained_argument_is_not_copied(self):
        source = row(); source["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = 99
        with self.assertRaises(ValidationError):
            subject.variant(source, ["client_name", "product_name"], "en", 0, 0)

    def test_language_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "English or French"):
            subject.variant(row(), ["client_name", "product_name"], "fr", 0, 0)


if __name__ == "__main__":
    unittest.main()
