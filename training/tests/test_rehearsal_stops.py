"""Synthetic captures through the real Colibri parser, without model inference."""
from contextlib import nullcontext
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
sys.path.insert(0, str(ROOT / 'runtime/colibri/c'))
import openai_server as serving
import rehearse_cpu_v2 as rehearsal
from training.tests.test_cpu_rehearsal import Tensor, row


class ServingStopCaptureTests(unittest.TestCase):
    def call(self, arguments=None):
        arguments = {'query': 'synthetic'} if arguments is None else arguments
        return ('<tool_call>\n<function=find>\n' + ''.join(
            '<parameter=' + key + '>\n' + value + '\n</parameter>\n'
            for key, value in arguments.items()) + '</function>\n</tool_call>')

    def capture(self, reply, *, terminal=True, budget=512):
        history, decoded = [], []
        class Tokenizer:
            bos_token_id = pad_token_id = None
            def convert_tokens_to_ids(self, token):
                return {'<|im_end|>': 1, '<|endoftext|>': 2}[token]
            def apply_chat_template(self, messages, **kwargs):
                return 'prompt'
            def __call__(self, text, **kwargs):
                return {'input_ids': Tensor([[9] * (8192 - budget)])}
            def decode(self, tokens, **kwargs):
                decoded.append(tokens.tolist())
                return reply
        class Model:
            training = True
            def eval(self):
                self.training = False
            def train(self, mode):
                self.training = mode
            def generate(self, **kwargs):
                return Tensor([kwargs['input_ids'].values[0] + [42, 2 if terminal else 43]])
        model = Model()
        torch = SimpleNamespace(inference_mode=nullcontext, random=SimpleNamespace(
            get_rng_state=lambda: 'original', set_rng_state=history.append))
        records = []
        with patch.object(serving, 'ARCH', 'qwen36'), patch.object(serving, 'CHAT_FLAVOR', None):
            stops, ignore = serving.stop_policy({}, chat=True)
            self.assertEqual(stops, ('<|im_end|>', '<|im_start|>'))
            self.assertFalse(ignore)
            result = rehearsal.capture(model, Tokenizer(), {'train': [row('facturation', 'synthetic')], 'valid': []},
                {'train': [0], 'valid': []}, serving.parse_qwen_tool_calls,
                lambda *a, **kw: 'prompt', serving.split_thinking_reply, serving.StopFilter, stops,
                torch, SimpleNamespace, 8192, records.append, lambda: None)
        self.assertEqual(result, records)
        self.assertTrue(model.training)
        self.assertEqual(history, ['original'])
        self.assertEqual(decoded, [[42]] if terminal else [[42, 43]])
        return result[0]

    def test_tool_after_role_boundary_is_not_credited(self):
        reply = '<|im_start|>assistant\n' + self.call()
        self.assertEqual(len(serving.parse_qwen_tool_calls(reply, row('facturation', 'x')['tools'])[1]), 1)
        result = self.capture(reply)
        self.assertEqual(result['reply'], reply)
        self.assertEqual(result['generated_token_ids'], [42, 2])
        self.assertEqual(result['served_reply'], '')
        self.assertEqual(result['matched_stop'], '<|im_start|>')
        self.assertFalse(result['schema_valid'])
        self.assertFalse(result['matches_training_or_development_target'])
        self.assertIsNone(result['action'])

    def test_textual_end_marker_prevents_later_call(self):
        for marker in ('<|im_end|>', '<|im_start|>'):
            with self.subTest(marker=marker):
                result = self.capture('Visible text. ' + marker + self.call())
                self.assertEqual(result['served_reply'], 'Visible text. ')
                self.assertEqual(result['matched_stop'], marker)
                self.assertIsNone(result['action'])

    def test_valid_call_before_boundary_preserved_and_second_call_removed(self):
        reply = self.call() + '<|im_start|>assistant\n' + self.call({'query': 'other'})
        result = self.capture(reply, terminal=False)
        self.assertEqual(result['served_reply'], self.call())
        self.assertTrue(result['schema_valid'])
        self.assertTrue(result['matches_training_or_development_target'])
        self.assertFalse(result['terminal_eos'])

    def test_stop_precedes_thinking_split(self):
        reply = '<think>private analysis<|im_start|></think>' + self.call()
        result = self.capture(reply)
        self.assertEqual(result['served_reply'], '<think>private analysis')
        self.assertIsNone(result['action'])

    def test_thinking_disabled_matches_native_streamed_answer(self):
        # The pinned runtime starts in answer mode and strips markers. It does
        # not re-enter reasoning upon an unexpected opening marker in this mode.
        reply = '<think>' + self.call() + '</think>Visible text'
        answer = []
        native = serving.ThinkingStreamSplit(lambda text: None, answer.append, initial_thinking=False)
        for character in reply:
            native.feed(character)
        native.finish()
        _, calls = serving.parse_qwen_tool_calls(''.join(answer), row('facturation', 'x')['tools'])
        result = self.capture(reply)
        self.assertIsNone(result['matched_stop'])
        self.assertEqual(result['action']['name'], calls[0]['function']['name'])
        self.assertTrue(result['schema_valid'])

    def test_complete_call_without_eos_remains_valid(self):
        result = self.capture(self.call(), terminal=False)
        self.assertTrue(result['schema_valid'])
        self.assertTrue(result['matches_training_or_development_target'])
        self.assertEqual(result['served_reply'], result['reply'])
        self.assertIsNone(result['matched_stop'])

    def test_invalid_schema_is_not_credited(self):
        result = self.capture(self.call({'query': 'synthetic', 'extra': 'not offered'}))
        self.assertFalse(result['schema_valid'])
        self.assertEqual(result['parse_error'], 'ValidationError')
        self.assertFalse(result['matches_training_or_development_target'])

    def test_budget_exhaustion_without_call_remains_incomplete(self):
        result = self.capture('unfinished text', terminal=False, budget=2)
        self.assertEqual(result['parse_error'], 'INCOMPLETE_RESPONSE')
        self.assertFalse(result['schema_valid'])

    def test_stop_is_not_misreported_as_budget_exhaustion(self):
        result = self.capture('<|im_start|>' + self.call(), terminal=False, budget=2)
        self.assertIsNone(result['parse_error'])
        self.assertEqual(result['matched_stop'], '<|im_start|>')
        self.assertFalse(result['schema_valid'])

    def test_partial_stop_suffix_matches_native_finish(self):
        reply = self.call() + '<|im_sta'
        result = self.capture(reply)
        self.assertEqual(result['served_reply'], reply)
        self.assertIsNone(result['matched_stop'])
        self.assertTrue(result['schema_valid'])

    def test_one_shot_filter_matches_native_fragmented_stream(self):
        for reply in (self.call(), '<|im_start|>' + self.call(),
                      self.call() + '<|im_end|>' + self.call({'query': 'other'}),
                      '<think>analysis<|im_start|></think>' + self.call()):
            with self.subTest(reply=reply):
                streamed = []
                native = serving.StopFilter(serving.DEFAULT_QWEN36_CHAT_STOP_SEQUENCES,
                                            streamed.append, ignore_leading=False)
                for character in reply:
                    native.feed(character)
                native.finish()
                result = self.capture(reply)
                self.assertEqual(result['served_reply'], ''.join(streamed))
                self.assertEqual(result['matched_stop'], native.matched)


if __name__ == '__main__':
    unittest.main()
