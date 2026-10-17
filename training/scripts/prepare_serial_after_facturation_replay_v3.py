"""Prepare serial curricula retaining the complete Facturation replay V3 dataset.

This creates data only. Model/run acceptance, current native checks and server
resource admission remain separate requirements before numerical work.
"""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BASE_VERSION = 'facturation-replay-v3-en-fr'
BASE_SHA256 = '38b3d6d148940b2cfa7e44a9f59550fc4847ebb4e709b6c372b682f96c5b696f'
DEPENDENCIES = {
    'serial_scope_v3.py': '83986f89fbf075a72faad32ed6f45d9332736d47d1bd5d0c7b40124e654e2312',
    'prepare_serial_dialogue_v7.py': '15fbd17a081a62371992148f2502b42a1e088da5b962e18c3fe9a45973d2c948',
}
STAGES = {
    'contrat': ('shared-v6r11-en-fr', 'e22916a84cc694f35298a837ffe0db4abad9df320c1232133206fd4255b92343',
                'shared-v6-facturation-replay-v3-en-fr', 3128, 319, 564),
    'gestion_magasin': ('shared-v7r11-en-fr', 'd03b8977bf5c284a78212efaafde53a25cf1858a1cdc3a59ca4f19a97335da65',
                       'shared-v7-facturation-replay-v3-en-fr', 3326, 362, 654),
    'reservation': ('shared-v8r12-en-fr', 'a7853bd6aae523feb65bffd42ba42ee0c6ebcb5fb895fd63b233f1178413f743',
                    'shared-v8-facturation-replay-v3-en-fr', 3506, 402, 738),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_dependencies():
    for name, wanted in DEPENDENCIES.items():
        if digest(Path(__file__).with_name(name).read_bytes()) != wanted:
            raise ValueError('Reviewed preparation helper changed: ' + name)


verify_dependencies()
from serial_scope_v3 import SOURCE_SHA256, validate_retained_curriculum
from prepare_serial_dialogue_v7 import prompt_key


def checked(directory, wanted):
    raw = (directory / 'manifest.json').read_bytes()
    if digest(raw) != wanted:
        raise ValueError('Pinned preparation manifest changed')
    manifest = json.loads(raw)
    payloads = {}
    for name, expected in manifest['files'].items():
        if Path(name).name != name:
            raise ValueError('Split must be a local filename')
        value = (directory / name).read_bytes()
        if digest(value) != expected:
            raise ValueError('Pinned preparation split changed')
        payloads[name] = value
    return manifest, payloads


def frozen_evaluations(manifest):
    excluded = set()
    for name, info in {**manifest['historical_regression_held_out'], **manifest['held_out']}.items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Invalid frozen evaluation path')
        raw = (ROOT / relative).read_bytes()
        if digest(raw) != info['sha256'] or len(raw.splitlines()) != info['count']:
            raise ValueError('Frozen evaluation bytes changed')
        excluded.update(prompt_key(row) for row in map(json.loads, raw.splitlines()))
    return excluded


def assemble(stage, retained, expected_predecessor):
    verify_dependencies()
    if stage not in STAGES:
        raise ValueError('Unsupported serial stage')
    old_name, old_hash, version, train_count, valid_count, held_count = STAGES[stage]
    prior, old = checked(ROOT / 'training/datasets' / old_name, old_hash)
    preceding, prefix = checked(Path(retained), expected_predecessor)
    index = list(STAGES).index(stage)
    expected_version = BASE_VERSION if index == 0 else list(STAGES.values())[index - 1][2]
    if preceding['version'] != expected_version:
        raise ValueError('Only the exact preceding replay V3 preparation may be retained')
    if stage == 'contrat' and expected_predecessor != BASE_SHA256:
        raise ValueError('Contracts must retain the pinned Facturation replay V3 curriculum')
    source = prior['added_dataset']
    added, additions = checked(ROOT / 'training/datasets' / source['version'], source['manifest_sha256'])
    if added['application'] != stage or added['languages'] != ['en', 'fr'] or added['files'] != source['files']:
        raise ValueError('Reviewed new-application source changed')
    payloads = {}
    for name in ('train.jsonl', 'valid.jsonl'):
        if not old[name].endswith(additions[name]):
            raise ValueError('Queued application suffix differs from its reviewed source')
        if not prefix[name].endswith(b'\n') or not additions[name].endswith(b'\n'):
            raise ValueError('JSONL splits require complete line boundaries')
        payloads[name] = prefix[name] + additions[name]
    if payloads['valid.jsonl'] != old['valid.jsonl']:
        raise ValueError('Existing validation must remain byte-identical')
    for group in ('held_out', 'historical_regression_held_out'):
        if any(prior[group].get(name) != info for name, info in preceding[group].items()):
            raise ValueError('Retained evaluation identity changed')
    if any(prior['fresh_controls'][key] != preceding['fresh_controls'][key]
           for key in ('manifest_sha256', 'files')):
        raise ValueError('Fresh-control identity changed')
    excluded = frozen_evaluations(prior)
    rows = {name: list(map(json.loads, raw.splitlines())) for name, raw in payloads.items()}
    if (len(rows['train.jsonl']), len(rows['valid.jsonl']), prior['held_out_count']) != (train_count, valid_count, held_count):
        raise ValueError('Unexpected cumulative case counts')
    keys = {name: {prompt_key(row) for row in values} for name, values in rows.items()}
    if keys['train.jsonl'] & keys['valid.jsonl'] or (keys['train.jsonl'] | keys['valid.jsonl']) & excluded:
        raise ValueError('Logical request crosses a split or evaluation boundary')
    if held_count != sum(info['count'] for info in prior['held_out'].values()):
        raise ValueError('Evaluation count disagrees with its files')
    for raw in payloads.values():
        if re.search(r'[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+|(?:password|api_key|secret)\s*[:=]', raw.decode(), re.I):
            raise ValueError('Disallowed language or sensitive content in preparation')
    manifest = deepcopy(prior)
    for name in ('retained_corrections', 'native_correction_evidence', 'retained_refinement'):
        manifest.pop(name, None)
    manifest.update(
        version=version, generator_sha256=digest(Path(__file__).read_bytes()),
        scope_validator_sha256=SOURCE_SHA256['serial_scope_v3.py'],
        scope_dependencies=dict(SOURCE_SHA256), prompt_helper_sha256=DEPENDENCIES['prepare_serial_dialogue_v7.py'],
        source_preparation={'version': old_name, 'manifest_sha256': old_hash},
        retained_dataset={'version': preceding['version'], 'manifest_sha256': expected_predecessor,
                          'files': {name: preceding['files'][name] for name in payloads}},
        files={name: digest(raw) for name, raw in payloads.items()},
        counts={name: dict(Counter(row['application'] for row in values)) for name, values in rows.items()},
        retained_refinement={'version': BASE_VERSION, 'manifest_sha256': BASE_SHA256,
                             'complete_training_rows': 2975, 'new_facturation_rows_retained': 556},
        split_policy='Retain every replay V3 train/validation byte. Append only unchanged reviewed new-app examples in original splits. Preserve all evaluation inputs. Normalized logical overlap is rejected; semantic independence is not established.',
        training_status='PREPARATION ONLY. The original R11 launcher cannot accept this lineage. Require a separately reviewed actual accepted preceding model/run binding, server numerical/export rehearsal, frozen comparisons and resource checks. No training or automatic activation.',
        model_binding={'status': 'UNBOUND; actual predecessor acceptance is not verified',
                       'accepted_predecessor_required': preceding['version']})
    proof = validate_retained_curriculum(stage, manifest, payloads['train.jsonl'], payloads['valid.jsonl'], retained)
    if proof['retention_mode'] != 'exact retained bytes':
        raise ValueError('Replay successors require exact retention')
    return payloads, manifest


def prepare(base, output):
    base, output = Path(base).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Never overwrite a versioned preparation')
    checked(base, BASE_SHA256)
    # Exclusive creation protects existing files. A partial preparation remains
    # unbound and is never sufficient evidence for launching numerical work.
    output.mkdir()
    previous, expected, summaries = base, BASE_SHA256, []
    for stage, spec in STAGES.items():
        payloads, manifest = assemble(stage, previous, expected)
        raw = (json.dumps(manifest, indent=2) + '\n').encode()
        directory = output / spec[2]
        directory.mkdir()
        for name, value in {**payloads, 'manifest.json': raw}.items():
            with (directory / name).open('xb') as stream:
                stream.write(value)
        summaries.append({'stage': stage, 'version': spec[2], 'train': spec[3], 'valid': spec[4],
                          'held_out': spec[5], 'training_started': False, 'model_acceptance_verified': False})
        previous, expected = directory, digest(raw)
    return summaries


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.base, args.output_root)))
