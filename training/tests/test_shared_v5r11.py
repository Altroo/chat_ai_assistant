"""Six wording corrections must preserve the frozen task and evaluation contracts."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'training/scripts'))
import prepare_shared_v5r11 as m


class WordingCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = ROOT/'training/datasets'/m.PARENT
        cls.raw = (cls.parent/'train.jsonl').read_bytes()
        cls.output, cls.changes, cls.updated = m.correct(cls.raw)

    def test_only_six_user_texts_change(self):
        old = self.raw.splitlines(keepends=True); new = self.output.splitlines(keepends=True)
        self.assertEqual(len(old), len(new))
        changed = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
        self.assertEqual(changed, [c['row_index'] for c in self.changes])
        self.assertEqual(len(changed), 6)
        for index in changed:
            a, b = json.loads(old[index]), json.loads(new[index])
            text = b['messages'][-2]['content']
            self.assertIn(m.NEW, text)
            b['messages'][-2]['content'] = text.replace(m.NEW, m.OLD, 1)
            self.assertEqual(a, b)

    def test_missing_or_mislabeled_source_rejects(self):
        for mutation in ('missing', 'target', 'language'):
            with self.subTest(mutation=mutation):
                rows = list(map(json.loads, self.raw.splitlines()))
                index = self.changes[0]['row_index']
                if mutation == 'missing': rows.pop(index)
                elif mutation == 'target': rows[index]['messages'][-1]['tool_calls'][0]['function']['arguments']['metric'] = 'invoiced_net_ttc'
                else: rows[index]['language'] = 'fr'
                with self.assertRaises(ValueError):
                    m.correct((''.join(json.dumps(r)+'\n' for r in rows)).encode())

    def test_changed_parent_helper_rejects_before_native_read(self):
        manifest = json.loads((self.parent/'manifest.json').read_text())
        actual_sha = m.sha
        for name in manifest['helper_sha256']:
            with self.subTest(helper=name):
                changed = ROOT/name
                def digest(path):
                    return 'changed' if path == changed else actual_sha(path)
                with mock.patch.object(m, 'sha', side_effect=digest):
                    with self.assertRaisesRegex(ValueError, 'parent helper source changed'):
                        m.assemble({})

    def test_generated_splits_and_exclusions_remain_frozen(self):
        current = ROOT/'training/datasets'/m.VERSION
        if not current.exists():
            self.fail('Generate the reviewed correction before this integrity check')
        parent = json.loads((self.parent/'manifest.json').read_text())
        manifest = json.loads((current/'manifest.json').read_text())
        self.assertEqual((current/'train.jsonl').read_bytes(), self.output)
        self.assertEqual((current/'valid.jsonl').read_bytes(), (self.parent/'valid.jsonl').read_bytes())
        for key in ('held_out', 'historical_regression_held_out', 'fresh_controls', 'corrections', 'native_metadata'):
            self.assertEqual(manifest[key], parent[key])
        self.assertTrue(manifest['wording_corrections']['targets_unchanged'])


if __name__ == '__main__':
    unittest.main()
