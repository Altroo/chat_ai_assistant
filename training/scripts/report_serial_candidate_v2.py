"""Keep R8 fresh controls separate in serial-stage acceptance reports.

Read-only evaluation analysis. Never starts training or activates a model.
The original reporter and all frozen training/evaluation inputs stay unchanged.
"""
import argparse
import ast
import types
import json
from pathlib import Path

import report_serial_candidate_v1 as previous
import model_acceptance
import report_dialogue_candidate as dialogue
from model_acceptance import FROZEN_EVALUATOR_SHA256
from report_dialogue_candidate import application, cases, read, sha

ROOT = Path(__file__).resolve().parents[2]
FRESH = 'training/datasets/shared-v5r8-fresh-en-fr/controls.eval.jsonl'
CLARIFICATIONS = 'src/chat_ai_assistant/clarifications.py'


def bound_scoring(driver_proof, clarifications):
    """Bind scorer dependencies without mutating imported modules or executing provider code."""
    proof = read(driver_proof)
    if proof.get('provider_sha256', {}).get(CLARIFICATIONS) != sha(clarifications):
        raise ValueError('Clarification renderer does not match attested provider')
    tree = ast.parse(clarifications.read_text())
    assignments = [node.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'MESSAGES' for target in node.targets)]
    if len(assignments) != 1:
        raise ValueError('Expected one literal clarification message table')
    messages = ast.literal_eval(assignments[0])
    reasons = {'missing_details', 'ambiguous_metric', 'unsupported'}
    if (not isinstance(messages, dict) or set(messages) != {'en', 'fr'} or
            any(not isinstance(value, dict) or set(value) != reasons or
                any(not isinstance(text, str) or not text for text in value.values())
                for value in messages.values())):
        raise ValueError('Unexpected clarification message table')

    def clone(function, namespace):
        return types.FunctionType(function.__code__, namespace, function.__name__, function.__defaults__)

    acceptance = dict(vars(model_acceptance))
    acceptance['clarification_message'] = lambda reason, language: messages[language][reason]
    frozen_assess = clone(model_acceptance.assess, acceptance)
    reporting = {**vars(dialogue), 'assess': frozen_assess}
    frozen_grouped = clone(dialogue.grouped, reporting)
    serial = {**vars(previous), 'assess': frozen_assess, 'grouped': frozen_grouped,
              'checked_set': clone(dialogue.checked_set, reporting)}
    serial['checked_run'] = clone(previous.checked_run, serial)
    return types.SimpleNamespace(assess=frozen_assess, grouped=frozen_grouped,
                                 build=clone(previous.build, serial))


def checked_groups(stage, data, root=ROOT):
    manifest, snapshots = previous.checked_manifest(stage, data, root)
    metadata = manifest.get('fresh_controls', {})
    source = root / Path(FRESH).parent / 'manifest.json'
    if metadata.get('manifest_sha256') != sha(source):
        raise ValueError('Fresh control manifest binding changed')
    fresh = read(source)
    expected = {FRESH: {'sha256': fresh['files']['controls.eval.jsonl'], 'count': 48}}
    if (metadata.get('files') != expected or
            manifest['held_out'].get(FRESH) != expected[FRESH] or
            fresh.get('count') != 48 or
            fresh.get('applications') != list(previous.BASE_APPLICATIONS) or
            fresh.get('languages') != ['en', 'fr']):
        raise ValueError('Fresh control scope or binding changed')
    rows = snapshots[FRESH]
    counts = {app: sum(application(row) == app for row in rows) for app in previous.BASE_APPLICATIONS}
    if counts != {app: 16 for app in previous.BASE_APPLICATIONS} or fresh.get('by_application') != counts:
        raise ValueError('Fresh controls require 16 cases per retained base application')
    if any({row['language'] for row in rows if application(row) == app} != {'en', 'fr'}
           for app in previous.BASE_APPLICATIONS):
        raise ValueError('Fresh controls require both languages for each base application')
    regression = {name: values for name, values in snapshots.items() if name != FRESH}
    if {application(row) for values in regression.values() for row in values} != set(manifest['applications']):
        raise ValueError('Regression group omits an application')
    return manifest, {'regression': regression, 'fresh_controls': {FRESH: rows}}


def targets(result):
    metrics = result['metrics']
    return (result['model_targets_passed'] and metrics['count'] > 0 and
            100 * metrics['counts']['action_matches'] >= 95 * metrics['count'])


def group_results(run, evidence, groups, evaluations, scoring):
    completion = run / 'evaluation-complete.json'
    if sha(completion) != evidence['completion_sha256']:
        raise ValueError('Completion changed during group analysis')
    completed = read(completion)
    output = {}
    for name, datasets in groups.items():
        snapshots, events = [], []
        for relative, rows in datasets.items():
            label = completed['sets'][relative]
            folder = (evaluations / label).resolve()
            if not folder.is_relative_to(evaluations.resolve()):
                raise ValueError('Evaluation evidence escapes its root')
            pin = completed['results'][relative]
            if (sha(folder / 'events.jsonl') != pin['events_sha256'] or
                    sha(folder / 'summary.json') != pin['summary_sha256']):
                raise ValueError('Recorded evaluation result changed during group analysis')
            snapshots.extend(rows)
            events.extend(cases(folder / 'events.jsonl'))
        assessment = scoring.assess(snapshots, events)
        by_app = scoring.grouped(snapshots, events)
        output[name] = {
            'assessment': assessment, 'by_application': by_app,
            'full_action_target_percent': 95,
            'targets_passed': targets(assessment) and all(targets(value) for value in by_app.values()),
        }
    if sha(completion) != evidence['completion_sha256']:
        raise ValueError('Completion changed during group analysis')
    return output


def not_regressed(before, after):
    old, new = before['metrics'], after['metrics']
    return (old['count'] == new['count'] and
            old['exact_arguments']['count'] == new['exact_arguments']['count'] and
            all(new['counts'][key] >= value for key, value in old['counts'].items()) and
            new['exact_arguments']['passed'] >= old['exact_arguments']['passed'])


def build(stage, data, baseline, candidate, evaluations, driver_proof, clarifications, root=ROOT):
    scoring = bound_scoring(driver_proof, clarifications)
    manifest_hash = sha(data / 'manifest.json')
    manifest, groups = checked_groups(stage, data, root)
    result = scoring.build(stage, data, baseline, candidate, evaluations, driver_proof, root)
    for key, run in (('baseline', baseline), ('candidate', candidate)):
        result[key]['groups'] = group_results(run, result[key], groups, evaluations, scoring)
    retained = previous.BASE_APPLICATIONS + previous.STAGES[:previous.STAGES.index(stage)]
    regression = {}
    for group_name in groups:
        before = result['baseline']['groups'][group_name]['by_application']
        after = result['candidate']['groups'][group_name]['by_application']
        regression[group_name] = {app: not_regressed(before[app], after[app])
                                  for app in retained if app in before}
    result['separate_group_targets_passed'] = all(
        value['targets_passed'] for value in result['candidate']['groups'].values())
    result['retained_group_application_nonregression'] = regression
    result['retained_groups_not_regressed'] = all(all(values.values()) for values in regression.values())
    result['model_acceptance_passed'] = (result['model_acceptance_passed'] and
        result['separate_group_targets_passed'] and result['retained_groups_not_regressed'])
    result['previous_report_script_sha256'] = sha(Path(previous.__file__))
    result['report_script_sha256'] = sha(Path(__file__))
    result['clarifications_sha256'] = sha(clarifications)
    result['fresh_controls_manifest_sha256'] = manifest['fresh_controls']['manifest_sha256']
    result['limitations'].append(
        'Original regressions and 48 R8 fresh controls are scored separately per application; '
        'each group also requires at least 95% full actions, with no retained-app count regression. '
        'Fresh controls cover the three base applications; later applications use their separate held-out sets.')
    if sha(data / 'manifest.json') != manifest_hash or result['manifest_sha256'] != manifest_hash:
        raise ValueError('Stage manifest changed during group analysis')
    # Recheck group inputs after evidence reads, without running inference.
    if checked_groups(stage, data, root) != (manifest, groups):
        raise ValueError('Frozen group inputs changed during analysis')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=previous.STAGES, required=True)
    for name in ('data', 'baseline', 'candidate', 'evaluations', 'driver-proof', 'clarifications', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if sha(ROOT / 'training/scripts/evaluate_snapshot.py') != FROZEN_EVALUATOR_SHA256:
        raise ValueError('Frozen evaluator changed')
    result = build(args.stage, args.data, args.baseline, args.candidate, args.evaluations, args.driver_proof, args.clarifications)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    print(json.dumps({'stage': args.stage, 'model_acceptance_passed': result['model_acceptance_passed'],
                      'separate_group_targets_passed': result['separate_group_targets_passed']}))


if __name__ == '__main__':
    main()
