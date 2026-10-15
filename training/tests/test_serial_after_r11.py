"""R11 successor integrity and startup checks, without model libraries."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import prepare_serial_after_r11 as preparation
from serial_scope_v3 import validate_retained_curriculum
from rehearse_cpu_v2 import prepare_inputs
import training.tests.test_serial_runtime_v4 as startup


class R11SerialPreparationTests(unittest.TestCase):
    def stages(self):
        previous = ROOT / 'training/datasets' / preparation.BASE
        for stage, spec in preparation.STAGES.items():
            current = ROOT / 'training/datasets' / spec[2]
            yield stage, spec, current, previous
            previous = current

    def test_reconstructs_exact_pinned_predecessor_and_new_application(self):
        for stage, spec, folder, parent in self.stages():
            expected = preparation.digest((parent / 'manifest.json').read_bytes())
            payloads, manifest = preparation.assemble(stage, parent, expected)
            self.assertEqual(manifest, json.loads((folder / 'manifest.json').read_text()))
            self.assertFalse('retained_corrections' in manifest)
            source = ROOT / 'training/datasets' / manifest['added_dataset']['version']
            for name, raw in payloads.items():
                self.assertEqual(raw, (folder / name).read_bytes())
                self.assertEqual(raw, (parent / name).read_bytes() + (source / name).read_bytes())
            proof = validate_retained_curriculum(stage, manifest, payloads['train.jsonl'],
                                                payloads['valid.jsonl'], parent)
            self.assertEqual(proof['retention_mode'], 'exact retained bytes')
            self.assertFalse(proof['training_authorized'])
            self.assertFalse(proof['model_acceptance_verified'])
            self.assertTrue(manifest['model_binding']['status'].startswith('UNBOUND'))

    def test_keeps_full_r11_and_unchanged_validation_and_evaluation(self):
        base = ROOT / 'training/datasets' / preparation.BASE
        for stage, spec, folder, parent in self.stages():
            old = ROOT / 'training/datasets' / spec[0]
            current = json.loads((folder / 'manifest.json').read_text())
            prior = json.loads((old / 'manifest.json').read_text())
            self.assertTrue((folder / 'train.jsonl').read_bytes().startswith((base / 'train.jsonl').read_bytes()))
            self.assertEqual(len((folder / 'train.jsonl').read_bytes().splitlines()),
                             len((old / 'train.jsonl').read_bytes().splitlines()) + 80)
            self.assertEqual((folder / 'valid.jsonl').read_bytes(), (old / 'valid.jsonl').read_bytes())
            for key in ('held_out', 'historical_regression_held_out', 'fresh_controls', 'held_out_count', 'added_dataset'):
                self.assertEqual(current[key], prior[key])
            for name, info in {**current['held_out'], **current['historical_regression_held_out']}.items():
                raw = (ROOT / name).read_bytes()
                self.assertEqual(preparation.digest(raw), info['sha256'])
                self.assertEqual(len(raw.splitlines()), info['count'])

    def test_runtime_admits_all_stages_before_model_imports(self):
        for stage, spec, folder, parent in self.stages():
            for script in ('train_cpu_serial_v4.py', 'probe_cpu_serial_v2.py'):
                with self.subTest(stage=stage, script=script), self.assertRaises(startup.BeforeModelLibraries):
                    startup.CorrectedSerialRuntimeTests.start(self, script, folder, parent,
                                                               stage=stage, correction_root=None)

    def test_rehearsal_checks_complete_curricula(self):
        for stage, spec, folder, parent in self.stages():
            result, rows, captures, lineage = prepare_inputs(folder, stage, parent)
            self.assertEqual(result['rows_checked'], {'train': spec[3], 'valid': spec[4]})
            self.assertEqual(lineage['retention_mode'], 'exact retained bytes')
            self.assertFalse(lineage['model_acceptance_verified'])
            self.assertFalse(lineage['training_authorized'])
            self.assertTrue(rows)
            self.assertTrue(captures['train'])
            self.assertTrue(captures['valid'])

    def test_skipped_or_superseded_predecessors_fail_before_weights(self):
        wrong = ROOT / 'training/datasets/shared-v5r8-en-fr'
        for stage, spec, folder, parent in self.stages():
            for script in ('train_cpu_serial_v4.py', 'probe_cpu_serial_v2.py'):
                with self.subTest(stage=stage, script=script), self.assertRaises(SystemExit):
                    startup.CorrectedSerialRuntimeTests.start(self, script, folder, wrong,
                                                               stage=stage, correction_root=None)
            with self.assertRaises(ValueError):
                preparation.assemble(stage, wrong, preparation.digest((wrong / 'manifest.json').read_bytes()))

    def test_changed_retained_row_rejects_even_with_rehashed_current_split(self):
        for stage, spec, folder, parent in self.stages():
            manifest = json.loads((folder / 'manifest.json').read_text())
            lines = (folder / 'train.jsonl').read_bytes().splitlines(keepends=True)
            row = json.loads(lines[100])
            row['messages'][-2]['content'] += ' unreviewed scope change'
            lines[100] = (json.dumps(row) + '\n').encode()
            changed = b''.join(lines)
            manifest['files']['train.jsonl'] = preparation.digest(changed)
            with self.assertRaisesRegex(ValueError, 'retain every preceding'):
                validate_retained_curriculum(stage, manifest, changed,
                                             (folder / 'valid.jsonl').read_bytes(), parent)

    def test_pinned_manifest_and_request_helper_changes_reject(self):
        base = ROOT / 'training/datasets' / preparation.BASE
        with self.assertRaisesRegex(ValueError, 'Pinned preparation manifest'):
            preparation.checked(base, '0' * 64)
        with patch.object(preparation, 'PROMPT_HELPER_SHA256', '0' * 64):
            with self.assertRaisesRegex(ValueError, 'request-boundary helper'):
                preparation.assemble('contrat', base, preparation.BASE_SHA256)

    def test_never_overwrites_versioned_preparations(self):
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            preparation.prepare()


if __name__ == '__main__':
    unittest.main()
