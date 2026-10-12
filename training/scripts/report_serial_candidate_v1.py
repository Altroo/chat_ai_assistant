"""Compare complete serial-stage evaluations without running models or tools.

The launch controller supplies independently attested baseline/candidate evidence.
This report cannot authorize another training run or production activation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from model_acceptance import assess, FROZEN_EVALUATOR_SHA256
from report_dialogue_candidate import read, sha, application, checked_set, checked_process, grouped
from serial_scope_v2 import BASE_APPLICATIONS, STAGES

ROOT = Path(__file__).resolve().parents[2]


def checked_manifest(stage, data, root=ROOT):
    if stage not in STAGES:
        raise ValueError('Unexpected serial stage')
    manifest = read(data / 'manifest.json')
    apps = list(BASE_APPLICATIONS + STAGES[:STAGES.index(stage) + 1])
    if manifest.get('applications') != apps or manifest.get('languages') != ['en', 'fr']:
        raise ValueError('Serial application/language scope changed')
    frozen = manifest.get('held_out', {})
    if not frozen:
        raise ValueError('No frozen evaluation sets')
    snapshots = {}
    for relative, info in frozen.items():
        path = (root / relative).resolve()
        if not path.is_relative_to((root / 'training/datasets').resolve()):
            raise ValueError('Evaluation input escapes approved datasets')
        if sha(path) != info['sha256']:
            raise ValueError('Frozen evaluation input changed')
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if len(rows) != info['count'] or not rows:
            raise ValueError('Frozen set count changed')
        if any(row['language'] not in ('en', 'fr') or application(row) not in apps for row in rows):
            raise ValueError('Unexpected evaluation application/language')
        snapshots[relative] = rows
    rows = [row for values in snapshots.values() for row in values]
    if len(rows) != manifest.get('held_out_count') or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Incomplete or duplicate frozen cases')
    if {application(row) for row in rows} != set(apps):
        raise ValueError('A retained application has no evaluation cases')
    if any({row['language'] for row in rows if application(row) == app} != {'en', 'fr'} for app in apps):
        raise ValueError('Every application requires English and French evaluation cases')
    return manifest, snapshots


def checked_artifacts(artifacts):
    if set(artifacts) != {'weights', 'tokenizer', 'config', 'runtime'}:
        raise ValueError('Incomplete model artifact attestation')
    def digest(value):
        return isinstance(value, str) and len(value) == 64 and all(char in '0123456789abcdef' for char in value)
    for group in artifacts.values():
        entries = group.get('files')
        if not isinstance(entries, dict) or not entries or not digest(group.get('sha256')):
            raise ValueError('Incomplete artifact file evidence')
        for name, value in entries.items():
            path = Path(name)
            if (not name or path.is_absolute() or '..' in path.parts or not isinstance(value, dict) or
                    set(value) != {'sha256', 'size_bytes'} or not digest(value.get('sha256')) or
                    type(value.get('size_bytes')) is not int or value['size_bytes'] < 1):
                raise ValueError('Invalid artifact file evidence')
        canonical = json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()
        if hashlib.sha256(canonical).hexdigest() != group['sha256']:
            raise ValueError('Artifact group digest does not match its file evidence')


def checked_run(data, manifest, run, evaluations, driver_proof, root=ROOT):
    completed = read(run / 'evaluation-complete.json')
    binding = read(run / 'evaluation-binding.json')
    required = ('model_id', 'manifest_sha256', 'provider_sha256', 'driver_sha256')
    if any(binding.get(key) != completed.get(key) for key in required):
        raise ValueError('Completion and launch binding differ')
    if completed.get('manifest_sha256') != sha(data / 'manifest.json'):
        raise ValueError('Evaluation belongs to another frozen stage')
    proof = read(driver_proof)
    if (not completed.get('driver_sha256') or completed['driver_sha256'] != proof.get('driver_sha256') or
            not completed.get('provider_sha256') or completed['provider_sha256'] != proof.get('provider_sha256') or
            proof.get('evaluator_sha256') != FROZEN_EVALUATOR_SHA256):
        raise ValueError('Evaluation driver/provider do not match frozen proof')
    sets = completed.get('sets', {})
    assignments = binding.get('assignment', {})
    result_pins = completed.get('results', {})
    if set(sets) != set(manifest['held_out']) or set(assignments) != set(sets) or set(result_pins) != set(sets) or len(set(sets.values())) != len(sets):
        raise ValueError('Every frozen set requires one unique completed assignment')
    workers = read(run / 'evaluation-workers-before.json')
    if not workers or workers != read(run / 'evaluation-workers-after.json') or binding.get('workers') != workers:
        raise ValueError('Worker identity or artifacts changed')
    if set(assignments.values()) != set(workers):
        raise ValueError('Unbound evaluation worker')
    artifacts = None
    for unit, worker in workers.items():
        att, identity = worker['attestation'], worker['identity']
        checked_process(att, identity, completed['model_id'])
        if (att.get('service_unit') != unit or identity.get('unit') != unit or att.get('threads') != 4 or
                identity.get('engine', {}).get('threads') != 4 or identity.get('properties', {}).get('CPUQuotaPerSecUSec') != '4s'):
            raise ValueError('Unexpected worker resource configuration')
        checked_artifacts(att.get('artifacts', {}))
        if artifacts is not None and att['artifacts'] != artifacts:
            raise ValueError('Workers did not use identical attested artifacts')
        artifacts = att['artifacts']
    snapshots, events, results = [], [], {}
    for relative, label in sets.items():
        if not isinstance(label, str) or Path(label).name != label or label in ('.', '..'):
            raise ValueError('Invalid private evaluation label')
        folder = (evaluations / label).resolve()
        if not folder.is_relative_to(evaluations.resolve()):
            raise ValueError('Evaluation evidence escapes its root')
        expected_result = {'label': label, 'events_sha256': sha(folder / 'events.jsonl'),
                           'summary_sha256': sha(folder / 'summary.json')}
        if result_pins[relative] != expected_result:
            raise ValueError('Recorded evaluation result changed after completion')
        rows, actual, result = checked_set(root / relative, manifest['held_out'][relative]['sha256'],
            folder / 'summary.json', folder / 'events.jsonl', model_id=completed['model_id'])
        snapshots.extend(rows); events.extend(actual)
        results[relative] = {'assessment': result, 'events_sha256': sha(folder / 'events.jsonl'),
                            'summary_sha256': sha(folder / 'summary.json')}
    if completed.get('count') != len(snapshots) or len(snapshots) != manifest['held_out_count']:
        raise ValueError('Incomplete stage evaluation')
    return {'model_id': completed['model_id'], 'provider_sha256': completed['provider_sha256'],
            'driver_sha256': completed['driver_sha256'], 'completion_sha256': sha(run / 'evaluation-complete.json'),
            'binding_sha256': sha(run / 'evaluation-binding.json'), 'worker_proof_sha256': sha(run / 'evaluation-workers-before.json'),
            'artifact_digests': {name: item['sha256'] for name, item in artifacts.items()},
            'assessment': assess(snapshots, events), 'by_application': grouped(snapshots, events), 'sets': results}


def build(stage, data, baseline, candidate, evaluations, driver_proof, root=ROOT):
    manifest, _ = checked_manifest(stage, data, root)
    before = checked_run(data, manifest, baseline, evaluations, driver_proof, root)
    after = checked_run(data, manifest, candidate, evaluations, driver_proof, root)
    if before['provider_sha256'] != after['provider_sha256'] or before['driver_sha256'] != after['driver_sha256']:
        raise ValueError('Baseline and candidate use different evaluators/providers')
    unchanged = set(before['artifact_digests']) - {'weights'}
    if set(before['artifact_digests']) != set(after['artifact_digests']) or any(
            before['artifact_digests'][name] != after['artifact_digests'][name] for name in unchanged):
        raise ValueError('Non-weight inference artifacts changed between baseline and candidate')
    retained = BASE_APPLICATIONS + STAGES[:STAGES.index(stage)]
    regression = {}
    for app in retained:
        old, new = before['by_application'][app]['metrics'], after['by_application'][app]['metrics']
        regression[app] = (old['count'] == new['count'] and
            old['exact_arguments']['count'] == new['exact_arguments']['count'] and
            all(new['counts'][key] >= value for key, value in old['counts'].items()) and
            new['exact_arguments']['passed'] >= old['exact_arguments']['passed'])
    passed = (after['assessment']['model_targets_passed'] and
              all(value['assessment']['model_targets_passed'] for value in after['sets'].values()) and
              all(value['model_targets_passed'] for value in after['by_application'].values()))
    return {'stage': stage, 'version': manifest['version'], 'manifest_sha256': sha(data / 'manifest.json'),
            'baseline': before, 'candidate': after, 'all_frozen_sets_passed': passed,
            'retained_application_nonregression': regression, 'retained_applications_not_regressed': all(regression.values()),
            'model_acceptance_passed': passed and all(regression.values()),
            'frozen_evaluator_sha256': FROZEN_EVALUATOR_SHA256, 'driver_proof_sha256': sha(driver_proof),
            'acceptance_script_sha256': sha(Path(__file__).with_name('model_acceptance.py')),
            'report_script_sha256': sha(Path(__file__)), 'native_backend_security_verified': None,
            'production_activation': False, 'next_training_started': False,
            'limitations': ['Synthetic English/French cases are not external certification.',
                'Every frozen set and application must pass existing gates; retained application counts must not regress.',
                'Knowledge query matching does not establish retrieval factuality.',
                'Performance, native security and live application verification remain separate.',
                'This analysis neither executes business tools nor authorizes deployment or the next training.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=STAGES, required=True)
    for name in ('data', 'baseline', 'candidate', 'evaluations', 'driver-proof', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if sha(ROOT / 'training/scripts/evaluate_snapshot.py') != FROZEN_EVALUATOR_SHA256:
        raise ValueError('Frozen evaluator changed')
    result = build(args.stage, args.data, args.baseline, args.candidate, args.evaluations, args.driver_proof)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False);stream.write('\n')
    print(json.dumps({'stage': args.stage, 'model_acceptance_passed': result['model_acceptance_passed']}))


if __name__ == '__main__':
    main()
