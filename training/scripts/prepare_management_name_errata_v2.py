"""Extend immutable name-label corrections to two explicit project-name requests."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from jsonschema import validate
import prepare_management_name_errata as parent

ROOT, SOURCE = parent.ROOT, parent.SOURCE
OUTPUT = ROOT / 'training/datasets/management-name-errata-v2-en-fr'
PRIOR = '3caec977105c98adc000d85abd40200add6c98ada2cf30e8dc8c25cd63d231d8'
PROJECT_FILTER = '53f7ffe6a4aa09bed4d67dd975facb3a30110d6ac583524d73209c8eec58c7e1'
CHANGES = {
    968: ('Recherche le projet qui porte le nom « Facturation ».',
          'ed434c21ce0c6b2d1866ec4f65e2dd27f32bdfa8a1ff37db240f8165bae520e1'),
    969: ('Search for the project named “Facturation”.',
          'b952860eaf683abb608aeea60b7dc2c1eb85bda2fe316dbe3dcfdfccec90285a'),
}
EXPECTED = {'name': 'search_records', 'arguments': {'resource': 'project', 'project_name': 'Facturation'}}


def check_labels(rows):
    parent.check_labels(rows)
    requests = {text for text, _ in CHANGES.values()}
    found = set()
    for index, row in enumerate(rows):
        if row.get('application') != 'management_projet':
            continue
        text = parent.request(row)
        if text not in requests:
            continue
        calls = row['messages'][-1].get('tool_calls', [])
        if len(calls) != 1 or calls[0].get('function') != EXPECTED:
            raise ValueError(f'Known incorrect project-name target at row {index}')
        found.add(text)
    if found != requests:
        raise ValueError('Reviewed project-name examples missing from retained curriculum')
    return {'reviewed_requests': 6, 'known_name_targets_passed': True,
            'accuracy_measured': False, 'training_authorized': False}


def replacements(rows):
    values, provenance = parent.replacements(rows)
    for index, (text, original_hash) in CHANGES.items():
        old = rows[index]
        if (parent.row_digest(old) != original_hash or parent.request(old) != text or
                old['application'] != 'management_projet'):
            raise ValueError('Reviewed project-name row changed')
        value = deepcopy(old)
        value['messages'][-1]['tool_calls'][0]['function'] = deepcopy(EXPECTED)
        schema = next(t['function']['parameters'] for t in value['tools']
                      if t['function']['name'] == 'search_records')
        validate(EXPECTED['arguments'], schema)
        values.append(value)
        provenance.append({'source_index': index, 'source_row_sha256': original_hash,
                           'resource': 'project', 'old_filter': 'query', 'new_filter': 'project_name'})
    check_labels(values)
    return values, provenance


def prepare(backend):
    if OUTPUT.exists():
        raise ValueError('Never overwrite versioned corrections')
    old_raw = (parent.OUTPUT / 'manifest.json').read_bytes()
    if parent.digest(old_raw) != PRIOR:
        raise ValueError('Reviewed prior correction changed')
    old = json.loads(old_raw)
    for name, wanted in old['files'].items():
        if parent.digest((parent.OUTPUT / name).read_bytes()) != wanted:
            raise ValueError('Prior replacement rows changed')
    if parent.digest(Path(parent.__file__).read_bytes()) != old['generator_sha256']:
        raise ValueError('Reviewed prior generator changed')
    if parent.digest((SOURCE / 'manifest.json').read_bytes()) != parent.PARENT:
        raise ValueError('Reviewed parent manifest changed')
    source = json.loads((SOURCE / 'manifest.json').read_text())
    for name, wanted in source['files'].items():
        if parent.digest((SOURCE / name).read_bytes()) != wanted:
            raise ValueError('Reviewed parent split changed')
    native = {**parent.NATIVE, 'project/filters.py': PROJECT_FILTER}
    for name, wanted in native.items():
        if parent.digest((backend / name).read_bytes()) != wanted:
            raise ValueError('Reviewed native search implementation changed')
    values, provenance = replacements(list(map(json.loads, (SOURCE / 'train.jsonl').read_text().splitlines())))
    raw = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values).encode()
    result = deepcopy(old)
    result.update(version=OUTPUT.name, prior_correction_manifest_sha256=PRIOR,
        generator_sha256=parent.digest(Path(__file__).read_bytes()),
        helper_sha256={Path(parent.__file__).name: old['generator_sha256']},
        native_sources=native, replacement_count=6, unchanged_rows=2333, targets_changed=6,
        provenance=provenance, files={'train.replacements.jsonl': parent.digest(raw)},
        policy='Replace six indexed training targets in a new cumulative curriculum. Explicit customer/supplier/project name requests use client_name, supplier_name or project_name. Preserve all requests, history, tools, contexts, other rows, validation and held-out inputs. V1 remains historical evidence; V2 includes all its four corrections plus two project-name corrections. Active R8 is unchanged.',
        limitations=['Six confirmed name-only scope mismatches; generic initial lookups before rename remain unchanged.',
                     'Known-label checks are bounded, not a general semantic classifier.',
                     'No numerical training, export or model accuracy improvement is claimed.'])
    OUTPUT.mkdir()
    (OUTPUT / 'train.replacements.jsonl').write_bytes(raw)
    (OUTPUT / 'manifest.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument('--backend', type=Path)
    choice.add_argument('--check-data', type=Path)
    args = parser.parse_args()
    if args.check_data:
        rows = list(map(json.loads, (args.check_data / 'train.jsonl').read_text().splitlines()))
        print(json.dumps(check_labels(rows)))
    else:
        result = prepare(args.backend)
        print(json.dumps({key: result[key] for key in ('status', 'replacement_count', 'unchanged_rows')}))
