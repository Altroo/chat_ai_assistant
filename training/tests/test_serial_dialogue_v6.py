"""R8 continuation preserves every prior row and existing evaluation envelope."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
from prepare_serial_dialogue_v6 import SOURCES, main, prompt_key, frozen_rows
from serial_scope_v2 import STAGES, validate_stage, validate_retained_curriculum
from training_schedule import complete_epoch_order


class R8SerialPreparationTests(unittest.TestCase):
    def test_exact_retention_counts_and_frozen_evaluations(self):
        previous = ROOT / 'training/datasets/shared-v5r8-en-fr'
        for stage, source, version, train_count, valid_count, held_count in zip(
                STAGES, SOURCES, range(6, 9), (2492, 2690, 2870), (319, 362, 402), (564, 654, 738)):
            with self.subTest(stage=stage):
                directory = previous.parent / f'shared-v{version}r8-en-fr'
                manifest = json.loads((directory / 'manifest.json').read_text())
                revised = previous.parent / 'shared-dialogue-v2-en-fr'
                frozen = json.loads((revised / 'manifest.json').read_text())
                for name, info in frozen['inputs'].items():
                    self.assertEqual(manifest['held_out'][str((revised / name).relative_to(ROOT))], {'sha256':frozen['files'][name], 'count':info['count']})
                fresh = previous.parent / 'shared-v5r8-fresh-en-fr'
                fresh_manifest = json.loads((fresh / 'manifest.json').read_text())
                fresh_key = str((fresh / 'controls.eval.jsonl').relative_to(ROOT))
                self.assertEqual(manifest['held_out'][fresh_key], {'sha256':fresh_manifest['files']['controls.eval.jsonl'], 'count':48})
                self.assertEqual(manifest['fresh_controls']['files'][fresh_key], manifest['held_out'][fresh_key])
                self.assertEqual(manifest['fresh_controls']['manifest_sha256'], hashlib.sha256((fresh/'manifest.json').read_bytes()).hexdigest())
                parent = json.loads((previous / 'manifest.json').read_text())
                self.assertEqual(manifest['historical_regression_held_out'], parent['historical_regression_held_out'])
                self.assertEqual(manifest['generator_sha256'], hashlib.sha256((ROOT / 'training/scripts/prepare_serial_dialogue_v6.py').read_bytes()).hexdigest())
                payloads = [(directory / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')]
                rows = [list(map(json.loads, raw.splitlines())) for raw in payloads]
                validate_stage(stage, manifest, *rows, complete_epochs=1)
                validate_retained_curriculum(stage, manifest, *payloads, previous)
                self.assertEqual([len(split) for split in rows], [train_count, valid_count])
                self.assertEqual(sorted(complete_epoch_order(rows[0])), list(range(train_count)))
                for name, raw in zip(('train.jsonl', 'valid.jsonl'), payloads):
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), manifest['files'][name])
                    self.assertEqual(raw, (previous / name).read_bytes() + (previous.parent / source / name).read_bytes())
                    self.assertNotRegex(raw.decode(), r'[\u0600-\u06ff]|BEGIN.{0,12}PRIVATE KEY|Bearer\s+\S+')
                excluded = {prompt_key(row) for name, info in {**manifest['historical_regression_held_out'], **manifest['held_out']}.items() for row in frozen_rows(name, info)}
                self.assertEqual(manifest['held_out_count'], held_count)
                self.assertEqual(sum(info['count'] for info in manifest['held_out'].values()), held_count)
                keys = [{prompt_key(row) for row in split} for split in rows]
                self.assertFalse(keys[0] & keys[1])
                self.assertFalse((keys[0] | keys[1]) & excluded)
                previous = directory

    def test_rejects_loss_of_the_current_refinement(self):
        base = ROOT / 'training/datasets/shared-v5r8-en-fr'
        directory = base.parent / 'shared-v6r8-en-fr'
        manifest = json.loads((directory / 'manifest.json').read_text())
        old_payload = (base.parent / 'shared-v6r7-en-fr/train.jsonl').read_bytes()
        with self.assertRaisesRegex(ValueError, 'byte-for-byte'):
            validate_retained_curriculum('contrat', manifest, old_payload, (directory / 'valid.jsonl').read_bytes(), base)

    def test_rerun_refuses_to_overwrite_versioned_data(self):
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            main()
