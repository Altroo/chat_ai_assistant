"""Mutation tests for the only reviewed correction-aware retention exception."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import serial_scope_v3 as scope
import prepare_serial_name_corrections as preparation


class SerialCorrectionScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = ROOT / 'training/datasets/shared-v6r10-en-fr'
        cls.parent = ROOT / 'training/datasets/shared-v5r8-en-fr'
        cls.manifest = json.loads((cls.folder / 'manifest.json').read_text())
        cls.train = (cls.folder / 'train.jsonl').read_bytes()
        cls.valid = (cls.folder / 'valid.jsonl').read_bytes()

    def check(self, manifest=None, train=None, valid=None, parent=None, stage='contrat', correction_root=ROOT):
        return scope.validate_retained_curriculum(stage, manifest or self.manifest,
            self.train if train is None else train, self.valid if valid is None else valid, parent or self.parent, correction_root=correction_root)

    def rebound(self, train=None, valid=None):
        value = deepcopy(self.manifest)
        for name, payload in (('train.jsonl', self.train if train is None else train),
                              ('valid.jsonl', self.valid if valid is None else valid)):
            value['files'][name] = scope.digest(payload)
        return value

    def test_exact_reviewed_correction_retains_actual_r8_identity(self):
        proof = self.check()
        self.assertEqual(proof['manifest_sha256'], scope.R8_MANIFEST)
        self.assertEqual(proof['files']['train.jsonl'], scope.digest((self.parent / 'train.jsonl').read_bytes()))
        self.assertEqual(proof['corrections']['replaced_targets'], 6)
        self.assertEqual(proof['corrections']['unchanged_training_rows'], 2333)
        self.assertFalse(proof['model_acceptance_verified'])
        self.assertFalse(proof['training_authorized'])

    def test_only_the_six_known_target_lines_change_from_previous_contracts(self):
        old = ROOT / 'training/datasets/shared-v6r9-en-fr'
        before = (old / 'train.jsonl').read_bytes().splitlines(keepends=True)
        after = self.train.splitlines(keepends=True)
        self.assertEqual(len(before), 2492)
        self.assertEqual(len(before), len(after))
        self.assertEqual([i for i, (a,b) in enumerate(zip(before,after)) if a != b],
                         [620,621,622,623,968,969])
        self.assertEqual((old / 'valid.jsonl').read_bytes(), self.valid)
        prior = json.loads((old / 'manifest.json').read_text())
        for key in ('counts','retained_dataset','added_dataset','held_out','historical_regression_held_out','fresh_controls'):
            self.assertEqual(self.manifest[key], prior[key])

    def test_missing_malformed_or_broader_exception_is_rejected(self):
        for declaration in (None, {}, {**scope.DECLARATION,'allow_other_changes':True},
                            {**scope.DECLARATION,'manifest_sha256':'0'*64}):
            value = deepcopy(self.manifest); value['retained_corrections'] = declaration
            with self.subTest(declaration=declaration), self.assertRaisesRegex(ValueError,'pinned six-target'):
                self.check(value)
        value = deepcopy(self.manifest);value.pop('retained_corrections')
        with self.assertRaisesRegex(ValueError,'byte-for-byte'):
            self.check(value, correction_root=None)

    def test_changed_unreviewed_row_missing_row_or_reordered_rows_reject(self):
        original = self.train.splitlines(keepends=True)
        variants = [original[1:], original + [original[0]], list(original)]
        variants[-1][100],variants[-1][101]=variants[-1][101],variants[-1][100]
        changed = list(original);row=json.loads(changed[100]);row['messages'][-2]['content']+=' different'
        changed[100]=(json.dumps(row)+'\n').encode();variants.append(changed)
        for lines in variants:
            raw=b''.join(lines)
            with self.subTest(size=len(raw)), self.assertRaisesRegex(ValueError,'prefix|current application'):
                self.check(self.rebound(train=raw),train=raw)

    def test_original_incorrect_prefix_cannot_claim_correction(self):
        raw=(ROOT/'training/datasets/shared-v6r9-en-fr/train.jsonl').read_bytes()
        with self.assertRaisesRegex(ValueError,'corrected prefix'):
            self.check(self.rebound(train=raw),train=raw)

    def test_validation_changes_reject_even_if_rehashed(self):
        raw=self.valid.split(b'\n',1)[1]
        with self.assertRaisesRegex(ValueError,'byte-for-byte'):
            self.check(self.rebound(valid=raw),valid=raw)

    def test_untrained_corrected_dataset_cannot_replace_actual_r8_predecessor(self):
        parent=ROOT/'training/datasets/shared-v5r9-en-fr'
        value=deepcopy(self.manifest)
        m=json.loads((parent/'manifest.json').read_text())
        value['retained_dataset']={'version':parent.name,'manifest_sha256':scope.digest((parent/'manifest.json').read_bytes()),'files':m['files']}
        with self.assertRaisesRegex(ValueError,'Pinned retained-correction'):
            self.check(value,parent=parent)

    def test_frozen_evaluation_and_fresh_control_identities_cannot_change(self):
        variants=[]
        value=deepcopy(self.manifest);value['held_out'].pop(next(iter(value['held_out'])));variants.append(value)
        value=deepcopy(self.manifest);value['historical_regression_held_out']={};variants.append(value)
        value=deepcopy(self.manifest);value['fresh_controls']['manifest_sha256']='0'*64;variants.append(value)
        value=deepcopy(self.manifest);value['held_out_count']-=1;variants.append(value)
        for value in variants:
            with self.subTest(keys=len(value['held_out'])), self.assertRaises(ValueError):
                self.check(value)

    def test_wrong_appended_application_and_skipped_stage_reject(self):
        lines=self.train.splitlines(keepends=True);row=json.loads(lines[-1]);row['application']='management_projet'
        lines[-1]=(json.dumps(row)+'\n').encode();raw=b''.join(lines)
        with self.assertRaisesRegex(ValueError,'current application'):
            self.check(self.rebound(train=raw),train=raw)
        with self.assertRaises(ValueError):
            self.check(stage='reservation')

    def test_old_labels_fail_on_the_normal_strict_path(self):
        old=ROOT/'training/datasets/shared-v6r9-en-fr'
        value=json.loads((old/'manifest.json').read_text())
        value['scope_validator_sha256']=scope.SOURCE_SHA256['serial_scope_v3.py']
        with self.assertRaisesRegex(ValueError,'Known incorrect'):
            self.check(value,train=(old/'train.jsonl').read_bytes(),correction_root=None)

    def test_later_stage_retains_corrected_predecessor_without_exception(self):
        old=ROOT/'training/datasets/shared-v7r9-en-fr'
        old_parent=ROOT/'training/datasets/shared-v6r9-en-fr'
        old_train=(old/'train.jsonl').read_bytes();old_prefix=(old_parent/'train.jsonl').read_bytes()
        self.assertTrue(old_train.startswith(old_prefix))
        raw=self.train+old_train[len(old_prefix):];valid=(old/'valid.jsonl').read_bytes()
        value=json.loads((old/'manifest.json').read_text())
        value['retained_dataset']={'version':self.folder.name,'manifest_sha256':scope.digest((self.folder/'manifest.json').read_bytes()),'files':self.manifest['files']}
        value['scope_validator_sha256']=scope.SOURCE_SHA256['serial_scope_v3.py']
        value['files']={'train.jsonl':scope.digest(raw),'valid.jsonl':scope.digest(valid)}
        proof=scope.validate_retained_curriculum('gestion_magasin',value,raw,valid,self.folder)
        self.assertEqual(proof['retention_mode'],'exact retained bytes')
        self.assertNotIn('corrections',proof)
        value['retained_corrections']=dict(scope.DECLARATION)
        with self.assertRaisesRegex(ValueError,'pinned six-target'):
            scope.validate_retained_curriculum('gestion_magasin',value,raw,valid,self.folder)

    def test_explicit_artifact_root_is_required_and_has_no_fallback(self):
        with self.assertRaisesRegex(ValueError, 'Explicit correction artifact root'):
            self.check(correction_root=None)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, 'root is unavailable'):
                self.check(correction_root=root/'missing')
            with self.assertRaises(FileNotFoundError):
                self.check(correction_root=root)
            prefix = ROOT/'training/datasets/shared-v5r9-en-fr'
            info = json.loads((prefix/'manifest.json').read_text())
            names = set(info['held_out']) | set(info['historical_regression_held_out'])
            names.update('training/datasets/shared-v5r9-en-fr/'+name
                         for name in ('manifest.json', 'train.jsonl', 'valid.jsonl'))
            names.update('training/datasets/management-name-errata-v2-en-fr/'+name
                         for name in ('manifest.json', 'train.replacements.jsonl'))
            for name in names:
                destination = root/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT/name, destination)
            proof = self.check(correction_root=root)
            self.assertEqual(proof['corrections']['replaced_targets'], 6)
            # A valid repository copy must never mask a bad isolated artifact.
            evaluation = root/next(iter(info['held_out']))
            evaluation.write_bytes(evaluation.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError, 'Frozen evaluation bytes changed'):
                self.check(correction_root=root)

    def test_artifact_root_without_declaration_is_rejected(self):
        value = deepcopy(self.manifest)
        value.pop('retained_corrections')
        with self.assertRaisesRegex(ValueError, 'requires an explicit correction declaration'):
            self.check(value)

    def test_hash_or_validator_drift_and_overwrite_reject(self):
        value=deepcopy(self.manifest);value['files']['train.jsonl']='0'*64
        with self.assertRaisesRegex(ValueError,'Current split'):
            self.check(value)
        value=deepcopy(self.manifest);value['scope_validator_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'scope validator'):
            self.check(value)
        with patch.object(scope,'SOURCE_SHA256',{**scope.SOURCE_SHA256,'serial_scope_v2.py':'0'*64}),self.assertRaisesRegex(ValueError,'source changed'):
            self.check()
        with self.assertRaisesRegex(ValueError,'Never overwrite'):
            preparation.prepare()


if __name__=='__main__':
    unittest.main()
