"""Clarify six English collection-summary prompts; preserve every target."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from audit_training_inputs import checked_rows
from prepare_coverage_contrasts_v1 import check_exclusions

ROOT = Path(__file__).resolve().parents[2]
PARENT = 'shared-v5r10-en-fr'
PARENT_SHA = 'd76e13b44f6e679b4bfa792c9020cd20f37abaf5a690dfdbfcf6de5d37ca32a6'
VERSION = 'shared-v5r11-en-fr'
OLD = 'Current request: Give the collected payments in '
NEW = 'Current request: Give the total amount collected in '


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correct(payload):
    lines = payload.splitlines(keepends=True)
    changes, updated = [], []
    for index, line in enumerate(lines):
        row = json.loads(line)
        content = row['messages'][-2].get('content', '')
        if OLD not in content:
            continue
        function = row['messages'][-1]['tool_calls'][0]['function']
        if (content.count(OLD) != 1 or row.get('language') != 'en' or
                row['application'] != 'facturation' or
                row.get('curriculum_category') != 'custom_currency_summary' or
                function['name'] != 'financial_summary' or
                function['arguments'].get('metric') != 'collected' or
                function['arguments'].get('period') != 'custom'):
            raise ValueError('Unexpected collection-summary source row')
        revised = deepcopy(row)
        revised['messages'][-2]['content'] = content.replace(OLD, NEW, 1)
        output = (json.dumps(revised, ensure_ascii=False) + '\n').encode()
        lines[index] = output
        changes.append({'row_index': index, 'source_row_sha256': hashlib.sha256(line).hexdigest(),
                        'revised_row_sha256': hashlib.sha256(output).hexdigest()})
        updated.append(revised)
    combinations = {(r['messages'][-1]['tool_calls'][0]['function']['arguments']['currency'],
                     r['messages'][-1]['tool_calls'][0]['function']['arguments']['date_from']) for r in updated}
    if len(changes) != 6 or combinations != {(c, d) for c in ('MAD', 'EUR', 'USD') for d in ('2034-02-04', '2036-09-07')}:
        raise ValueError('Exactly six reviewed collection prompts are required')
    return b''.join(lines), changes, updated


def assemble(roots):
    parent = ROOT/'training/datasets'/PARENT
    if sha(parent/'manifest.json') != PARENT_SHA:
        raise ValueError('Reviewed parent manifest changed')
    manifest = json.loads((parent/'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        if sha(parent/name) != expected:
            raise ValueError('Reviewed parent payload changed')
    for name, expected in manifest['helper_sha256'].items():
        if sha(ROOT/name) != expected:
            raise ValueError('Reviewed parent helper source changed')
    if set(roots) != set(manifest['native_metadata']):
        raise ValueError('All three native roots are required')
    for app, files in manifest['native_metadata'].items():
        for name, expected in files.items():
            if sha(roots[app]/name) != expected:
                raise ValueError('Native source changed')
    revised, changes, updated = correct((parent/'train.jsonl').read_bytes())
    check_exclusions(manifest, updated)
    checked_rows(revised, set(manifest['applications']))
    payloads = {'train.jsonl': revised, 'valid.jsonl': (parent/'valid.jsonl').read_bytes()}
    manifest.update(version=VERSION, status='PREPARATION ONLY; six prompt clarifications, no full training',
        parent_manifest_sha256=PARENT_SHA, generator_sha256=sha(Path(__file__)),
        source_manifest_sha256={**manifest['source_manifest_sha256'], PARENT: PARENT_SHA},
        files={name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()},
        counts={**manifest['counts'], 'retained_parent_rows_byte_identical': 2413,
                'corrected_parent_rows': 6, 'added': 0},
        training_policy='Retain all R10 targets, tools, validation and evaluation inputs. Clarify exactly six English collection-summary requests. Complete the R10 numerical/export rehearsal and targeted checks of these wording changes before a full continuation.',
        wording_corrections={'count': 6, 'reason': 'Make the total amount explicit rather than implying a payment list.',
                             'targets_unchanged': True, 'rows': changes},
        model_binding={'status': 'UNBOUND; R10 rehearsal and export comparison must finish.',
                       'changed_prompt_validation': 'Metadata and targeted serving checks are required before a full run.',
                       'later_stage_policy': 'Use the actual accepted model and complete curriculum for later applications.'})
    return payloads, manifest


def prepare(roots):
    output = ROOT/'training/datasets'/VERSION
    if output.exists():
        raise ValueError('Never replace a versioned dataset')
    payloads, manifest = assemble(roots)
    output.mkdir()
    for name, raw in payloads.items():
        with (output/name).open('xb') as f: f.write(raw)
    with (output/'manifest.json').open('x') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False); f.write('\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for app in ('facturation', 'management_projet', 'design_workflow'):
        parser.add_argument('--'+app.replace('_', '-')+'-backend', type=Path, required=True)
    args = parser.parse_args()
    result = prepare({a: getattr(args, a+'_backend') for a in ('facturation', 'management_projet', 'design_workflow')})
    print(json.dumps({'version': result['version'], 'changed_prompts': 6, 'training_started': False}))
