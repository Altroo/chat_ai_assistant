"""Read-only pre-training checks and a deterministic rehearsal selection.

Loads JSON and schemas only. Does not load weights, train, infer, or predict
accuracy. The selected training rows require a separate server rehearsal.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from jsonschema import validate
from training_schedule import complete_epoch_order


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def target(row):
    return row['messages'][-1]['tool_calls'][0]['function']


def model_input_key(row):
    # Only values consumed by the model define input identity.
    return encoded({'messages': row['messages'][:-1], 'tools': row['tools']})


def checked_rows(payload, applications):
    rows = [json.loads(line) for line in payload.splitlines()]
    if not rows or {row.get('application') for row in rows} != applications:
        raise ValueError('Every declared application must occur in each split')
    for index, row in enumerate(rows):
        messages = row.get('messages', [])
        if (len(messages) < 3 or messages[0].get('role') != 'system' or
                messages[-2].get('role') != 'user' or messages[-1].get('role') != 'assistant' or
                len(messages[-1].get('tool_calls', [])) != 1):
            raise ValueError(f'Invalid supervised message boundary at row {index}')
        if 'language' in row and row['language'] not in ('en', 'fr'):
            raise ValueError(f'Unsupported explicit language at row {index}')
        content = messages[0].get('content')
        if not isinstance(content, str) or 'Trusted context: ' not in content:
            raise ValueError(f'Missing trusted application context at row {index}')
        try:
            context = json.loads(content.split('Trusted context: ', 1)[1])
        except ValueError as exc:
            raise ValueError(f'Invalid trusted application context at row {index}') from exc
        if not isinstance(context, dict) or context.get('application') != row['application']:
            raise ValueError(f'Application metadata differs from trusted context at row {index}')
        definitions = [tool['function'] for tool in row['tools']]
        names = [definition['name'] for definition in definitions]
        if len(names) != len(set(names)):
            raise ValueError(f'Duplicate tool schema at row {index}')
        expected = target(row)
        offered = {definition['name']: definition['parameters'] for definition in definitions}
        if expected['name'] not in offered:
            raise ValueError(f'Target tool is not offered at row {index}')
        validate(expected['arguments'], offered[expected['name']])
    return rows


def features(row):
    action = target(row)
    app, arguments = row['application'], action['arguments']
    result = {(app, 'tool', action['name'])}
    for key in ('operation', 'reason'):
        if key in arguments:
            result.add((app, key, encoded(arguments[key])))
    if row.get('language') in ('en', 'fr'):
        result.add((app, 'explicit_language', row['language']))
    return result


def rehearsal(rows, maximum):
    if type(maximum) is not int or maximum < 1:
        raise ValueError('Positive rehearsal size required')
    # Collapse only exact model-input duplicates. Genuine history is preserved.
    unique = {}
    for index, row in enumerate(rows):
        key = model_input_key(row)
        unique.setdefault(key, index)
    candidates = sorted(unique.values(), key=lambda index: digest(encoded(rows[index]).encode()))
    coverage = {index: features(rows[index]) for index in candidates}
    required = set().union(*coverage.values())
    remaining, selected = set(required), []
    while remaining:
        best = max(candidates, key=lambda index: len(coverage[index] & remaining))
        if not coverage[best] & remaining or len(selected) >= maximum:
            raise ValueError('Rehearsal budget cannot cover declared tool/operation/reason groups')
        selected.append(best)
        remaining -= coverage[best]
        candidates.remove(best)
    # Interleave the selected applications without changing the chosen rows.
    selected = [selected[i] for i in complete_epoch_order([rows[i] for i in selected])]
    return {'row_indices': selected, 'count': len(selected),
            'by_application': dict(Counter(rows[i]['application'] for i in selected)),
            'covered_features': [list(value) for value in sorted(required)],
            'selected_rows_sha256': digest(encoded([rows[i] for i in selected]).encode()),
            'status': 'PREPARATION ONLY; server numerical and export rehearsal not executed',
            'limitations': [
                'Covers tool, operation and clarification-reason groups, not every argument combination.',
                'Language coverage is checked only where rows have explicit language metadata.',
                'Selection uses training rows only and preserves genuine history.',
                'This is a mechanics rehearsal proposal, not a validation set or accuracy forecast.']}


def audit(data, maximum_rehearsal=96, window=300):
    manifest_payload = (data / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_payload)
    applications = manifest.get('applications', [])
    if (not applications or len(applications) != len(set(applications)) or
            manifest.get('languages') != ['en', 'fr']):
        raise ValueError('Declared English/French application scope required')
    payloads = {split: (data / (split + '.jsonl')).read_bytes() for split in ('train', 'valid')}
    for split, payload in payloads.items():
        if digest(payload) != manifest.get('files', {}).get(split + '.jsonl'):
            raise ValueError('Dataset hash mismatch: ' + split)
    rows = {split: checked_rows(payload, set(applications)) for split, payload in payloads.items()}
    grouped = defaultdict(list)
    for split, values in rows.items():
        for index, row in enumerate(values):
            key = model_input_key(row)
            grouped[key].append((split, index, encoded(target(row))))
    if any(len({item[2] for item in values}) > 1 for values in grouped.values()):
        raise ValueError('Identical model inputs have contradictory training labels')
    if any(len({item[0] for item in values}) > 1 for values in grouped.values()):
        raise ValueError('Identical model inputs cross training and validation')
    order = complete_epoch_order(rows['train'])
    if sorted(order) != list(range(len(rows['train']))):
        raise ValueError('Training schedule omits or duplicates rows')
    if type(window) is not int or window < 1:
        raise ValueError('Positive schedule window required')
    schedule = [{'first_step': start + 1, 'last_step': min(start + window, len(order)),
                 'by_application': dict(Counter(rows['train'][i]['application'] for i in order[start:start + window]))}
                for start in range(0, len(order), window)]
    result = {
        'status': 'STATIC CHECKS PASSED; NUMERICAL REHEARSAL PENDING',
        'manifest_sha256': digest(manifest_payload),
        'input_sha256': {split: digest(payload) for split, payload in payloads.items()},
        'rows_checked': {split: len(values) for split, values in rows.items()},
        'exact_input_label_conflicts': 0, 'exact_input_cross_split_overlap': 0,
        'complete_epoch_schedule': schedule, 'rehearsal': rehearsal(rows['train'], maximum_rehearsal),
        'model_weights_loaded': False, 'training_executed': False, 'accuracy_estimated': False,
        'limitations': ['Exact input checks preserve all history and tool order; near-duplicate semantic independence is not established.',
                       'Schemas do not prove business-label correctness; native semantic checks and review remain required.',
                       'Tokenizer/loss-mask parity, numeric updates and export checks are separate required checks.'],
    }
    if (data / 'manifest.json').read_bytes() != manifest_payload or any(
            (data / (split + '.jsonl')).read_bytes() != payload for split, payload in payloads.items()):
        raise ValueError('Dataset changed during audit')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--maximum-rehearsal', type=int, default=96)
    args = parser.parse_args()
    result = audit(args.data, args.maximum_rehearsal)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'rows_checked': result['rows_checked'], 'rehearsal_count': result['rehearsal']['count'],
                      'status': result['status']}))


if __name__ == '__main__':
    main()
