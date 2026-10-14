import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from jsonschema import ValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import audit_training_inputs as audit


class InputAuditTests(unittest.TestCase):
    def row(self, text, app='facturation', tool='find', arguments=None):
        return {'application': app, 'language': 'en',
                'messages': [{'role': 'system', 'content': 'synthetic Trusted context: ' + json.dumps({'application': app})},
                             {'role': 'user', 'content': text},
                             {'role': 'assistant', 'tool_calls': [{'function': {
                                 'name': tool, 'arguments': arguments or {'query': 'synthetic'}}}]}],
                'tools': [{'function': {'name': 'find', 'parameters': {
                    'type': 'object', 'properties': {'query': {'type': 'string'}},
                    'required': ['query'], 'additionalProperties': False}}}]}

    def fixture(self, root, train=None, valid=None):
        train = train if train is not None else [self.row('find train')]
        valid = valid if valid is not None else [self.row('find validation')]
        files = {}
        for split, rows in [('train', train), ('valid', valid)]:
            payload = ''.join(json.dumps(row) + '\n' for row in rows).encode()
            (root / (split + '.jsonl')).write_bytes(payload)
            files[split + '.jsonl'] = audit.digest(payload)
        (root / 'manifest.json').write_text(json.dumps({
            'applications': sorted({row['application'] for row in train}),
            'languages': ['en', 'fr'], 'files': files}))
        return root

    def test_dry_run_has_no_accuracy_claim_and_preserves_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(Path(folder))
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            result = audit.audit(root)
            self.assertFalse(result['training_executed'])
            self.assertFalse(result['accuracy_estimated'])
            self.assertEqual(result['rows_checked'], {'train': 1, 'valid': 1})
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_contradictory_labels_rejected_before_rehearsal(self):
        with tempfile.TemporaryDirectory() as folder:
            first = self.row('same request')
            second = copy.deepcopy(first)
            second['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 'different'
            with self.assertRaisesRegex(ValueError, 'contradictory'):
                audit.audit(self.fixture(Path(folder), train=[first, second]))

    def test_cross_split_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            row = self.row('same request')
            with self.assertRaisesRegex(ValueError, 'cross training and validation'):
                audit.audit(self.fixture(Path(folder), train=[row], valid=[copy.deepcopy(row)]))

    def test_input_identity_ignores_application_metadata_and_targets(self):
        first = self.row('same request')
        second = copy.deepcopy(first)
        second['application'] = 'management_projet'
        second['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 'different'
        self.assertEqual(audit.model_input_key(first), audit.model_input_key(second))
        self.assertEqual(audit.rehearsal([first, second], 96)['count'], 1)

    def test_forged_application_cannot_hide_conflicts_or_split_overlap(self):
        for split in ('train', 'valid'):
            with self.subTest(split=split), tempfile.TemporaryDirectory() as folder:
                first = self.row('same request')
                forged = copy.deepcopy(first)
                forged['application'] = 'management_projet'
                train = [first, self.row('other train', app='management_projet')]
                valid = [self.row('validation'), self.row('other validation', app='management_projet')]
                if split == 'train':
                    forged['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 'different'
                    train.append(forged)
                else:
                    valid.append(forged)
                with self.assertRaisesRegex(ValueError, 'differs from trusted context'):
                    audit.audit(self.fixture(Path(folder), train=train, valid=valid))

    def test_trusted_context_must_be_present_valid_and_match(self):
        contents = [None, 'synthetic', 'Trusted context: invalid',
                    'Trusted context: []', 'Trusted context: {}',
                    'Trusted context: {"application":"management_projet"}']
        for content in contents:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as folder:
                row = self.row('request')
                row['messages'][0]['content'] = content
                with self.assertRaisesRegex(ValueError, 'context'):
                    audit.audit(self.fixture(Path(folder), train=[row]))

    def test_unsupported_explicit_language_rejected_and_missing_supported(self):
        for language in ('es', 'ar', 'ary', 'EN', None):
            with self.subTest(language=language), tempfile.TemporaryDirectory() as folder:
                row = self.row('request')
                row['language'] = language
                with self.assertRaisesRegex(ValueError, 'Unsupported explicit language'):
                    audit.audit(self.fixture(Path(folder), train=[row]))
        with tempfile.TemporaryDirectory() as folder:
            row = self.row('request')
            del row['language']
            result = audit.audit(self.fixture(Path(folder), train=[row]))
            self.assertEqual(result['rows_checked']['train'], 1)

    def test_genuine_history_is_not_collapsed(self):
        first = self.row('open it')
        second = copy.deepcopy(first)
        first['messages'].insert(1, {'role': 'user', 'content': 'find first'})
        second['messages'].insert(1, {'role': 'user', 'content': 'find second'})
        second['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 'different'
        with tempfile.TemporaryDirectory() as folder:
            result = audit.audit(self.fixture(Path(folder), train=[first, second]))
            self.assertEqual(result['rows_checked']['train'], 2)

    def test_unoffered_invalid_and_duplicate_tool_schema_rejected(self):
        for change in ('unoffered', 'invalid', 'duplicate'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as folder:
                row = self.row('request')
                if change == 'unoffered':
                    row['messages'][-1]['tool_calls'][0]['function']['name'] = 'shell'
                elif change == 'invalid':
                    row['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 7
                else:
                    row['tools'].append(copy.deepcopy(row['tools'][0]))
                with self.assertRaises((ValueError, ValidationError)):
                    audit.audit(self.fixture(Path(folder), train=[row]))

    def test_changed_payload_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.fixture(Path(folder))
            (root / 'train.jsonl').write_text((root / 'train.jsonl').read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                audit.audit(root)

    def test_selection_is_deterministic_and_covers_declared_features(self):
        rows = [self.row('request ' + str(i), app=app)
                for app in ('facturation', 'management_projet') for i in range(6)]
        for row in rows[::2]:
            row['language'] = 'fr'
        chosen = audit.rehearsal(rows, 96)
        self.assertEqual(chosen, audit.rehearsal(rows, 96))
        actual = set().union(*(audit.features(rows[i]) for i in chosen['row_indices']))
        self.assertEqual(actual, set().union(*(audit.features(row) for row in rows)))
        with self.assertRaisesRegex(ValueError, 'budget'):
            audit.rehearsal(rows, 1)


if __name__ == '__main__':
    unittest.main()
