"""Version three reviewed benchmark corrections without rewriting old results.

This prepares evaluation inputs only. It never reads candidate predictions,
changes training data, runs inference, alters acceptance gates or deploys.
"""
from copy import deepcopy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'training/datasets/shared-dialogue-v1-en-fr'
OUTPUT = ROOT / 'training/datasets/shared-dialogue-v2-en-fr'
SOURCE_MANIFEST_SHA256 = '5bfa383c276e28cf3a78a20788d1b51fd7769563243aa26f33fcab7fed9b13e3'
EVIDENCE = {
    'training/reports/shared-v5r6-date-label-errata.json': 'eb4aa7000c1f3354f3ea9dc2f25bc56557a23628e92ce145de909e3eb6f69d1d',
    'training/reports/shared-v5r5-clarification-audit.json': 'e3563a2a9ed4591d5f35a61df3690a09fed5a1a12a7d6128a10281b80950799a',
}
DATE_REQUESTS = {
    'search-schedule-fr': 'Échéances du projet Cobalt avant le 2026-11-01.',
    'search-schedule-en': 'Payment schedules for project Cobalt before 2026-11-01.',
}
SUPPLIER_ID = 'management-projet-refinement-v2-en-fr-supplier-metric-fr'
SUPPLIER_OLD = 'Earlier user messages (background only): ["Hello"]\nCurrent request: Pour Fictif Marbre, calcule le total des dépenses du mois précédent.'
SUPPLIER_NEW = 'Earlier user messages (background only): ["Hello"]\nCurrent request: Pour le fournisseur Fictif Marbre, calcule le total des dépenses du mois précédent.'
CHANGED_IDS = set(DATE_REQUESTS) | {SUPPLIER_ID}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def correct(row):
    """Apply only the exact documented correction; preserve every other field."""
    value = deepcopy(row)
    if row['id'] in DATE_REQUESTS:
        require(row['messages'][-1]['content'] == DATE_REQUESTS[row['id']], 'Date request drifted')
        expected = {'tool': 'search_records', 'arguments': {
            'resource': 'payment_schedule', 'project_name': 'Cobalt', 'date_to': '2026-11-01'}}
        require(row['expected'] == expected, 'Date target drifted')
        # Native date_to uses an inclusive due_date__lte predicate on a DateField.
        value['expected']['arguments']['date_to'] = (date(2026, 11, 1) - timedelta(days=1)).isoformat()
    elif row['id'] == SUPPLIER_ID:
        require(row['messages'][-1]['content'] == SUPPLIER_OLD, 'French supplier request drifted')
        require(row['expected'] == {'tool': 'clarify', 'arguments': {
            'reason': 'unsupported', 'language': 'fr'}}, 'Supplier target drifted')
        # Match the existing English request's explicit supplier scope. The native
        # financial_summary tool supports project scope, not supplier scope.
        value['messages'][-1]['content'] = SUPPLIER_NEW
    return value


def prepare(source=SOURCE, output=OUTPUT):
    require(not output.exists(), 'Never overwrite a versioned benchmark')
    require(sha(source / 'manifest.json') == SOURCE_MANIFEST_SHA256, 'Parent manifest changed')
    manifest = json.loads((source / 'manifest.json').read_text())
    require(manifest['count'] == 438 and len(manifest['inputs']) == 15, 'Unexpected parent scope')
    for relative, expected in EVIDENCE.items():
        require(sha(ROOT / relative) == expected, 'Reviewed errata evidence changed')
    for name, expected in manifest['files'].items():
        require(Path(name).name == name, 'Unsafe input filename')
        require(sha(source / name) == expected, 'Parent input changed')
    payloads, inputs, changed, all_ids, changes = {}, {}, [], [], []
    for name in manifest['inputs']:
        raw_lines = (source / name).read_text().splitlines(keepends=True)
        lines, ids = [], []
        for raw in raw_lines:
            row = json.loads(raw)
            require(row['language'] in ('en', 'fr'), 'Unexpected language')
            all_ids.append(row['id'])
            value = correct(row)
            if value != row:
                ids.append(row['id'])
                changed.append(value)
                changes.append({'id': row['id'], 'file': name,
                                'change': 'expected_inclusive_date_to' if row['id'] in DATE_REQUESTS else 'explicit_french_supplier_scope'})
                lines.append(json.dumps(value, ensure_ascii=False) + '\n')
            else:
                lines.append(raw)
        require(len(raw_lines) == manifest['inputs'][name]['count'], 'Parent count changed')
        payloads[name] = ''.join(lines)
        inputs[name] = {'source': str(Path('training/datasets') / SOURCE.name / name),
                        'source_sha256': manifest['files'][name], 'count': len(lines), 'changed_ids': ids}
    require(len(all_ids) == len(set(all_ids)) == 438, 'Duplicate or missing cases')
    require({row['id'] for row in changed} == CHANGED_IDS and len(changed) == 3, 'Unexpected correction scope')
    payloads['changed.eval.jsonl'] = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in changed)
    report = {
        'version': 'shared-dialogue-v2-en-fr', 'languages': manifest['languages'],
        'applications': manifest['applications'], 'parent_manifest_sha256': SOURCE_MANIFEST_SHA256,
        'generator_sha256': sha(Path(__file__)), 'reviewed_errata_sha256': EVIDENCE,
        'planning_messages_sha256': manifest['planning_messages_sha256'],
        'evaluator_sha256': sha(ROOT / 'training/scripts/evaluate_snapshot.py'),
        'acceptance_sha256': sha(ROOT / 'training/scripts/model_acceptance.py'),
        'count': 438, 'unchanged_count': 435, 'changed_count': 3, 'inputs': inputs, 'changes': changes,
        'status': 'PREPARED; not measured, trained or accepted',
        'policy': 'Separate benchmark version. Preserve all historical V1 inputs and scores. Same 438 cases, tool schemas, context, EN/FR scope and acceptance thresholds. Correct only two exclusive-before date labels and the documented missing French supplier noun. No historical candidate is re-scored as if the inputs were unchanged. Before using V2 for acceptance, bind its own baseline/candidate evidence and report V1 and V2 separately. Changed cases require fresh measurement; unchanged-case reuse requires exact input/provider/model evidence. No combined performance claim from reused results.',
        'limitations': ['These repeatedly inspected regressions are not fresh blind certification.',
                       'Dataset preparation does not establish model quality, backend authorization or deployment readiness.'],
        'files': {name: hashlib.sha256(raw.encode()).hexdigest() for name, raw in payloads.items()},
    }
    output.mkdir()
    for name, raw in payloads.items():
        (output / name).write_text(raw)
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    result = prepare()
    print(json.dumps({key: result[key] for key in ('version', 'count', 'unchanged_count', 'changed_count', 'status')}))
