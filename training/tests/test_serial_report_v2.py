"""Synthetic fixtures test reporting gates, not model performance."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import report_serial_candidate_v2 as report
from model_acceptance import FROZEN_EVALUATOR_SHA256
import test_serial_report as previous_tests
from test_dialogue_report import write, lines


class SeparateGroupReportTests(unittest.TestCase):
    def fixture(self, root, *, wrong_fresh=False, improve_regression=False):
        args = previous_tests.SerialReportTests().fixture(root)
        data, evaluations = args[1], args[4]
        renderer = root / 'clarifications.py'
        messages = {language: {reason: 'frozen-' + language + '-' + reason
                    for reason in ('missing_details', 'ambiguous_metric', 'unsupported')}
                    for language in ('en', 'fr')}
        renderer.write_text('MESSAGES = ' + repr(messages))
        proof = report.read(args[5])
        proof['provider_sha256'][report.CLARIFICATIONS] = report.sha(renderer)
        write(args[5], proof)
        rows = [{'id': 'fresh-' + app + '-' + str(i), 'language': 'en' if i % 2 else 'fr',
                 'category': 'synthetic', 'trusted_context': {'application': app},
                 'expected': {'tool': 'search_records', 'arguments': {'resource': 'project'}}}
                for app in report.previous.BASE_APPLICATIONS for i in range(16)]
        lines(root / report.FRESH, rows)
        fresh = {'count': 48, 'languages': ['en', 'fr'], 'applications': list(report.previous.BASE_APPLICATIONS),
                 'by_application': {app: 16 for app in report.previous.BASE_APPLICATIONS},
                 'files': {'controls.eval.jsonl': report.sha(root / report.FRESH)}}
        source = root / Path(report.FRESH).parent / 'manifest.json'
        write(source, fresh)
        info = {'sha256': report.sha(root / report.FRESH), 'count': 48}
        manifest = report.read(data / 'manifest.json')
        manifest['held_out'][report.FRESH] = info
        manifest['held_out_count'] += 48
        manifest['fresh_controls'] = {'manifest_sha256': report.sha(source), 'files': {report.FRESH: info}}
        write(data / 'manifest.json', manifest)
        for model in ('baseline', 'candidate'):
            events = [{**row, 'action': copy.deepcopy(row['expected']), 'structured_valid': True} for row in rows]
            if model == 'candidate' and wrong_fresh:
                events[0]['action']['arguments']['resource'] = 'wrong'
            label = model + '-fresh'
            lines(evaluations / label / 'events.jsonl', [{'case': row} for row in events])
            write(evaluations / label / 'summary.json', {'dataset_sha256': info['sha256'],
                'evaluator_sha256': FROZEN_EVALUATOR_SHA256, 'model_id': model, 'max_output_tokens': 512,
                'thinking': False, 'mode': 'native', 'metrics': {'count': 48}})
            if model == 'baseline' and improve_regression:
                path = evaluations / 'baseline-facturation/events.jsonl'
                values = [json.loads(line) for line in path.read_text().splitlines()]
                values[0]['case']['action']['arguments']['resource'] = 'wrong'
                lines(path, values)
            run = root / model
            for filename in ('evaluation-complete.json', 'evaluation-binding.json'):
                value = report.read(run / filename)
                value['manifest_sha256'] = report.sha(data / 'manifest.json')
                value['provider_sha256'] = proof['provider_sha256']
                value['count'] += 48
                value['sets'][report.FRESH] = label
                value['results'] = {relative: {'label': name,
                    'events_sha256': report.sha(evaluations / name / 'events.jsonl'),
                    'summary_sha256': report.sha(evaluations / name / 'summary.json')}
                    for relative, name in value['sets'].items()}
                if filename == 'evaluation-binding.json':
                    value['assignment'][report.FRESH] = 'synthetic-worker.service'
                write(run / filename, value)
        return (*args[:-1], renderer, args[-1])

    def test_real_prepared_stages_have_separate_counts(self):
        for stage, version, count in [('contrat', 'shared-v6r8-en-fr', 516),
                                      ('gestion_magasin', 'shared-v7r8-en-fr', 606),
                                      ('reservation', 'shared-v8r8-en-fr', 690)]:
            with self.subTest(stage=stage):
                _, groups = report.checked_groups(stage, ROOT / 'training/datasets' / version)
                self.assertEqual(sum(map(len, groups['regression'].values())), count)
                self.assertEqual(sum(map(len, groups['fresh_controls'].values())), 48)

    def test_complete_pass_still_cannot_activate_or_start_training(self):
        with tempfile.TemporaryDirectory() as folder:
            result = report.build(*self.fixture(Path(folder)))
            self.assertTrue(result['model_acceptance_passed'])
            self.assertTrue(result['separate_group_targets_passed'])
            self.assertEqual(result['candidate']['groups']['regression']['assessment']['metrics']['count'], 104)
            self.assertEqual(result['candidate']['groups']['fresh_controls']['assessment']['metrics']['count'], 48)
            self.assertFalse(result['production_activation'])
            self.assertFalse(result['next_training_started'])

    def test_combined_pass_cannot_hide_failed_fresh_application(self):
        with tempfile.TemporaryDirectory() as folder:
            result = report.build(*self.fixture(Path(folder), wrong_fresh=True))
            self.assertTrue(result['all_frozen_sets_passed'])
            self.assertTrue(result['candidate']['groups']['fresh_controls']['assessment']['model_targets_passed'])
            self.assertFalse(result['candidate']['groups']['fresh_controls']['by_application']['facturation']['model_targets_passed'])
            self.assertFalse(result['separate_group_targets_passed'])
            self.assertFalse(result['model_acceptance_passed'])

    def test_regression_improvement_cannot_offset_fresh_regression(self):
        with tempfile.TemporaryDirectory() as folder:
            result = report.build(*self.fixture(Path(folder), wrong_fresh=True, improve_regression=True))
            self.assertTrue(result['retained_applications_not_regressed'])
            self.assertTrue(result['retained_group_application_nonregression']['regression']['facturation'])
            self.assertFalse(result['retained_group_application_nonregression']['fresh_controls']['facturation'])
            self.assertFalse(result['model_acceptance_passed'])

    def test_fresh_manifest_binding_and_partition_cannot_change(self):
        for mutation in ('missing', 'hash', 'files', 'scope'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as folder:
                args = self.fixture(Path(folder)); path = args[1] / 'manifest.json'
                value = report.read(path)
                if mutation == 'missing':
                    del value['fresh_controls']
                elif mutation == 'hash':
                    value['fresh_controls']['manifest_sha256'] = '0' * 64
                elif mutation == 'files':
                    value['fresh_controls']['files'] = {}
                else:
                    value['fresh_controls']['files'][report.FRESH]['count'] = 47
                write(path, value)
                with self.assertRaises(ValueError):
                    report.checked_groups(args[0], args[1], args[-1])

    def test_events_changed_between_overall_and_group_scoring_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder))
            original = report.bound_scoring
            def changed_after_check(*values):
                scoring = original(*values)
                build = scoring.build
                def mutate(*arguments):
                    result = build(*arguments)
                    path = args[4] / 'candidate-fresh/events.jsonl'
                    events = [json.loads(line) for line in path.read_text().splitlines()]
                    events[0]['case']['action']['arguments']['resource'] = 'changed'
                    lines(path, events)
                    return result
                scoring.build = mutate
                return scoring
            with patch.object(report, 'bound_scoring', side_effect=changed_after_check):
                with self.assertRaisesRegex(ValueError, 'result changed during group'):
                    report.build(*args)


    def test_frozen_clarifications_are_used_without_changing_global_scorer(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder))
            scoring = report.bound_scoring(args[5], args[6])
            row = {'id': 'frozen-clarify-en', 'language': 'en', 'category': 'synthetic',
                   'trusted_context': {'application': 'facturation'},
                   'expected': {'tool': 'clarify', 'arguments': {'reason': 'unsupported', 'language': 'en'}}}
            event = {**row, 'structured_valid': True,
                     'action': {'tool': 'clarify', 'message': 'frozen-en-unsupported'}}
            self.assertEqual(scoring.assess([row], [event])['metrics']['counts']['action_matches'], 1)
            self.assertEqual(report.model_acceptance.assess([row], [event])['metrics']['counts']['action_matches'], 0)
            self.assertEqual(scoring.grouped([row], [event])['facturation']['metrics']['counts']['action_matches'], 1)
            # Exercise the inherited checked_set/checked_run/build path too.
            relative = 'training/datasets/serial-synthetic/facturation.jsonl'
            path = args[-1] / relative
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            row['id'] = rows[0]['id'];event['id'] = row['id'];rows[0] = row
            lines(path, rows)
            manifest = report.read(args[1] / 'manifest.json')
            manifest['held_out'][relative]['sha256'] = report.sha(path)
            write(args[1] / 'manifest.json', manifest)
            for model in ('baseline', 'candidate'):
                folder = args[4] / (model + '-facturation')
                events = [json.loads(line) for line in (folder / 'events.jsonl').read_text().splitlines()]
                events[0] = {'case': event};lines(folder / 'events.jsonl', events)
                summary = report.read(folder / 'summary.json')
                summary['dataset_sha256'] = report.sha(path);write(folder / 'summary.json', summary)
                for filename in ('evaluation-complete.json', 'evaluation-binding.json'):
                    p = args[-1] / model / filename;value = report.read(p)
                    value['manifest_sha256'] = report.sha(args[1] / 'manifest.json')
                    value['results'][relative]['events_sha256'] = report.sha(folder / 'events.jsonl')
                    value['results'][relative]['summary_sha256'] = report.sha(folder / 'summary.json')
                    write(p, value)
            self.assertTrue(report.build(*args)['model_acceptance_passed'])

    def test_unattested_renderer_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.fixture(Path(folder))
            args[6].write_text(args[6].read_text() + '\\n# changed')
            with self.assertRaisesRegex(ValueError, 'does not match attested'):
                report.build(*args)

    def test_full_action_gate_is_not_only_tool_accuracy(self):
        rows = [{'id': str(i), 'language': 'en', 'category': 'synthetic',
                 'expected': {'tool': 'knowledge', 'arguments': {'query': 'workflow'}}}
                for i in range(100)]
        rows[0]['expected'] = {'tool': 'search_records', 'arguments': {'resource': 'project'}}
        events = [{**row, 'structured_valid': True, 'action': copy.deepcopy(row['expected'])} for row in rows]
        for event in events[1:7]:
            event['action']['arguments']['query'] = ''
        result = report.model_acceptance.assess(rows, events)
        self.assertTrue(result['model_targets_passed'])
        self.assertFalse(report.targets(result))


if __name__ == '__main__':
    unittest.main()
