"""Prepare training-only context contrasts from approved synthetic examples.

The same request must use the displayed identifier or clarify when its ordinal
is unavailable. No held-out outcome selects sources or changes a label.
"""
import argparse
import ast
from collections import Counter
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from chat_ai_assistant.clarifications import message_language
from chat_ai_assistant.selection_context import ordinal_target_matches, explicit_target_matches
from build_dialogue_v1 import digest, encode, write_dataset
from build_shared_v5r3 import key
from prepare_shared_v5r6 import current_request, function
from jsonschema import validate

BARE = ('project', 'client', 'supplier', 'expense', 'revenue', 'payment_schedule', 'budget_entry')
NOW = datetime(2031, 2, 3, tzinfo=timezone.utc)


def aliases_from_source(path):
    values = [ast.literal_eval(node.value) for node in ast.parse(path.read_text()).body
              if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ALIASES' for t in node.targets)]
    if len(values) != 1 or not isinstance(values[0], dict):
        raise ValueError('Expected one literal native ALIASES mapping')
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in values[0].items()):
        raise ValueError('Invalid native aliases')
    return values[0]


def context(row):
    return json.loads(row['messages'][0]['content'].split('Trusted context: ', 1)[1])


def state(ctx):
    return {'resource': ctx['previous_result_type'], 'ids': ctx['previous_result_identifiers'],
            'expires_at': (NOW + timedelta(hours=1)).isoformat()}


def generate(rows, aliases):
    selected, seen = [], set()
    for index, source in enumerate(rows):
        target = function(source)
        if source['application'] != 'management_projet' or target['name'] != 'prepare_change':
            continue
        ctx = context(source); args = target['arguments']; request = current_request(source)
        ids = ctx.get('previous_result_identifiers', [])
        if (ctx.get('current_resource') or ctx.get('current_identifier') or ctx.get('current_invoice_id')
                or not ids or len(ids) != ctx.get('previous_result_count')
                or ctx.get('previous_result_type') != args['resource'] or args['identifier'] not in ids):
            continue
        if explicit_target_matches(request, args['resource'], args['identifier'], aliases, BARE) is not None:
            continue
        if ordinal_target_matches(request, args['resource'], args['identifier'], state(ctx), NOW, aliases) is not True:
            continue
        identity = key(source['application'], request)
        if identity in seen:
            continue
        seen.add(identity)
        selected.append((index, source, ids.index(args['identifier'])))
    if not selected:
        raise ValueError('No independently verified ordinal training sources')
    result, provenance = [], []
    for index, source, position in selected:
        original = context(source); old_args = function(source)['arguments']; request = current_request(source)
        seed = hashlib.sha256(encode([source]).encode()).digest()
        ids = [10000 + int.from_bytes(hashlib.sha256(seed + bytes([i])).digest()[:4], 'big') % 900000
               for i in range(len(original['previous_result_identifiers']))]
        if len(set(ids)) != len(ids) or set(ids) & set(original['previous_result_identifiers']):
            raise ValueError('Synthetic identifier collision')
        variants = [('rebound', ids), ('missing_selection', [])]
        if position:
            variants.append(('out_of_range', ids[:position]))
        for kind, selected_ids in variants:
            row = deepcopy(source); ctx = deepcopy(original)
            ctx.update(previous_result_type=old_args['resource'] if selected_ids else None,
                       previous_result_count=len(selected_ids), previous_result_identifiers=selected_ids)
            prefix = row['messages'][0]['content'].split('Trusted context: ', 1)[0]
            row['messages'][0]['content'] = prefix + 'Trusted context: ' + json.dumps(ctx, ensure_ascii=False)
            if not selected_ids:
                row['tools'] = [t for t in row['tools'] if t['function']['name'] != 'previous_results']
            if kind == 'rebound':
                target = function(row); target['arguments']['identifier'] = ids[position]
                if ordinal_target_matches(request, old_args['resource'], ids[position], state(ctx), NOW, aliases) is not True:
                    raise ValueError('Rebound target differs from the native guard')
            else:
                if ordinal_target_matches(request, old_args['resource'], ids[position], state(ctx), NOW, aliases) is not False:
                    raise ValueError('Absent target must fail the native guard')
                target = function(row); target.clear()
                target.update(name='clarify', arguments={'reason': 'missing_details',
                    'language': message_language(request, original['interface_language'])})
            schema = [t['function']['parameters'] for t in row['tools'] if t['function']['name'] == target['name']]
            if len(schema) != 1:
                raise ValueError('Target schema missing or duplicated')
            validate(target['arguments'], schema[0])
            result.append(row)
            provenance.append({'source_index': index, 'source_sha256': hashlib.sha256(encode([source]).encode()).hexdigest(),
                               'kind': kind, 'position': position + 1, 'resource': old_args['resource']})
    keys = [json.dumps({'messages':r['messages'][:-1], 'tools':r['tools']}, sort_keys=True) for r in result]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate generated planner inputs')
    return result, provenance


def prepare(native_targets, output):
    parent = ROOT/'training/datasets/shared-v5r6-en-fr'; manifest = json.loads((parent/'manifest.json').read_text())
    for name in ('train.jsonl', 'valid.jsonl'):
        if digest(parent/name) != manifest['files'][name]:
            raise ValueError('Reviewed parent changed')
    train = list(map(json.loads, (parent/'train.jsonl').read_text().splitlines()))
    aliases = aliases_from_source(native_targets)
    extra, provenance = generate(train, aliases)
    excluded = {key(r['application'], current_request(r)) for r in map(json.loads, (parent/'valid.jsonl').read_text().splitlines())}
    # Exclusion checks only. No held-out prompt, context or label creates an example.
    frozen = ROOT/'training/datasets/shared-dialogue-v2-en-fr'; held = json.loads((frozen/'manifest.json').read_text())
    for name in held['inputs']:
        path = frozen/name
        if digest(path) != held['files'][name]:
            raise ValueError('Frozen exclusion set changed')
        for row in map(json.loads, path.read_text().splitlines()):
            excluded.add(key(context(row)['application'], current_request({'messages':row['messages']+[{}]})))
    if any(key(r['application'], current_request(r)) in excluded for r in extra):
        raise ValueError('Training source overlaps validation or evaluation request')
    payload = encode(extra)
    if re.search(r'[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+|(?:password|api_key|secret)\s*[:=]', payload, re.I):
        raise ValueError('Sensitive or out-of-scope training text')
    report = {'version': output.name, 'status': 'PREPARED ONLY; not trained or measured',
        'applications':['management_projet'], 'languages':['en','fr'], 'count':len(extra),
        'source_scenarios':len({p['source_index'] for p in provenance}),
        'categories':dict(Counter(p['kind'] for p in provenance)),
        'parent_manifest_sha256':digest(parent/'manifest.json'), 'source_training_sha256':digest(parent/'train.jsonl'),
        'exclusion_manifest_sha256':digest(frozen/'manifest.json'), 'native_target_source_sha256':digest(native_targets), 'native_aliases':aliases,
        'generator_sha256':digest(Path(__file__)),
        'helper_sha256':{n:digest(ROOT/n) for n in ['src/chat_ai_assistant/selection_context.py','src/chat_ai_assistant/clarifications.py','training/scripts/prepare_shared_v5r6.py','training/scripts/build_shared_v5r3.py','training/scripts/build_dialogue_v1.py']},
        'provenance':provenance,
        'policy':'Training-only contrasts. Source requests and field values are retained exactly from approved synthetic training, with rebound IDs, missing selection, or too-short selection. Native ordinal guard verifies labels. Correlated variants are not independent scenarios. Current training, validation and benchmark inputs remain unchanged. No optimizer, model download, production activation or acceptance follows preparation.'}
    write_dataset(output, {'train.jsonl':payload}, report)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-targets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=prepare(a.native_targets,a.output);print(json.dumps({k:result[k] for k in ('count','source_scenarios','categories','status')}))
