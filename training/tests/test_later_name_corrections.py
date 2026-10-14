"""Checks for corrected final-stage preparations and bounded startup."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'training/scripts'))
import prepare_later_name_corrections as preparation
from rehearse_cpu_v2 import prepare_inputs
from serial_scope_v3 import validate_retained_curriculum
from prepare_management_name_errata_v2 import check_labels
import training.tests.test_serial_runtime_v4 as startup


class LaterNameCorrectionTests(unittest.TestCase):
    def stages(self):
        parent = ROOT/'training/datasets'/preparation.BASE
        for stage, (old, _, new) in preparation.STAGES.items():
            folder = ROOT/'training/datasets'/new
            yield stage, ROOT/'training/datasets'/old, folder, parent
            parent = folder

    def test_reconstructs_each_preparation_with_exact_predecessor(self):
        for stage, old, folder, parent in self.stages():
            expected = preparation.digest((parent/'manifest.json').read_bytes())
            payloads, manifest = preparation.assemble(stage, parent, expected)
            self.assertEqual(manifest, json.loads((folder/'manifest.json').read_text()))
            self.assertEqual(manifest['generator_sha256'], preparation.digest(Path(preparation.__file__).read_bytes()))
            self.assertEqual(manifest['retained_dataset']['manifest_sha256'], expected)
            self.assertNotIn('retained_corrections', manifest)
            self.assertTrue(manifest['model_binding']['status'].startswith('UNBOUND'))
            for name, raw in payloads.items():
                self.assertEqual(raw, (folder/name).read_bytes())
                self.assertTrue(raw.startswith((parent/name).read_bytes()))
            proof = validate_retained_curriculum(stage, manifest, payloads['train.jsonl'], payloads['valid.jsonl'], parent)
            self.assertEqual(proof['retention_mode'], 'exact retained bytes')
            self.assertFalse(proof['model_acceptance_verified'])
            self.assertFalse(proof['training_authorized'])

    def test_only_six_retained_labels_change_and_new_app_rows_stay_exact(self):
        for stage, old, folder, parent in self.stages():
            prior = json.loads((old/'manifest.json').read_text())
            current = json.loads((folder/'manifest.json').read_text())
            before, after = [(x/'train.jsonl').read_bytes().splitlines(keepends=True) for x in (old, folder)]
            self.assertEqual(len(before), len(after))
            self.assertEqual([i for i, (a,b) in enumerate(zip(before,after)) if a!=b], preparation.CORRECTED_INDICES)
            for i in preparation.CORRECTED_INDICES:
                original, corrected = json.loads(before[i]), json.loads(after[i])
                restored = deepcopy(corrected)
                restored['messages'][-1] = original['messages'][-1]
                self.assertEqual(restored, original)
            self.assertEqual((old/'valid.jsonl').read_bytes(), (folder/'valid.jsonl').read_bytes())
            for key in ('counts','added_dataset','held_out','historical_regression_held_out','fresh_controls','held_out_count'):
                self.assertEqual(current[key], prior[key])
            source = ROOT/'training/datasets'/prior['added_dataset']['version']
            for name in ('train.jsonl','valid.jsonl'):
                self.assertEqual((folder/name).read_bytes(), (parent/name).read_bytes()+(source/name).read_bytes())
            check_labels(list(map(json.loads, after)))
            with self.assertRaisesRegex(ValueError,'Known incorrect'):
                check_labels(list(map(json.loads, before)))

    def test_every_frozen_evaluation_file_is_unchanged(self):
        for stage, old, folder, parent in self.stages():
            manifest = json.loads((folder/'manifest.json').read_text())
            for name, info in {**manifest['held_out'], **manifest['historical_regression_held_out']}.items():
                raw = (ROOT/name).read_bytes()
                self.assertEqual(preparation.digest(raw),info['sha256'])
                self.assertEqual(len(raw.splitlines()),info['count'])

    def test_rehearsal_checks_complete_datasets_without_correction_exception(self):
        expected={'gestion_magasin':(2690,362,72,10),'reservation':(2870,402,84,12)}
        for stage, old, folder, parent in self.stages():
            result, rows, captures, lineage = prepare_inputs(folder,stage,parent)
            train,valid,size,captured=expected[stage]
            self.assertEqual(result['rows_checked'],{'train':train,'valid':valid})
            self.assertEqual(result['rehearsal']['count'],size)
            self.assertEqual({key:len(value) for key,value in captures.items()},{'train':captured,'valid':captured})
            self.assertEqual(lineage['retention_mode'],'exact retained bytes')
            self.assertNotIn('corrections',lineage)

    def test_both_runtime_entrypoints_admit_each_stage_before_weights(self):
        for stage, old, folder, parent in self.stages():
            for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
                with self.subTest(stage=stage,script=script),self.assertRaises(startup.BeforeModelLibraries):
                    startup.CorrectedSerialRuntimeTests.start(self,script,folder,parent,stage=stage,correction_root=None)

    def test_skipped_predecessors_fail_before_model_imports(self):
        wrong = ROOT/'training/datasets/shared-v5r8-en-fr'
        for stage, old, folder, parent in self.stages():
            for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
                with self.subTest(stage=stage,script=script),self.assertRaises(SystemExit):
                    startup.CorrectedSerialRuntimeTests.start(self,script,folder,wrong,stage=stage,correction_root=None)
            with self.assertRaises(ValueError):
                prepare_inputs(folder,stage,wrong)

    def test_changed_retained_row_rejects_even_with_rehashed_current_split(self):
        for stage, old, folder, parent in self.stages():
            manifest=json.loads((folder/'manifest.json').read_text())
            lines=(folder/'train.jsonl').read_bytes().splitlines(keepends=True)
            row=json.loads(lines[100]);row['messages'][-2]['content']+=' changed request'
            lines[100]=(json.dumps(row)+'\n').encode();raw=b''.join(lines)
            manifest['files']['train.jsonl']=preparation.digest(raw)
            with self.assertRaisesRegex(ValueError,'byte-for-byte'):
                validate_retained_curriculum(stage,manifest,raw,(folder/'valid.jsonl').read_bytes(),parent)

    def test_changed_manifest_or_file_cannot_reuse_reviewed_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            (folder/'train.jsonl').write_bytes(b'{}\n')
            raw=json.dumps({'files':{'train.jsonl':preparation.digest(b'{}\n')}}).encode()
            (folder/'manifest.json').write_bytes(raw)
            wanted=preparation.digest(raw)
            preparation.checked(folder,wanted)
            (folder/'train.jsonl').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'split changed'):
                preparation.checked(folder,wanted)
            (folder/'manifest.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError,'manifest changed'):
                preparation.checked(folder,wanted)

    def test_unknown_stage_stale_base_helper_drift_and_overwrite_fail(self):
        parent=ROOT/'training/datasets'/preparation.BASE
        with self.assertRaisesRegex(ValueError,'Only the two final'):
            preparation.assemble('contrat',parent,preparation.BASE_SHA256)
        with self.assertRaisesRegex(ValueError,'manifest changed'):
            preparation.assemble('gestion_magasin',parent,'0'*64)
        with patch.object(preparation,'PROMPT_HELPER_SHA256','0'*64),self.assertRaisesRegex(ValueError,'helper changed'):
            preparation.assemble('gestion_magasin',parent,preparation.BASE_SHA256)
        with self.assertRaisesRegex(ValueError,'Never overwrite'):
            preparation.prepare()


if __name__=='__main__':
    unittest.main()
