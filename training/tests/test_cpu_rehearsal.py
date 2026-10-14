"""Synthetic rehearsal-contract tests. No model loading, inference, or training."""
import ast
import copy
from contextlib import nullcontext
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import rehearse_cpu as rehearsal


def row(app, text, language='en'):
    return {'application': app, 'language': language,
        'messages': [{'role': 'system', 'content': 'Trusted context: ' + json.dumps({'application': app})},
                     {'role': 'user', 'content': text},
                     {'role': 'assistant', 'tool_calls': [{'function': {
                         'name': 'find', 'arguments': {'query': 'synthetic'}}}]}],
        'tools': [{'function': {'name': 'find', 'parameters': {
            'type': 'object', 'properties': {'query': {'type': 'string'}},
            'required': ['query'], 'additionalProperties': False}}}]}


def fixture(folder, apps, parent=None):
    folder.mkdir()
    files = {}
    for split in ('train', 'valid'):
        rows = [row(app, split + language + app + str(i), language) for app in apps for language in ('en', 'fr') for i in range(2)]
        payload = ''.join(json.dumps(value) + '\n' for value in rows).encode()
        (folder / (split + '.jsonl')).write_bytes(payload)
        files[split + '.jsonl'] = rehearsal.digest(payload)
    manifest = {'applications': list(apps), 'languages': ['en', 'fr'], 'files': files}
    if parent:
        previous = json.loads((parent / 'manifest.json').read_text())
        manifest['retained_dataset'] = {'manifest_sha256': rehearsal.digest((parent / 'manifest.json').read_bytes()),
                                        'files': previous['files']}
    (folder / 'manifest.json').write_text(json.dumps(manifest))
    return folder


class RehearsalContractTests(unittest.TestCase):
    def test_exact_trainer_functions_match_shared_and_serial(self):
        paths = [ROOT / 'training/scripts' / name for name in ('train_cpu.py', 'train_cpu_serial_v3.py')]
        bodies = []
        for path in paths:
            tree = ast.parse(path.read_text())
            bodies.append({node.name: ast.dump(node, include_attributes=False) for node in tree.body
                           if isinstance(node, ast.FunctionDef) and node.name in rehearsal.FUNCTIONS})
            bound = rehearsal.trainer_functions(path, rehearsal.digest(path.read_bytes()))
            self.assertTrue(all(callable(bound[name]) for name in rehearsal.FUNCTIONS))
            self.assertNotIn('torch', bound)
            self.assertNotIn('model', bound)
        self.assertEqual(bodies[0], bodies[1])

    def test_pin_mismatch_and_top_level_code_do_not_execute(self):
        path = ROOT / 'training/scripts/train_cpu.py'
        with self.assertRaisesRegex(ValueError, 'source changed'):
            rehearsal.trainer_functions(path, '0' * 64)
        with tempfile.TemporaryDirectory() as directory:
            variant = Path(directory) / 'variant.py'
            variant.write_text('raise RuntimeError("top-level must never run")\n' + path.read_text())
            bound = rehearsal.trainer_functions(variant, rehearsal.digest(variant.read_bytes()))
            self.assertTrue(callable(bound['encode']))
            variant.write_text('def encode(row): return row\n')
            with self.assertRaisesRegex(ValueError, 'contract changed'):
                rehearsal.trainer_functions(variant, rehearsal.digest(variant.read_bytes()))

    def test_trainer_helper_mismatch_and_dependency_drift_reject(self):
        trainer = ROOT / 'training/scripts/train_cpu.py'
        rehearsal.verify_sources(trainer)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, expected in rehearsal.SOURCE_SHA256.items():
                (root / name).write_bytes((ROOT / 'training/scripts' / name).read_bytes())
            for name in ('semantic_loss.py', 'text_lora.py'):
                mismatch = root / 'other'
                mismatch.mkdir(exist_ok=True)
                for helper in ('semantic_loss.py', 'text_lora.py'):
                    (mismatch / helper).write_bytes((root / helper).read_bytes())
                (mismatch / name).write_text((mismatch / name).read_text() + '\n# drift\n')
                with self.subTest(helper=name), self.assertRaisesRegex(ValueError, 'Trainer helper differs'):
                    rehearsal.verify_sources(mismatch / 'train_cpu.py')
            with patch.object(rehearsal, '__file__', str(root / 'rehearse_cpu.py')):
                rehearsal.verify_sources(trainer)
                (root / 'semantic_loss.py').write_text('# changed')
                with self.assertRaisesRegex(ValueError, 'dependency changed'):
                    rehearsal.verify_sources(trainer)

    def test_captures_do_not_depend_on_labels_and_preserve_distinct_history(self):
        rows = [row('facturation', str(i)) for i in range(8)]
        rows[1]['messages'].insert(1, {'role': 'user', 'content': 'previous context'})
        before = rehearsal.capture_indices(rows, range(len(rows)))
        changed = copy.deepcopy(rows)
        for value in changed:
            value['messages'][-1]['tool_calls'][0]['function'] = {'name': 'different', 'arguments': {}}
        self.assertEqual(before, rehearsal.capture_indices(changed, range(len(changed))))
        duplicate = copy.deepcopy(rows[0])
        with self.assertRaisesRegex(ValueError, 'distinct'):
            rehearsal.capture_indices([rows[0], duplicate], range(2))

    def test_full_cumulative_scope_is_validated_before_subset_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            apps = list(rehearsal.BASE_APPLICATIONS)
            previous = fixture(base / 'shared', apps)
            checked, rows, captures, lineage = rehearsal.prepare_inputs(previous, 'shared', None)
            self.assertEqual(checked['rows_checked']['train'], 12)
            self.assertIsNone(lineage)
            for stage in rehearsal.STAGES:
                apps.append(stage)
                current = fixture(base / stage, apps, previous)
                checked, rows, captures, lineage = rehearsal.prepare_inputs(current, stage, previous)
                self.assertEqual(len(checked['rehearsal']['row_indices']), len(apps) * 2)
                self.assertEqual(set(rows), {'train', 'valid'})
                self.assertEqual(len(captures['valid']), len(apps) * 2)
                self.assertIsNotNone(lineage)
                self.assertLessEqual(set(captures['train']), set(checked['rehearsal']['row_indices']))
                previous = current

    def test_missing_predecessor_skipped_stage_and_input_mutation_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            previous = fixture(base / 'shared', rehearsal.BASE_APPLICATIONS)
            current = fixture(base / 'contract', (*rehearsal.BASE_APPLICATIONS, 'contrat'), previous)
            for stage, retained in [('contrat', None), ('reservation', previous), ('shared', None)]:
                with self.subTest(stage=stage), self.assertRaises(ValueError):
                    rehearsal.prepare_inputs(current, stage, retained)
            (current / 'train.jsonl').write_text((current / 'train.jsonl').read_text() + '\n')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                rehearsal.prepare_inputs(current, 'contrat', previous)

    def test_server_offline_output_and_configuration_guards(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = SimpleNamespace(stage='shared', output=root/'out', model=root/'model',
                data=root/'data', runtime=root/'runtime', trainer=ROOT/'training/scripts/train_cpu.py',
                retained_data=None, threads=14, learning_rate=1e-5, semantic_loss_weight=4,
                max_seq_length=8192, lora_layers=24, lora_rank=16, lora_alpha=32)
            env = {'CHAT_AI_TRAINING_SERVER': '1', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'}
            with patch('platform.system', return_value='Linux'), patch.dict(os.environ, env):
                rehearsal.validate_options(args)
                for key, value in [('threads',15), ('learning_rate',float('nan')),
                                   ('semantic_loss_weight',float('inf')), ('max_seq_length',4096),
                                   ('lora_rank',0), ('lora_alpha',float('nan')),
                                   ('trainer',ROOT/'training/scripts/train_cpu_serial_v3.py'),
                                   ('output',args.model/'inside')]:
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        rehearsal.validate_options(SimpleNamespace(**{**vars(args), key:value}))
                args.output.mkdir()
                with self.assertRaisesRegex(ValueError, 'overwrite'):
                    rehearsal.validate_options(args)
            with patch('platform.system', return_value='Darwin'), self.assertRaisesRegex(ValueError, 'Linux server'):
                rehearsal.validate_options(args)
            with patch('platform.system', return_value='Linux'), patch.dict(os.environ, {**env, 'HF_HUB_OFFLINE':'0'}):
                with self.assertRaisesRegex(ValueError, 'Offline'):
                    rehearsal.validate_options(args)

    def test_evaluation_export_and_starting_jobs_block_rehearsal(self):
        own = 'chat-ai-pretraining-rehearsal.service'
        cgroup = '0::/system.slice/' + own
        for phase in ('training', 'capacity', 'export', 'eval', 'functional', 'reference', 'rehearsal'):
            for state in ('active running', 'activating start', 'deactivating stop'):
                with self.subTest(phase=phase,state=state), self.assertRaisesRegex(RuntimeError, 'service is active'):
                    rehearsal.assert_idle_units('chat-ai-synthetic-' + phase + '.service loaded ' + state, cgroup)
        rehearsal.assert_idle_units(own + ' loaded active running', cgroup)
        rehearsal.assert_idle_units('chat-ai-facturation-model.service loaded active running', cgroup)

    def test_another_optimizer_is_rejected_but_production_inference_is_allowed(self):
        class Missing(Exception):
            pass
        def fake(commands):
            return SimpleNamespace(NoSuchProcess=Missing, AccessDenied=Missing,
                process_iter=lambda fields: [SimpleNamespace(info={'pid':pid,'cmdline':cmd})
                    for pid,cmd in commands])
        rehearsal.no_other_optimizer(fake([(os.getpid(), ['python','rehearse_cpu.py']),
                                            (99999,['python','openai_server.py'])]))
        for script in ('train_cpu.py','train_cpu_serial_v3.py','probe_cpu_serial_v1.py','rehearse_cpu.py'):
            with self.subTest(script=script), self.assertRaisesRegex(RuntimeError, 'Another trainer'):
                rehearsal.no_other_optimizer(fake([(99999,['python','-B','/synthetic/'+script])]))


class Tensor:
    def __init__(self, values):
        self.values = values
        self.shape = (1, len(values[0])) if values and isinstance(values[0], list) else (len(values),)
    def __getitem__(self, key):
        if isinstance(key, tuple):
            return Tensor(self.values[key[0]][key[1]])
        value = self.values[key]
        return Tensor(value) if isinstance(key, slice) else value
    def __len__(self):
        return len(self.values)
    def tolist(self):
        return self.values


class CaptureTests(unittest.TestCase):
    def capture(self, *, fail=False, prompt_tokens=2, terminal=True, arguments='{"query":"synthetic"}'):
        history = []
        class Tokenizer:
            bos_token_id = None
            pad_token_id = None
            def convert_tokens_to_ids(self, token):
                return {'<|im_end|>':1,'<|endoftext|>':2}[token]
            def apply_chat_template(self, messages, **kwargs):
                history.append(copy.deepcopy(messages))
                return 'prompt'
            def __call__(self, text, **kwargs):
                return {'input_ids':Tensor([[9] * prompt_tokens])}
            def decode(self, tokens, **kwargs):
                return 'reply'
        class Model:
            training = True
            def eval(self):
                self.training = False
            def train(self, mode=True):
                self.training = mode
            def generate(self, **kwargs):
                self.budget = kwargs['generation_config'].max_new_tokens
                if fail:
                    raise RuntimeError('synthetic generation failure')
                return Tensor([kwargs['input_ids'].values[0] + [42, 2 if terminal else 43]])
        model = Model()
        random = SimpleNamespace(get_rng_state=lambda:'initial', set_rng_state=lambda state: history.append(state))
        torch = SimpleNamespace(random=random,inference_mode=nullcontext)
        emit = []
        rows = {'train':[row('facturation','user request')], 'valid':[]}
        try:
            result = rehearsal.capture(model, Tokenizer(), rows, {'train':[0], 'valid':[]},
                lambda text,tools: ('', [{'function':{'name':'find','arguments':arguments}}]),
                lambda *args,**kwargs:'prompt', lambda text,**kwargs:('',text),
                torch, SimpleNamespace, 8192, emit.append, lambda:None)
        except RuntimeError:
            result = None
        return result, emit, model, history, rows

    def test_independent_prompt_raw_tokens_context_budget_and_mode_restoration(self):
        result, emit, model, history, rows = self.capture(prompt_tokens=7704)
        self.assertEqual(history[0], rows['train'][0]['messages'][:-1])
        self.assertEqual(result, emit)
        self.assertEqual(result[0]['generated_token_ids'], [42,2])
        self.assertTrue(result[0]['matches_training_or_development_target'])
        self.assertEqual(model.budget,488)
        self.assertTrue(model.training)
        self.assertEqual(history[-1],'initial')

    def test_complete_tool_call_without_eos_matches_serving_behavior(self):
        result, _, _, _, _ = self.capture(terminal=False)
        self.assertFalse(result[0]['terminal_eos'])
        self.assertIsNotNone(result[0]['action'])
        self.assertTrue(result[0]['schema_valid'])
        self.assertTrue(result[0]['matches_training_or_development_target'])

    def test_invalid_generated_arguments_are_recorded_not_credited(self):
        result, _, _, _, _ = self.capture(arguments='{"query":true}')
        self.assertFalse(result[0]['schema_valid'])
        self.assertEqual(result[0]['parse_error'], 'ValidationError')
        self.assertFalse(result[0]['matches_training_or_development_target'])
        self.assertEqual(result[0]['action']['arguments'], {'query': True})

    def test_generation_failure_is_recorded_and_mode_restored(self):
        result, emit, model, history, _ = self.capture(fail=True)
        self.assertIsNone(result)
        self.assertEqual(emit[0]['generation_error'],'RuntimeError')
        self.assertTrue(model.training)
        self.assertEqual(history[-1],'initial')


if __name__ == '__main__':
    unittest.main()
