from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_facturation_entity_pilot_v1 as subject


def row(tool, text, arguments, schema, language=None):
    result = {"application": "management_projet",
              "messages": [{"role": "system", "content": "Trusted context."},
                           {"role": "user", "content": text},
                           {"role": "assistant", "tool_calls": [{"function": {
                               "name": tool, "arguments": arguments}}]}],
              "tools": [{"function": {"name": tool, "parameters": schema}}]}
    if language is not None:
        result["language"] = language
    return result


SCHEMA = {"type": "object", "properties": {
    "period": {"type": "string", "enum": ["current_year", "previous_year"]},
    "query": {"type": "string"}}, "additionalProperties": False}


class RetentionTests(unittest.TestCase):
    def sample(self):
        return [row(name, f"{name} request {i}", {"period": period}, SCHEMA)
                for name in ("search_records", "financial_summary", "clarify")
                for i, period in enumerate(("current_year", "previous_year", "current_year"))]

    def test_every_tool_and_enum_covered_without_repeating_or_mutating(self):
        source = self.sample(); original = deepcopy(source)
        indices, report = subject.retained(source, "management_projet", 6)
        self.assertEqual(len(set(indices)), 6)
        self.assertEqual(set(report["by_tool"]), {"search_records", "financial_summary", "clarify"})
        self.assertTrue(all(value["uncovered"] == [] for value in report["feature_coverage"].values()))
        self.assertEqual(source, original)
        self.assertTrue(all("language" not in source[index] for index in indices))

    def test_selection_is_deterministic_and_order_independent(self):
        source = self.sample()
        first, _ = subject.retained(source, "management_projet", 6)
        second, _ = subject.retained(list(reversed(source)), "management_projet", 6)
        self.assertEqual([source[i] for i in first], [list(reversed(source))[i] for i in second])

    def test_budget_must_cover_tools_and_never_oversample(self):
        for count in (0, 2, 10, True):
            with self.assertRaises(ValueError):
                subject.retained(self.sample(), "management_projet", count)

    def test_canonical_neutral_history_duplicates_do_not_consume_budget(self):
        source = self.sample()[:1]
        wrapped = deepcopy(source[0])
        wrapped["messages"][-2]["content"] = (
            'Earlier user messages (background only): ["Hello"]\nCurrent request: '
            + wrapped["messages"][-2]["content"])
        with self.assertRaisesRegex(ValueError, "without repeating"):
            subject.retained(source + [wrapped], "management_projet", 2)

    def test_conflicting_canonical_target_rejected(self):
        source = self.sample()[:1]
        conflict = deepcopy(source[0])
        conflict["messages"][-1]["tool_calls"][0]["function"]["arguments"]["period"] = "previous_year"
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            subject.retained(source + [conflict], "management_projet", 1)

    def test_unoffered_target_and_invalid_schema_rejected(self):
        from jsonschema import ValidationError
        source = self.sample()[:1]
        source[0]["tools"] = []
        with self.assertRaisesRegex(ValueError, "not offered"):
            subject.retained(source, "management_projet", 1)
        source = self.sample()[:1]
        source[0]["messages"][-1]["tool_calls"][0]["function"]["arguments"]["period"] = "wrong"
        with self.assertRaises(ValidationError):
            subject.retained(source, "management_projet", 1)

    def test_feature_extraction_ignores_free_text_literals(self):
        first = subject.features({"query": "SYN-Alice"}, SCHEMA)
        second = subject.features({"query": "SYN-Bob"}, SCHEMA)
        self.assertEqual(first, second)
        self.assertNotEqual(subject.features({"period": "current_year"}, SCHEMA),
                            subject.features({"period": "previous_year"}, SCHEMA))

    def test_no_other_application_and_no_invented_language(self):
        source = self.sample()
        ignored = deepcopy(source[0]); ignored["application"] = "facturation"
        indices, report = subject.retained(source + [ignored], "management_projet", 6)
        self.assertNotIn(len(source), indices)
        self.assertEqual(report["language_metadata"], {"unspecified": 6})


if __name__ == "__main__":
    unittest.main()
