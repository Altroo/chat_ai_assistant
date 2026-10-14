"""Synthetic supervisor tests. No model libraries, network or server mutations."""
from contextlib import contextmanager
from copy import deepcopy
import json
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import replay_rehearsal as supervisor


def predecessor_fixture(root):
    evidence, retained, exports = (root / name for name in ('evidence', 'retained', 'exports'))
    evidence.mkdir(); retained.mkdir(); exports.mkdir()
    files = {}
    for name in ('train.jsonl', 'valid.jsonl'):
        (retained / name).write_text(name)
        files[name] = supervisor.file_sha(retained / name)
    (retained / 'manifest.json').write_text(json.dumps({'files': files}))
    artifacts = {'weights': 'synthetic', 'runtime': 'synthetic', 'tokenizer': 'synthetic', 'config': 'synthetic'}
    proofs = {'pipeline-state.json': {'phase': 'finished', 'selected_step': 900, 'accepted': True,
        'regression_passed': True, 'fresh_passed': True}, 'selection.json': {'selected_step': 900},
        'acceptance.json': {'selected_step': 900, 'all_frozen_sets_passed': True,
            'assessment': {'model_targets_passed': True}, 'sets': [{'assessment': {'model_targets_passed': True}}]},
        'fresh.json': {'selected_step': 900, 'all_fresh_sets_passed': True, 'assessment': {'model_targets_passed': True},
            'by_application': {app: {'model_targets_passed': True} for app in
                ('facturation', 'management_projet', 'design_workflow')}},
        'validation-0-collect.json': {'report': {'steps': 2339, 'dataset_sha256': files['train.jsonl'],
                                               'validation_sha256': files['valid.jsonl']}}}
    for phase in ('validation', 'acceptance', 'fresh'):
        for when in ('before', 'after'):
            proofs[f'{phase}-900-{when}.json'] = {'step': 900, 'artifacts': artifacts, 'worker': phase}
        proofs[f'{phase}-900-stop.json'] = {'stopped_workers': 3}
    binding = {'base': str(exports / 'step-900/merged'), 'runtime': str(root / 'runtime'), 'predecessor': {
        'evidence_root': str(evidence), 'exports_root': str(exports), 'retained_data': str(retained),
        'base_artifacts': {'weights': 'selected-fp32'}, 'files': {}}}
    plan = {'stage': 'contrat', 'base_artifacts': binding['predecessor']['base_artifacts'],
        'retained_dataset': {'manifest_sha256': supervisor.file_sha(retained / 'manifest.json'), 'files': files}}
    def persist():
        for name, value in proofs.items():
            (evidence / name).write_text(json.dumps(value))
        binding['predecessor']['files'] = {name: supervisor.file_sha(evidence / name) for name in proofs}
    persist()
    return binding, plan, proofs, persist, artifacts


class PredecessorTests(unittest.TestCase):
    def test_complete_selected_predecessor_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            binding, plan, _, _, artifacts = predecessor_fixture(Path(temp))
            with patch.object(supervisor, 'served_artifacts', return_value=artifacts):
                self.assertEqual(supervisor.check_predecessor(binding, plan)['step'], 900)

    def test_unfinished_or_unaccepted_predecessor_is_rejected(self):
        for field, value in (('phase', 'evaluating_fresh_controls'), ('accepted', False),
                             ('regression_passed', False), ('fresh_passed', False), ('selected_step', 0)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                binding, plan, proofs, persist, _ = predecessor_fixture(Path(temp))
                proofs['pipeline-state.json'][field] = value; persist()
                with self.assertRaisesRegex(ValueError, 'has not accepted'):
                    supervisor.check_predecessor(binding, plan)

    def test_failed_application_cannot_hide_behind_overall_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            binding, plan, proofs, persist, _ = predecessor_fixture(Path(temp))
            proofs['fresh.json']['by_application']['facturation']['model_targets_passed'] = False; persist()
            with self.assertRaisesRegex(ValueError, 'Incomplete predecessor acceptance'):
                supervisor.check_predecessor(binding, plan)

    def test_before_after_drift_and_missing_cleanup_are_rejected(self):
        for mutation in ('after', 'stop'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                binding, plan, proofs, persist, _ = predecessor_fixture(Path(temp))
                if mutation == 'after': proofs['fresh-900-after.json']['worker'] = 'replaced'
                else: proofs['fresh-900-stop.json']['stopped_workers'] = 2
                persist()
                with self.assertRaisesRegex(ValueError, 'verification incomplete'):
                    supervisor.check_predecessor(binding, plan)

    def test_other_fp32_export_or_changed_served_artifact_is_rejected(self):
        for mutation in ('base', 'served'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                binding, plan, _, _, artifacts = predecessor_fixture(Path(temp))
                if mutation == 'base': binding['base'] = binding['base'].replace('900', '600')
                else: artifacts = {'changed': True}
                with patch.object(supervisor, 'served_artifacts', return_value=artifacts), self.assertRaises(ValueError):
                    supervisor.check_predecessor(binding, plan)

    def test_actual_trained_curriculum_must_match_retention(self):
        with tempfile.TemporaryDirectory() as temp:
            binding, plan, proofs, persist, artifacts = predecessor_fixture(Path(temp))
            proofs['validation-0-collect.json']['report']['dataset_sha256'] = 'wrong'; persist()
            with patch.object(supervisor, 'served_artifacts', return_value=artifacts), self.assertRaisesRegex(ValueError, 'actual accepted R8'):
                supervisor.check_predecessor(binding, plan)

    def test_changed_proof_is_not_silently_rebound(self):
        with tempfile.TemporaryDirectory() as temp:
            binding, plan, _, _, _ = predecessor_fixture(Path(temp))
            (Path(binding['predecessor']['evidence_root']) / 'pipeline-state.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'evidence changed'):
                supervisor.check_predecessor(binding, plan)


class NumericalTests(unittest.TestCase):
    def test_step_order_settings_layers_and_finite_loss_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / 'config.json').write_text(json.dumps({'text_config': {'num_hidden_layers': 24}}))
            rows = [{'step': 1, 'training_row_index': 7, 'loss': .1, 'gradient_norm': .2},
                    {'step': 2, 'training_row_index': 3, 'loss': .09, 'gradient_norm': .1}]
            evidence = {'plan': {'audit': {'rehearsal': {'row_indices': [7, 3]}}, 'settings': {
                'threads': 14, 'max_seq_length': 8192, 'learning_rate': 1e-5, 'semantic_loss_weight': 4,
                'lora_layers': 24, 'lora_rank': 16, 'lora_alpha': 32}}, 'complete': {
                'steps': 2, 'updated_layers': list(range(24)), 'nonzero_gradient_layers': list(range(24))}}
            for mutation in ('none', 'order', 'loss', 'steps', 'layers', 'settings'):
                current, metrics = deepcopy(evidence), deepcopy(rows)
                if mutation == 'order': metrics.reverse()
                if mutation == 'loss': metrics[0]['loss'] = float('nan')
                if mutation == 'steps': metrics.pop()
                if mutation == 'layers': current['complete']['updated_layers'].pop()
                if mutation == 'settings': current['plan']['settings']['lora_rank'] = 8
                (root / 'steps.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in metrics))
                with self.subTest(mutation=mutation):
                    if mutation == 'none': supervisor.check_numerical(current, root, root)
                    else:
                        with self.assertRaises(ValueError): supervisor.check_numerical(current, root, root)

    def test_running_failed_or_wrong_numerical_invocation_is_rejected(self):
        command = ['/synthetic/python', '/synthetic/rehearse_cpu_v2.py', '--output', '/synthetic/rehearsal',
                   '--data', '/synthetic/data', '--model', '/synthetic/base', '--trainer', '/synthetic/train_cpu_serial_v4.py']
        properties = {'SubState': 'exited', 'MainPID': '0', 'Result': 'success', 'ExecMainStatus': '0',
            'InvocationID': 'a' * 32, 'ExecStart': '{ path=/synthetic/python ; argv[]=' + ' '.join(command) + ' ; ignore_errors=no ; status=0 }'}
        binding = {'rehearsal_unit': 'chat-ai-synthetic-rehearsal.service', 'rehearsal_unit_properties': properties,
            'rehearsal_command': command, 'trainer': '/synthetic/train_cpu_serial_v4.py',
            'rehearsal': '/synthetic/rehearsal', 'data': '/synthetic/data', 'base': '/synthetic/base'}
        for mutation in ('none', 'running', 'failure', 'invocation', 'output', 'command'):
            actual, current = deepcopy(properties), deepcopy(binding)
            if mutation == 'running': actual['SubState'] = 'running'
            if mutation == 'failure': actual['Result'] = 'exit-code'
            if mutation == 'invocation': actual['InvocationID'] = 'b' * 32
            if mutation == 'output': current['rehearsal'] = '/synthetic/other'
            if mutation == 'command': current['rehearsal_command'][0] = '/synthetic/other-python'
            text = ''.join(key + '=' + value + '\n' for key, value in actual.items())
            with self.subTest(mutation=mutation), patch.object(supervisor.subprocess, 'check_output', return_value=text):
                if mutation == 'none': supervisor.completed_unit(current)
                else:
                    with self.assertRaises(ValueError): supervisor.completed_unit(current)


class IsolationTests(unittest.TestCase):
    def test_inherited_engine_credentials_and_loader_overrides_are_removed(self):
        with patch.dict(supervisor.os.environ, {'Q36_EOS': '9', 'HF_TOKEN': 'synthetic',
                'LD_PRELOAD': 'synthetic', 'HTTP_PROXY': 'synthetic', 'COLI_MODEL': 'other'}):
            for env in (supervisor.environment(), supervisor.environment(Path('/synthetic/runtime'))):
                self.assertFalse({'Q36_EOS', 'HF_TOKEN', 'LD_PRELOAD', 'HTTP_PROXY', 'COLI_MODEL'} & env.keys())
            self.assertEqual(supervisor.environment()['OMP_NUM_THREADS'], '10')
            self.assertEqual(supervisor.environment(Path('/synthetic/runtime'))['OMP_NUM_THREADS'], '4')

    def test_service_resource_limits_are_enforced(self):
        good = 'CPUQuotaPerSecUSec=14s\nMemoryMax=17179869184\nMemorySwapMax=0\nKillMode=control-group\n'
        for text in (good, good.replace('14s', '16s'), good.replace('MemorySwapMax=0', 'MemorySwapMax=infinity'), good.replace('control-group', 'process')):
            with self.subTest(text=text), patch.object(Path, 'read_text', return_value='0::/system.slice/chat-ai-synthetic-rehearsal.service'), patch.object(supervisor.subprocess, 'check_output', return_value=text):
                if text == good: supervisor.enclosing_service()
                else:
                    with self.assertRaises(ValueError): supervisor.enclosing_service()

    def test_replay_outside_a_service_is_rejected(self):
        with patch.object(Path, 'read_text', return_value='0::/user.slice/session.scope'), self.assertRaises(ValueError):
            supervisor.enclosing_service()

    def test_incomplete_source_binding_rejects_before_reading_weights(self):
        binding = {key: '/synthetic/' + key for key in ('rehearsal', 'data', 'base', 'runtime', 'trainer', 'exporter', 'converter')}
        binding['source_sha256'] = {}
        with patch.object(supervisor, 'load_captures') as load, self.assertRaisesRegex(ValueError, 'source binding'):
            supervisor.verify_inputs(binding)
        load.assert_not_called()

    def test_owned_group_cleanup_after_readiness_error_and_exited_parent(self):
        for parent_exited in (False, True):
            with self.subTest(parent_exited=parent_exited):
                proc = Mock(pid=541, args=['synthetic']); calls = []
                proc.wait.side_effect = lambda **kw: calls.append('reap')
                fake_os = SimpleNamespace(P_PID=1, WEXITED=2, WNOHANG=4, WNOWAIT=8, CLD_EXITED=1,
                    waitid=Mock(return_value=SimpleNamespace(si_code=1, si_status=0)),
                    killpg=Mock(side_effect=lambda pid, sig: calls.append((pid, sig))))
                with patch.object(supervisor.subprocess, 'Popen', return_value=proc), patch.object(supervisor, 'os', fake_os):
                    with self.assertRaisesRegex(RuntimeError, 'synthetic readiness'):
                        with supervisor.owned_process(['synthetic'], {}, None) as child:
                            if parent_exited: self.assertEqual(child.poll(), 0)
                            proc.wait.assert_not_called()
                            raise RuntimeError('synthetic readiness')
                self.assertEqual(calls, [(541, signal.SIGTERM), (541, signal.SIGKILL), 'reap'])
                proc.poll.assert_not_called()
                self.assertTrue(fake_os.waitid.call_args.args[2] & fake_os.WNOWAIT)

    def test_cleanup_kills_owned_group_after_grace_timeout(self):
        proc = Mock(pid=541, args=['synthetic'])
        with patch.object(supervisor.subprocess, 'Popen', return_value=proc), patch.object(supervisor.os, 'killpg') as kill, patch.object(supervisor.UnreapedChild, 'wait', side_effect=supervisor.subprocess.TimeoutExpired('synthetic', 10)):
            with supervisor.owned_process(['synthetic'], {}, None): pass
        self.assertEqual(kill.call_args_list[-1].args, (541, signal.SIGKILL))
        proc.wait.assert_called_once_with(timeout=10)



class SupervisorFlowTests(unittest.TestCase):
    def exercise(self, failure=None):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'output'
            binding = {'runtime': str(Path(temp) / 'runtime'), 'base': '/synthetic/base',
                'rehearsal': '/synthetic/rehearsal', 'exporter': '/synthetic/export_adapter.py',
                'converter': '/synthetic/convert_colibri.py', 'server_python': '/synthetic/python',
                'port': 18999, 'model_id': 'chat-ai-synthetic-replay'}
            artifacts = {'runtime': {'sha256': 'runtime'}, 'tokenizer': {'sha256': 'tokenizer'}}
            evidence = {'plan': {'runtime_artifacts': artifacts['runtime']},
                'predecessor': {'served_artifacts': artifacts}}
            request = {'payload': {'messages': ['synthetic']}}
            identity = {'pid': 41, 'created': 1, 'engine_pid': 42, 'engine_created': 2}
            order = []
            @contextmanager
            def owned(command, env, log):
                phase = 'worker' if 'serve' in command else ('convert' if 'convert_colibri.py' in command[1] else 'merge')
                order.append('start-' + phase)
                try:
                    yield SimpleNamespace(wait=lambda timeout: 1 if failure == 'export' and phase == 'merge' else 0,
                                          poll=lambda: 1 if failure == 'readiness' and phase == 'worker' else None)
                finally:
                    order.append('stop-' + phase)
            class Missing(Exception): pass
            psutil = SimpleNamespace(NoSuchProcess=Missing, STATUS_ZOMBIE='zombie', Process=Mock(side_effect=Missing),
                virtual_memory=lambda: SimpleNamespace(total=64 * 1024 ** 3, available=48 * 1024 ** 3))
            serving = SimpleNamespace(render_chat_qwen=lambda *a, **kw: 'prompt')
            transformers = SimpleNamespace(AutoTokenizer=SimpleNamespace(from_pretrained=lambda *a, **kw: object()))
            identities = [identity, {**identity, 'engine_created': 3} if failure == 'identity' else identity]
            report = {'transport_complete': failure != 'transport', 'responses': 1,
                      'comparison': {'pairs': [{'same_valid_action': False}]}}
            with patch.object(supervisor.sys, 'platform', 'linux'), \
                 patch.dict(supervisor.os.environ, {'CHAT_AI_TRAINING_SERVER': '1'}), \
                 patch.object(supervisor, 'bootstrap'), \
                 patch.object(supervisor, 'validate_binding', return_value=output), \
                 patch.object(supervisor, 'verify_inputs', return_value=evidence), \
                 patch.object(supervisor, 'owned_process', side_effect=owned), \
                 patch.object(supervisor, 'served_artifacts', return_value=artifacts), \
                 patch.object(supervisor, 'worker_identity', side_effect=identities), \
                 patch.object(supervisor, 'get_json', return_value={}), \
                 patch.object(supervisor, 'no_other_jobs'), \
                 patch.object(supervisor, 'replay_requests', return_value=[request]), \
                 patch.object(supervisor, 'collect_replay', return_value=report) as collect, \
                 patch.object(supervisor, 'file_sha', return_value='synthetic'), \
                 patch.object(supervisor.socket, 'socket'), \
                 patch.dict(sys.modules, {'openai_server': serving, 'transformers': transformers}):
                if failure:
                    with self.assertRaises((ValueError, RuntimeError)):
                        supervisor.run(binding, psutil)
                    self.assertFalse((output / 'complete.json').exists())
                else:
                    supervisor.run(binding, psutil)
                    result = json.loads((output / 'complete.json').read_text())
                    self.assertFalse(result['model_accepted'])
                    self.assertFalse(result['full_training_authorized'])
                    self.assertTrue(result['worker_stopped'])
                    self.assertEqual(collect.call_args.args[0], [request])
                    self.assertEqual(order, ['start-merge', 'stop-merge', 'start-convert', 'stop-convert', 'start-worker', 'stop-worker'])
                if failure == 'export':
                    self.assertEqual(order, ['start-merge', 'stop-merge'])
                    collect.assert_not_called()
                elif failure:
                    self.assertEqual(order[-1], 'stop-worker')

    def test_export_then_replay_with_action_failures_never_grants_acceptance(self):
        self.exercise()

    def test_export_failure_prevents_worker_launch(self):
        self.exercise('export')

    def test_readiness_failure_stops_owned_worker(self):
        self.exercise('readiness')

    def test_incomplete_collection_stops_worker_without_completion(self):
        self.exercise('transport')

    def test_changed_worker_stops_without_completion(self):
        self.exercise('identity')

class SourceAdmissionTests(unittest.TestCase):
    def test_mutated_helper_rejects_before_any_local_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            names = (*supervisor.HELPER_NAMES, 'replay_rehearsal.py', 'trainer.py', 'exporter.py', 'converter.py')
            for name in names: (root / name).write_text('raise RuntimeError("must not execute")\n')
            binding = {key: str(root / (key + '.py')) for key in ('trainer', 'exporter', 'converter')}
            binding['source_sha256'] = {str(root / name): supervisor.file_sha(root / name) for name in names}
            (root / 'attest_colibri.py').write_text('raise RuntimeError("changed helper must not execute")\n')
            with patch.object(supervisor, '__file__', str(root / 'replay_rehearsal.py')), patch.object(supervisor.importlib, 'import_module') as imported:
                with self.assertRaisesRegex(ValueError, 'source changed'): supervisor.bootstrap(binding)
                imported.assert_not_called()

    def test_self_consistent_replacement_cannot_rebind_numerical_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); rehearsal = root / 'rehearsal'; data = root / 'data'
            rehearsal.mkdir(); data.mkdir()
            (rehearsal / 'complete.json').write_text('{"steps":1,"evidence_sha256":{"plan.json":"original"}}')
            (data / 'manifest.json').write_text('{"files":{"train.jsonl":"original"}}')
            binding = {key: str(root / key) for key in ('rehearsal', 'data', 'base', 'runtime', 'trainer')}
            binding.update(rehearsal_complete_sha256=supervisor.file_sha(rehearsal / 'complete.json'),
                           data_manifest_sha256=supervisor.file_sha(data / 'manifest.json'))
            for name in ('complete', 'manifest'):
                path = rehearsal / 'complete.json' if name == 'complete' else data / 'manifest.json'
                original = path.read_bytes(); path.write_text('{"internally_rehashed":"replacement"}')
                with self.subTest(name=name), patch.object(supervisor, 'verify_sources'), patch.object(supervisor, 'load_captures') as loaded:
                    with self.assertRaisesRegex(ValueError, 'evidence or dataset manifest changed'):
                        supervisor.verify_inputs(binding)
                    loaded.assert_not_called()
                path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
