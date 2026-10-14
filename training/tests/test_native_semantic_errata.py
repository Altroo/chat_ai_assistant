"""Semantic wording corrections preserve targets, history and split lineage."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
from prepare_native_semantic_errata import SOURCES, EXPECTED_COUNTS, replace_request, sha, prepare
from prepare_serial_dialogue_v7 import prompt_key, historical_gm_input
from serial_scope_v2 import validate_stage, validate_retained_curriculum
from audit_training_inputs import audit


class NativeSemanticErrataTests(unittest.TestCase):
    def test_only_reviewed_requests_and_native_metadata_change(self):
        for app, (prefix, parent) in SOURCES.items():
            source = ROOT / 'training/datasets' / (prefix + '-dialogue-v3-en-fr')
            output = source.with_name(prefix + '-dialogue-v4-en-fr')
            manifest = json.loads((output / 'manifest.json').read_text())
            self.assertEqual(sha(source / 'manifest.json'), parent)
            self.assertEqual(manifest['source_manifest_sha256'], parent)
            self.assertEqual(manifest['generator_sha256'], sha(ROOT / 'training/scripts/prepare_native_semantic_errata.py'))
            self.assertEqual(manifest['targets_changed'], 0)
            for name, expected_count in EXPECTED_COUNTS[app].items():
                before = [json.loads(x) for x in (source / name).read_text().splitlines()]
                after = [json.loads(x) for x in (output / name).read_text().splitlines()]
                self.assertEqual(len(before), len(after))
                self.assertEqual(sha(output / name), manifest['files'][name])
                changes = []
                for index, (old, new) in enumerate(zip(before, after)):
                    position = -1 if name.endswith('.eval.jsonl') else -2
                    self.assertEqual(new['messages'][position]['content'], replace_request(old['messages'][position]['content'], app))
                    if new['messages'][position] != old['messages'][position]:
                        changes.append(index)
                    restored = deepcopy(new)
                    restored['messages'][0] = old['messages'][0]
                    restored['messages'][position] = old['messages'][position]
                    if name.endswith('.eval.jsonl'):
                        restored['offered_tools'] = old['offered_tools']
                        restored['offered_tool_schemas'] = old['offered_tool_schemas']
                    else:
                        restored['tools'] = old['tools']
                    self.assertEqual(restored, old)
                    self.assertEqual(
                        new['messages'][0]['content'].split('Trusted context: ', 1)[1],
                        old['messages'][0]['content'].split('Trusted context: ', 1)[1])
                self.assertEqual(changes, manifest['changed_request_indices'][name])
                self.assertEqual(len(changes), expected_count)

    def test_gm_all_envelopes_use_creation_date_semantics(self):
        output = ROOT / 'training/datasets/gestion-magasin-dialogue-v4-en-fr'
        for name in EXPECTED_COUNTS['gestion_magasin']:
            for row in map(json.loads, (output / name).read_text().splitlines()):
                self.assertIn('sales CREATED TODAY', row['messages'][0]['content'])
                self.assertIn('does not filter payment dates', row['messages'][0]['content'])
                tools = row.get('tools', row.get('offered_tool_schemas', []))
                for tool in tools:
                    if tool['function']['name'] == 'financial_summary':
                        self.assertIn('not payment-date receipts', tool['function']['description'])

    def test_cumulative_curricula_keep_predecessor_and_pass_input_audit(self):
        previous = ROOT / 'training/datasets/shared-v5r8-en-fr'
        for app, version, count in (('contrat', 6, 2492), ('gestion_magasin', 7, 2690), ('reservation', 8, 2870)):
            path = previous.with_name(f'shared-v{version}r9-en-fr')
            manifest = json.loads((path / 'manifest.json').read_text())
            payloads = [(path / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')]
            rows = [list(map(json.loads, raw.splitlines())) for raw in payloads]
            self.assertEqual(len(rows[0]), count)
            validate_stage(app, manifest, *rows, complete_epochs=1)
            validate_retained_curriculum(app, manifest, *payloads, previous)
            report = audit(path)
            self.assertEqual(report['exact_input_label_conflicts'], 0)
            self.assertEqual(report['exact_input_cross_split_overlap'], 0)
            excluded = set()
            for name, info in {**manifest['held_out'], **manifest['historical_regression_held_out']}.items():
                p = ROOT / name
                self.assertEqual(sha(p), info['sha256'])
                excluded.update(prompt_key(row) for row in map(json.loads, p.read_text().splitlines()))
            self.assertFalse({prompt_key(row) for split in rows for row in split} & excluded)
            previous = path

    def test_versions_cannot_be_overwritten(self):
        for app in SOURCES:
            with self.assertRaisesRegex(ValueError, 'Never overwrite'):
                prepare(app, ROOT)

    def test_historical_evaluation_is_bound_to_reviewed_source(self):
        from unittest.mock import patch
        source = ROOT / 'training/datasets/gestion-magasin-dialogue-v3-en-fr'
        expected = historical_gm_input(source)
        original = (source / 'test.eval.jsonl').read_bytes()
        read_bytes = Path.read_bytes
        def altered(path):
            return original + b'{}\n' if path == source / 'test.eval.jsonl' else read_bytes(path)
        with patch.object(Path, 'read_bytes', altered):
            with self.assertRaisesRegex(ValueError, 'evaluation changed'):
                historical_gm_input(source)
        self.assertEqual(expected['sha256'], sha(source / 'test.eval.jsonl'))

    def test_replacement_never_changes_quoted_background(self):
        old = '/voir les contrats de Démo Acacia concernant peinture.'
        text = 'Earlier user messages (background only): ["' + old + '"]\nCurrent request: Hello'
        self.assertEqual(replace_request(text, 'contrat'), text)
        self.assertEqual(replace_request('Quoted request: ' + old, 'contrat'), 'Quoted request: ' + old)


if __name__ == '__main__':
    unittest.main()
