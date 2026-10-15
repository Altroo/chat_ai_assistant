"""Shared refinement replay guards; synthetic fixtures only, no model loading."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import replay_shared_rehearsal_v1 as current
import replay_rehearsal as previous
from training.tests import test_replay_supervisor as inherited


def fixture(root):
    data, evidence, exports = (root / name for name in ('data', 'evidence', 'exports'))
    for folder in (data, evidence, exports): folder.mkdir()
    cats = ['category_' + str(i) for i in range(8)]
    manifest = {'version': 'shared-v5r10-en-fr',
        'applications': ['facturation', 'management_projet', 'design_workflow'],
        'languages': ['en', 'fr'], 'counts': {'added_categories': {c: 2 for c in cats}}}
    artifacts = {'weights': 'synthetic', 'runtime': 'synthetic', 'tokenizer': 'synthetic', 'config': 'synthetic'}
    proof = {'step': 2339, 'artifacts': artifacts}
    report = {'selected_step': 2339, 'training_updates_completed': 2339,
        'complete_identity_and_scoring_verified': True, 'fresh_controls_verified': True,
        'production_activation': False, 'accepted': False, 'evidence_sha256': {}}
    audit, captures = {'synthetic_audit': True}, {'train': [2], 'valid': [1]}
    plan = {'stage': 'shared', 'retained_dataset': None, 'audit': deepcopy(audit),
        'captures': deepcopy(captures), 'rehearsal_categories': cats, 'base_artifacts': {'weights': 'fp32'}}
    binding = {'base': str(exports / 'step-2339/merged'), 'data': str(data), 'runtime': str(root/'runtime'),
        'predecessor': {'report': str(evidence/'report.json'), 'exports_root': str(exports),
            'base_artifacts': deepcopy(plan['base_artifacts']),
            'before': str(evidence/'before.json'), 'after': str(evidence/'after.json')}}
    def persist():
        (data/'manifest.json').write_text(json.dumps(manifest))
        for when in ('before', 'after'):
            raw = json.dumps(proof, indent=2).encode()
            (evidence/(when+'.json')).write_bytes(raw+b'\n')
            report['evidence_sha256'][f'fresh-2339-{when}.json'] = hashlib.sha256(raw).hexdigest()
        (evidence/'report.json').write_text(json.dumps(report))
        binding['predecessor']['report_sha256'] = current.file_sha(evidence/'report.json')
    persist()
    prepare = lambda *a, **kw: (audit, {}, captures, None)
    return binding, plan, manifest, report, proof, artifacts, prepare, persist


class SharedBaseTests(unittest.TestCase):
    def evaluate(self, values):
        binding, plan, _, _, _, artifacts, prepare, _ = values
        with patch.object(current.importlib, 'import_module', return_value=SimpleNamespace(prepare_inputs=prepare)), \
             patch.object(current, 'served_artifacts', return_value=artifacts):
            return current.check_predecessor(binding, plan)

    def test_failed_candidate_can_be_diagnosed_without_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.evaluate(fixture(Path(tmp)))
            self.assertFalse(result['model_acceptance_established'])
            self.assertEqual(result['step'], 2339)

    def test_missing_terminal_verification_rejects(self):
        for key in ('complete_identity_and_scoring_verified', 'fresh_controls_verified'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                values = fixture(Path(tmp)); values[3][key] = False; values[-1]()
                with self.assertRaisesRegex(ValueError, 'incomplete'): self.evaluate(values)

    def test_later_app_cannot_use_shared_refinement_admission(self):
        for mutation in ('stage', 'manifest', 'retained'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                values = fixture(Path(tmp))
                if mutation == 'stage': values[1]['stage'] = 'contrat'
                elif mutation == 'manifest': values[2]['applications'].append('contrat')
                else: values[1]['retained_dataset'] = {'manifest_sha256': 'synthetic'}
                values[-1]()
                with self.assertRaises(ValueError): self.evaluate(values)

    def test_other_selected_model_and_changed_artifacts_reject(self):
        for mutation in ('path', 'fp32', 'served'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                values = fixture(Path(tmp))
                if mutation == 'path': values[0]['base'] = values[0]['base'].replace('2339', '2100')
                elif mutation == 'fp32': values[1]['base_artifacts'] = {'weights': 'different'}
                else: values[5]['weights'] = 'changed after proof was saved'
                with self.assertRaises(ValueError): self.evaluate(values)

    def test_original_server_format_and_full_proof_are_required(self):
        for mutation in ('missing_newline', 'extra_newline', 'changed'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                values = fixture(Path(tmp)); path = Path(values[0]['predecessor']['after'])
                raw = path.read_bytes()
                if mutation == 'missing_newline': path.write_bytes(raw[:-1])
                elif mutation == 'extra_newline': path.write_bytes(raw+b'\n')
                else: path.write_bytes(raw.replace(b'2339', b'2100'))
                with self.assertRaisesRegex(ValueError, 'serving evidence'): self.evaluate(values)

    def test_selection_category_and_capture_drift_reject(self):
        for mutation in ('audit', 'capture', 'category'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                values = fixture(Path(tmp))
                if mutation == 'audit': values[1]['audit'] = {'changed': True}
                elif mutation == 'capture': values[1]['captures']['train'].append(3)
                else: values[1]['rehearsal_categories'] = []
                with self.assertRaises(ValueError): self.evaluate(values)

    def test_report_cannot_be_replaced_without_pinned_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            values = fixture(Path(tmp))
            Path(values[0]['predecessor']['report']).write_text('{}')
            with self.assertRaisesRegex(ValueError, 'report changed'): self.evaluate(values)

    def test_export_and_resource_mechanics_remain_unchanged(self):
        def functions(name):
            tree = ast.parse((ROOT/'training/scripts'/name).read_text())
            return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
        old, new = functions('replay_rehearsal.py'), functions('replay_shared_rehearsal_v1.py')
        self.assertEqual(set(old), set(new))
        self.assertEqual({n for n in old if old[n] != new[n]},
                         {'bootstrap', 'check_predecessor', 'completed_unit', 'verify_inputs'})
        self.assertIn('rehearse_cpu_v3.py', current.HELPER_NAMES)
        self.assertIn('audit_training_inputs_v2.py', current.HELPER_NAMES)
        self.assertNotIn('rehearse_cpu_v2.py', current.HELPER_NAMES)


class SharedHarness:
    def setUp(self):
        self.rebind = patch.object(inherited, 'supervisor', current)
        self.rebind.start()
        self.addCleanup(self.rebind.stop)


class SharedNumericalTests(SharedHarness, inherited.NumericalTests):
    def test_running_failed_or_wrong_numerical_invocation_is_rejected(self):
        command = ['/synthetic/python', '/synthetic/rehearse_cpu_v3.py', '--output', '/synthetic/rehearsal',
                   '--data', '/synthetic/data', '--model', '/synthetic/base', '--trainer', '/synthetic/train_cpu.py']
        properties = {'SubState': 'exited', 'MainPID': '0', 'Result': 'success', 'ExecMainStatus': '0',
            'InvocationID': 'a' * 32, 'ExecStart': '{ path=/synthetic/python ; argv[]=' + ' '.join(command) + ' ; ignore_errors=no ; status=0 }'}
        binding = {'rehearsal_unit': 'chat-ai-synthetic-rehearsal.service', 'rehearsal_unit_properties': properties,
            'rehearsal_command': command, 'trainer': '/synthetic/train_cpu.py',
            'rehearsal': '/synthetic/rehearsal', 'data': '/synthetic/data', 'base': '/synthetic/base'}
        for mutation in ('none', 'running', 'failure', 'invocation', 'output', 'command'):
            actual, current = deepcopy(properties), deepcopy(binding)
            if mutation == 'running': actual['SubState'] = 'running'
            if mutation == 'failure': actual['Result'] = 'exit-code'
            if mutation == 'invocation': actual['InvocationID'] = 'b' * 32
            if mutation == 'output': current['rehearsal'] = '/synthetic/other'
            if mutation == 'command': current['rehearsal_command'][0] = '/synthetic/other-python'
            text = ''.join(key + '=' + value + '\n' for key, value in actual.items())
            with self.subTest(mutation=mutation), patch.object(inherited.supervisor.subprocess, 'check_output', return_value=text):
                if mutation == 'none': inherited.supervisor.completed_unit(current)
                else:
                    with self.assertRaises(ValueError): inherited.supervisor.completed_unit(current)

class SharedIsolationTests(SharedHarness, inherited.IsolationTests): pass
class SharedFlowTests(SharedHarness, inherited.SupervisorFlowTests): pass
class SharedSourceTests(SharedHarness, inherited.SourceAdmissionTests): pass


if __name__ == '__main__':
    unittest.main()
