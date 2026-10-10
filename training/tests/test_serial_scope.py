import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
from serial_scope_v1 import BASE_APPLICATIONS, STAGES, validate_stage, validate_retained_curriculum
from training_schedule import complete_epoch_order


class SerialScopeTests(unittest.TestCase):
    def fixture(self, stage):
        apps = list(BASE_APPLICATIONS + STAGES[:STAGES.index(stage) + 1])
        return {'applications': apps, 'languages': ['en', 'fr']}, [{'application': app} for app in apps]

    def test_all_prepared_stages_have_exact_scope_and_complete_epoch_coverage(self):
        previous_path = ROOT / 'training/datasets/shared-v5r2-en-fr'
        for stage, version in zip(STAGES, ['shared-v6r2-en-fr', 'shared-v7r2-en-fr', 'shared-v8r2-en-fr']):
            with self.subTest(stage=stage):
                path = ROOT / 'training/datasets' / version
                manifest = json.loads((path / 'manifest.json').read_text())
                splits = {name: (path / name).read_bytes() for name in ['train.jsonl', 'valid.jsonl']}
                train, valid = [[json.loads(line) for line in splits[name].splitlines()] for name in splits]
                scope = validate_stage(stage, manifest, train, valid, complete_epochs=1)
                order = complete_epoch_order(train)
                self.assertEqual(sorted(order), list(range(len(train))))
                self.assertEqual({train[index]['application'] for index in order}, scope)
                provenance = validate_retained_curriculum(stage, manifest, splits['train.jsonl'], splits['valid.jsonl'], previous_path)
                self.assertEqual(set(provenance['files']), {'train.jsonl', 'valid.jsonl'})
                previous_path = path

    def test_rejects_old_curriculum_even_when_all_applications_are_present(self):
        old = ROOT / 'training/datasets/shared-v6-en-fr'
        previous = ROOT / 'training/datasets/shared-v5r2-en-fr'
        with self.assertRaises(ValueError):
            validate_retained_curriculum('contrat', json.loads((old / 'manifest.json').read_text()),
                (old / 'train.jsonl').read_bytes(), (old / 'valid.jsonl').read_bytes(), previous)

    def test_retained_manifest_hash_and_rows_are_both_checked(self):
        current = ROOT / 'training/datasets/shared-v6r2-en-fr'
        previous = ROOT / 'training/datasets/shared-v5r2-en-fr'
        manifest = json.loads((current / 'manifest.json').read_text())
        train, valid = [(current / name).read_bytes() for name in ['train.jsonl', 'valid.jsonl']]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            for name in ['manifest.json', 'train.jsonl', 'valid.jsonl']:
                (path / name).write_bytes((previous / name).read_bytes())
            (path / 'train.jsonl').write_bytes((path / 'train.jsonl').read_bytes() + b'{}\n')
            with self.assertRaisesRegex(ValueError, 'validated manifest'):
                validate_retained_curriculum('contrat', manifest, train, valid, path)
        for bad_train, bad_valid in [(train.split(b'\n', 1)[1], valid), (train, valid.split(b'\n', 1)[1])]:
            with self.assertRaisesRegex(ValueError, 'byte-for-byte'):
                validate_retained_curriculum('contrat', manifest, bad_train, bad_valid, previous)
        with self.assertRaisesRegex(ValueError, 'preceding cumulative stage'):
            validate_retained_curriculum('contrat', manifest, train, valid, current)

    def test_no_skipped_or_extra_application_and_no_removed_earlier_curriculum(self):
        manifest, rows = self.fixture('gestion_magasin')
        for removed in manifest['applications']:
            changed = copy.deepcopy(manifest)
            changed['applications'].remove(removed)
            with self.subTest(removed=removed), self.assertRaises(ValueError):
                validate_stage('gestion_magasin', changed, rows, rows, complete_epochs=1)
        for extra in ['reservation', 'unrelated_application', 'facturation']:
            changed = copy.deepcopy(manifest)
            changed['applications'].append(extra)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                validate_stage('gestion_magasin', changed, rows, rows, complete_epochs=1)

    def test_rejects_missing_or_forged_split_metadata(self):
        manifest, rows = self.fixture('contrat')
        for bad in [[], rows[:-1], rows + [{}], rows + [{'application': 'reservation'}], rows + [None]]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_stage('contrat', manifest, bad, rows, complete_epochs=1)
            with self.subTest(bad_validation=bad), self.assertRaises(ValueError):
                validate_stage('contrat', manifest, rows, bad, complete_epochs=1)

    def test_rejects_partial_or_oversampled_epochs_and_other_languages(self):
        manifest, rows = self.fixture('contrat')
        for epochs in [None, 0, -1, True, 1.5]:
            with self.subTest(epochs=epochs), self.assertRaises(ValueError):
                validate_stage('contrat', manifest, rows, rows, complete_epochs=epochs)
        with self.assertRaises(ValueError):
            validate_stage('contrat', manifest, rows, rows, complete_epochs=1, balanced_applications=True)
        for languages in [['en'], ['en', 'fr', 'ar'], ['en', 'fr', 'fr'], 'en,fr']:
            changed = {**manifest, 'languages': languages}
            with self.subTest(languages=languages), self.assertRaises(ValueError):
                validate_stage('contrat', changed, rows, rows, complete_epochs=1)

    def test_invalid_stage_or_manifest_fails_before_model_loading(self):
        manifest, rows = self.fixture('contrat')
        with self.assertRaises(ValueError):
            validate_stage('contracts', manifest, rows, rows, complete_epochs=1)
        for applications in [None, 'contrat', [{'application': 'contrat'}]]:
            with self.subTest(applications=applications), self.assertRaises(ValueError):
                validate_stage('contrat', {**manifest, 'applications': applications}, rows, rows, complete_epochs=1)


if __name__ == '__main__':
    unittest.main()
