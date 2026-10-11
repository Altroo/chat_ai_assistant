"""Later stages retain exact curricula and frozen evaluation separation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
from serial_scope_v2 import STAGES, validate_stage, validate_retained_curriculum
from prepare_serial_dialogue import SOURCES, prompt_key, frozen_rows
from training_schedule import complete_epoch_order


def read(path):
    return json.loads(path.read_text())


class DialogueCurriculumTests(unittest.TestCase):
    def test_native_sources_preserve_questions_labels_splits_and_valid_context(self):
        for name in SOURCES:
            directory = ROOT / 'training/datasets' / name
            manifest = read(directory / 'manifest.json')
            old = directory.parent / manifest['source_dataset']
            self.assertEqual(hashlib.sha256((old / 'manifest.json').read_bytes()).hexdigest(), manifest['source_manifest_sha256'])
            keys = {}
            for split in ('train', 'valid', 'test'):
                original = list(map(json.loads, (old / (split + '.eval.jsonl')).read_text().splitlines()))
                current = list(map(json.loads, (directory / (split + '.eval.jsonl')).read_text().splitlines()))
                self.assertEqual(len(original),len(current))
                for before,after in zip(original,current):
                    self.assertEqual(before['id'],after['id'])
                    self.assertEqual(before['expected'],after['expected'])
                    self.assertEqual(prompt_key(before),prompt_key(after))
                    context=after['trusted_context']; ids=context['previous_result_identifiers']
                    self.assertEqual(len(ids),context['previous_result_count'])
                    self.assertEqual(len(ids),len(set(ids)))
                    self.assertTrue(all(type(value) is int and 0<value<=2147483647 for value in ids))
                keys[split]={prompt_key(row) for row in current}
            self.assertFalse(keys['train'] & keys['valid'])
            self.assertFalse((keys['train'] | keys['valid']) & keys['test'])
            for filename,digest in manifest['files'].items():
                self.assertEqual(hashlib.sha256((directory/filename).read_bytes()).hexdigest(),digest)

    def test_cumulative_prefixes_full_coverage_and_all_heldouts(self):
        previous=ROOT/'training/datasets/shared-v5r4-en-fr'
        for stage,version,expected_count in zip(STAGES,('shared-v6r4-en-fr','shared-v7r4-en-fr','shared-v8r4-en-fr'),(516,606,690)):
            path=previous.parent/version;manifest=read(path/'manifest.json')
            payloads={name:(path/name).read_bytes() for name in ('train.jsonl','valid.jsonl')}
            rows={name:list(map(json.loads,raw.splitlines())) for name,raw in payloads.items()}
            validate_stage(stage,manifest,*rows.values(),complete_epochs=1)
            validate_retained_curriculum(stage,manifest,*payloads.values(),previous)
            self.assertEqual(sorted(complete_epoch_order(rows['train.jsonl'])),list(range(len(rows['train.jsonl']))))
            excluded={prompt_key(row) for name,info in manifest['held_out'].items() for row in frozen_rows(name,info)}
            self.assertEqual(sum(info['count'] for info in manifest['held_out'].values()),expected_count)
            keys=[{prompt_key(row) for row in split} for split in rows.values()]
            self.assertFalse(keys[0]&keys[1]);self.assertFalse((keys[0]|keys[1])&excluded)
            previous=path

    def test_retention_rejects_manifest_changes_missing_rows_and_wrong_stage_suffix(self):
        base=ROOT/'training/datasets/shared-v5r4-en-fr'
        current=base.parent/'shared-v6r4-en-fr';manifest=read(current/'manifest.json')
        train,valid=[(current/name).read_bytes() for name in ('train.jsonl','valid.jsonl')]
        for wrong in ('manifest_sha256','files'):
            changed=copy.deepcopy(manifest);changed['retained_dataset'][wrong]='wrong' if wrong=='manifest_sha256' else {}
            with self.assertRaises(ValueError):validate_retained_curriculum('contrat',changed,train,valid,base)
        with self.assertRaises(ValueError):validate_retained_curriculum('contrat',manifest,train.split(b'\n',1)[1],valid,base)
        with self.assertRaises(ValueError):validate_retained_curriculum('contrat',manifest,(base/'train.jsonl').read_bytes(),valid,base)
        bad=(base/'train.jsonl').read_bytes()+b'{"application":"reservation"}\n'
        with self.assertRaises(ValueError):validate_retained_curriculum('contrat',manifest,bad,valid,base)
        with tempfile.TemporaryDirectory() as folder:
            directory=Path(folder)
            for name in ('manifest.json','train.jsonl','valid.jsonl'):(directory/name).write_bytes((base/name).read_bytes())
            altered=read(directory/'manifest.json');altered['training_policy']='modified lineage'
            (directory/'manifest.json').write_text(json.dumps(altered))
            with self.assertRaises(ValueError):validate_retained_curriculum('contrat',manifest,train,valid,directory)
