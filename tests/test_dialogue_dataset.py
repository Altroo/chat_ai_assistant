"""Prevent dialogue adaptation from changing labels or crossing frozen splits."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dialogue_builder', ROOT / 'training/scripts/build_dialogue_v1.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def rows(path):
    return list(map(json.loads, path.read_text().splitlines()))


class DialogueDatasetTests(unittest.TestCase):
    def test_frozen_evaluation_changes_only_history_envelope(self):
        root = ROOT / 'training/datasets/shared-dialogue-v1-en-fr'
        manifest = json.loads((root / 'manifest.json').read_text())
        changed = []
        for name, info in manifest['inputs'].items():
            original = rows(ROOT / info['source'])
            actual = rows(root / name)
            self.assertEqual(len(actual), len(original))
            for before, after in zip(original, actual):
                self.assertEqual(after, {**before, 'messages': builder.reframe(before['messages'])})
                self.assertEqual(before['messages'][0], after['messages'][0])
                if before != after:
                    changed.append(after)
        self.assertEqual(len(changed), 78)
        self.assertEqual(changed, rows(root / 'changed.eval.jsonl'))

    def test_retained_examples_and_augmented_labels_stay_in_their_split(self):
        parent = ROOT / 'training/datasets/shared-v5r3-en-fr'
        current = ROOT / 'training/datasets/shared-v5r4-en-fr'
        manifest = json.loads((current / 'manifest.json').read_text())
        for split in ('train', 'valid'):
            original = rows(parent / (split + '.jsonl'))
            actual = rows(current / (split + '.jsonl'))
            self.assertEqual(actual[:len(original)], [
                {**row, 'messages': builder.reframe(row['messages'])} for row in original])
            extra = actual[len(original):]
            self.assertEqual(len(extra), len(manifest['augmentation'][split]))
            for row, source in zip(extra, manifest['augmentation'][split]):
                before = original[source['source_index']]
                self.assertEqual(row['tools'], before['tools'])
                self.assertEqual(row['messages'][-1], before['messages'][-1])
                self.assertEqual(row['messages'][0], before['messages'][0])
                self.assertTrue(row['messages'][1]['content'].endswith('\nCurrent request: ' + before['messages'][1]['content']))

    def test_unexpected_history_roles_are_not_silently_used(self):
        with self.assertRaises(ValueError):
            builder.reframe([{'role': 'system', 'content': 'Rules'},
                {'role': 'tool', 'content': 'Private record'}, {'role': 'user', 'content': 'Hello'}])
