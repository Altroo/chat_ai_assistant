"""V2 adds two proven project-name corrections without widening the erratum."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_management_name_errata_v2 as correction


class ManagementNameErrataV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = list(map(json.loads, (correction.SOURCE / 'train.jsonl').read_text().splitlines()))
        cls.values = list(map(json.loads, (correction.OUTPUT / 'train.replacements.jsonl').read_text().splitlines()))
        cls.manifest = json.loads((correction.OUTPUT / 'manifest.json').read_text())

    def test_exact_reconstruction_and_provenance(self):
        values, provenance = correction.replacements(self.rows)
        self.assertEqual(values, self.values)
        self.assertEqual(provenance, self.manifest['provenance'])
        sha = correction.parent.digest
        self.assertEqual(sha(Path(correction.__file__).read_bytes()), self.manifest['generator_sha256'])
        self.assertEqual(sha(Path(correction.parent.__file__).read_bytes()), self.manifest['helper_sha256'][Path(correction.parent.__file__).name])
        self.assertEqual(sha((correction.parent.OUTPUT / 'manifest.json').read_bytes()), correction.PRIOR)
        self.assertEqual(sha((correction.OUTPUT / 'train.replacements.jsonl').read_bytes()), self.manifest['files']['train.replacements.jsonl'])

    def test_exactly_six_target_rows_change(self):
        future = deepcopy(self.rows)
        indices = [item['source_index'] for item in self.manifest['provenance']]
        self.assertEqual(indices, [620, 621, 622, 623, 968, 969])
        for index, row in zip(indices, self.values):
            restored = deepcopy(row)
            restored['messages'][-1] = self.rows[index]['messages'][-1]
            self.assertEqual(restored, self.rows[index])
            future[index] = row
        self.assertEqual(sum(a != b for a, b in zip(self.rows, future)), 6)
        self.assertTrue(correction.check_labels(future)['known_name_targets_passed'])
        for index in (918, 919, 1068, 1069, 1712):
            self.assertEqual(future[index], self.rows[index])

    def test_partial_correction_wrong_fields_and_append_only_reject(self):
        future = deepcopy(self.rows)
        for index, row in zip((620, 621, 622, 623), self.values[:4]):
            future[index] = row
        with self.assertRaisesRegex(ValueError, 'project-name'):
            correction.check_labels(future)
        for rows in (self.rows, self.rows + self.values):
            with self.assertRaises(ValueError):
                correction.check_labels(rows)
        with self.assertRaisesRegex(ValueError, 'missing'):
            correction.check_labels(self.values[:-1])
        values = deepcopy(self.values)
        values[-1]['messages'][-1]['tool_calls'][0]['function']['arguments']['query'] = 'Facturation'
        with self.assertRaisesRegex(ValueError, 'project-name'):
            correction.check_labels(values)

    def test_drift_and_overwrite_reject(self):
        rows = deepcopy(self.rows)
        rows[968]['messages'][-2]['content'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'row changed'):
            correction.replacements(rows)
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            correction.prepare(Path('.'))

    def test_requests_excluded_from_validation_and_held_out(self):
        requests = {correction.parent.request(row) for row in self.values}
        source = json.loads((correction.SOURCE / 'manifest.json').read_text())
        valid = list(map(json.loads, (correction.SOURCE / 'valid.jsonl').read_text().splitlines()))
        self.assertFalse(requests & {correction.parent.request(row) for row in valid})
        paths = set(source['held_out']) | set(source['historical_regression_held_out'])
        paths.add('training/datasets/shared-v5r8-fresh-en-fr/controls.eval.jsonl')
        for name in paths:
            for row in map(json.loads, (correction.ROOT / name).read_text().splitlines()):
                self.assertNotIn(row['messages'][-1]['content'].split('\nCurrent request: ', 1)[-1], requests)


if __name__ == '__main__':
    unittest.main()
