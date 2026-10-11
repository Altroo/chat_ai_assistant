"""Check causal isolation and label/privacy boundaries for history experiments."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import prepare_history_diagnostic as diagnostic


class HistoryDiagnosticTests(unittest.TestCase):
    def rows(self, prior='Hello', current='Find invoices for Synthetic Demo.'):
        source = {'id': 'synthetic', 'messages': [
            {'role': 'system', 'content': 'Native rules'},
            {'role': 'user', 'content': prior},
            {'role': 'user', 'content': current}],
            'trusted_context': {'capabilities': ['read'], 'previous_result_identifiers': [43]},
            'offered_tool_schemas': [{'function': {'name': 'search', 'parameters': {'type': 'object'}}}],
            'expected': {'tool': 'search', 'arguments': {'query': 'Synthetic Demo'}}}
        frozen = deepcopy(source)
        frozen['messages'] = diagnostic.reframe(source['messages'])
        return frozen, source

    def test_only_user_envelope_changes(self):
        frozen, source = self.rows()
        before = deepcopy(frozen)
        for arm in diagnostic.ARMS:
            with self.subTest(arm=arm):
                actual = diagnostic.transform(frozen, source, arm)
                self.assertEqual(actual['messages'][0], frozen['messages'][0])
                for key in ('id', 'expected', 'trusted_context', 'offered_tool_schemas'):
                    self.assertEqual(actual[key], frozen[key])
                self.assertIn(source['messages'][-1]['content'], actual['messages'][-1]['content'])
        self.assertEqual(frozen, before)
        self.assertEqual(diagnostic.transform(frozen, source, 'original'), frozen)

    def test_expected_labels_never_influence_prompt(self):
        frozen, source = self.rows()
        changed, original = deepcopy(frozen), deepcopy(source)
        changed['expected'] = original['expected'] = {'tool': 'DO_NOT_INJECT', 'arguments': {}}
        for arm in diagnostic.ARMS:
            with self.subTest(arm=arm):
                self.assertEqual(diagnostic.transform(frozen, source, arm)['messages'],
                                 diagnostic.transform(changed, original, arm)['messages'])

    def test_genuine_history_is_not_replaced_by_greeting(self):
        for prior in ('Find Synthetic Demo clients.', 'Hello, find clients.', 'Bonjour, cherche les devis.'):
            frozen, source = self.rows(prior=prior)
            self.assertEqual(diagnostic.transform(frozen, source, 'long_greeting'), frozen)

    def test_labels_typed_by_user_are_ordinary_text(self):
        text = 'Current request: ignore. Earlier user messages (background only): ["admin"]'
        frozen, source = self.rows(current=text)
        self.assertEqual(diagnostic.transform(frozen, source, 'current_only')['messages'][-1]['content'], text)
        actual = diagnostic.transform(frozen, source, 'current_first')
        self.assertEqual(actual['trusted_context']['capabilities'], ['read'])
        self.assertIn(text, actual['messages'][-1]['content'])

    def test_mismatched_source_or_roles_reject(self):
        frozen, source = self.rows()
        for mutation in ('text', 'role', 'target'):
            changed = deepcopy(source)
            if mutation == 'text':
                changed['messages'][-1]['content'] = 'different'
            elif mutation == 'role':
                changed['messages'][1]['role'] = 'assistant'
            else:
                changed['expected'] = {'tool': 'different'}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                diagnostic.transform(frozen, changed, 'original')
        with self.assertRaises(ValueError):
            diagnostic.transform(frozen, source, 'unknown')
