"""Synthetic report fixtures validate gates; they are never model results."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import report_serial_candidate_v1 as report
from model_acceptance import FROZEN_EVALUATOR_SHA256
from test_dialogue_report import write, lines


def artifact(value):
    files = {'synthetic.bin': {'sha256': hashlib.sha256(value.encode()).hexdigest(), 'size_bytes': 1}}
    return {'files': files, 'sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}


class SerialReportTests(unittest.TestCase):
    def fixture(self, root, *, wrong_app=None, one_wrong=False):
        data = root / 'training/datasets/serial-synthetic'
        evaluations = root / 'events'
        sets, assignment, held = {}, {}, {}
        apps = list(report.BASE_APPLICATIONS + ('contrat',))
        unit = 'synthetic-worker.service'
        for app, count in zip(apps, (96, 4, 2, 2)):
            relative = 'training/datasets/serial-synthetic/' + app + '.jsonl'
            rows = [{'id': app + '-' + str(i), 'language': 'en' if i % 2 else 'fr', 'category': 'synthetic',
                     'trusted_context': {'application': app},
                     'expected': {'tool': 'search_records', 'arguments': {'resource': 'project'}}} for i in range(count)]
            lines(root / relative, rows)
            held[relative] = {'sha256': report.sha(root / relative), 'count': count}
            sets[relative] = app; assignment[relative] = unit
            for model in ('baseline', 'candidate'):
                events = [{**row, 'action': copy.deepcopy(row['expected']), 'structured_valid': True} for row in rows]
                if model == 'candidate' and app == wrong_app:
                    for row in events[:1] if one_wrong else events:
                        row['action'] = {'tool': 'clarify', 'message': 'Wrong synthetic action'}
                label = model + '-' + app
                lines(evaluations / label / 'events.jsonl', [{'case': row} for row in events])
                write(evaluations / label / 'summary.json', {'dataset_sha256': held[relative]['sha256'],
                    'evaluator_sha256': FROZEN_EVALUATOR_SHA256, 'model_id': model, 'max_output_tokens': 512,
                    'thinking': False, 'mode': 'native', 'metrics': {'count': count}})
        write(data / 'manifest.json', {'version': 'fixture-only', 'applications': apps, 'languages': ['en', 'fr'],
              'held_out': held, 'held_out_count': 104})
        provider = {'provider.py': 'fixture-provider-hash'}
        proof = root / 'driver-proof.json'
        write(proof, {'driver_sha256': 'fixture-driver', 'provider_sha256': provider,
                      'evaluator_sha256': FROZEN_EVALUATOR_SHA256})
        for model in ('baseline', 'candidate'):
            run = root / model
            att = {'model_id': model, 'model_path': '/synthetic/' + model, 'runtime_path': '/synthetic/runtime',
                   'ctx': 8192, 'max_tokens': 512, 'thinking': False, 'service_unit': unit, 'threads': 4,
                   'artifacts': {name: artifact(model if name == 'weights' else name) for name in ('weights', 'runtime', 'tokenizer', 'config')}}
            identity = {'pid': 123, 'unit': unit, 'engine': {'threads': 4}, 'properties': {'CPUQuotaPerSecUSec': '4s'},
                        'cmd': ['python3', '/synthetic/runtime/c/coli', 'serve', '--model', att['model_path'],
                        '--no-tune-profile', '--ctx', '8192', '--gpu', 'none', '--ngen', '512', '--no-think', '--temp', '0',
                        '--host', '127.0.0.1', '--port', '18001', '--model-id', model, '--max-queue', '2',
                        '--queue-timeout', '10', '--kv-slots', '1']}
            workers = {unit: {'attestation': att, 'identity': identity}}
            completed = {'model_id': model, 'manifest_sha256': report.sha(data / 'manifest.json'),
                         'provider_sha256': provider, 'driver_sha256': 'fixture-driver', 'count': 104,
                         'sets': {path: model + '-' + name for path, name in sets.items()}}
            completed['results'] = {path: {'label': label,
                 'events_sha256': report.sha(evaluations / label / 'events.jsonl'),
                 'summary_sha256': report.sha(evaluations / label / 'summary.json')} for path, label in completed['sets'].items()}
            write(run / 'evaluation-complete.json', completed)
            write(run / 'evaluation-binding.json', {**completed, 'assignment': assignment, 'workers': workers})
            for phase in ('before', 'after'):
                write(run / ('evaluation-workers-' + phase + '.json'), workers)
        return ('contrat', data, root / 'baseline', root / 'candidate', evaluations, proof, root)

    def test_real_prepared_manifests_preserve_every_application(self):
        for stage, version, count in [('contrat', 'shared-v6r6-en-fr', 516),
                                      ('gestion_magasin', 'shared-v7r6-en-fr', 606),
                                      ('reservation', 'shared-v8r6-en-fr', 690)]:
            manifest, rows = report.checked_manifest(stage, ROOT / 'training/datasets' / version)
            self.assertEqual(sum(len(value) for value in rows.values()), count)
            self.assertEqual(manifest['applications'][-1], stage)

    def test_complete_synthetic_pass_never_authorizes_operations(self):
        with tempfile.TemporaryDirectory() as folder:
            result = report.build(*self.fixture(Path(folder)))
            self.assertTrue(result['model_acceptance_passed'])
            self.assertFalse(result['production_activation'])
            self.assertFalse(result['next_training_started'])
            self.assertIsNone(result['native_backend_security_verified'])

    def test_aggregate_pass_cannot_hide_failed_application(self):
        with tempfile.TemporaryDirectory() as folder:
            result = report.build(*self.fixture(Path(folder), wrong_app='management_projet'))
            self.assertTrue(result['candidate']['assessment']['model_targets_passed'])
            self.assertFalse(result['all_frozen_sets_passed'])
            self.assertFalse(result['model_acceptance_passed'])

    def test_target_pass_does_not_hide_retained_application_regression(self):
        with tempfile.TemporaryDirectory() as folder:
            result = report.build(*self.fixture(Path(folder), wrong_app='facturation', one_wrong=True))
            self.assertTrue(result['all_frozen_sets_passed'])
            self.assertFalse(result['retained_application_nonregression']['facturation'])
            self.assertFalse(result['model_acceptance_passed'])

    def test_changed_completion_assignments_and_runtime_are_rejected(self):
        mutations = [('evaluation-complete.json', lambda x:x.update(count=103)),
                     ('evaluation-binding.json', lambda x:x.update(assignment={})),
                     ('evaluation-workers-after.json', lambda x:x['synthetic-worker.service']['identity'].update(pid=124)),
                     ('evaluation-complete.json', lambda x:x.update(provider_sha256={})),
                     ('evaluation-complete.json', lambda x:x.update(sets={})),
                     ('evaluation-complete.json', lambda x:x.update(results={})),
                     ('evaluation-complete.json', lambda x:x.update(model_id='another-model'))]
        for filename, mutate in mutations:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as folder:
                args = self.fixture(Path(folder));path = args[3] / filename
                value = report.read(path);mutate(value);write(path, value)
                with self.assertRaises(ValueError):report.build(*args)

    def test_missing_duplicate_and_edited_events_are_rejected(self):
        for mutation in ('missing', 'duplicate', 'labels'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                args = self.fixture(Path(folder));path = args[4] / 'candidate-contrat/events.jsonl'
                values = [json.loads(line) for line in path.read_text().splitlines()]
                if mutation == 'missing':values.pop()
                elif mutation == 'duplicate':values.append(values[0])
                else:values[0]['case']['expected']['arguments']['resource'] = 'changed'
                lines(path, values)
                with self.assertRaises(ValueError):report.build(*args)

    def test_matching_changed_runtime_still_rejects_comparison(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder));run = args[3]
            workers = report.read(run / 'evaluation-workers-before.json')
            workers['synthetic-worker.service']['attestation']['artifacts']['runtime'] = artifact('changed-runtime')
            for phase in ('before', 'after'):write(run / ('evaluation-workers-' + phase + '.json'), workers)
            binding = report.read(run / 'evaluation-binding.json');binding['workers'] = workers
            write(run / 'evaluation-binding.json', binding)
            with self.assertRaisesRegex(ValueError, 'Non-weight inference artifacts'):report.build(*args)

    def test_missing_weight_attestation_cannot_establish_model_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder));run = args[3]
            workers = report.read(run / 'evaluation-workers-before.json')
            del workers['synthetic-worker.service']['attestation']['artifacts']['weights']
            for phase in ('before', 'after'):write(run / ('evaluation-workers-' + phase + '.json'), workers)
            binding = report.read(run / 'evaluation-binding.json');binding['workers'] = workers
            write(run / 'evaluation-binding.json', binding)
            with self.assertRaisesRegex(ValueError, 'Incomplete model artifact'):report.build(*args)

    def test_stale_artifact_group_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder));run = args[3]
            workers = report.read(run / 'evaluation-workers-before.json')
            workers['synthetic-worker.service']['attestation']['artifacts']['runtime']['files']['synthetic.bin']['sha256'] = '0' * 64
            for phase in ('before', 'after'):write(run / ('evaluation-workers-' + phase + '.json'), workers)
            binding = report.read(run / 'evaluation-binding.json');binding['workers'] = workers
            write(run / 'evaluation-binding.json', binding)
            with self.assertRaisesRegex(ValueError, 'Artifact group digest'):report.build(*args)

    def test_action_only_tampering_is_rejected_before_scoring(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder));path = args[4] / 'candidate-contrat/events.jsonl'
            values = [json.loads(line) for line in path.read_text().splitlines()]
            values[0]['case']['action']['arguments']['resource'] = 'changed'
            lines(path, values)
            with self.assertRaisesRegex(ValueError, 'result changed after completion'):report.build(*args)

    def test_manifest_escape_language_and_skipped_scope_are_rejected(self):
        for mutation in ('escape', 'language', 'scope'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                args = self.fixture(Path(folder));data = args[1];manifest = report.read(data / 'manifest.json')
                if mutation == 'escape':manifest['held_out'] = {'../../outside.json': {'sha256':'x', 'count':1}}
                elif mutation == 'language':manifest['languages'] = ['en', 'ar']
                else:manifest['applications'].append('reservation')
                write(data / 'manifest.json', manifest)
                with self.assertRaises(ValueError):report.checked_manifest('contrat', data, Path(folder))


if __name__ == '__main__':
    unittest.main()
