"""Configuration-only startup simulations; imports stop before model libraries."""
import ast
import builtins
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import textwrap
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=ROOT/'training/scripts'
sys.path.insert(0,str(SCRIPTS))
import rehearse_cpu_v2 as rehearsal
import prepare_serial_name_corrections as preparation


class BeforeModelLibraries(Exception):
    pass


class CorrectedSerialRuntimeTests(unittest.TestCase):
    def start(self,script,data,retained,*,stage='contrat',platform='Linux',server='1',correction_root=ROOT):
        original=builtins.__import__
        def bounded(name,*args,**kwargs):
            if name in ('torch','transformers','psutil'):
                raise BeforeModelLibraries
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'unused-output'
            argv=[script,'--stage',stage,'--data',str(data),'--retained-data',str(retained),
                  '--model',str(Path(temporary)/'no-model-exists'),'--output',str(output)]
            if correction_root is not None:
                argv+=['--correction-root',str(correction_root)]
            if script.startswith('train_cpu'):
                argv+=['--complete-epochs','1']
            try:
                with patch.object(sys,'argv',argv),patch('platform.system',return_value=platform),\
                     patch.dict(os.environ,{'CHAT_AI_TRAINING_SERVER':server}),\
                     patch('builtins.__import__',side_effect=bounded):
                    runpy.run_path(str(SCRIPTS/script),run_name='__main__')
            finally:
                self.assertFalse(output.exists(),'Startup simulation must never create training output')

    def test_trainer_and_capacity_admit_only_the_corrected_preparation_before_weights(self):
        data=ROOT/'training/datasets/shared-v6r10-en-fr'
        parent=ROOT/'training/datasets/shared-v5r8-en-fr'
        for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
            with self.subTest(script=script),self.assertRaises(BeforeModelLibraries):
                self.start(script,data,parent)

    def test_missing_artifact_root_fails_before_model_imports(self):
        data=ROOT/'training/datasets/shared-v6r10-en-fr'
        parent=ROOT/'training/datasets/shared-v5r8-en-fr'
        for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
            with self.subTest(script=script), self.assertRaisesRegex(SystemExit, 'Explicit correction artifact root'):
                self.start(script,data,parent,correction_root=None)
        with self.assertRaisesRegex(ValueError, 'Explicit correction artifact root'):
            rehearsal.prepare_inputs(data,'contrat',parent)

    def test_isolated_server_layout_works_without_repository_relative_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            isolated=Path(temporary)
            scripts=isolated/'scripts'; scripts.mkdir()
            names=set(rehearsal.DEPENDENCY_NAMES) | {'rehearse_cpu_v2.py','train_cpu_serial_v4.py','probe_cpu_serial_v2.py','validation_selection.py'}
            for name in names:
                shutil.copyfile(SCRIPTS/name,scripts/name)
            shutil.copytree(ROOT/'training/datasets/shared-v6r10-en-fr',isolated/'data')
            shutil.copytree(ROOT/'training/datasets/shared-v5r8-en-fr',isolated/'accepted-data')
            controls=isolated/'controls'
            for version in ('shared-v5r9-en-fr','management-name-errata-v2-en-fr'):
                source=ROOT/'training/datasets'/version
                destination=controls/'training/datasets'/version
                destination.mkdir(parents=True)
                wanted=('manifest.json','train.jsonl','valid.jsonl') if version.startswith('shared') else ('manifest.json','train.replacements.jsonl')
                for name in wanted:
                    shutil.copyfile(source/name,destination/name)
            manifest=json.loads((ROOT/'training/datasets/shared-v5r9-en-fr/manifest.json').read_text())
            for name in set(manifest['held_out'])|set(manifest['historical_regression_held_out']):
                destination=controls/name;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,destination)
            code=textwrap.dedent("""
                import builtins, os, platform, runpy, sys
                from pathlib import Path
                root=Path(sys.argv[1]);scripts=root/'scripts'
                sys.path.insert(0,str(scripts))
                class BeforeModelLibraries(Exception):pass
                original=builtins.__import__
                def bounded(name,*args,**kwargs):
                    if name in ('torch','transformers','psutil'):
                        raise BeforeModelLibraries
                    return original(name,*args,**kwargs)
                builtins.__import__=bounded
                platform.system=lambda:'Linux'
                os.environ['CHAT_AI_TRAINING_SERVER']='1'
                for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
                    sys.argv=[script,'--stage','contrat','--data',str(root/'data'),
                              '--retained-data',str(root/'accepted-data'),
                              '--correction-root',str(root/'controls'),
                              '--model',str(root/'absent-model'),'--output',str(root/'absent-output')]
                    if script.startswith('train_cpu'):sys.argv+=['--complete-epochs','1']
                    try:runpy.run_path(str(scripts/script),run_name='__main__')
                    except BeforeModelLibraries:pass
                    else:raise AssertionError('Expected the model import sentinel')
                import rehearse_cpu_v2 as rehearsal
                rehearsal.verify_sources(scripts/'train_cpu_serial_v4.py')
                result,rows,captures,lineage=rehearsal.prepare_inputs(root/'data','contrat',root/'accepted-data',root/'controls')
                assert result['rows_checked']=={'train':2492,'valid':319}
                assert lineage['corrections']['replaced_targets']==6
                assert not lineage['model_acceptance_verified']
                for name in ('serial_scope_v3','serial_scope_v2','prepare_management_name_errata','prepare_management_name_errata_v2','rehearse_cpu_v2'):
                    assert Path(sys.modules[name].__file__).parent==scripts,name
                assert not (root/'absent-output').exists()
                print('isolated startup and full curriculum checks passed; no weights loaded')
            """)
            result=subprocess.run([sys.executable,'-B','-c',code,str(isolated)],cwd=isolated,
                                  text=True,capture_output=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('no weights loaded',result.stdout)

    def test_wrong_base_and_server_scope_fail_before_model_imports(self):
        data=ROOT/'training/datasets/shared-v6r10-en-fr'
        for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
            for retained,platform,flag in (
                    ('shared-v5r9-en-fr','Linux','1'),
                    ('shared-v5r8-en-fr','Darwin','1'),
                    ('shared-v5r8-en-fr','Linux','0')):
                with self.subTest(script=script,base=retained,platform=platform),self.assertRaises(SystemExit):
                    self.start(script,data,ROOT/'training/datasets'/retained,platform=platform,server=flag)

    def test_trainer_capacity_and_rehearsal_reject_the_same_unreviewed_row_change(self):
        original=ROOT/'training/datasets/shared-v6r10-en-fr'
        parent=ROOT/'training/datasets/shared-v5r8-en-fr'
        with tempfile.TemporaryDirectory() as temporary:
            data=Path(temporary)
            raw=(original/'train.jsonl').read_bytes()
            lines=raw.splitlines(keepends=True);row=json.loads(lines[100])
            row['messages'][-2]['content']+=' unrelated scope change'
            lines[100]=(json.dumps(row)+'\n').encode();changed=b''.join(lines)
            manifest=json.loads((original/'manifest.json').read_text())
            manifest['files']['train.jsonl']=hashlib.sha256(changed).hexdigest()
            (data/'train.jsonl').write_bytes(changed)
            (data/'valid.jsonl').write_bytes((original/'valid.jsonl').read_bytes())
            (data/'manifest.json').write_text(json.dumps(manifest))
            for script in ('train_cpu_serial_v4.py','probe_cpu_serial_v2.py'):
                with self.subTest(script=script),self.assertRaisesRegex(SystemExit,'corrected prefix'):
                    self.start(script,data,parent)
            with self.assertRaisesRegex(ValueError,'corrected prefix'):
                rehearsal.prepare_inputs(data,'contrat',parent,ROOT)

    def test_rehearsal_validates_the_full_corrected_curriculum_before_selection(self):
        data=ROOT/'training/datasets/shared-v6r10-en-fr'
        parent=ROOT/'training/datasets/shared-v5r8-en-fr'
        result,rows,captures,lineage=rehearsal.prepare_inputs(data,'contrat',parent,ROOT)
        self.assertEqual(result['rows_checked'],{'train':2492,'valid':319})
        self.assertEqual(lineage['corrections']['replaced_targets'],6)
        self.assertFalse(lineage['model_acceptance_verified'])
        self.assertLessEqual(set(captures['train']),set(result['rehearsal']['row_indices']))
        self.assertEqual(len(captures['valid']),8)
        self.assertEqual(set(rows),{'train','valid'})

    def test_training_numerics_remain_identical_to_reviewed_versions(self):
        pairs=(('train_cpu_serial_v3.py','train_cpu_serial_v4.py'),
               ('probe_cpu_serial_v1.py','probe_cpu_serial_v2.py'))
        for old,new in pairs:
            expected=(SCRIPTS/old).read_text().replace('from serial_scope_v2 import','from serial_scope_v3 import')
            expected=expected.replace("with_name('serial_scope_v2.py')","with_name('serial_scope_v3.py')")
            if old.startswith('train_cpu'):
                expected=expected.replace("p.add_argument('--model'", "p.add_argument('--correction-root',type=Path);p.add_argument('--model'")
                expected=expected.replace('validation_bytes,a.retained_data)', 'validation_bytes,a.retained_data,correction_root=a.correction_root)')
            else:
                expected=expected.replace("    parser.add_argument('--model'", "    parser.add_argument('--correction-root', type=Path)\n    parser.add_argument('--model'")
                expected=expected.replace('valid_payload, args.retained_data)', 'valid_payload, args.retained_data, correction_root=args.correction_root)')
            self.assertEqual(expected,(SCRIPTS/new).read_text())
        source=[]
        for name in ('train_cpu.py','train_cpu_serial_v4.py'):
            path=SCRIPTS/name;tree=ast.parse(path.read_text())
            source.append({node.name:ast.dump(node,include_attributes=False) for node in tree.body
                           if isinstance(node,ast.FunctionDef) and node.name in rehearsal.FUNCTIONS})
            namespace=rehearsal.trainer_functions(path,rehearsal.digest(path.read_bytes()))
            self.assertNotIn('torch',namespace);self.assertNotIn('model',namespace)
        self.assertEqual(source[0],source[1])

    def test_trainer_and_rehearsal_retention_helpers_must_match(self):
        trainer=SCRIPTS/'train_cpu_serial_v4.py'
        rehearsal.verify_sources(trainer)
        helpers=('semantic_loss.py','text_lora.py','serial_scope_v3.py','serial_scope_v2.py',
                 'prepare_management_name_errata.py','prepare_management_name_errata_v2.py')
        with tempfile.TemporaryDirectory() as temporary:
            other=Path(temporary)
            for name in helpers:
                (other/name).write_bytes((SCRIPTS/name).read_bytes())
            for name in helpers:
                original=(other/name).read_bytes();(other/name).write_bytes(original+b'\n# drift\n')
                with self.subTest(helper=name),self.assertRaisesRegex(ValueError,'Trainer helper differs'):
                    rehearsal.verify_sources(other/'train_cpu_serial_v4.py')
                (other/name).write_bytes(original)

    def test_new_rehearsal_detects_old_and_new_model_jobs(self):
        class Absent(Exception):pass
        for name in ('train_cpu.py','train_cpu_serial_v3.py','train_cpu_serial_v4.py',
                     'probe_cpu_serial_v1.py','probe_cpu_serial_v2.py','rehearse_cpu.py','rehearse_cpu_v2.py'):
            fake=SimpleNamespace(NoSuchProcess=Absent,AccessDenied=Absent,
                process_iter=lambda fields:[SimpleNamespace(info={'pid':os.getpid()+1,'cmdline':['python',name]})])
            with self.subTest(job=name),self.assertRaisesRegex(RuntimeError,'Another trainer'):
                rehearsal.no_other_optimizer(fake)

    def test_preparation_reconstructs_exact_generated_files_and_hashes(self):
        payloads,manifest=preparation.assemble()
        folder=ROOT/'training/datasets/shared-v6r10-en-fr'
        self.assertEqual(manifest,json.loads((folder/'manifest.json').read_text()))
        for name,raw in payloads.items():
            self.assertEqual(raw,(folder/name).read_bytes())
        self.assertEqual(manifest['generator_sha256'],hashlib.sha256(Path(preparation.__file__).read_bytes()).hexdigest())
        self.assertTrue(manifest['model_binding']['status'].startswith('UNBOUND'))


if __name__=='__main__':
    unittest.main()
