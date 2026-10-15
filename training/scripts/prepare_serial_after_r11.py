"""Prepare later applications with exact R11 retention; never launch training."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from serial_scope_v3 import SOURCE_SHA256, validate_retained_curriculum
from prepare_serial_dialogue_v7 import prompt_key

ROOT = Path(__file__).resolve().parents[2]
BASE = 'shared-v5r11-en-fr'
BASE_SHA256 = '02f2addad85051fd20a180b29c01239f67f8ceeb8265ace8b054d09f1f81ccdc'
PROMPT_HELPER_SHA256 = '15fbd17a081a62371992148f2502b42a1e088da5b962e18c3fe9a45973d2c948'
STAGES = {
    'contrat': ('shared-v6r10-en-fr',
        '57683e286e0a585f9eef6c6f9ed13a86b27d458cf8a990d30e97a43c776c3f75',
        'shared-v6r11-en-fr', 2572, 319, 564),
    'gestion_magasin': ('shared-v7r10-en-fr',
        '598f53bd51608000105df40ee1b666c585c960916d8ba28cc47dcc3e11e91a94',
        'shared-v7r11-en-fr', 2770, 362, 654),
    'reservation': ('shared-v8r11-en-fr',
        'a7c42869e348c275aeb34d43bc3d96233637c27c9d44a5a4cae1d36d6987f3ff',
        'shared-v8r12-en-fr', 2950, 402, 738),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(directory, expected):
    raw = (directory / 'manifest.json').read_bytes()
    if digest(raw) != expected:
        raise ValueError('Pinned preparation manifest changed')
    manifest = json.loads(raw)
    payloads = {}
    for name, wanted in manifest['files'].items():
        if Path(name).name != name:
            raise ValueError('Split must be a local filename')
        payloads[name] = (directory / name).read_bytes()
        if digest(payloads[name]) != wanted:
            raise ValueError('Pinned preparation split changed')
    return manifest, payloads


def assemble(stage, retained, expected_predecessor):
    if stage not in STAGES:
        raise ValueError('Unsupported serial stage')
    if digest(Path(__file__).with_name('prepare_serial_dialogue_v7.py').read_bytes()) != PROMPT_HELPER_SHA256:
        raise ValueError('Reviewed request-boundary helper changed')
    old_name, old_hash, version, train_count, valid_count, held_count = STAGES[stage]
    prior, old = checked(ROOT / 'training/datasets' / old_name, old_hash)
    preceding, prefix = checked(retained, expected_predecessor)
    index = list(STAGES).index(stage)
    expected_version = BASE if index == 0 else list(STAGES.values())[index - 1][2]
    if preceding['version'] != expected_version:
        raise ValueError('Only the exact preceding R11 preparation may be retained')
    if stage == 'contrat' and expected_predecessor != BASE_SHA256:
        raise ValueError('Contracts must retain the pinned R11 curriculum')
    source_info = prior['added_dataset']
    added, additions = checked(ROOT / 'training/datasets' / source_info['version'],
                               source_info['manifest_sha256'])
    if (added['application'] != stage or added['languages'] != ['en', 'fr']
            or added['files'] != source_info['files']):
        raise ValueError('Reviewed new-application source changed')
    payloads = {}
    for name in ('train.jsonl', 'valid.jsonl'):
        if not old[name].endswith(additions[name]):
            raise ValueError('Prior application suffix differs from its source')
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
    excluded = set()
    for name, info in {**prior['historical_regression_held_out'], **prior['held_out']}.items():
        raw = (ROOT / name).read_bytes()
        if digest(raw) != info['sha256'] or len(raw.splitlines()) != info['count']:
            raise ValueError('Frozen evaluation bytes changed')
        excluded.update(prompt_key(row) for row in map(json.loads, raw.splitlines()))

    rows = {name: list(map(json.loads, raw.splitlines())) for name, raw in payloads.items()}
    if (len(rows['train.jsonl']), len(rows['valid.jsonl']), prior['held_out_count']) != (train_count, valid_count, held_count):
        raise ValueError('Unexpected cumulative case counts')
    keys = {name: {prompt_key(row) for row in values} for name, values in rows.items()}
    if keys['train.jsonl'] & keys['valid.jsonl'] or (keys['train.jsonl'] | keys['valid.jsonl']) & excluded:
        raise ValueError('Logical request crosses a split or evaluation boundary')
    if held_count != sum(info['count'] for info in prior['held_out'].values()):
        raise ValueError('Evaluation count disagrees with its files')
    for raw in payloads.values():
        if re.search(r'[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+|(?:password|api_key|secret)\s*[:=]',
                     raw.decode(), re.I):
            raise ValueError('Disallowed language or sensitive content in preparation')

    manifest = deepcopy(prior)
    manifest.pop('retained_corrections', None)
    manifest.pop('native_correction_evidence', None)
    manifest.update(
        version=version,
        generator_sha256=digest(Path(__file__).read_bytes()),
        scope_validator_sha256=SOURCE_SHA256['serial_scope_v3.py'],
        scope_dependencies=dict(SOURCE_SHA256),
        prompt_helper_sha256=PROMPT_HELPER_SHA256,
        source_preparation={'version': old_name, 'manifest_sha256': old_hash},
        retained_dataset={'version': preceding['version'], 'manifest_sha256': expected_predecessor,
                          'files': {name: preceding['files'][name] for name in payloads}},
        files={name: digest(raw) for name, raw in payloads.items()},
        counts={name: dict(Counter(row['application'] for row in values))
                for name, values in rows.items()},
        retained_refinement={'version': BASE, 'manifest_sha256': BASE_SHA256,
                             'includes_all_80_coverage_rows_and_six_wording_changes': True},
        split_policy='Retain the complete R11 successor train/validation bytes. Append only unchanged reviewed new-application examples in their original splits. Preserve every evaluation input. Exact normalized request overlap is rejected; semantic independence is not established.',
        training_status='PREPARATION ONLY. Require the actual accepted preceding model/run, frozen baseline, server numerical/export rehearsal and resource checks. No concurrent training or automatic activation.',
        model_binding={'status': 'UNBOUND; actual predecessor model has not passed acceptance',
                       'accepted_predecessor_required': preceding['version']})
    proof = validate_retained_curriculum(stage, manifest, payloads['train.jsonl'],
                                        payloads['valid.jsonl'], retained)
    if proof['retention_mode'] != 'exact retained bytes':
        raise ValueError('Refinement successors require exact retention')
    return payloads, manifest


def prepare():
    datasets = ROOT / 'training/datasets'
    if any((datasets / spec[2]).exists() for spec in STAGES.values()):
        raise ValueError('Never overwrite a versioned preparation')
    previous, expected = datasets / BASE, BASE_SHA256
    summaries = []
    for stage, spec in STAGES.items():
        payloads, manifest = assemble(stage, previous, expected)
        raw = (json.dumps(manifest, indent=2) + '\n').encode()
        output = datasets / spec[2]
        output.mkdir()
        for name, value in {**payloads, 'manifest.json': raw}.items():
            with (output / name).open('xb') as stream:
                stream.write(value)
        summaries.append({'stage': stage, 'version': spec[2], 'train': spec[3],
                          'valid': spec[4], 'held_out': spec[5],
                          'training_started': False, 'model_acceptance_verified': False})
        previous, expected = output, digest(raw)
    return summaries


if __name__ == '__main__':
    print(json.dumps(prepare()))
