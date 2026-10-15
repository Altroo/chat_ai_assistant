"""Pretraining must reject targets that the serving budget cannot complete."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "training/scripts"), str(ROOT / "runtime/colibri/c")]
from preflight_training import verify_split
from openai_server import parse_qwen_tool_calls

TOOLS = [{"type": "function", "function": {
    "name": "find", "parameters": {
        "type": "object", "properties": {"query": {"type": "string"}},
        "required": ["query"], "additionalProperties": False,
    },
}}]


class CharacterTokenizer:
    """Inspectable token boundaries; no model, tokenizer downloads or inference."""

    def __init__(self, prompt_size, value="example", overlap=False):
        self.prefix = "P" * prompt_size
        self.target = ("<tool_call>\n<function=find>\n<parameter=query>\n"
                       + value + "\n</parameter>\n</function>\n</tool_call><|im_end|>\n")
        self.overlap = overlap

    def token_ids(self, text):
        values = list(map(ord, text))
        if self.overlap and len(text) > len(self.prefix):
            values[len(self.prefix) - 1] = 1000
        return values

    def apply_chat_template(self, messages, tokenize, add_generation_prompt, **options):
        text = self.prefix if add_generation_prompt else self.prefix + self.target
        return self.token_ids(text) if tokenize else text

    def __call__(self, text, **options):
        return {"input_ids": self.token_ids(text),
                "offset_mapping": [(i, i + 1) for i in range(len(text))]}


def payload(value="example"):
    return (json.dumps({
        "messages": [{"role": "user", "content": "Find example"},
                     {"role": "assistant", "tool_calls": [{"function": {
                         "name": "find", "arguments": {"query": value},
                     }}]}],
        "tools": TOOLS,
    }) + "\n").encode()


class OutputBudgetTests(unittest.TestCase):
    def check(self, tokenizer, context=8192, output=512, value="example"):
        return verify_split(
            payload(value), parse_qwen_tool_calls, tokenizer, context,
            lambda *args, **kwargs: tokenizer.prefix, 4,
            maximum_output_tokens=output,
        )

    def test_target_larger_than_default_512_is_rejected_even_with_context_space(self):
        tokenizer = CharacterTokenizer(10, value="x" * 600)
        with self.assertRaisesRegex(ValueError, "serving output budget"):
            self.check(tokenizer, value="x" * 600)

    def test_exact_budget_includes_eos_and_template_suffix(self):
        tokenizer = CharacterTokenizer(10)
        count = len(tokenizer.target)
        report = self.check(tokenizer, output=count)
        self.assertEqual(report["maximum_target_tokens"], count)
        self.assertEqual(report["output_budget_passed"], 1)
        self.assertEqual(report["output_budget_contract"], "conservative-target-v1")
        self.assertEqual(report["minimum_output_budget"], count)
        with self.assertRaisesRegex(ValueError, "serving output budget"):
            self.check(tokenizer, output=count - 1)

    def test_context_space_can_reduce_the_output_budget(self):
        tokenizer = CharacterTokenizer(8000)
        target = len(tokenizer.target)
        self.assertLess(target, 192)
        report = self.check(tokenizer)
        self.assertEqual(report["minimum_output_budget"], 192)
        with self.assertRaisesRegex(ValueError, "serving output budget"):
            self.check(tokenizer, context=8000 + target - 1)

    def test_boundary_overlap_is_counted_conservatively(self):
        tokenizer = CharacterTokenizer(10, overlap=True)
        count = len(tokenizer.target)
        with self.assertRaisesRegex(ValueError, "serving output budget"):
            self.check(tokenizer, output=count)
        report = self.check(tokenizer, output=count + 1)
        self.assertEqual(report["maximum_target_tokens"], count + 1)

    def test_no_remaining_context_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "serving output budget"):
            self.check(CharacterTokenizer(8192))

    def test_nonpositive_and_noninteger_budgets_are_rejected(self):
        for value in (0, -1, True, 1.5, float("nan")):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "Positive integer"):
                    self.check(CharacterTokenizer(10), output=value)
                with self.assertRaisesRegex(ValueError, "Positive integer"):
                    self.check(CharacterTokenizer(10), context=value)


if __name__ == "__main__":
    unittest.main()
