"""Verify the reviewed Reservation corrections without changing any targets."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import prepare_reservation_temporal_errata as preparation
from audit_training_inputs import audit
from serial_scope_v2 import validate_stage, validate_retained_curriculum


class ReservationTemporalErrataTests(unittest.TestCase):
    def test_only_four_training_requests_change(self):
        source = ROOT / 'training/datasets/reservation-dialogue-v3-en-fr'
        output = source.with_name('reservation-dialogue-v4-en-fr')
        manifest = json.loads((output / 'manifest.json').read_text())
        self.assertEqual(manifest['source_manifest_sha256'], preparation.SOURCE_HASH)
        self.assertEqual(manifest['generator_sha256'], preparation.digest(
            (ROOT / 'training/scripts/prepare_reservation_temporal_errata.py').read_bytes()))
        for name, digest in manifest['files'].items():
            old, new = (source / name).read_bytes(), (output / name).read_bytes()
            self.assertEqual(preparation.digest(new), digest)
            if name not in ('train.jsonl', 'train.eval.jsonl'):
                self.assertEqual(new, old)
                continue
            original, corrected = [list(map(json.loads, payload.splitlines())) for payload in (old, new)]
            self.assertEqual(len(original), len(corrected))
            changed = []
            for index, (before, after) in enumerate(zip(original, corrected)):
                if before == after:
                    continue
                changed.append(index)
                position = -1 if name.endswith('.eval.jsonl') else -2
                restored = deepcopy(after)
                restored['messages'][position] = before['messages'][position]
                self.assertEqual(restored, before)
                self.assertNotEqual(after['messages'][position], before['messages'][position])
                self.assertIn('2029' if index < 68 else '2028', after['messages'][position]['content'])
            self.assertEqual(changed, [60, 61, 68, 69])
            actual, indices = preparation.corrected(old, name.endswith('.eval.jsonl'))
            self.assertEqual(actual, new)
            self.assertEqual(indices, changed)

    def test_complete_retained_curriculum_and_held_out_bytes_preserved(self):
        data = ROOT / 'training/datasets/shared-v8r10-en-fr'
        prior = data.with_name('shared-v8r9-en-fr')
        retained = data.with_name('shared-v7r9-en-fr')
        manifest = json.loads((data / 'manifest.json').read_text())
        old = json.loads((prior / 'manifest.json').read_text())
        self.assertEqual(manifest['held_out'], old['held_out'])
        self.assertEqual(manifest['fresh_controls'], old['fresh_controls'])
        self.assertEqual(manifest['historical_regression_held_out'], old['historical_regression_held_out'])
        for name, info in manifest['held_out'].items():
            self.assertEqual(preparation.digest((ROOT / name).read_bytes()), info['sha256'])
        payloads = [(data / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')]
        rows = [list(map(json.loads, raw.splitlines())) for raw in payloads]
        validate_stage('reservation', manifest, *rows, complete_epochs=1)
        validate_retained_curriculum('reservation', manifest, *payloads, retained)
        self.assertEqual([len(split) for split in rows], [2870, 402])
        self.assertEqual(payloads[1], (prior / 'valid.jsonl').read_bytes())
        changed = [i for i, (a, b) in enumerate(zip(
            payloads[0].splitlines(), (prior / 'train.jsonl').read_bytes().splitlines())) if a != b]
        self.assertEqual(changed, [2750, 2751, 2758, 2759])
        report = audit(data)
        self.assertEqual(report['exact_input_label_conflicts'], 0)
        self.assertEqual(report['exact_input_cross_split_overlap'], 0)

    def test_native_date_semantics_sources_are_pinned(self):
        manifest = json.loads((ROOT / 'training/datasets/reservation-dialogue-v4-en-fr/manifest.json').read_text())
        for name, expected in preparation.EXTRA_NATIVE.items():
            self.assertEqual(manifest['native_sources'][name], expected)
        self.assertEqual(manifest['inherited_metadata_provenance']['version'], 'reservation-dialogue-v3-en-fr')
        self.assertIn('V3 provenance', manifest['policy'])
        source = json.loads((ROOT / 'training/datasets/reservation-dialogue-v3-en-fr/manifest.json').read_text())
        for field in manifest['inherited_metadata_provenance']['fields']:
            self.assertEqual(manifest[field], source[field])
        self.assertEqual(manifest['targets_changed'], 0)
        self.assertEqual(manifest['splits_changed'], 0)

    def test_changed_manifest_or_split_fails_before_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            (data / 'train.jsonl').write_bytes(b'{}\n')
            manifest = {'files': {'train.jsonl': preparation.digest(b'{}\n')}}
            raw = json.dumps(manifest).encode()
            (data / 'manifest.json').write_bytes(raw)
            expected = preparation.digest(raw)
            self.assertEqual(preparation.read_manifest(data, expected), manifest)
            (data / 'train.jsonl').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'split changed'):
                preparation.read_manifest(data, expected)
            (data / 'manifest.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                preparation.read_manifest(data, expected)

    def test_existing_version_and_unexpected_correction_indices_reject(self):
        with self.assertRaisesRegex(ValueError, 'Never overwrite'):
            preparation.prepare(ROOT)
        raw = (ROOT / 'training/datasets/reservation-dialogue-v3-en-fr/train.jsonl').read_bytes()
        with self.assertRaisesRegex(ValueError, 'indices'):
            preparation.corrected(b'\n'.join(raw.splitlines()[1:]) + b'\n')


if __name__ == '__main__':
    unittest.main()
