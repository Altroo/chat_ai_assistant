"""Server-only export/replay of the shared V3 refinement rehearsal.

A completed selected candidate may be diagnosed even when acceptance failed.
This never grants acceptance or permission to start later-application training.
The original accepted-predecessor Contracts supervisor remains unchanged.
"""
import argparse
from contextlib import contextmanager
import http.client
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import signal
import shutil
import socket
import subprocess
import sys
import time

# Bootstrap source checks use only the standard library. Imported helper code
# must never run before its operator-pinned source has been checked.
HELPER_NAMES = ('attest_colibri.py', 'audit_training_inputs_v2.py', 'audit_training_inputs.py', 'collect_rehearsal.py',
    'rehearse_cpu_v3.py', 'rehearsal_comparison.py', 'training_schedule.py', 'serial_scope_v3.py',
    'serial_scope_v2.py', 'prepare_management_name_errata.py', 'prepare_management_name_errata_v2.py',
    'semantic_loss.py', 'text_lora.py', 'preflight_training.py')
fingerprint = collect_replay = no_other_jobs = trainer_functions = load_captures = replay_requests = None


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def verify_sources(binding):
    root = Path(__file__).resolve().parent
    required = {str(Path(__file__).resolve()), *(str(root / name) for name in HELPER_NAMES)}
    required.update(str(Path(binding[key]).resolve()) for key in ('trainer', 'exporter', 'converter'))
    if not required <= set(binding['source_sha256']):
        raise ValueError('Incomplete supervisor source binding')
    for name, expected in binding['source_sha256'].items():
        if file_sha(name) != expected:
            raise ValueError('Bound export/replay source changed')


def bootstrap(binding):
    verify_sources(binding)
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root))
    for name in HELPER_NAMES:
        old = sys.modules.get(Path(name).stem)
        if old is not None and Path(old.__file__).resolve() != root / name:
            raise ValueError('A helper from another source is already imported')
    modules = {name: importlib.import_module(name) for name in
               ('attest_colibri', 'collect_rehearsal', 'rehearse_cpu_v3', 'rehearsal_comparison')}
    globals().update(fingerprint=modules['attest_colibri'].fingerprint,
        collect_replay=modules['collect_rehearsal'].collect_replay,
        no_other_jobs=modules['rehearse_cpu_v3'].no_other_jobs,
        trainer_functions=modules['rehearse_cpu_v3'].trainer_functions,
        load_captures=modules['rehearsal_comparison'].load_captures,
        replay_requests=modules['rehearsal_comparison'].replay_requests)
    verify_sources(binding)


def read(path):
    return json.loads(Path(path).read_text())


def file_sha(path):
    path = Path(path)
    value = hashlib.sha256(); before = path.stat()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            value.update(chunk)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError('Input changed while hashing')
    return value.hexdigest()


def save(path, value):
    with path.open('x') as handle:
        # Request artifacts must retain tool-schema key order for exact replay.
        handle.write(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')


def check_predecessor(binding, plan):
    """Bind a completed selected shared candidate without claiming acceptance."""
    pred = binding['predecessor']
    report_path = Path(pred['report'])
    if file_sha(report_path) != pred['report_sha256']:
        raise ValueError('Completed shared evaluation report changed')
    report = read(report_path)
    step = report.get('selected_step')
    if (step != 2339 or report.get('training_updates_completed') != 2339 or
            report.get('complete_identity_and_scoring_verified') is not True or
            report.get('fresh_controls_verified') is not True or
            report.get('production_activation') is not False or
            type(report.get('accepted')) is not bool):
        raise ValueError('Shared candidate evaluation is incomplete')
    if (plan.get('stage') != 'shared' or plan.get('retained_dataset') is not None):
        raise ValueError('Refinement replay is restricted to the three shared applications')
    data = Path(binding['data'])
    manifest = read(data / 'manifest.json')
    if (manifest.get('version') != 'shared-v5r10-en-fr' or
            set(manifest.get('applications', [])) != {'facturation', 'management_projet', 'design_workflow'} or
            manifest.get('languages') != ['en', 'fr']):
        raise ValueError('Unexpected shared refinement curriculum')
    categories = sorted(manifest['counts']['added_categories'])
    if len(categories) != 8 or plan.get('rehearsal_categories') != categories:
        raise ValueError('Declared bilingual category coverage changed')
    prepare = importlib.import_module('rehearse_cpu_v3').prepare_inputs
    audit, _, captures, lineage = prepare(data, 'shared', None, categories=categories)
    if audit != plan['audit'] or captures != plan['captures'] or lineage is not None:
        raise ValueError('Rehearsal selection differs from the reviewed curriculum')
    base = Path(binding['base']).resolve()
    if (base != Path(pred['exports_root']).resolve() / ('step-' + str(step)) / 'merged' or
            plan['base_artifacts'] != pred['base_artifacts']):
        raise ValueError('Rehearsal used another selected FP32 model')
    proofs = []
    for when in ('before', 'after'):
        path = Path(pred[when])
        value = read(path)
        canonical = json.dumps(value, indent=2).encode()
        if (path.read_bytes() != canonical + b'\n' or
                hashlib.sha256(canonical).hexdigest() != report['evidence_sha256'][f'fresh-{step}-{when}.json']):
            raise ValueError('Selected serving evidence changed')
        proofs.append(value)
    if proofs[0] != proofs[1] or proofs[0]['step'] != step:
        raise ValueError('Selected serving identity changed during evaluation')
    artifacts = proofs[0]['artifacts']
    if served_artifacts(base.parent / 'colibri', Path(binding['runtime'])) != artifacts:
        raise ValueError('Selected serving artifacts changed')
    return {'step': step, 'served_artifacts': artifacts,
            'source_report_sha256': pred['report_sha256'],
            'model_acceptance_established': False}


def completed_unit(binding):
    unit = binding['rehearsal_unit']
    if not re.fullmatch(r'chat-ai-[a-z0-9-]+\.service', unit):
        raise ValueError('Invalid rehearsal service name')
    keys = ('SubState', 'MainPID', 'Result', 'ExecMainStatus', 'InvocationID', 'ExecStart')
    result = dict(line.split('=', 1) for line in subprocess.check_output(
        ['systemctl', 'show', unit, *['--property=' + key for key in keys]], text=True).splitlines())
    if (result != binding['rehearsal_unit_properties'] or
            any(result.get(k) != v for k, v in {'SubState': 'exited', 'MainPID': '0',
                'Result': 'success', 'ExecMainStatus': '0'}.items()) or
            not re.fullmatch('[a-f0-9]{32}', result.get('InvocationID', ''))):
        raise ValueError('Numerical rehearsal invocation did not finish as bound')
    raw = result['ExecStart']
    prefix, suffix = 'argv[]=', ' ; ignore_errors='
    if raw.count(prefix) != 1 or raw.count(suffix) != 1:
        raise ValueError('Unexpected numerical service command encoding')
    command = binding['rehearsal_command']
    if (not command or any(not isinstance(arg, str) or not arg or re.search(r'[\s;{}]', arg) for arg in command) or
            raw.split(prefix, 1)[1].split(suffix, 1)[0] != ' '.join(command)):
        raise ValueError('Numerical service command differs from reviewed command')
    if str(Path(binding['trainer']).with_name('rehearse_cpu_v3.py')) not in command:
        raise ValueError('Numerical unit used another runner')
    for flag, value in (('--output', binding['rehearsal']), ('--data', binding['data']),
                        ('--model', binding['base']), ('--trainer', binding['trainer'])):
        if command.count(flag) != 1 or command[command.index(flag) + 1] != value:
            raise ValueError('Numerical unit input or output differs')
    return result


def check_numerical(evidence, rehearsal, base):
    plan, complete = evidence['plan'], evidence['complete']
    metrics = [json.loads(line) for line in (rehearsal / 'steps.jsonl').read_text().splitlines()]
    selected = plan['audit']['rehearsal']['row_indices']
    if (complete['steps'] != len(selected) or len(metrics) != len(selected) or
            [item['step'] for item in metrics] != list(range(1, len(selected) + 1)) or
            [item['training_row_index'] for item in metrics] != selected or
            any(not math.isfinite(item['loss']) or not math.isfinite(item['gradient_norm']) for item in metrics)):
        raise ValueError('Numerical rehearsal step coverage is incomplete')
    config = read(base / 'config.json'); text = config.get('text_config', config)
    expected = {'threads': 14, 'max_seq_length': 8192, 'learning_rate': 1e-5,
                'semantic_loss_weight': 4, 'lora_layers': 24, 'lora_rank': 16, 'lora_alpha': 32}
    if plan['settings'] != expected:
        raise ValueError('Unexpected numerical rehearsal settings')
    count = plan['settings']['lora_layers']
    layers = list(range(text['num_hidden_layers'] - count, text['num_hidden_layers']))
    if count != 24 or complete['updated_layers'] != layers or complete['nonzero_gradient_layers'] != layers:
        raise ValueError('Numerical rehearsal layer coverage is incomplete')


def runtime_artifacts(runtime):
    return fingerprint(runtime, [runtime / 'c/qwen36', runtime / 'c/coli',
        *sorted((runtime / 'c').glob('*.py')), *sorted((runtime / 'c/tools').glob('*.py'))])


def served_artifacts(model, runtime):
    return {'weights': fingerprint(model, model.glob('*.safetensors')),
        'tokenizer': fingerprint(model, [model / n for n in ('tokenizer.json', 'tokenizer_config.json', 'chat_template.jinja')]),
        'config': fingerprint(model, [model / n for n in ('config.json', 'qwen36_meta.json')]),
        'runtime': runtime_artifacts(runtime)}


def environment(runtime=None):
    # Do not inherit EOS, backend, model, proxy or dynamic-loader overrides.
    values = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONUNBUFFERED': '1',
              'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1'}
    if runtime is None:
        values.update(CHAT_AI_TRAINING_SERVER='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      TOKENIZERS_PARALLELISM='false', OMP_NUM_THREADS='10')
    else:
        values.update(OMP_NUM_THREADS='4', COLI_DENSE_I8='1', COLI_ENGINE=str(runtime / 'c/qwen36'))
    return values


def worker_command(binding, output):
    return [binding['server_python'], str(Path(binding['runtime']) / 'c/coli'), 'serve',
        '--model', str(output / 'colibri'), '--no-tune-profile', '--ctx', '8192', '--gpu', 'none',
        '--ngen', '512', '--no-think', '--temp', '0', '--host', '127.0.0.1',
        '--port', str(binding['port']), '--model-id', binding['model_id'],
        '--max-queue', '2', '--queue-timeout', '10', '--kv-slots', '1']


def get_json(port, path):
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=3)
    try:
        connection.request('GET', path, headers={'Connection': 'close'})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError('Worker health request failed')
        body = response.read(65537)
        if len(body) > 65536:
            raise ValueError('Oversized worker health response')
        return json.loads(body)
    finally:
        connection.close()


def worker_identity(proc, binding, output, psutil):
    if proc.poll() is not None:
        raise RuntimeError('Owned worker exited')
    parent = psutil.Process(proc.pid)
    command = worker_command(binding, output); env = environment(Path(binding['runtime']))
    if parent.cmdline() != command or Path(parent.exe()).resolve() != Path(command[0]).resolve():
        raise ValueError('Owned worker command or executable changed')
    if parent.environ() != env or os.getsid(parent.pid) != parent.pid:
        raise ValueError('Owned worker environment or session changed')
    engines = parent.children(recursive=True)
    if len(engines) != 1:
        raise ValueError('Unexpected worker child inventory')
    engine = engines[0]
    if (Path(engine.exe()).resolve() != (Path(binding['runtime']) / 'c/qwen36').resolve() or
            engine.num_threads() != 4 or
            any(engine.environ().get(k) != v for k, v in env.items()) or
            'Q36_EOS' in engine.environ()):
        raise ValueError('Owned engine configuration changed')
    listeners = [item for process in (parent, engine) for item in process.net_connections(kind='inet')
                 if item.status == 'LISTEN']
    if len(listeners) != 1 or listeners[0].laddr.ip != '127.0.0.1' or listeners[0].laddr.port != binding['port']:
        raise ValueError('Worker listener differs from the private endpoint')
    if [m['id'] for m in get_json(binding['port'], '/v1/models')['data']] != [binding['model_id']]:
        raise ValueError('Worker model identity changed')
    health = get_json(binding['port'], '/health')
    if health['kv_slots'] != 1 or health['scheduler']['active'] or health['scheduler']['queued']:
        raise ValueError('Worker is not idle')
    return {'pid': parent.pid, 'created': parent.create_time(), 'command': command, 'environment': env,
            'engine_pid': engine.pid, 'engine_created': engine.create_time(), 'engine_threads': 4,
            'engine_environment': engine.environ(), 'engine_command': engine.cmdline()}


class UnreapedChild:
    """Observe a Linux child without releasing its PID/session during cleanup."""
    def __init__(self, proc):
        self.proc, self.pid = proc, proc.pid

    def poll(self):
        result = os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if result is None:
            return None
        return result.si_status if result.si_code == os.CLD_EXITED else -result.si_status

    def wait(self, timeout):
        deadline = time.monotonic() + timeout
        while True:
            result = self.poll()
            if result is not None:
                return result
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(self.proc.args, timeout)
            time.sleep(.1)


@contextmanager
def owned_process(command, env, log):
    """Own a fresh session, including children left after a failed parent exit."""
    proc = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    child = UnreapedChild(proc)
    try:
        yield child
    finally:
        # WNOWAIT keeps the child PID reserved even when the worker has exited.
        # Its process group therefore cannot have been reassigned to another job.
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
            # Also terminate any engine left behind by an exited parent.
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        finally:
            proc.wait(timeout=10)


def enclosing_service():
    units = {part for line in Path('/proc/self/cgroup').read_text().splitlines()
             for part in line.split('/') if part.startswith('chat-ai-') and part.endswith('.service')}
    if len(units) != 1:
        raise ValueError('Replay requires its dedicated resource-limited service')
    unit = units.pop()
    keys = ('CPUQuotaPerSecUSec', 'MemoryMax', 'MemorySwapMax', 'KillMode')
    actual = dict(line.split('=', 1) for line in subprocess.check_output(
        ['systemctl', 'show', unit, *['--property=' + key for key in keys]], text=True).splitlines())
    if actual != {'CPUQuotaPerSecUSec': '14s', 'MemoryMax': str(16 * 1024 ** 3),
                  'MemorySwapMax': '0', 'KillMode': 'control-group'}:
        raise ValueError('Replay service resource limits differ')
    if not any(kind in unit for kind in ('rehearsal', 'export', 'eval')):
        raise ValueError('Replay service is outside the shared job admission guard')
    return {'unit': unit, 'limits': actual}


def validate_binding(binding, psutil):
    if sys.platform != 'linux' or os.environ.get('CHAT_AI_TRAINING_SERVER') != '1':
        raise ValueError('Export/replay is restricted to the approved Linux server')
    if binding.get('version') != 1 or not re.fullmatch(r'chat-ai-[a-z0-9-]+', binding['model_id']):
        raise ValueError('Invalid rehearsal binding')
    if type(binding['port']) is not int or not 1024 <= binding['port'] <= 65535:
        raise ValueError('Invalid isolated worker port')
    if not Path(binding['output']).is_absolute():
        raise ValueError('Output must be an absolute private path')
    output = Path(binding['output']).resolve()
    if output.exists():
        raise ValueError('Refusing to overwrite an export/replay attempt')
    for name in ('rehearsal', 'data', 'base', 'runtime', 'trainer', 'exporter', 'converter', 'server_python'):
        source = Path(binding[name])
        if not source.is_absolute() or not source.exists():
            raise ValueError('Missing absolute input path')
        source = source.resolve()
        if output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError('Export output overlaps a source')
    enclosing_service()
    no_other_jobs(psutil)
    if not output.parent.is_dir() or shutil.disk_usage(output.parent).free < 12 * 1024 ** 3:
        raise RuntimeError('Insufficient isolated export storage')
    state = psutil.virtual_memory()
    if state.available - 16 * 1024 ** 3 < state.total * .10:
        raise RuntimeError('Insufficient export memory reserve')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', binding['port']))
    return output


def verify_inputs(binding):
    rehearsal, data, base, runtime, trainer = (Path(binding[key]) for key in ('rehearsal', 'data', 'base', 'runtime', 'trainer'))
    verify_sources(binding)
    if (file_sha(rehearsal / 'complete.json') != binding['rehearsal_complete_sha256'] or
            file_sha(data / 'manifest.json') != binding['data_manifest_sha256']):
        raise ValueError('Reviewed rehearsal evidence or dataset manifest changed')
    evidence = load_captures(rehearsal, data); plan = evidence['plan']
    evidence['predecessor'] = check_predecessor(binding, plan)
    completed_unit(binding)
    check_numerical(evidence, rehearsal, base)
    for name, expected in {**plan['dependencies'], 'rehearse_cpu_v3.py': plan['rehearsal_sha256']}.items():
        if Path(name).name != name or file_sha(trainer.with_name(name)) != expected:
            raise ValueError('Numerical rehearsal source changed')
    source = trainer_functions(trainer, plan['trainer_sha256'])
    if source['model_fingerprint'](base) != plan['base_artifacts'] or runtime_artifacts(runtime) != plan['runtime_artifacts']:
        raise ValueError('Bound base or runtime changed')
    return evidence


def run(binding, psutil):
    if sys.platform != 'linux' or os.environ.get('CHAT_AI_TRAINING_SERVER') != '1':
        raise ValueError('Export/replay is restricted to the approved Linux server')
    bootstrap(binding)
    output = validate_binding(binding, psutil)
    evidence = verify_inputs(binding)
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'binding.json', binding)
    runtime = Path(binding['runtime'])
    merged, converted = output / 'merged', output / 'colibri'
    commands = [[sys.executable, binding['exporter'], '--base', binding['base'],
                 '--adapter', str(Path(binding['rehearsal']) / 'disposable-adapter'), '--output', str(merged), '--threads', '10'],
                [sys.executable, binding['converter'], str(merged), str(converted), '--runtime', str(runtime)]]
    for index, command in enumerate(commands):
        with (output / ('export-' + str(index) + '.log')).open('x') as log:
            with owned_process(command, environment(), log) as proc:
                if proc.wait(timeout=3600) != 0:
                    raise RuntimeError('Rehearsal export failed')
    verify_inputs(binding)
    artifacts = served_artifacts(converted, runtime)
    if (artifacts['runtime'] != evidence['plan']['runtime_artifacts'] or
            artifacts['tokenizer'] != evidence['predecessor']['served_artifacts']['tokenizer']):
        raise ValueError('Export runtime or tokenizer changed')
    sys.path.insert(0, str(runtime / 'c'))
    import openai_server as serving
    serving.ARCH, serving.CHAT_FLAVOR = 'qwen36', None
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(converted, local_files_only=True, trust_remote_code=False)
    requests = replay_requests(evidence, serving.render_chat_qwen, tokenizer, binding['model_id'])
    # No requests leave this isolated loopback worker. Preserve exact payloads first.
    save(output / 'requests.json', requests)
    no_other_jobs(psutil)
    if psutil.virtual_memory().available < psutil.virtual_memory().total * .10 + 6 * 1024 ** 3:
        raise RuntimeError('Insufficient inference memory reserve')
    with (output / 'worker.log').open('x') as log:
        with owned_process(worker_command(binding, output), environment(runtime), log) as proc:
            deadline = time.monotonic() + 180
            while True:
                if proc.poll() is not None:
                    raise RuntimeError('Worker exited before readiness')
                try:
                    get_json(binding['port'], '/health')
                    break
                except (OSError, ValueError, http.client.HTTPException):
                    if time.monotonic() >= deadline:
                        raise TimeoutError('Worker readiness timed out')
                    time.sleep(1)
            before = worker_identity(proc, binding, output, psutil)
            save(output / 'before.json', {'artifacts': artifacts, 'worker': before})
            report = collect_replay(requests, 'http://127.0.0.1:' + str(binding['port']) + '/v1/chat/completions', output / 'replay')
            after = worker_identity(proc, binding, output, psutil)
            current = served_artifacts(converted, runtime)
            save(output / 'after.json', {'artifacts': current, 'worker': after})
            if before != after or current != artifacts:
                raise ValueError('Worker or artifacts changed during replay')
            verify_inputs(binding)
            if report['transport_complete'] is not True or report['responses'] != len(requests):
                raise RuntimeError('Replay collection is incomplete')
    for pid, created in ((before['pid'], before['created']), (before['engine_pid'], before['engine_created'])):
        try:
            process = psutil.Process(pid)
            if process.create_time() == created and process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                raise RuntimeError('An owned worker process is still running')
        except psutil.NoSuchProcess:
            pass
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', binding['port']))
    save(output / 'complete.json', {'status': 'EXPORT REPLAY COMPLETE; ACTION REVIEW REQUIRED',
        'requests': len(requests), 'model_accepted': False, 'full_training_authorized': False,
        'production_activation': False, 'worker_stopped': True,
        'evidence_sha256': {name: file_sha(output / name) for name in (
            'binding.json', 'requests.json', 'before.json', 'after.json', 'replay/collection.json',
            'replay/requests.json', 'replay/responses.jsonl')}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--binding-sha256', required=True)
    args = parser.parse_args()
    if file_sha(args.binding) != args.binding_sha256:
        raise ValueError('Private operator binding changed')
    if sys.platform != 'linux' or os.environ.get('CHAT_AI_TRAINING_SERVER') != '1':
        raise ValueError('Export/replay is restricted to the approved Linux server')
    import psutil
    run(read(args.binding), psutil)


if __name__ == '__main__':
    main()
