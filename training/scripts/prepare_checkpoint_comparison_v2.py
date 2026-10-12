"""Freeze a functional fallback comparison without inference or model selection.

The active R6 training and original loss-based selection remain unchanged.
Run a comparison only after successful complete training and failed acceptance.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from compare_saved_checkpoints import encode, select

ROOT = Path(__file__).resolve().parents[2]
STEPS = [0, 300, 600, 900, 1200, 1500, 1800, 1969]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output):
    if output.exists():
        raise ValueError('Never overwrite a frozen checkpoint comparison')
    data = ROOT / 'training/datasets/shared-v5r6-en-fr'
    manifest = json.loads((data / 'manifest.json').read_text())
    reference = ROOT / 'training/reports/shared-v5r5-checkpoint-selection-policy.json'
    prior = json.loads(reference.read_text())
    for name in ('train.jsonl', 'valid.jsonl'):
        if digest(data / name) != manifest['files'][name]:
            raise ValueError('Current dataset changed')
    if (manifest['counts']['train'] != 1969 or manifest['counts']['valid'] != 275
            or digest(data / 'valid.jsonl') != prior['source_validation_sha256']):
        raise ValueError('Validation comparison must retain the exact existing inputs')
    training_rows = list(map(json.loads, (data / 'valid.jsonl').read_text().splitlines()))
    original = ROOT / 'training/datasets/shared-v5r3-en-fr/valid.jsonl'
    augmentation = json.loads((ROOT / 'training/datasets/shared-v5r4-en-fr/manifest.json').read_text())['augmentation']['valid']
    groups = list(range(len(original.read_text().splitlines()))) + [row['source_index'] for row in augmentation]
    if len(training_rows) != 275 or len(groups) != 275:
        raise ValueError('Incomplete validation inputs or scenario grouping')
    rows = []
    for index, (source, group) in enumerate(zip(training_rows, groups)):
        target = source['messages'][-1]['tool_calls'][0]['function']
        rows.append({'id': f'validation-{index:03}', 'category': source['application'],
                     'language': 'en_fr_unlabeled', 'scenario_group': f"{source['application']}-{group:03}",
                     'messages': source['messages'][:-1],
                     'offered_tool_schemas': [t for t in source['tools'] if t['function']['name'] != 'clarify'],
                     'expected': {'tool': target['name'], 'arguments': target['arguments']}})
    raw = encode(rows)
    envelope_sha = hashlib.sha256(raw.encode()).hexdigest()
    if envelope_sha != prior['evaluation_sha256']:
        raise ValueError('Reconstructed validation envelope differs from the frozen reference')
    for key, path in (('evaluator_sha256', 'training/scripts/evaluate_snapshot.py'),
                      ('acceptance_sha256', 'training/scripts/model_acceptance.py')):
        if digest(ROOT / path) != prior[key]:
            raise ValueError('Frozen scoring implementation changed')
    policy = {
        'version': 'shared-v5r6-functional-validation-v1',
        'dataset_manifest_sha256': digest(data / 'manifest.json'),
        'training_sha256': digest(data / 'train.jsonl'),
        'source_validation_sha256': digest(data / 'valid.jsonl'),
        'evaluation_sha256': envelope_sha,
        'reference_policy_sha256': digest(reference),
        'script_sha256': digest(Path(__file__)),
        'selection_script_sha256': digest(ROOT / 'training/scripts/compare_saved_checkpoints.py'),
        'evaluator_sha256': prior['evaluator_sha256'],
        'acceptance_sha256': prior['acceptance_sha256'],
        'candidate_steps': STEPS,
        'rows': 275, 'underlying_scenarios': 222,
        'selection': prior['selection'],
        'scoring': prior['scoring'],
        'prerequisites': [
            'Successful complete R6 training, unchanged provenance and all candidate artifacts verified.',
            'Run only if the original candidate remains unaccepted; no concurrent optimization.',
            'Each candidate including the baseline requires the same full validation inputs and inference settings.',
            'Reuse prior measurements only for identical artifacts, inputs, provider, settings and complete results.',
            'Only the selected changed candidate may advance to the unchanged 438-case acceptance suite.',
            'No automatic activation or subsequent-application training follows validation selection.',
        ],
        'limitations': prior['limitations'],
    }
    output.mkdir(parents=True)
    (output / 'validation.eval.jsonl').write_text(raw)
    (output / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n')
    return policy


def bind_completed_training(policy, report):
    """Bind measured validation losses; never accept an incomplete or different run."""
    expected = set(policy['candidate_steps'])
    config = report.get('training_config', {})
    metrics = report.get('steps_metrics', [])
    if (report.get('steps') != 1969 or config.get('complete_epochs') != 1
            or config.get('checkpoint_interval_steps') != 300
            or config.get('validation_interval_steps') != 300
            or report.get('dataset_sha256') != policy['training_sha256']
            or report.get('validation_sha256') != policy['source_validation_sha256']
            or [r.get('step') for r in metrics] != list(range(1, 1970))):
        raise ValueError('Complete exact training coverage is required')
    history = report.get('validation_history', [])
    if len(history) != len(expected) or {r.get('step') for r in history} != expected:
        raise ValueError('Every predetermined checkpoint requires measured validation')
    losses = {}
    for row in history:
        loss = row.get('loss', {}).get('macro')
        if type(loss) not in (int, float) or not math.isfinite(loss) or loss < 0:
            raise ValueError('Finite validation losses are required')
        losses[row['step']] = loss
    return {**policy, 'candidates': [{'step': step, 'validation_macro_loss': losses[step]}
                                   for step in policy['candidate_steps']]}


def select_completed(policy, report, rows, results):
    """Use the existing functional scorer; validation never establishes acceptance."""
    for key, relative in [('script_sha256', 'training/scripts/prepare_checkpoint_comparison_v2.py'),
                          ('selection_script_sha256', 'training/scripts/compare_saved_checkpoints.py'),
                          ('evaluator_sha256', 'training/scripts/evaluate_snapshot.py'),
                          ('acceptance_sha256', 'training/scripts/model_acceptance.py')]:
        if digest(ROOT / relative) != policy[key]:
            raise ValueError('Pinned scoring implementation changed')
    if policy['candidate_steps'] != STEPS:
        raise ValueError('Candidate shortlist changed')
    return select(bind_completed_training(policy, report), rows, results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.output), indent=2))
