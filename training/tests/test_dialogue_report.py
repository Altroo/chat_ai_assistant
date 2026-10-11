"""Report validation uses temporary synthetic evidence, never real model scores."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'training/scripts'))
import report_dialogue_candidate as report
from model_acceptance import assess, FROZEN_EVALUATOR_SHA256


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value))


def lines(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows))


class DialogueReportTests(unittest.TestCase):
    def fixture(self,root):
        data=root/'training/datasets/frozen-synthetic';candidate=root/'candidate';baseline=root/'baseline';evaluations=root/'events'
        snapshots=[];old_events=[];inputs={};files={};sets={}
        for app,count,correct in [('facturation',96,True),('management_projet',4,False)]:
            name=app+'.jsonl';label='candidate-'+app
            rows=[{'id':app+'-'+str(i),'category':'synthetic','language':'en',
                   'trusted_context':{'application':app},
                   'expected':{'tool':'search_records','arguments':{'resource':'project'}}} for i in range(count)]
            old=[{**row,'action':{'tool':'search_records','arguments':{'resource':'project'}},'structured_valid':True} for row in rows]
            actual=copy.deepcopy(old)
            if not correct:
                for row in actual:row['action']={'tool':'clarify','message':'Wrong synthetic action'}
            lines(data/name,rows);lines(evaluations/label/'events.jsonl',[{'case':row} for row in actual])
            write(evaluations/label/'summary.json',{'dataset_sha256':report.sha(data/name),
                'evaluator_sha256':FROZEN_EVALUATOR_SHA256,'model_id':'synthetic-candidate',
                'max_output_tokens':512,'thinking':False,'mode':'native','metrics':{'count':count}})
            inputs[name]={'count':count};files[name]=report.sha(data/name);sets['frozen-synthetic/'+name]=label
            snapshots+=rows;old_events+=old
        write(data/'manifest.json',{'version':'synthetic-only','inputs':inputs,'files':files})
        write(candidate/'evaluation-complete.json',{'manifest_sha256':report.sha(data/'manifest.json'),
            'sets':sets,'provider_sha256':{'provider.py':'synthetic-hash'},'model_id':'synthetic-candidate','count':100,'driver_sha256':'synthetic-driver-hash'})
        for name in ('inference-attestation.json','inference-post-evaluation-attestation.json'):
            write(candidate/name,{'model_id':'synthetic-candidate','model_path':'/synthetic/model',
                'runtime_path':'/synthetic/runtime','ctx':8192,'max_tokens':512,'thinking':False,
                'artifacts':{'weights':{'sha256':'synthetic-weight-hash'}}})
        for name in ('candidate-process-before.json','candidate-process-after.json'):
            write(candidate/name,{'pid':123,'cmd':['python3','/synthetic/runtime/c/coli','serve',
                '--model','/synthetic/model','--no-tune-profile','--ctx','8192','--gpu','none',
                '--ngen','512','--no-think','--temp','0','--host','127.0.0.1','--port','18001',
                '--model-id','synthetic-candidate','--max-queue','2','--queue-timeout','10','--kv-slots','1','']})
        write(baseline/'baseline-complete.json',{'provider_sha256':{'provider.py':'synthetic-hash'},'model':'synthetic-baseline'})
        baseline_report=root/'published-baseline.json'
        write(baseline_report,{'manifest_sha256':report.sha(data/'manifest.json'),'model_id':'synthetic-baseline',
            'reframed':assess(snapshots,old_events)})
        lines(baseline/'combined-events.jsonl',[{'case':row} for row in old_events])
        write(baseline/'baseline-report.json',{'report_sha256':report.sha(baseline_report)})
        driver_proof=root/'pinned-driver.json'
        write(driver_proof,{'driver_sha256':'synthetic-driver-hash','model':'synthetic-baseline',
            'provider_sha256':{'provider.py':'synthetic-hash'},'evaluator_sha256':FROZEN_EVALUATOR_SHA256})
        return data,candidate,baseline,baseline_report,evaluations,driver_proof

    def test_aggregate_pass_does_not_hide_a_failed_application_set(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);args=self.fixture(root)
            with patch.object(report,'ROOT',root):result=report.build(*args)
            self.assertTrue(result['candidate']['model_targets_passed'])
            self.assertFalse(result['all_frozen_sets_passed'])
            self.assertEqual(result['candidate']['metrics']['percent']['tool_correct'],96)
            self.assertFalse(result['candidate_by_application']['management_projet']['model_targets_passed'])
            self.assertIsNone(result['native_backend_security_verified'])
            self.assertEqual(result['production_activation'],'NOT AUTHORIZED BY THIS REPORT')

    def test_changed_model_provider_process_and_artifacts_are_rejected(self):
        changes=[('candidate/evaluation-complete.json','model_id','another-model'),
                 ('candidate/evaluation-complete.json','provider_sha256',{}),
                 ('candidate/evaluation-complete.json','driver_sha256','changed'),
                 ('pinned-driver.json','model','another-baseline'),
                 ('candidate/inference-post-evaluation-attestation.json','model_id','another-model'),
                 ('candidate/inference-post-evaluation-attestation.json','ctx',4096),
                 ('candidate/evaluation-complete.json','sets',{}),
                 ('candidate/evaluation-complete.json','count',99),
                 ('candidate/candidate-process-after.json','pid',124),
                 ('candidate/inference-post-evaluation-attestation.json','artifacts',{})]
        for name,key,value in changes:
            with self.subTest(name=name,key=key),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);args=self.fixture(root);path=root/name;data=report.read(path);data[key]=value;write(path,data)
                with patch.object(report,'ROOT',root),self.assertRaises(ValueError):report.build(*args)

    def test_changed_labels_config_incomplete_and_duplicate_events_are_rejected(self):
        for mutation in ('labels','duplicate','missing','tokens','evaluator'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);args=self.fixture(root);data,candidate,baseline,old,evaluations,driver_proof=args
                event_path=evaluations/'candidate-management_projet/events.jsonl'
                if mutation in ('labels','duplicate','missing'):
                    events=report.cases(event_path)
                    if mutation=='labels':events[0]['expected']['arguments']['resource']='customer'
                    elif mutation=='duplicate':events.append(events[0])
                    else:events.pop()
                    lines(event_path,[{'case':row} for row in events])
                else:
                    path=event_path.with_name('summary.json');summary=report.read(path)
                    summary['max_output_tokens' if mutation=='tokens' else 'evaluator_sha256']=1024
                    write(path,summary)
                with patch.object(report,'ROOT',root),self.assertRaises(ValueError):report.build(*args)

    def test_matching_but_unrelated_process_is_rejected(self):
        for mutation in ('runtime','model','config','identity','duplicate-flag','pid'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as folder:
                root=Path(folder);args=self.fixture(root);candidate=args[1]
                process=report.read(candidate/'candidate-process-before.json')
                cmd=process['cmd']
                if mutation=='runtime':cmd[1]='/unrelated/runtime/c/coli'
                elif mutation=='model':cmd[cmd.index('--model')+1]='/unrelated/model'
                elif mutation=='config':cmd[cmd.index('--ngen')+1]='1024'
                elif mutation=='identity':cmd[cmd.index('--model-id')+1]='unrelated-model'
                elif mutation=='duplicate-flag':cmd[-1:-1]=['--ngen','1024']
                else:process['pid']=0
                for name in ('candidate-process-before.json','candidate-process-after.json'):
                    write(candidate/name,process)
                with patch.object(report,'ROOT',root),self.assertRaises(ValueError):report.build(*args)
