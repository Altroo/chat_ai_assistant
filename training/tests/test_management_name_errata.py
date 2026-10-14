"""Known wrong name-search labels must be replaced, never duplicated."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_management_name_errata as correction


class ManagementNameErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(map(json.loads, (correction.SOURCE / 'train.jsonl').read_text().splitlines()))
        cls.manifest = json.loads((correction.OUTPUT / 'manifest.json').read_text())
        cls.replaced = list(map(json.loads, (correction.OUTPUT / 'train.replacements.jsonl').read_text().splitlines()))

    def test_artifact_is_reproducible_and_parent_unchanged(self):
        values, provenance = correction.replacements(self.rows)
        self.assertEqual(values, self.replaced)
        self.assertEqual(provenance, self.manifest['provenance'])
        self.assertEqual(correction.digest((correction.SOURCE / 'manifest.json').read_bytes()), correction.PARENT)
        self.assertEqual(correction.digest((correction.SOURCE / 'train.jsonl').read_bytes()), self.manifest['parent_training_sha256'])
        self.assertEqual(correction.digest((correction.SOURCE / 'valid.jsonl').read_bytes()), self.manifest['unchanged_validation_sha256'])
        self.assertEqual(correction.digest(Path(correction.__file__).read_bytes()), self.manifest['generator_sha256'])
        self.assertEqual(correction.digest((correction.OUTPUT / 'train.replacements.jsonl').read_bytes()), self.manifest['files']['train.replacements.jsonl'])

    def test_only_four_targets_change_all_other_content_preserved(self):
        future = deepcopy(self.rows)
        for row, item in zip(self.replaced, self.manifest['provenance']):
            index = item['source_index']
            before = self.rows[index]
            restored = deepcopy(row)
            restored['messages'][-1] = before['messages'][-1]
            self.assertEqual(restored, before)
            future[index] = row
        self.assertEqual(len(future), 2339)
        self.assertEqual(sum(a != b for a, b in zip(future, self.rows)), 4)
        self.assertTrue(correction.check_labels(future)['known_name_targets_passed'])

    def test_gate_rejects_old_labels_append_only_and_missing_curriculum(self):
        for rows in (self.rows, self.rows + self.replaced):
            with self.assertRaisesRegex(ValueError, 'incorrect name-search'):
                correction.check_labels(rows)
        with self.assertRaisesRegex(ValueError, 'missing'):
            correction.check_labels(self.replaced[:-1])

    def test_gate_rejects_wrong_field_tool_or_resource(self):
        for change in ('field', 'tool', 'resource'):
            rows = deepcopy(self.replaced)
            fn = rows[0]['messages'][-1]['tool_calls'][0]['function']
            if change == 'field':
                fn['arguments']['query'] = fn['arguments'].pop('client_name')
            elif change == 'tool':
                fn['name'] = 'get_record'
            else:
                fn['arguments']['resource'] = 'supplier'
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, 'incorrect name-search'):
                    correction.check_labels(rows)

    def test_generator_rejects_drift_and_existing_output(self):
        rows = deepcopy(self.rows)
        rows[620]['messages'][-2]['content'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'row changed'):
            correction.replacements(rows)
        with self.assertRaisesRegex(ValueError, 'count'):
            correction.replacements(self.rows[:-1])
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            correction.prepare(Path('.'))

    def test_corrected_requests_absent_from_validation_and_held_out(self):
        requests = {correction.request(row) for row in self.replaced}
        source = json.loads((correction.SOURCE / 'manifest.json').read_text())
        validation = list(map(json.loads, (correction.SOURCE / 'valid.jsonl').read_text().splitlines()))
        self.assertFalse(requests & {correction.request(row) for row in validation})
        paths = set(source['held_out']) | set(source['historical_regression_held_out'])
        paths.add('training/datasets/shared-v5r8-fresh-en-fr/controls.eval.jsonl')
        for name in paths:
            for row in map(json.loads, (correction.ROOT / name).read_text().splitlines()):
                text = row['messages'][-1]['content'].split('\nCurrent request: ', 1)[-1]
                self.assertNotIn(text, requests)


if __name__ == '__main__':
    unittest.main()
