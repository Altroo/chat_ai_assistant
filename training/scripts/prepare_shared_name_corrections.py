"""Assemble six reviewed target corrections without changing any frozen input.

Preparation only: this does not bind a model, load weights or launch training.
A later application must still bind the actual accepted predecessor curriculum.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import prepare_management_name_errata_v2 as corrections
from audit_training_inputs import checked_rows
from prepare_serial_dialogue_v7 import prompt_key

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'shared-v5r8-en-fr'
OUTPUT = 'shared-v5r9-en-fr'
PARENT = '56f803ca7110ae78bc53c4a208a7dc7456819c024dc588109da46d7fb1520738'
ERRATA = '1ebded1f21cca3921b6e03339df65441255c5d2a883e4241d06028643ad4d0ec'
REVIEW = 'a3d7d66f242c5a2cf641009ec4637afc2baef33ac4eb01df4cc33cd887402e7d'
FRESH = '3c67453ad50eff5883a8c58fb0d2c208ac813dcc700c9680401e1cabc5bd3d7a'
HELPERS = ('prepare_management_name_errata.py', 'prepare_management_name_errata_v2.py',
           'audit_training_inputs.py', 'training_schedule.py', 'prepare_serial_dialogue_v7.py')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_json(path, expected):
    raw = path.read_bytes()
    if digest(raw) != expected:
        raise ValueError('Pinned metadata changed: ' + path.name)
    return json.loads(raw)


def corrected_payload(original, replacement_payload, provenance):
    lines, replacements = original.splitlines(keepends=True), replacement_payload.splitlines(keepends=True)
    if len(lines) != 2339 or len(replacements) != 6 or len(provenance) != 6:
        raise ValueError('Unexpected source or replacement count')
    if any(not line.endswith(b'\n') for line in lines + replacements):
        raise ValueError('Complete newline-terminated records required')
    expected_indices = [620, 621, 622, 623, 968, 969]
    if [item['source_index'] for item in provenance] != expected_indices:
        raise ValueError('Only the reviewed six target positions may change')
    result = list(lines)
    original_rows = list(map(json.loads, lines))
    expected_rows, expected_provenance = corrections.replacements(original_rows)
    if expected_provenance != provenance or list(map(json.loads, replacements)) != expected_rows:
        raise ValueError('Replacement rows differ from the reviewed corrections')
    for index, raw in zip(expected_indices, replacements):
        result[index] = raw
    if [i for i, (old, new) in enumerate(zip(lines, result)) if old != new] != expected_indices:
        raise ValueError('Unexpected byte changes outside reviewed targets')
    rows = list(map(json.loads, result))
    corrections.check_labels(rows)
    return b''.join(result)


def native_metadata(parent, review, roots):
    """Accept only previously reviewed source changes; reject unrelated drift."""
    expected = deepcopy(parent['native_metadata'])
    for fix in review['native_fixes']:
        expected[fix['application']].update(fix['source_sha256'])
    expected['management_projet']['project/filters.py'] = corrections.PROJECT_FILTER
    if set(roots) != set(expected):
        raise ValueError('Exact three-application native source scope required')
    for app, files in expected.items():
        for name, wanted in files.items():
            if digest((roots[app] / name).read_bytes()) != wanted:
                raise ValueError('Native source drift: ' + app + '/' + name)
    return expected


def assemble(roots, root=ROOT):
    source = root / 'training/datasets' / SOURCE
    parent = checked_json(source / 'manifest.json', PARENT)
    errata_path = root / 'training/datasets/management-name-errata-v2-en-fr'
    errata = checked_json(errata_path / 'manifest.json', ERRATA)
    review = checked_json(root / 'training/reports/target-label-review-20261014.json', REVIEW)
    if errata['parent_manifest_sha256'] != PARENT:
        raise ValueError('Corrections do not match the parent curriculum')
    for name, wanted in errata['helper_sha256'].items():
        if digest((root / 'training/scripts' / name).read_bytes()) != wanted:
            raise ValueError('Correction helper changed')
    if digest(Path(corrections.__file__).read_bytes()) != errata['generator_sha256']:
        raise ValueError('Correction generator changed')
    raw_replacements = (errata_path / 'train.replacements.jsonl').read_bytes()
    if digest(raw_replacements) != errata['files']['train.replacements.jsonl']:
        raise ValueError('Correction rows changed')
    payloads = {name: (source / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')}
    if any(digest(raw) != parent['files'][name] for name, raw in payloads.items()):
        raise ValueError('Frozen parent split changed')
    payloads['train.jsonl'] = corrected_payload(payloads['train.jsonl'], raw_replacements, errata['provenance'])
    metadata = native_metadata(parent, review, roots)
    applications = set(parent['applications'])
    rows = {name: checked_rows(raw, applications) for name, raw in payloads.items()}
    fresh_path = root / 'training/datasets/shared-v5r8-fresh-en-fr'
    fresh = checked_json(fresh_path / 'manifest.json', FRESH)
    if fresh['training_manifest_sha256'] != PARENT:
        raise ValueError('Unexpected frozen fresh-control lineage')
    fresh_key = 'training/datasets/shared-v5r8-fresh-en-fr/controls.eval.jsonl'
    fresh_info = {'sha256': fresh['files']['controls.eval.jsonl'], 'count': fresh['count']}
    held = {**parent['held_out'], fresh_key: fresh_info}
    excluded = set()
    for name, info in {**parent['historical_regression_held_out'], **held}.items():
        raw = (root / name).read_bytes()
        values = list(map(json.loads, raw.splitlines()))
        if digest(raw) != info['sha256'] or len(values) != info['count']:
            raise ValueError('Frozen evaluation changed')
        excluded.update(prompt_key(row) for row in values)
    keys = {name: {prompt_key(row) for row in values} for name, values in rows.items()}
    if keys['train.jsonl'] & keys['valid.jsonl'] or any(values & excluded for values in keys.values()):
        raise ValueError('Logical request overlap with validation or evaluation')
    manifest = deepcopy(parent)
    # These counts and source bindings describe this preparation, not R8's append.
    manifest.update(
        version=OUTPUT, status='PREPARATION ONLY; no model selected, training or evaluation executed',
        parent_manifest_sha256=PARENT,
        generator_sha256=digest(Path(__file__).read_bytes()),
        helper_sha256={'training/scripts/' + n: digest((root / 'training/scripts' / n).read_bytes()) for n in HELPERS},
        inherited_preparation={'version': SOURCE, 'manifest_sha256': PARENT,
                              'counts': parent['counts'], 'generator_sha256': parent['generator_sha256'],
                              'native_metadata': parent['native_metadata']},
        corrections={'version': errata_path.name, 'manifest_sha256': ERRATA,
                     'review_report_sha256': REVIEW, 'provenance': errata['provenance']},
        counts={'train': len(rows['train.jsonl']), 'valid': len(rows['valid.jsonl']),
                'replaced_targets': 6, 'unchanged_training_rows_byte_identical': 2333,
                'added': 0, 'by_application': dict(Counter(row['application'] for row in rows['train.jsonl']))},
        files={name: digest(raw) for name, raw in payloads.items()},
        native_metadata=metadata, held_out=held, held_out_count=sum(info['count'] for info in held.values()),
        fresh_controls={'manifest_sha256': FRESH, 'files': {fresh_key: fresh_info},
                        'scoring': 'Report separately from 438 original regressions; excluded from optimization and checkpoint selection.'},
        training_policy='Replace exactly six reviewed training targets. Preserve every input message, tool schema and trusted context, all other training bytes and every validation/evaluation byte. Model binding and server numerical/export rehearsal remain required; no automatic training or activation.',
        model_binding={'status': 'UNBOUND; wait for the active R8 controller and evaluation',
                       'later_stage_policy': 'Do not label this untrained curriculum as an accepted predecessor. Retention must bind the actual accepted model run; no extra full epoch is mandated by this preparation.'})
    manifest['source_manifest_sha256'] = {**parent['source_manifest_sha256'],
                                         SOURCE: PARENT, errata_path.name: ERRATA}
    return payloads, manifest


def prepare(roots, root=ROOT):
    output = root / 'training/datasets' / OUTPUT
    if output.exists():
        raise ValueError('Never overwrite a versioned curriculum')
    payloads, manifest = assemble(roots, root)
    output.mkdir()
    for name, raw in payloads.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
    with (output / 'manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for app in ('facturation', 'management_projet', 'design_workflow'):
        parser.add_argument('--' + app.replace('_', '-') + '-backend', type=Path, required=True)
    args = parser.parse_args()
    roots = {app: getattr(args, app + '_backend') for app in ('facturation', 'management_projet', 'design_workflow')}
    value = prepare(roots)
    print(json.dumps({'version': value['version'], 'counts': value['counts'], 'held_out': value['held_out_count'],
                      'training_started': False, 'model_bound': False}))
