"""Facturation contrast/replay pilot using the pinned trainer's encode/loss functions.

Only synthetic training rows receive updates. Development captures are diagnostics,
never acceptance scores. Export/Colibri comparison is a separate required step.
Run sequentially on the approved server; never resume full training from this adapter.
"""
import argparse
import ast
from collections.abc import Mapping
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import time

from jsonschema import validate, ValidationError

# Capture source identities before importing or using local helper functions.
DEPENDENCY_NAMES = ('prepare_facturation_replay_v1.py', 'facturation_focus_v2_admission.py', 'audit_training_inputs_v2.py', 'audit_training_inputs.py', 'training_schedule.py', 'serial_scope_v3.py', 'serial_scope_v2.py',
                    'prepare_management_name_errata.py', 'prepare_management_name_errata_v2.py',
                    'semantic_loss.py', 'text_lora.py', 'preflight_training.py', 'attest_colibri.py')
SOURCE_SHA256 = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                 for name in (*DEPENDENCY_NAMES, Path(__file__).name)}

from audit_training_inputs import digest, encoded, model_input_key, target
from audit_training_inputs_v2 import audit
from semantic_loss import semantic_token_weights
from serial_scope_v3 import BASE_APPLICATIONS, STAGES, validate_stage, validate_retained_curriculum


FUNCTIONS = ('file_fingerprint', 'artifact_group', 'model_fingerprint', 'encode', 'loss_for')
FOCUS_MANIFEST_SHA256 = 'd4350995c0899c56b372fe13a20ff3cb5fce4527844e9e1c4f694b726bbdf4ae'
FOCUS_CATEGORIES = ('date_optional_document', 'date_optional_operation', 'mixed_document_filters',
    'unpaid_optional_filters', 'exclusive_boundary', 'literal_field_copy', 'account_navigation',
    'explicit_result_choice', 'payment_reference_limit', 'payment_party_filters')



def trainer_functions(path, expected_sha):
    payload = path.read_bytes()
    if digest(payload) != expected_sha:
        raise ValueError('Pinned trainer source changed')
    tree = ast.parse(payload)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS]
    if len(selected) != len(FUNCTIONS) or {node.name for node in selected} != set(FUNCTIONS):
        raise ValueError('Trainer function contract changed')
    # The source is trusted, hash-pinned repository code. Never execute its
    # top-level CLI, model loading, optimizer loop, or any model-generated code.
    namespace = {'Mapping': Mapping, 'Path': Path, 'hashlib': hashlib, 'json': json,
                 'semantic_token_weights': semantic_token_weights}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def verify_sources(trainer):
    for name, expected in SOURCE_SHA256.items():
        path = Path(__file__).with_name(name)
        if not path.is_file() or digest(path.read_bytes()) != expected:
            raise ValueError('Rehearsal source or dependency changed')
    for name in ('semantic_loss.py', 'text_lora.py', 'serial_scope_v3.py', 'serial_scope_v2.py',
                 'prepare_management_name_errata.py', 'prepare_management_name_errata_v2.py'):
        helper = trainer.with_name(name)
        if not helper.is_file() or digest(helper.read_bytes()) != SOURCE_SHA256[name]:
            raise ValueError('Trainer helper differs from the rehearsal helper')


def capture_indices(rows, eligible, per_application=2):
    """Select inputs before inference, without using outcomes or expected targets."""
    chosen = []
    for app in sorted({row['application'] for row in rows}):
        unique = {}
        for index in eligible:
            if rows[index]['application'] == app:
                unique.setdefault(model_input_key(rows[index]), index)
        order = sorted(unique, key=lambda key: digest(key.encode()))
        if len(order) < per_application:
            raise ValueError('Insufficient distinct development inputs per application')
        chosen.extend(unique[key] for key in order[:per_application])
    return chosen


def prepare_inputs(data, stage, retained, correction_root=None, *, categories=()):
    """Admit this pinned Facturation experiment with unchanged-app replay."""
    if stage != "facturation" or retained is not None or correction_root is not None:
        raise ValueError("This experiment admits Facturation focus with explicit replay only")
    if categories and (len(categories) != len(FOCUS_CATEGORIES) or set(categories) != set(FOCUS_CATEGORIES)):
        raise ValueError("Every published Facturation contrast category is required")
    from prepare_facturation_replay_v1 import admit_prepared
    return admit_prepared(data, FOCUS_MANIFEST_SHA256)



def validate_options(args):
    if platform.system() != 'Linux' or os.environ.get('CHAT_AI_TRAINING_SERVER') != '1':
        raise ValueError('Rehearsal is restricted to the approved Linux server')
    if any(os.environ.get(name) != '1' for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE')):
        raise ValueError('Offline model loading must be enabled')
    expected_trainer = 'train_cpu.py' if args.stage == 'facturation' else None
    if args.trainer.name != expected_trainer:
        raise ValueError('Rehearsal must use the matching shared or serial trainer')
    if args.output.exists():
        raise ValueError('Refusing to overwrite a rehearsal')
    for source in (args.model, args.data, args.runtime, args.trainer.parent, args.retained_data, args.correction_root):
        if source is not None and (args.output.resolve().is_relative_to(source.resolve()) or
                                   source.resolve().is_relative_to(args.output.resolve())):
            raise ValueError('Rehearsal output must be isolated from source artifacts')
    if not 1 <= args.threads <= 14:
        raise ValueError('Use between one and fourteen CPU threads')
    if not 0 < args.learning_rate < float('inf') or not 1 <= args.semantic_loss_weight < float('inf'):
        raise ValueError('Finite positive learning rate and semantic weight >= 1 required')
    if args.max_seq_length != 8192:
        raise ValueError('Rehearsal must use the current 8192-token serving context')
    if args.lora_layers < 1 or args.lora_rank < 1 or not math.isfinite(args.lora_alpha) or args.lora_alpha <= 0:
        raise ValueError('Positive finite LoRA settings required')


def no_other_optimizer(psutil):
    busy = {'train_cpu.py', 'probe_cpu_capacity.py', 'probe_cpu_serial_v1.py', 'probe_cpu_serial_v2.py', 'rehearse_cpu.py', 'rehearse_cpu_v2.py', 'rehearse_cpu_v3.py', 'rehearse_facturation_v1.py', 'rehearse_facturation_v2.py', 'probe_cpu_selective.py', Path(__file__).name}
    busy.update('train_cpu_serial_v' + str(version) + '.py' for version in range(1, 5))
    for process in psutil.process_iter(['pid', 'cmdline']):
        try:
            if process.info['pid'] != os.getpid() and any(Path(arg).name in busy for arg in (process.info['cmdline'] or [])):
                raise RuntimeError('Another trainer or rehearsal is active; run sequentially')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def assert_idle_units(listing, cgroups):
    own = {part for line in cgroups.splitlines() for part in line.split('/')
           if part.startswith('chat-ai-') and part.endswith('.service')}
    jobs = ('training', 'capacity', 'preflight', 'precision', 'smoke',
            'eval', 'functional', 'export', 'reference', 'rehearsal')
    for line in listing.splitlines():
        if not line.strip():
            continue
        unit = line.split()[0]
        if unit.startswith('chat-ai-') and unit not in own and any(kind in unit for kind in jobs):
            raise RuntimeError('Another training, export or evaluation service is active')


def no_other_jobs(psutil):
    no_other_optimizer(psutil)
    listing = subprocess.check_output(['systemctl', 'list-units', '--type=service',
        '--state=running,activating,deactivating', '--no-legend', '--plain', '--no-pager'], text=True)
    assert_idle_units(listing, Path('/proc/self/cgroup').read_text())


def frozen_parameter_digest(model, torch):
    value = hashlib.sha256()
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            value.update(encoded([name, list(parameter.shape), str(parameter.dtype)]).encode())
            # View bytes explicitly because NumPy has no native BF16 dtype.
            value.update(parameter.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes())
    return value.hexdigest()


def capture(model, tokenizer, rows, indices, parser, renderer, splitter, stop_filter_class,
            stop_sequences, torch, generation_class, context, emit, admit):
    mode, rng = model.training, torch.random.get_rng_state()
    model.eval()
    eos = [tokenizer.convert_tokens_to_ids(token) for token in ('<|im_end|>', '<|endoftext|>')]
    records = []
    try:
        if len(set(eos)) != 2 or any(type(value) is not int or value < 0 for value in eos):
            raise ValueError('Unexpected termination token IDs')
        for split, selected in indices.items():
            for index in selected:
                admit()
                row = rows[split][index]
                prompt = tokenizer.apply_chat_template(row['messages'][:-1], tools=row['tools'],
                    enable_thinking=False, tokenize=False, add_generation_prompt=True)
                if prompt != renderer(row['messages'][:-1], tools=row['tools'],
                                      enable_thinking=False, add_generation_prompt=True):
                    raise ValueError('Training and serving prompt templates differ')
                inputs = tokenizer(prompt, add_special_tokens=False, return_tensors='pt')
                count = inputs['input_ids'].shape[1]
                budget = min(512, context - count)
                if budget < 1:
                    raise ValueError('No generation room in the serving context')
                generation = generation_class(max_new_tokens=budget, do_sample=False, num_beams=1,
                    use_cache=True, bos_token_id=tokenizer.bos_token_id, eos_token_id=eos,
                    pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos[0])
                started = time.monotonic()
                try:
                    with torch.inference_mode():
                        output = model.generate(**inputs, generation_config=generation)
                except Exception as error:
                    emit({'split': split, 'row_index': index,
                          'input_sha256': digest(model_input_key(row).encode()),
                          'generation_error': type(error).__name__})
                    raise
                tokens = output[0, count:]
                terminal = bool(len(tokens) and int(tokens[-1]) in eos)
                reply = tokenizer.decode(tokens[:-1] if terminal else tokens,
                    skip_special_tokens=False, clean_up_tokenization_spaces=False)
                # Match the pinned Qwen chat serving path before interpreting tools.
                # Keep the unfiltered decode and all generated IDs for diagnosis.
                chunks = []
                stop_filter = stop_filter_class(stop_sequences, chunks.append, ignore_leading=False)
                stop_filter.feed(reply)
                stop_filter.finish()
                served_reply = ''.join(chunks)
                action, parse_error, schema_valid = None, None, False
                try:
                    _, answer = splitter(served_reply, enable_thinking=False, add_generation_prompt=True)
                    _, calls = parser(answer, row['tools'])
                    if len(calls) == 1:
                        function = calls[0]['function']
                        action = {'name': function['name'], 'arguments': json.loads(function['arguments'])}
                        offered = {tool['function']['name']: tool['function']['parameters'] for tool in row['tools']}
                        if action['name'] not in offered:
                            raise ValueError('Generated tool was not offered')
                        validate(action['arguments'], offered[action['name']])
                        schema_valid = True
                    elif not calls and not terminal and not stop_filter.stopped() and len(tokens) >= budget:
                        parse_error = 'INCOMPLETE_RESPONSE'
                except (KeyError, TypeError, ValueError, ValidationError) as error:
                    parse_error = type(error).__name__
                record = {'split': split, 'row_index': index, 'application': row['application'],
                    'input_sha256': digest(model_input_key(row).encode()),
                    'prompt_sha256': digest(prompt.encode()), 'prompt_tokens': count,
                    'generated_tokens': len(tokens), 'generated_token_ids': tokens.tolist(),
                    'terminal_eos': terminal, 'reply': reply, 'served_reply': served_reply,
                    'matched_stop': stop_filter.matched, 'capture_contract': 'qwen36-stop-filter-v1',
                    'parse_error': parse_error, 'schema_valid': schema_valid,
                    'action': action, 'matches_training_or_development_target': schema_valid and encoded(action) == encoded(target(row)),
                    'seconds': time.monotonic() - started}
                records.append(record)
                emit(record)
        return records
    finally:
        model.train(mode)
        torch.random.set_rng_state(rng)


def run(args):
    validate_options(args)
    verify_sources(args.trainer)
    source = trainer_functions(args.trainer, args.trainer_sha256)
    checked, rows, captures, lineage = prepare_inputs(args.data, args.stage, args.retained_data, args.correction_root, categories=args.rehearsal_categories)
    import psutil
    no_other_jobs(psutil)
    def memory():
        state = psutil.virtual_memory()
        if state.available < state.total * .10:
            raise RuntimeError('Spare-memory floor reached')
        return state.available
    memory()
    import sys
    sys.path.insert(0, str(args.runtime / 'c'))
    import openai_server as serving
    # Imported modules default to GLM; the isolated worker serves this Qwen model.
    serving.ARCH, serving.CHAT_FLAVOR = 'qwen36', None
    from openai_server import parse_qwen_tool_calls, render_chat_qwen, split_thinking_reply, StopFilter
    stop_sequences, ignore_leading = serving.stop_policy({}, chat=True)
    if tuple(stop_sequences) != ('<|im_end|>', '<|im_start|>') or ignore_leading:
        raise ValueError('Pinned Qwen chat stop policy changed')
    from preflight_training import verify_split
    from attest_colibri import fingerprint
    runtime = fingerprint(args.runtime, [args.runtime / 'c/qwen36', args.runtime / 'c/coli',
        *sorted((args.runtime / 'c').glob('*.py')), *sorted((args.runtime / 'c/tools').glob('*.py'))])
    base = source['model_fingerprint'](args.model)
    import torch
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration, GenerationConfig
    from text_lora import configure_text_lora
    from importlib.metadata import version
    versions = {name: version(name) for name in ('torch', 'transformers', 'peft', 'safetensors')}
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.manual_seed(17)
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    preflight = {split: verify_split((args.data / (split + '.jsonl')).read_bytes(),
        parse_qwen_tool_calls, tokenizer, args.max_seq_length, render_chat_qwen, args.semantic_loss_weight)
        for split in ('train', 'valid')}
    if any(preflight[split]['sha256'] != checked['input_sha256'][split] for split in preflight):
        raise ValueError('Dataset changed before numerical rehearsal')
    no_other_jobs(psutil)
    memory()
    model = Qwen3_5ForConditionalGeneration.from_pretrained(args.model, local_files_only=True,
        dtype=torch.bfloat16, attn_implementation='sdpa')
    model, regex = configure_text_lora(model, layers=args.lora_layers, rank=args.lora_rank,
        alpha=args.lora_alpha, checkpointing=True)
    source.update(torch=torch, model=model, tokenizer=tokenizer, a=args)
    selected = checked['rehearsal']['row_indices']
    items = [(index, source['encode'](rows['train'][index])) for index in selected]
    expected = set(range(model.config.text_config.num_hidden_layers - args.lora_layers,
                         model.config.text_config.num_hidden_layers))
    trainable = {name: value for name, value in model.named_parameters() if value.requires_grad}
    def layer(name):
        return int(re.search(r'language_model\.layers\.(\d+)\.', name).group(1))
    optimizer = torch.optim.AdamW(trainable.values(), lr=args.learning_rate, weight_decay=0)
    frozen = frozen_parameter_digest(model, torch)
    verify_sources(args.trainer)
    args.output.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        with (args.output / name).open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
    settings = {key: getattr(args, key) for key in ('threads', 'max_seq_length', 'learning_rate',
        'semantic_loss_weight', 'lora_layers', 'lora_rank', 'lora_alpha')}
    save('plan.json', {'scope': 'Disposable mechanics rehearsal; not model acceptance',
        'audit': checked, 'captures': captures, 'stage': args.stage, 'retained_dataset': lineage,
        'rehearsal_categories': list(args.rehearsal_categories),
        'capture_contract': 'qwen36-stop-filter-v1',
        'chat_stop_policy': {'sequences': list(stop_sequences), 'ignore_leading': False},
        'trainer_sha256': args.trainer_sha256, 'rehearsal_sha256': SOURCE_SHA256[Path(__file__).name],
        'base_artifacts': base, 'runtime_artifacts': runtime, 'preflight': preflight, 'settings': settings,
        'fixed_settings': {'seed': 17, 'dtype': 'bfloat16', 'attention': 'sdpa',
            'gradient_checkpointing': 'nonreentrant', 'optimizer': 'AdamW', 'weight_decay': 0,
            'gradient_clip_norm': 1, 'thinking': False, 'sampling': False},
        'dependencies': {name: SOURCE_SHA256[name] for name in DEPENDENCY_NAMES},
        'dependency_versions': versions, 'optimizer_defaults': optimizer.defaults,
        'lora_target_regex': regex})
    def admit():
        no_other_jobs(psutil)
        memory()
    def save_capture(label):
        with (args.output / (label + '.events.jsonl')).open('x') as stream:
            def emit(record):
                stream.write(json.dumps(record) + '\n')
                stream.flush()
            result = capture(model, tokenizer, rows, captures, parse_qwen_tool_calls,
                render_chat_qwen, split_thinking_reply, StopFilter, stop_sequences, torch, GenerationConfig,
                args.max_seq_length, emit, admit)
        save(label + '.json', result)
    save_capture('before')
    model.train()
    updated_layers, nonzero_layers, metrics = set(), set(), []
    started = time.monotonic()
    with (args.output / 'steps.jsonl').open('x') as stream:
        for index, item in items:
            admit()
            optimizer.zero_grad(set_to_none=True)
            loss = source['loss_for'](item)
            if not torch.isfinite(loss):
                raise RuntimeError('Non-finite rehearsal loss')
            loss.backward()
            seen = set()
            for name, value in trainable.items():
                if value.grad is None or not torch.isfinite(value.grad).all():
                    raise RuntimeError('Missing or non-finite adapter gradient')
                seen.add(layer(name))
                if value.grad.abs().max() > 0:
                    nonzero_layers.add(layer(name))
            if seen != expected:
                raise RuntimeError('Incomplete gradient participation')
            before = {name: value.detach().clone() for name, value in trainable.items()}
            norm = torch.nn.utils.clip_grad_norm_(list(trainable.values()), 1, error_if_nonfinite=True)
            optimizer.step()
            for name, value in trainable.items():
                if not torch.isfinite(value).all():
                    raise RuntimeError('Non-finite adapter update')
                if not torch.equal(before[name], value.detach()):
                    updated_layers.add(layer(name))
            if any(not torch.isfinite(value).all() for state in optimizer.state.values()
                   for value in state.values() if torch.is_tensor(value)):
                raise RuntimeError('Non-finite optimizer state')
            metric = {'step': len(metrics) + 1, 'training_row_index': index, 'loss': float(loss.detach()),
                'gradient_norm': float(norm), 'rss_bytes': psutil.Process().memory_info().rss,
                'available_memory_bytes': memory()}
            metrics.append(metric)
            stream.write(json.dumps(metric) + '\n')
            stream.flush()
            print(json.dumps(metric), flush=True)
            del loss, before
    if nonzero_layers != expected or updated_layers != expected:
        raise RuntimeError('Some intended layers never received gradients or actual updates')
    if frozen_parameter_digest(model, torch) != frozen:
        raise RuntimeError('Frozen base parameters changed')
    model.save_pretrained(args.output / 'disposable-adapter')
    tokenizer.save_pretrained(args.output / 'disposable-adapter')
    adapter = args.output / 'disposable-adapter'
    if not all((adapter / name).is_file() for name in ('adapter_model.safetensors', 'adapter_config.json')):
        raise RuntimeError('Incomplete adapter serialization')
    adapter_files = [path for path in adapter.rglob('*') if path.is_file()]
    adapter_proof = fingerprint(adapter, adapter_files)
    save_capture('after')
    from peft import get_peft_model_state_dict
    from safetensors import safe_open
    live_adapter = get_peft_model_state_dict(model)
    with safe_open(adapter / 'adapter_model.safetensors', framework='pt', device='cpu') as saved:
        if set(saved.keys()) != set(live_adapter) or any(
                not torch.equal(saved.get_tensor(name), value.detach().cpu()) for name, value in live_adapter.items()):
            raise RuntimeError('Saved adapter differs from the live model used for captures')
    if fingerprint(adapter, [adapter / name for name in adapter_proof['files']]) != adapter_proof:
        raise RuntimeError('Saved adapter changed during captures')
    if frozen_parameter_digest(model, torch) != frozen:
        raise RuntimeError('Frozen parameters changed during capture')
    verify_sources(args.trainer)
    plan = json.loads((args.output / 'plan.json').read_text())
    if any(digest(Path(__file__).with_name(name).read_bytes()) != expected_hash
           for name, expected_hash in plan['dependencies'].items()):
        raise RuntimeError('A rehearsal dependency changed')
    if digest(Path(__file__).read_bytes()) != plan['rehearsal_sha256']:
        raise RuntimeError('Rehearsal source changed')
    if fingerprint(args.runtime, [args.runtime / name for name in runtime['files']]) != runtime:
        raise RuntimeError('Runtime artifact changed')
    if digest((args.data / 'manifest.json').read_bytes()) != checked['manifest_sha256']:
        raise RuntimeError('Dataset manifest changed')
    if source['model_fingerprint'](args.model) != base:
        raise RuntimeError('Base artifact changed during rehearsal')
    for split in ('train', 'valid'):
        if digest((args.data / (split + '.jsonl')).read_bytes()) != checked['input_sha256'][split]:
            raise RuntimeError('Dataset changed during rehearsal')
    if digest(args.trainer.read_bytes()) != args.trainer_sha256:
        raise RuntimeError('Trainer source changed during rehearsal')
    save('complete.json', {'status': 'NUMERICAL REHEARSAL COMPLETE; EXPORT COMPARISON PENDING',
        'steps': len(metrics), 'updated_layers': sorted(updated_layers),
        'disposable_adapter': adapter_proof, 'saved_adapter_matches_live': True,
        'evidence_sha256': {name: digest((args.output / name).read_bytes())
                           for name in ('plan.json', 'before.json', 'after.json', 'steps.jsonl',
                                        'before.events.jsonl', 'after.events.jsonl')},
        'nonzero_gradient_layers': sorted(nonzero_layers), 'frozen_parameters_unchanged': True,
        'elapsed_seconds': time.monotonic() - started, 'model_accepted': False,
        'export_compared': False, 'full_training_may_resume_from_this_adapter': False})
    print('Rehearsal complete. Compare the disposable adapter through real export and Colibri before a full run.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('facturation',), required=True)
    parser.add_argument('--retained-data', type=Path)
    parser.add_argument('--correction-root', type=Path)
    parser.add_argument('--rehearsal-categories', nargs='+', default=list(FOCUS_CATEGORIES))
    for name in ('model', 'data', 'runtime', 'trainer', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--trainer-sha256', required=True)
    parser.add_argument('--threads', type=int, required=True)
    parser.add_argument('--max-seq-length', type=int, required=True)
    parser.add_argument('--learning-rate', type=float, required=True)
    parser.add_argument('--semantic-loss-weight', type=float, required=True)
    parser.add_argument('--lora-layers', type=int, required=True)
    parser.add_argument('--lora-rank', type=int, required=True)
    parser.add_argument('--lora-alpha', type=float, required=True)
    run(parser.parse_args())


if __name__ == '__main__':
    main()
