"""Verify exact errata scope and preservation of the original frozen evidence."""
from copy import deepcopy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
sys.path.insert(0, str(ROOT / 'src'))
import prepare_dialogue_errata_v2 as build
from jsonschema import validate
from chat_ai_assistant.clarifications import CLARIFICATION_SCHEMA


class DialogueErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = {p.name: p.read_bytes() for p in build.SOURCE.iterdir() if p.is_file()}
        cls.parent = json.loads(cls.source['manifest.json'])
        cls.rows = {row['id']: row for name in cls.parent['inputs']
                    for row in map(json.loads, cls.source[name].decode().splitlines())}

    def test_only_three_documented_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'v2'
            report = build.prepare(output=target)
            self.assertEqual(report['count'], 438)
            self.assertEqual(report['changed_count'], 3)
            changed = set()
            for name in self.parent['inputs']:
                old = self.source[name].decode().splitlines(keepends=True)
                new = (target / name).read_text().splitlines(keepends=True)
                self.assertEqual(len(old), len(new))
                for a, b in zip(old, new):
                    if a != b:
                        changed.add(json.loads(a)['id'])
                    else:
                        self.assertEqual(a, b)
            self.assertEqual(changed, build.CHANGED_IDS)
            self.assertEqual(self.source, {p.name: p.read_bytes() for p in build.SOURCE.iterdir() if p.is_file()})
            self.assertEqual(set(report['inputs']), set(self.parent['inputs']))
            self.assertEqual(report['acceptance_sha256'], build.sha(ROOT / 'training/scripts/model_acceptance.py'))

    def test_strict_before_date_is_excluded(self):
        for key in build.DATE_REQUESTS:
            with self.subTest(case=key):
                original = self.rows[key]
                corrected = build.correct(original)
                limit = date.fromisoformat(corrected['expected']['arguments']['date_to'])
                self.assertLess(limit, date(2026, 11, 1))
                self.assertEqual(limit, date(2026, 10, 31))
                restored = deepcopy(corrected)
                restored['expected']['arguments']['date_to'] = '2026-11-01'
                self.assertEqual(restored, original)

    def test_french_supplier_preserves_context_history_and_target(self):
        original = self.rows[build.SUPPLIER_ID]
        corrected = build.correct(original)
        self.assertIn('supplier Fictif Marbre', self.rows[build.SUPPLIER_ID[:-2] + 'en']['messages'][-1]['content'])
        self.assertIn('le fournisseur Fictif Marbre', corrected['messages'][-1]['content'])
        restored = deepcopy(corrected)
        restored['messages'][-1]['content'] = restored['messages'][-1]['content'].replace('le fournisseur Fictif Marbre', 'Fictif Marbre')
        self.assertEqual(restored, original)

    def test_all_corrected_targets_remain_offered_and_valid(self):
        for original in self.rows.values():
            row = build.correct(original)
            expected = row['expected']
            schema = CLARIFICATION_SCHEMA if expected['tool'] == 'clarify' else next(
                t['function']['parameters'] for t in row['offered_tool_schemas'] if t['function']['name'] == expected['tool'])
            validate(expected['arguments'], schema)

    def test_existing_output_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, 'overwrite'):
                build.prepare(output=Path(directory))

    def test_changed_parent_refused_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'source', Path(directory) / 'out'
            source.mkdir()
            for name, raw in self.source.items():
                (source / name).write_bytes(raw)
            name = next(iter(self.parent['inputs']))
            (source / name).write_bytes(self.source[name] + b'\n')
            with self.assertRaisesRegex(ValueError, 'input changed'):
                build.prepare(source=source, output=output)
            self.assertFalse(output.exists())

    def test_drifted_documented_cases_refused(self):
        for key in build.CHANGED_IDS:
            with self.subTest(case=key):
                row = deepcopy(self.rows[key])
                row['messages'][-1]['content'] += ' altered'
                with self.assertRaisesRegex(ValueError, 'drifted'):
                    build.correct(row)

    def test_no_input_rows_are_mutated(self):
        before = deepcopy(self.rows)
        for row in self.rows.values():
            build.correct(row)
        self.assertEqual(self.rows, before)


if __name__ == '__main__':
    unittest.main()
