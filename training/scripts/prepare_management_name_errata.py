"""Version four reviewed name-search target corrections, without touching R8.

The replacement rows are not extra examples. Replace their exact parent rows
in a future cumulative version; never append contradictory labels.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import validate

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'training/datasets/shared-v5r8-en-fr'
OUTPUT = ROOT / 'training/datasets/management-name-errata-v1-en-fr'
PARENT = '56f803ca7110ae78bc53c4a208a7dc7456819c024dc588109da46d7fb1520738'
NATIVE = {
    'chat_ai/tools.py': '4a34fe503ade55e048434ea1aae1a15a025a2578667d54e4ca35111da5d4f688',
    'chat_ai/resources.py': '3e8b0c1d816dc230ec7761fe482a90c2c5cd680ae1a786f5c70620706e73fb84',
}
CHANGES = {
    620: ('Recherche le client dont le nom contient SYN-Magnolia.', 'client', 'client_name',
          '595142b4809497ae1f85054b2d37c9d98922f5ae30003a650de071bc234f914a'),
    621: ('Search for the customer whose name contains SYN-Magnolia.', 'client', 'client_name',
          '71050933043e6ad6c196d7c493ec7d7bb860dbe9998829f79fcf84a88e840e09'),
    622: ('Recherche le fournisseur dont le nom contient SYN-Magnolia.', 'supplier', 'supplier_name',
          'bc835ff78f79ed53a5e7265d59bd8e113cc53caf3c91fa87ebbaa323c44264db'),
    623: ('Search for the supplier whose name contains SYN-Magnolia.', 'supplier', 'supplier_name',
          '9c78b9522b3e0c02e54038d1e2f4264fb4aa8d11e36750cedc6132889180acbf'),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def row_digest(row):
    return digest(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode())


def request(row):
    return row['messages'][-2]['content'].split('\nCurrent request: ', 1)[-1]


def expected(resource, field):
    return {'name': 'search_records', 'arguments': {'resource': resource, field: 'SYN-Magnolia'}}


def check_labels(rows):
    """Bounded known-label gate, not a general semantic classifier."""
    reviewed = {text: (resource, field) for text, resource, field, _ in CHANGES.values()}
    found = set()
    for index, row in enumerate(rows):
        if row.get('application') != 'management_projet':
            continue
        text = request(row)
        if text not in reviewed:
            continue
        calls = row['messages'][-1].get('tool_calls', [])
        if len(calls) != 1 or calls[0].get('function') != expected(*reviewed[text]):
            raise ValueError(f'Known incorrect name-search target at row {index}')
        found.add(text)
    if found != set(reviewed):
        raise ValueError('Reviewed name-search examples missing from retained curriculum')
    return {'reviewed_requests': len(found), 'known_name_targets_passed': True,
            'accuracy_measured': False, 'training_authorized': False}


def replacements(rows):
    if len(rows) != 2339:
        raise ValueError('Unexpected parent training count')
    values, provenance = [], []
    for index, (text, resource, field, original_hash) in CHANGES.items():
        old = rows[index]
        if (row_digest(old) != original_hash or request(old) != text or
                old['application'] != 'management_projet'):
            raise ValueError('Reviewed parent row changed')
        value = deepcopy(old)
        value['messages'][-1]['tool_calls'][0]['function'] = expected(resource, field)
        schema = next(t['function']['parameters'] for t in value['tools']
                      if t['function']['name'] == 'search_records')
        validate(expected(resource, field)['arguments'], schema)
        values.append(value)
        provenance.append({'source_index': index, 'source_row_sha256': original_hash,
                           'resource': resource, 'old_filter': 'query', 'new_filter': field})
    check_labels(values)
    return values, provenance


def prepare(backend, source=SOURCE, output=OUTPUT):
    if output.exists():
        raise ValueError('Never overwrite versioned corrections')
    if digest((source / 'manifest.json').read_bytes()) != PARENT:
        raise ValueError('Reviewed parent manifest changed')
    manifest = json.loads((source / 'manifest.json').read_text())
    for name, wanted in manifest['files'].items():
        if digest((source / name).read_bytes()) != wanted:
            raise ValueError('Reviewed parent split changed')
    for name, wanted in NATIVE.items():
        if digest((backend / name).read_bytes()) != wanted:
            raise ValueError('Reviewed native search implementation changed')
    rows = list(map(json.loads, (source / 'train.jsonl').read_text().splitlines()))
    values, provenance = replacements(rows)
    raw = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values).encode()
    result = {
        'version': output.name, 'languages': ['en', 'fr'], 'applications': ['management_projet'],
        'parent_manifest_sha256': PARENT, 'parent_training_sha256': manifest['files']['train.jsonl'],
        'unchanged_validation_sha256': manifest['files']['valid.jsonl'],
        'generator_sha256': digest(Path(__file__).read_bytes()), 'native_sources': NATIVE,
        'source_rows': 2339, 'replacement_count': 4, 'unchanged_rows': 2335,
        'targets_changed': 4, 'requests_changed': 0, 'tools_changed': 0, 'context_changed': 0,
        'provenance': provenance, 'files': {'train.replacements.jsonl': digest(raw)},
        'status': 'PREPARED replacements; not assembled into a cumulative dataset or trained',
        'policy': 'Replace the four indexed training targets in a separately versioned future curriculum. Name-only requests use client_name or supplier_name, rather than the multi-field query. All messages, history, tools and context stay identical. Active R8, validation, held-out cases and historical scores stay unchanged.',
        'limitations': ['The semantic review covered 61 non-dated Management Projet search rows.',
                       'The known-label gate covers these four requests and does not prove all labels correct.',
                       'Preparation and native-source checks do not establish model accuracy.'],
    }
    output.mkdir()
    (output / 'train.replacements.jsonl').write_bytes(raw)
    (output / 'manifest.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
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
