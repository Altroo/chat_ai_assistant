"""Behavior checks for training-only Facturation role-name variants."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "role_variants", ROOT / "training/scripts/prepare_facturation_role_variants_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def row(product="SYN-Article-A", location="SYN-Depot-B", *, history=False):
    context = {"application": "facturation", "capabilities": ["read"], "company_id": 7}
    properties = {
        "resource": {"const": "stock_balance"},
        "product_name": {"type": "string", "maxLength": 120},
        "location_name": {"type": "string", "maxLength": 120},
        "date_from": {"type": "string"}, "limit": {"type": "integer", "maximum": 10},
    }
    request = f"Depuis le 2031-04-12, cherche deux stocks de {product} dans {location}."
    if history:
        request = 'Earlier user messages (background only): ["Hello"]\nCurrent request: ' + request
    return {
        "application": "facturation", "language": "fr",
        "messages": [
            {"role": "system", "content": "Trusted context: " + json.dumps(context)},
            {"role": "user", "content": request},
            {"role": "assistant", "content": None, "tool_calls": [{
                "type": "function", "function": {"name": "search_operations", "arguments": {
                    "resource": "stock_balance", "product_name": product,
                    "location_name": location, "date_from": "2031-04-12", "limit": 2}}}]},
        ],
        "tools": [{"type": "function", "function": {
            "name": "search_operations", "description": "Search permitted stock.",
            "parameters": {"type": "object", "properties": properties,
                           "required": ["resource"], "additionalProperties": False}}}],
    }


class RoleVariantTests(unittest.TestCase):
    def test_rotation_changes_question_and_roles_together(self):
        original = row()
        rotated, _ = m.role_variants(original, 11)
        args = rotated["messages"][-1]["tool_calls"][0]["function"]["arguments"]
        self.assertEqual(args["product_name"], "SYN-Depot-B")
        self.assertEqual(args["location_name"], "SYN-Article-A")
        self.assertIn("stocks de SYN-Depot-B dans SYN-Article-A", rotated["messages"][-2]["content"])
        self.assertEqual(args["date_from"], "2031-04-12")
        self.assertEqual(args["limit"], 2)

    def test_original_permissions_schema_history_and_target_are_not_mutated(self):
        original = row(history=True)
        before = deepcopy(original)
        for variant in m.role_variants(original, 8):
            self.assertEqual(variant["messages"][0], original["messages"][0])
            self.assertEqual(variant["tools"], original["tools"])
            self.assertTrue(variant["messages"][-2]["content"].startswith(
                'Earlier user messages (background only): ["Hello"]\nCurrent request: '))
            self.assertEqual(variant["language"], "fr")
        self.assertEqual(original, before)

    def test_substitution_is_simultaneous_and_identifier_bounded(self):
        self.assertEqual(m.substitute("SYN-A puis SYN-B", {"SYN-A": "SYN-B", "SYN-B": "SYN-A"}),
                         "SYN-B puis SYN-A")
        self.assertEqual(m.substitute("SYN-A-2 puis SYN-A",
                                     {"SYN-A": "SYN-A-2", "SYN-A-2": "SYN-A"}),
                         "SYN-A puis SYN-A-2")
        with self.assertRaises(ValueError):
            m.substitute("SYN-A-2", {"SYN-A": "SYN-B"})

    def test_opaque_names_are_distinct_and_in_both_question_and_target(self):
        _, opaque = m.role_variants(row(), 5)
        args = opaque["messages"][-1]["tool_calls"][0]["function"]["arguments"]
        self.assertNotEqual(args["product_name"], args["location_name"])
        for key in ("product_name", "location_name"):
            self.assertIn(args[key], opaque["messages"][-2]["content"])
            self.assertTrue(args[key].startswith("SYN-CF-"))

    def test_bare_conjunctions_cannot_assign_literal_roles(self):
        for separator in (" and ", " et ", " & ", " + ", ", ", ", and ", " / "):
            original = row()
            original["messages"][-2]["content"] = (
                "Filter stock to SYN-Article-A" + separator + "SYN-Depot-B.")
            with self.subTest(separator=separator):
                self.assertEqual(len(m.role_variants(original, 0)), 0)

    def test_explicit_role_cues_preserve_transformable_requests(self):
        for request in (
            "Filter to product SYN-Article-A and location SYN-Depot-B.",
            "Article SYN-Article-A et emplacement SYN-Depot-B.",
            "Stock de SYN-Article-A dans SYN-Depot-B.",
        ):
            original = row()
            original["messages"][-2]["content"] = request
            with self.subTest(request=request):
                self.assertEqual(len(m.role_variants(original, 0)), 2)

    def test_neutral_greetings_share_seed_and_canonical_input(self):
        original = row()
        for greeting in sorted(m.NEUTRAL_HISTORY):
            wrapped = row(history=True)
            wrapped["messages"][-2]["content"] = wrapped["messages"][-2]["content"].replace(
                '["Hello"]', json.dumps([greeting], ensure_ascii=False))
            with self.subTest(greeting=greeting):
                self.assertEqual(m.canonical_input_key(original), m.canonical_input_key(wrapped))
                plain_variants = m.role_variants(original, 1)
                wrapped_variants = m.role_variants(wrapped, 2)
                self.assertEqual(
                    [v["messages"][-1] for v in plain_variants],
                    [v["messages"][-1] for v in wrapped_variants])
                for variant in wrapped_variants:
                    self.assertIn(json.dumps([greeting], ensure_ascii=False),
                                  variant["messages"][-2]["content"])

    def test_real_or_multiple_history_messages_are_never_canonicalized(self):
        for history in (["Find recent stock."], ["Hello", "Find recent stock."],
                        ["Hello", "Bonjour"], [" hello"], ["Thanks"]):
            wrapped = row(history=True)
            wrapped["messages"][-2]["content"] = wrapped["messages"][-2]["content"].replace(
                '["Hello"]', json.dumps(history))
            with self.subTest(history=history):
                self.assertNotEqual(m.canonical_input_key(row()), m.canonical_input_key(wrapped))

    def test_repeat_is_deterministic(self):
        self.assertEqual(m.role_variants(row(), 13), m.role_variants(row(), 13))

    def test_other_applications_and_nonsearch_tools_are_excluded(self):
        original = row()
        original["application"] = "management_projet"
        self.assertEqual(m.role_variants(original, 0), [])
        original = row()
        original["messages"][-1]["tool_calls"][0]["function"]["name"] = "prepare_change"
        self.assertEqual(m.role_variants(original, 0), [])

    def test_ambiguous_or_unapproved_literals_are_excluded(self):
        self.assertEqual(m.role_variants(row("SYN-A", "SYN-A"), 0), [])
        self.assertEqual(m.role_variants(row("Real Company", "SYN-A"), 0), [])
        self.assertEqual(m.role_variants(row("SYN-A<script>", "SYN-B"), 0), [])

    def test_nonstring_arguments_do_not_generate_examples(self):
        original = row()
        original["messages"][-1]["tool_calls"][0]["function"]["arguments"]["product_name"] = []
        self.assertEqual(m.role_variants(original, 0), [])

    def test_literals_in_trusted_context_or_history_are_excluded(self):
        original = row()
        original["messages"][0]["content"] += " SYN-Article-A"
        self.assertEqual(m.role_variants(original, 0), [])
        original = row(history=True)
        original["messages"][-2]["content"] = original["messages"][-2]["content"].replace(
            '["Hello"]', '["Earlier SYN-Article-A"]')
        self.assertEqual(m.role_variants(original, 0), [])

    def test_missing_user_literal_is_not_guessed(self):
        original = row()
        original["messages"][-2]["content"] = "Find the stock here."
        self.assertEqual(m.role_variants(original, 0), [])

    def test_invalid_target_fails_closed(self):
        original = row()
        original["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = 100
        with self.assertRaises(Exception) as error:
            m.role_variants(original, 0)
        self.assertEqual(type(error.exception).__name__, "ValidationError")

    def test_malformed_history_is_rejected(self):
        with self.assertRaises(ValueError):
            m.current_request('Earlier user messages (background only): {"bad":1}\nCurrent request: Hi')

    def test_development_template_pattern_ignores_literals_dates_and_counts(self):
        first, second = row(), row("SYN-Other", "SYN-Place")
        first["messages"][-2]["content"] = first["messages"][-2]["content"].replace("deux", "2")
        second["messages"][-2]["content"] = second["messages"][-2]["content"].replace(
            "2031-04-12", "2035-06-22").replace("deux", "3")
        second["messages"][-1]["tool_calls"][0]["function"]["arguments"]["limit"] = 3
        second["messages"][-1]["tool_calls"][0]["function"]["arguments"]["date_from"] = "2035-06-22"
        self.assertEqual(m.request_pattern(first), m.request_pattern(second))
        second["messages"][-2]["content"] = "Explain stock management."
        self.assertNotEqual(m.request_pattern(first), m.request_pattern(second))

    def test_prepare_deduplicates_neutral_parents_and_preserves_selected_history(self):
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / "source", Path(temp) / "output"
            source.mkdir()
            first = row(history=True)
            plain = row()
            development = row()
            development["messages"][-2]["content"] = "Explain stock permissions."
            content = {
                "manifest.json": json.dumps({"version": "facturation-replay-v3-en-fr"}).encode(),
                "train.jsonl": ("\n".join(json.dumps(r) for r in
                                          [first] + [plain] * 2974) + "\n").encode(),
                "valid.jsonl": (json.dumps(development) + "\n").encode(),
            }
            for name, data in content.items():
                (source / name).write_bytes(data)
            with patch.object(m, "SOURCE_SHA256", {k: m.digest(v) for k, v in content.items()}):
                result = m.prepare(source, output)
            generated = [json.loads(line) for line in (output / "contrasts.jsonl").read_text().splitlines()]
            self.assertEqual(result["count"], 2)
            self.assertEqual(result["distinct_source_parents"], 1)
            self.assertEqual(result["exclusions"]["neutral_parent_duplicate"], 2974)
            for variant in generated:
                self.assertEqual(variant["augmentation"]["source_row_index"], 0)
                self.assertTrue(variant["messages"][-2]["content"].startswith(
                    'Earlier user messages (background only): ["Hello"]'))
            for name, data in content.items():
                self.assertEqual((source / name).read_bytes(), data)

    def test_existing_output_or_immutable_source_destination_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            source.mkdir()
            existing = Path(temp) / "exists"
            existing.mkdir()
            for output in (source, source / "child", existing):
                with self.subTest(output=output), self.assertRaises(ValueError):
                    m.prepare(source, output)

    def test_changed_source_is_refused_before_writing(self):
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / "source", Path(temp) / "output"
            source.mkdir()
            for name in m.SOURCE_SHA256:
                (source / name).write_text("changed")
            with self.assertRaises(ValueError):
                m.prepare(source, output)
            self.assertFalse(output.exists())

    def test_provenance_binds_original_input_and_target(self):
        original = row()
        for variant in m.role_variants(original, 42):
            proof = variant["augmentation"]
            self.assertEqual(proof["source_row_index"], 42)
            self.assertEqual(proof["source_input_sha256"], m.digest(m.input_key(original).encode()))
            self.assertEqual(proof["fields"], ["product_name", "location_name"])


if __name__ == "__main__":
    unittest.main()
