"""Adversarial retention checks for the six source-reviewed target replacements."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_shared_name_corrections as prepared
from serial_scope_v2 import validate_retained_curriculum


class CorrectedSharedCurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = prepared.ROOT
        cls.parent = cls.root / 'training/datasets' / prepared.SOURCE
        cls.output = cls.root / 'training/datasets' / prepared.OUTPUT
        cls.original = (cls.parent / 'train.jsonl').read_bytes()
        cls.generated = (cls.output / 'train.jsonl').read_bytes()
        cls.errata = cls.root / 'training/datasets/management-name-errata-v2-en-fr'
        cls.replacements = (cls.errata / 'train.replacements.jsonl').read_bytes()
        cls.provenance = json.loads((cls.errata / 'manifest.json').read_text())['provenance']
        cls.manifest = json.loads((cls.output / 'manifest.json').read_text())

    def test_only_six_target_lines_change_and_no_input_changes(self):
        old = self.original.splitlines(keepends=True)
        new = self.generated.splitlines(keepends=True)
        self.assertEqual(len(old), len(new))
        self.assertEqual([i for i, (a, b) in enumerate(zip(old, new)) if a != b],
                         [620, 621, 622, 623, 968, 969])
        for index in (620, 621, 622, 623, 968, 969):
            before, after = json.loads(old[index]), json.loads(new[index])
            self.assertNotEqual(before['messages'][-1], after['messages'][-1])
            after['messages'][-1] = before['messages'][-1]
            self.assertEqual(before, after)
        self.assertEqual(self.generated, prepared.corrected_payload(self.original, self.replacements, self.provenance))

    def test_mutated_parent_rejects(self):
        lines = self.original.splitlines(keepends=True)
        row = json.loads(lines[620])
        row['messages'][-2]['content'] += ' changed'
        lines[620] = (json.dumps(row) + '\n').encode()
        with self.assertRaises(ValueError):
            prepared.corrected_payload(b''.join(lines), self.replacements, self.provenance)

    def test_replacements_cannot_change_history_or_broaden_filters(self):
        for key in ('history', 'arguments'):
            rows = list(map(json.loads, self.replacements.splitlines()))
            if key == 'history':
                rows[0]['messages'][-2]['content'] += ' changed'
            else:
                rows[0]['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 'SYN-Magnolia'
            raw = ''.join(json.dumps(row) + '\n' for row in rows).encode()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'reviewed corrections'):
                prepared.corrected_payload(self.original, raw, self.provenance)

    def test_wrong_positions_missing_or_extra_rows_reject(self):
        wrong = deepcopy(self.provenance)
        wrong[0]['source_index'] = 619
        for original, replacements, provenance in (
                (self.original, self.replacements, wrong),
                (self.original, self.replacements + self.replacements.splitlines(keepends=True)[0], self.provenance),
                (self.original[:-1], self.replacements, self.provenance),
                (self.original, self.replacements, self.provenance[:-1]),
                (self.original + self.original.splitlines(keepends=True)[0], self.replacements, self.provenance)):
            with self.subTest(lengths=(len(original), len(replacements))), self.assertRaises(ValueError):
                prepared.corrected_payload(original, replacements, provenance)

    def test_validation_and_all_frozen_evaluation_bytes_preserved(self):
        parent = json.loads((self.parent / 'manifest.json').read_text())
        self.assertEqual((self.output / 'valid.jsonl').read_bytes(), (self.parent / 'valid.jsonl').read_bytes())
        self.assertEqual(self.manifest['historical_regression_held_out'], parent['historical_regression_held_out'])
        for name, info in parent['held_out'].items():
            self.assertEqual(self.manifest['held_out'][name], info)
        self.assertEqual(self.manifest['held_out_count'], 438 + 48)
        for name, info in {**self.manifest['historical_regression_held_out'], **self.manifest['held_out']}.items():
            raw = (self.root / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), info['sha256'])
            self.assertEqual(len(raw.splitlines()), info['count'])

    def test_manifest_is_unbound_and_records_exact_artifacts(self):
        self.assertIn('PREPARATION ONLY', self.manifest['status'])
        self.assertTrue(self.manifest['model_binding']['status'].startswith('UNBOUND'))
        self.assertNotIn('retained_dataset', self.manifest)
        self.assertEqual(self.manifest['counts']['replaced_targets'], 6)
        self.assertEqual(self.manifest['counts']['added'], 0)
        for name, digest in self.manifest['files'].items():
            self.assertEqual(prepared.digest((self.output / name).read_bytes()), digest)
        self.assertEqual(prepared.digest(Path(prepared.__file__).read_bytes()), self.manifest['generator_sha256'])
        self.assertEqual(prepared.digest((self.parent / 'manifest.json').read_bytes()), self.manifest['parent_manifest_sha256'])
        for name, digest in self.manifest['helper_sha256'].items():
            self.assertEqual(prepared.digest((self.root / name).read_bytes()), digest)

    def test_native_drift_and_extra_application_reject(self):
        parent = {'native_metadata': {'facturation': {'chat_ai/tools.py': prepared.digest(b'expected')}}}
        review = {'native_fixes': []}
        # Supply the expected three-key map so all metadata access remains bounded.
        parent['native_metadata'].update(management_projet={}, design_workflow={})
        roots = {app: Path(app) for app in parent['native_metadata']}
        with patch.object(Path, 'read_bytes', return_value=b'drift'), self.assertRaisesRegex(ValueError, 'Native source drift'):
            prepared.native_metadata(parent, review, roots)
        with self.assertRaisesRegex(ValueError, 'scope'):
            prepared.native_metadata(parent, review, {**roots, 'contrat': Path('contrat')})

    def test_old_retention_validator_cannot_mislabel_corrected_base_as_r8(self):
        old = self.root / 'training/datasets/shared-v6r9-en-fr'
        manifest = json.loads((old / 'manifest.json').read_text())
        original = (old / 'train.jsonl').read_bytes()
        self.assertTrue(original.startswith(self.original))
        corrected = self.generated + original[len(self.original):]
        with self.assertRaisesRegex(ValueError, 'byte-for-byte'):
            validate_retained_curriculum('contrat', manifest, corrected, (old / 'valid.jsonl').read_bytes(), self.parent)

    def test_existing_preparation_cannot_be_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            prepared.prepare({})


if __name__ == '__main__':
    unittest.main()
