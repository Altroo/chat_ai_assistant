"""Correct four queued Reservation date-scope requests, never prior results.

Uses reviewed native-source hashes without Django imports or database access.
Only training request wording changes; validation and held-out bytes stay frozen.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from prepare_serial_dialogue_v7 import prompt_key, frozen_rows
from serial_scope_v2 import validate_stage, validate_retained_curriculum

ROOT = Path(__file__).resolve().parents[2]
DATASETS = ROOT / 'training/datasets'
SOURCE_HASH = '1bc9574db8f9dccdcf065cf5a41b32f3217a0b2328ae46e779f21846a27f57cd'
RETAINED_HASH = 'abfbc8107929e6b010a7047334114ae80bf9e508188e75584c140384be842b09'
CUMULATIVE_HASH = 'e5f785a0d68e2b802771edfff6bf0d054aa351949f1f2d32eecb42fc0f2f3e97'
EXTRA_NATIVE = {
    'reservation/views.py': 'b336abcff76387ed56ed172a180fd12f75ec5c2150cf48f27eb5b3c62a41e5be',
    'local/views.py': '660d0fb8dc7fa34fad8769d7014e7d72c3041cebff08dd76addab4cd8cc62552',
    'reservation/filters.py': '455de44b1cef334d377c855ebed441d2d13bf1aba03125aa8e045a3fdab4741d',
    'local/models.py': 'c50521552c9265399a695ff5f214fddb8bf09b57a83caa130a460ecaa33b5566',
    'local/filters.py': 'e00db99046ea55b524cb74577b6ba5db1826c1a11424c0a96fe8744aa4de7142',
}
REPLACEMENTS = {
    'Réservations Airbnb dont le montant est retourné en avril 2029.':
        'Réservations Airbnb avec une arrivée en avril 2029 dont le montant est actuellement marqué comme retourné.',
    'Airbnb reservations with returned amounts in April 2029.':
        'Airbnb reservations arriving in April 2029 whose amounts are currently marked returned.',
    'Loyers enregistrés payés en 2028.':
        'Loyers de l’année locative 2028 actuellement marqués comme payés.',
    'Recorded paid rents in 2028.':
        'Rents for rental year 2028 that are currently marked paid.',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_manifest(directory, expected):
    raw = (directory / 'manifest.json').read_bytes()
    if digest(raw) != expected:
        raise ValueError('Reviewed manifest changed')
    result = json.loads(raw)
    for name, expected_hash in result['files'].items():
        if digest((directory / name).read_bytes()) != expected_hash:
            raise ValueError('Reviewed source split changed')
    return result


def corrected(payload, evaluation=False):
    lines, changes = [], []
    for index, raw in enumerate(payload.splitlines(keepends=True)):
        row = json.loads(raw)
        position = -1 if evaluation else -2
        text = row['messages'][position]['content']
        for old, new in REPLACEMENTS.items():
            if text == old or text.endswith('\nCurrent request: ' + old):
                row['messages'][position]['content'] = text[:-len(old)] + new
                raw = (json.dumps(row, ensure_ascii=False) + '\n').encode()
                changes.append(index)
                break
        lines.append(raw)
    if changes != [60, 61, 68, 69]:
        raise ValueError('Unexpected Reservation correction indices')
    return b''.join(lines), changes


def prepare(backend):
    source = DATASETS / 'reservation-dialogue-v3-en-fr'
    retained = DATASETS / 'shared-v7r9-en-fr'
    old_cumulative = DATASETS / 'shared-v8r9-en-fr'
    output = DATASETS / 'reservation-dialogue-v4-en-fr'
    cumulative = DATASETS / 'shared-v8r10-en-fr'
    if output.exists() or cumulative.exists():
        raise ValueError('Never overwrite versioned corrections')
    old = read_manifest(source, SOURCE_HASH)
    read_manifest(retained, RETAINED_HASH)
    prior = read_manifest(old_cumulative, CUMULATIVE_HASH)
    native = {**old['native_sources'], **EXTRA_NATIVE}
    if any(digest((backend / name).read_bytes()) != wanted for name, wanted in native.items()):
        raise ValueError('Reviewed native semantics changed')
    payloads = {name: (source / name).read_bytes() for name in old['files']}
    changes = {}
    for name in ('train.jsonl', 'train.eval.jsonl'):
        payloads[name], changes[name] = corrected(payloads[name], name.endswith('.eval.jsonl'))
    generator_hash = digest(Path(__file__).read_bytes())
    manifest = deepcopy(old)
    manifest.update(version=output.name, source_dataset=source.name, source_manifest_sha256=SOURCE_HASH,
                    source_files=old['files'], native_sources=native, generator_sha256=generator_hash,
                    changed_request_indices=changes, targets_changed=0, splits_changed=0,
                    inherited_metadata_provenance={'version': source.name, 'manifest_sha256': SOURCE_HASH,
                        'fields': ['augmentation', 'neutral_history', 'synthetic_reference_fixtures', 'shared_sources'],
                        'note': 'Inherited history choices and assignment hashes describe V3 inputs, not corrected V4 requests. Histories were not recomputed or rebalanced.'},
                    policy='Four training request wordings explicitly match native arrival-date or rental-year scope and current status. All targets, contexts, history choices, split membership, validation and held-out bytes are unchanged. Inherited augmentation and history assignments describe V3 provenance. New V4 file hashes identify the corrected inputs. No training or model accuracy claim.',
                    files={name: digest(raw) for name, raw in payloads.items()},
                    status='PREPARED; four training request corrections, not trained or evaluated')
    manifest_raw = (json.dumps(manifest, indent=2) + '\n').encode()
    joined = {name: (retained / name).read_bytes() + payloads[name] for name in ('train.jsonl', 'valid.jsonl')}
    cumulative_manifest = deepcopy(prior)
    cumulative_manifest.update(version=cumulative.name, generator_sha256=generator_hash,
        source_preparation={'version': old_cumulative.name, 'manifest_sha256': CUMULATIVE_HASH},
        added_dataset={'version': output.name, 'manifest_sha256': digest(manifest_raw), 'files': manifest['files']},
        files={name: digest(raw) for name, raw in joined.items()})
    rows = [list(map(json.loads, joined[name].splitlines())) for name in ('train.jsonl', 'valid.jsonl')]
    validate_stage('reservation', cumulative_manifest, *rows, complete_epochs=1)
    validate_retained_curriculum('reservation', cumulative_manifest, joined['train.jsonl'],
                                joined['valid.jsonl'], retained)
    excluded = {prompt_key(row) for path, info in {
        **prior['historical_regression_held_out'], **prior['held_out']}.items() for row in frozen_rows(path, info)}
    keys = [{prompt_key(row) for row in split} for split in rows]
    if keys[0] & keys[1] or (keys[0] | keys[1]) & excluded:
        raise ValueError('Corrected request crosses split or held-out boundary')
    # All checks precede publication. The previous version is never edited.
    output.mkdir()
    for name, raw in payloads.items():
        (output / name).write_bytes(raw)
    (output / 'manifest.json').write_bytes(manifest_raw)
    cumulative.mkdir()
    for name, raw in joined.items():
        (cumulative / name).write_bytes(raw)
    (cumulative / 'manifest.json').write_text(json.dumps(cumulative_manifest, indent=2) + '\n')
    return {'source': output.name, 'cumulative': cumulative.name,
            'changed_training_indices': changes, 'train_count': len(rows[0]), 'valid_count': len(rows[1]),
            'held_out_count': prior['held_out_count'], 'held_out_changed': False, 'training_started': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', type=Path, required=True)
    print(json.dumps(prepare(parser.parse_args().backend)))
