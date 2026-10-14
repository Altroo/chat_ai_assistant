"""Version queued native wording corrections without changing frozen datasets.

No database, model or optimizer access. Questions become explicit about actual
native semantics; actions and splits remain unchanged. Old evaluation questions
remain historical evidence, and revised scores require a fresh bound baseline.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    'contrat': ('contracts', 'fdf52c310384eff6710c7cfc580f027783276b6d85ea559571136cff53b75397'),
    'gestion_magasin': ('gestion-magasin', '2ce7270c427ae6c3ae337fb15856d5ded08aea35277c95d0fe2096554d5241cd'),
}
REPLACEMENTS = {
    'contrat': {
        '/voir les contrats de Démo Acacia concernant peinture.':
            '/voir les contrats du client Démo Acacia concernant peinture.',
        '/search contracts for Démo Acacia concerning peinture.':
            '/search contracts for customer Démo Acacia concerning peinture.',
        'Supprime le contrat de Démo Acacia, je choisirai le bon résultat.':
            'Supprime le contrat du client Démo Acacia, je choisirai le bon résultat.',
        'Delete the contract for Démo Acacia; I will choose the matching result.':
            'Delete the contract for customer Démo Acacia; I will choose the matching result.',
    },
    'gestion_magasin': {
        'Donne le montants payés aujourd’hui pour le magasin actif, aujourd’hui.':
            'Donne le total des montants payés des ventes créées aujourd’hui, confirmées et actuellement marquées payées, pour le magasin actif.',
        'Give the amounts paid today for the active store, today.':
            'Give the total paid amounts on confirmed sales created today and currently marked paid, for the active store.',
        'Pour le magasin sélectionné, montants payés aujourd’hui à la date actuelle ?':
            'Pour le magasin sélectionné, quel est le total des montants payés sur les ventes créées aujourd’hui, confirmées et actuellement marquées payées ?',
        'For the selected store, amounts paid today as of the current date?':
            'For the selected store, what is the total paid amount on sales created today that are confirmed and currently marked paid?',
    },
}
EXPECTED_COUNTS = {
    'contrat': {'train.jsonl': 4, 'valid.jsonl': 0, 'train.eval.jsonl': 4, 'valid.eval.jsonl': 0, 'test.eval.jsonl': 0},
    'gestion_magasin': {'train.jsonl': 3, 'valid.jsonl': 0, 'train.eval.jsonl': 2, 'valid.eval.jsonl': 0, 'test.eval.jsonl': 2},
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_request(text, application):
    for old, new in REPLACEMENTS[application].items():
        if text == old or text.endswith('\nCurrent request: ' + old):
            return text[:-len(old)] + new
    return text


def prepare(application, backend):
    prefix, parent_hash = SOURCES[application]
    source = ROOT / 'training/datasets' / (prefix + '-dialogue-v3-en-fr')
    output = source.with_name(prefix + '-dialogue-v4-en-fr')
    if output.exists():
        raise ValueError('Never overwrite versioned native corrections')
    if sha(source / 'manifest.json') != parent_hash:
        raise ValueError('Reviewed source manifest changed')
    prior = json.loads((source / 'manifest.json').read_text())
    sys.path[:0] = [str(ROOT / 'src'), str(backend)]
    package = 'contracts' if application == 'contrat' else 'gestion_magasin'
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', package + '_backend.settings_release_test')
    from django.db.backends.base.base import BaseDatabaseWrapper
    def deny_database(*args, **kwargs):
        raise RuntimeError('Native metadata correction cannot access a database')
    BaseDatabaseWrapper.ensure_connection = deny_database
    import django
    django.setup()
    from chat_ai import planner, tools
    from chat_ai_assistant.planning_messages import planning_messages
    from chat_ai_assistant.clarifications import CLARIFICATION_SCHEMA
    from training_contracts import CLARIFICATION_DESCRIPTION
    from jsonschema import validate
    from prepare_serial_dialogue_v6 import logical_prompt, prompt_key

    clarify = {'type': 'function', 'function': {
        'name': 'clarify', 'description': CLARIFICATION_DESCRIPTION, 'parameters': CLARIFICATION_SCHEMA}}
    registry = tools.registry()
    payloads, counts, changes, keys = {}, {}, {}, {}
    for name, wanted in EXPECTED_COUNTS[application].items():
        if sha(source / name) != prior['files'][name]:
            raise ValueError('Reviewed source split changed')
        original = [json.loads(line) for line in (source / name).read_text().splitlines()]
        rows, changed = [], []
        evaluation = name.endswith('.eval.jsonl')
        for index, old in enumerate(original):
            row = deepcopy(old)
            user_index = -1 if evaluation else -2
            text = row['messages'][user_index]['content']
            replacement = replace_request(text, application)
            if text != replacement:
                changed.append(index)
            row['messages'][user_index]['content'] = replacement
            context = json.loads(row['messages'][0]['content'].split('Trusted context: ', 1)[1])
            row['messages'][0] = planning_messages(planner.SYSTEM, context, 'Metadata only')[0]
            selected = planner.shortlist(logical_prompt(row['messages']), registry.permitted(set(context['capabilities'])), context)
            schemas = [tool.schema() for tool in selected]
            expected = row['expected'] if evaluation else {
                'tool': row['messages'][-1]['tool_calls'][0]['function']['name'],
                'arguments': row['messages'][-1]['tool_calls'][0]['function']['arguments']}
            definitions = {tool['function']['name']: tool['function']['parameters'] for tool in schemas + [clarify]}
            validate(expected['arguments'], definitions[expected['tool']])
            if evaluation:
                row['offered_tools'] = [tool.name for tool in selected]
                row['offered_tool_schemas'] = schemas
            else:
                row['tools'] = schemas + [clarify]
            rows.append(row)
        if len(changed) != wanted:
            raise ValueError('Unexpected corrected request count: ' + name)
        payloads[name] = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows)
        counts[name] = len(rows)
        changes[name] = changed
        keys[name] = {prompt_key(row) for row in rows}
    if keys['train.jsonl'] & keys['valid.jsonl'] or (keys['train.jsonl'] | keys['valid.jsonl']) & keys['test.eval.jsonl']:
        raise ValueError('Corrected requests cross dataset splits')
    native_names = list(prior['native_sources'])
    if application == 'gestion_magasin':
        native_names += ['chat_ai/knowledge/store-finance.json', 'reporting/views.py']
    manifest = {
        'version': output.name, 'application': application, 'languages': ['en', 'fr'],
        'source_dataset': source.name, 'source_manifest_sha256': parent_hash,
        'source_files': prior['files'], 'counts': prior['counts'], 'row_counts': counts,
        'changed_request_indices': changes, 'targets_changed': 0, 'splits_changed': 0,
        'native_sources': {name: sha(backend / name) for name in native_names},
        'generator_sha256': sha(Path(__file__)),
        'files': {name: hashlib.sha256(raw.encode()).hexdigest() for name, raw in payloads.items()},
        'status': 'PREPARED; native metadata and request corrections, not trained or evaluated',
        'policy': 'Preserve original sources and historical scores. Rebind native metadata, retain history, targets and split order. Revised evaluation questions change interpretation and need a separately measured baseline/candidate comparison; do not rescore old predictions. Do not train from the superseded queued data.',
    }
    output.mkdir()
    for name, raw in payloads.items():
        (output / name).write_text(raw)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application', choices=SOURCES, required=True)
    parser.add_argument('--backend', type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.application, args.backend)
    print(json.dumps({'version': report['version'], 'changes': report['changed_request_indices'], 'training_started': False}))
