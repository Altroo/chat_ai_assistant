"""Carry the reviewed corrected curriculum through the last two serial stages.

Preparation only. Actual predecessor model acceptance, a frozen baseline and
server rehearsal remain required independently before each training stage.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from serial_scope_v3 import SOURCE_SHA256, validate_retained_curriculum
from prepare_serial_dialogue_v7 import prompt_key

ROOT = Path(__file__).resolve().parents[2]
BASE = 'shared-v6r10-en-fr'
BASE_SHA256 = '57683e286e0a585f9eef6c6f9ed13a86b27d458cf8a990d30e97a43c776c3f75'
STAGES = {
    'gestion_magasin': ('shared-v7r9-en-fr',
        'abfbc8107929e6b010a7047334114ae80bf9e508188e75584c140384be842b09',
        'shared-v7r10-en-fr'),
    'reservation': ('shared-v8r10-en-fr',
        '5a21824d9535309786b292f3965d3f7219860ea05446d5837609c6c3ff7bd7b2',
        'shared-v8r11-en-fr'),
}
CORRECTED_INDICES = [620, 621, 622, 623, 968, 969]
PROMPT_HELPER_SHA256 = '15fbd17a081a62371992148f2502b42a1e088da5b962e18c3fe9a45973d2c948'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(directory, expected):
    raw = (directory / 'manifest.json').read_bytes()
    if digest(raw) != expected:
        raise ValueError('Reviewed preparation manifest changed')
    manifest = json.loads(raw)
    payloads = {name: (directory / name).read_bytes() for name in manifest['files']}
    if any(digest(value) != manifest['files'][name] for name, value in payloads.items()):
        raise ValueError('Reviewed preparation split changed')
    return manifest, payloads


def assemble(stage, retained, expected_predecessor):
    if stage not in STAGES:
        raise ValueError('Only the two final serial stages are supported')
    if digest(Path(__file__).with_name('prepare_serial_dialogue_v7.py').read_bytes()) != PROMPT_HELPER_SHA256:
        raise ValueError('Reviewed request-boundary helper changed')
    source_name, source_hash, output_name = STAGES[stage]
    prior, old = checked(ROOT / 'training/datasets' / source_name, source_hash)
    preceding, prefix = checked(retained, expected_predecessor)
    old_parent, old_prefix = checked(
        ROOT / 'training/datasets' / prior['retained_dataset']['version'],
        prior['retained_dataset']['manifest_sha256'])
    added, additions = checked(ROOT / 'training/datasets' / prior['added_dataset']['version'],
                               prior['added_dataset']['manifest_sha256'])
    if added['application'] != stage or added['languages'] != ['en', 'fr']:
        raise ValueError('Reviewed application source scope changed')
    if old_parent['files'] != prior['retained_dataset']['files'] or added['files'] != prior['added_dataset']['files']:
        raise ValueError('Source lineage disagrees with its preparation')
    payloads = {}
    for name in ('train.jsonl', 'valid.jsonl'):
        if old[name] != old_prefix[name] + additions[name]:
            raise ValueError('Prior preparation differs from its retained and added sources')
        payloads[name] = prefix[name] + additions[name]
    before, after = [value.splitlines(keepends=True) for value in (old['train.jsonl'], payloads['train.jsonl'])]
    if len(before) != len(after) or [i for i, pair in enumerate(zip(before, after)) if pair[0] != pair[1]] != CORRECTED_INDICES:
        raise ValueError('Only the six reviewed targets may differ from the old preparation')
    if payloads['valid.jsonl'] != old['valid.jsonl']:
        raise ValueError('Validation must remain unchanged')
    rows = {name: list(map(json.loads, raw.splitlines())) for name, raw in payloads.items()}
    counts = {name: dict(Counter(row['application'] for row in values)) for name, values in rows.items()}
    if counts != prior['counts']:
        raise ValueError('Application counts changed')
    excluded = set()
    for name, info in {**prior['historical_regression_held_out'], **prior['held_out']}.items():
        raw = (ROOT / name).read_bytes()
        if digest(raw) != info['sha256'] or len(raw.splitlines()) != info['count']:
            raise ValueError('Frozen evaluation bytes changed')
        excluded.update(prompt_key(row) for row in map(json.loads, raw.splitlines()))
    keys = {name: {prompt_key(row) for row in values} for name, values in rows.items()}
    if keys['train.jsonl'] & keys['valid.jsonl'] or (keys['train.jsonl'] | keys['valid.jsonl']) & excluded:
        raise ValueError('Logical request crosses a split or evaluation boundary')
    if prior['held_out_count'] != sum(info['count'] for info in prior['held_out'].values()):
        raise ValueError('Evaluation count changed')

    manifest = deepcopy(prior)
    manifest.update(
        version=output_name, generator_sha256=digest(Path(__file__).read_bytes()),
        scope_validator_sha256=SOURCE_SHA256['serial_scope_v3.py'],
        scope_dependencies=SOURCE_SHA256, prompt_helper_sha256=PROMPT_HELPER_SHA256,
        source_preparation={'version': source_name, 'manifest_sha256': source_hash},
        retained_dataset={'version': preceding['version'], 'manifest_sha256': expected_predecessor,
                          'files': {name: preceding['files'][name] for name in payloads}},
        files={name: digest(raw) for name, raw in payloads.items()},
        native_correction_evidence=deepcopy(preceding['native_correction_evidence']),
        split_policy='Retain the exact corrected predecessor train/validation bytes. Append unchanged reviewed new-app rows. Preserve evaluation and original split membership. Reject normalized logical-request overlap; semantic independence is not established.',
        training_status='PREPARATION ONLY. Each stage requires acceptance of its actual preceding model/run, a frozen baseline, server numerical/export rehearsal and resource checks. No concurrent training or automatic activation.',
        model_binding={'status': 'UNBOUND; preceding stage has not been trained or accepted',
                       'accepted_predecessor_required': preceding['version']})
    if 'retained_corrections' in manifest:
        raise ValueError('Later stages must use exact retention without an exception')
    validate_retained_curriculum(stage, manifest, payloads['train.jsonl'], payloads['valid.jsonl'], retained)
    return payloads, manifest


def prepare():
    datasets = ROOT / 'training/datasets'
    if any((datasets / names[2]).exists() for names in STAGES.values()):
        raise ValueError('Never overwrite a versioned cumulative preparation')
    previous, expected = datasets / BASE, BASE_SHA256
    summaries = []
    for stage, (_, _, version) in STAGES.items():
        payloads, manifest = assemble(stage, previous, expected)
        raw = (json.dumps(manifest, indent=2) + '\n').encode()
        output = datasets / version
        output.mkdir()
        for name, value in {**payloads, 'manifest.json': raw}.items():
            with (output / name).open('xb') as stream:
                stream.write(value)
        summaries.append({'stage': stage, 'version': version,
                          'train': sum(manifest['counts']['train.jsonl'].values()),
                          'valid': sum(manifest['counts']['valid.jsonl'].values()),
                          'held_out': manifest['held_out_count'],
                          'model_acceptance_verified': False, 'training_started': False})
        previous, expected = output, digest(raw)
    return summaries


if __name__ == '__main__':
    print(json.dumps(prepare()))
