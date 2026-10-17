"""Actual-data retention and rejection tests; no model, database or server work."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import prepare_serial_after_facturation_replay_v3 as prep
import prepare_facturation_replay_v3 as replay
from serial_scope_v3 import validate_retained_curriculum



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReplayV3SerialPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temporary.name) / 'prepared'
        cls.base = Path(cls.temporary.name) / 'base'
        cls.base.mkdir()
        manifest, payloads, _, _ = replay.material()
        raw = (json.dumps(manifest, indent=2) + '\n').encode()
        if hashlib.sha256(raw).hexdigest() != prep.BASE_SHA256:
            raise AssertionError('Reproduced V3 base differs from reviewed manifest')
        (cls.base / 'manifest.json').write_bytes(raw)
        for split, payload in payloads.items():
            (cls.base / (split + '.jsonl')).write_bytes(payload)
        paths = {cls.base / name for name in ('manifest.json', 'train.jsonl', 'valid.jsonl')}
        for spec in prep.STAGES.values():
            directory = ROOT / 'training/datasets' / spec[0]
            manifest = json.loads((directory / 'manifest.json').read_text())
            paths.update(directory / name for name in ('manifest.json', 'train.jsonl', 'valid.jsonl'))
            source = ROOT / 'training/datasets' / manifest['added_dataset']['version']
            source_manifest = json.loads((source / 'manifest.json').read_text())
            paths.add(source / 'manifest.json')
            paths.update(source / name for name in source_manifest['files'])
            paths.update(ROOT / name for name in {**manifest['held_out'], **manifest['historical_regression_held_out']})
        cls.originals = {path: sha(path) for path in paths}
        cls.summary = prep.prepare(cls.base, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_all_current_facturation_rows_and_new_app_suffixes_retained(self):
        previous = self.base
        for stage, spec in prep.STAGES.items():
            with self.subTest(stage=stage):
                directory = self.output / spec[2]
                manifest = json.loads((directory / 'manifest.json').read_text())
                queued = json.loads((ROOT / 'training/datasets' / spec[0] / 'manifest.json').read_text())
                added = ROOT / 'training/datasets' / queued['added_dataset']['version']
                for name in ('train.jsonl', 'valid.jsonl'):
                    self.assertEqual((directory / name).read_bytes(), (previous / name).read_bytes() + (added / name).read_bytes())
                self.assertTrue((directory / 'train.jsonl').read_bytes().startswith((self.base / 'train.jsonl').read_bytes()))
                self.assertEqual(manifest['counts']['train.jsonl']['facturation'], 1487)
                self.assertEqual(manifest['model_binding']['status'], 'UNBOUND; actual predecessor acceptance is not verified')
                self.assertEqual(manifest['held_out'], queued['held_out'])
                self.assertEqual(manifest['historical_regression_held_out'], queued['historical_regression_held_out'])
                self.assertEqual(manifest['fresh_controls'], queued['fresh_controls'])
                self.assertEqual((directory / 'valid.jsonl').read_bytes(), (ROOT / 'training/datasets' / spec[0] / 'valid.jsonl').read_bytes())
                previous = directory
        self.assertEqual([r['train'] for r in self.summary], [3128, 3326, 3506])
        self.assertEqual([r['valid'] for r in self.summary], [319, 362, 402])
        self.assertEqual([r['held_out'] for r in self.summary], [564, 654, 738])
        self.assertTrue(all(not r['training_started'] and not r['model_acceptance_verified'] for r in self.summary))

    def test_complete_metadata_preflight_for_each_queued_stage(self):
        from rehearse_cpu_v2 import prepare_inputs
        previous = self.base
        for stage, spec in prep.STAGES.items():
            with self.subTest(stage=stage):
                directory = self.output / spec[2]
                result, rows, captures, lineage = prepare_inputs(directory, stage, previous)
                self.assertEqual(result['rows_checked'], {'train': spec[3], 'valid': spec[4]})
                self.assertEqual(lineage['retention_mode'], 'exact retained bytes')
                self.assertFalse(lineage['model_acceptance_verified'])
                self.assertFalse(lineage['training_authorized'])
                self.assertTrue(captures['train'])
                self.assertTrue(captures['valid'])
                self.assertEqual(len(rows['train']), spec[3])
                previous = directory

    def test_original_inputs_unchanged(self):
        self.assertEqual({path: sha(path) for path in self.originals}, self.originals)

    def test_old_r11_parent_rejected(self):
        old = ROOT / 'training/datasets/shared-v5r11-en-fr'
        with self.assertRaisesRegex(ValueError, 'preceding|pinned'):
            prep.assemble('contrat', old, sha(old / 'manifest.json'))

    def test_skipping_contracts_rejected(self):
        with self.assertRaisesRegex(ValueError, 'preceding'):
            prep.assemble('gestion_magasin', self.base, prep.BASE_SHA256)

    def test_dropping_the_556_facturation_rows_rejected_even_with_updated_hash(self):
        spec = prep.STAGES['contrat']
        directory = self.output / spec[2]
        manifest = json.loads((directory / 'manifest.json').read_text())
        old_train = (ROOT / 'training/datasets' / spec[0] / 'train.jsonl').read_bytes()
        manifest['files']['train.jsonl'] = hashlib.sha256(old_train).hexdigest()
        with self.assertRaisesRegex(ValueError, 'byte-for-byte'):
            validate_retained_curriculum('contrat', manifest, old_train, (directory / 'valid.jsonl').read_bytes(), self.base)

    def test_changed_base_bytes_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base, output = Path(temporary) / 'base', Path(temporary) / 'output'
            base.mkdir()
            for name in ('manifest.json', 'train.jsonl', 'valid.jsonl'):
                shutil.copyfile(self.base / name, base / name)
            with (base / 'train.jsonl').open('ab') as stream:
                stream.write(b'{}\n')
            with self.assertRaisesRegex(ValueError, 'split changed'):
                prep.prepare(base, output)
            self.assertFalse(output.exists())

    def test_changed_frozen_evaluation_and_unsafe_path_rejected(self):
        manifest = json.loads((ROOT / 'training/datasets/shared-v6r11-en-fr/manifest.json').read_text())
        name = next(iter(manifest['held_out']))
        wrong = deepcopy(manifest)
        wrong['held_out'][name]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'evaluation bytes changed'):
            prep.frozen_evaluations(wrong)
        unsafe = deepcopy(manifest)
        unsafe['held_out']['../not-a-training-source.jsonl'] = unsafe['held_out'].pop(name)
        with self.assertRaisesRegex(ValueError, 'evaluation path'):
            prep.frozen_evaluations(unsafe)

    def test_existing_output_cannot_be_overwritten(self):
        artifact = self.output / prep.STAGES['contrat'][2] / 'manifest.json'
        before = sha(artifact)
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            prep.prepare(self.base, self.output)
        self.assertEqual(sha(artifact), before)


if __name__ == '__main__':
    unittest.main()
