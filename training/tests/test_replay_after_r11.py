"""Synthetic R11 admission tests; no model libraries, network or business data."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import replay_contracts_after_r11 as supervisor
from training.tests import test_replay_supervisor as shared_tests
original_fixture = shared_tests.predecessor_fixture

# Frozen evaluation denominators only. All successes below are synthetic fixtures,
# never model accuracy measurements or accepted model evidence.
ARGUMENT_COUNTS = {
 'shared-adapter-v2-en-fr--design-workflow-v1-en-fr--test.eval.jsonl':48,
 'shared-adapter-v2-en-fr--design-workflow-v2-en-fr--independent.eval.jsonl':18,
 'shared-adapter-v2-en-fr--design-workflow-v3-en-fr--independent.eval.jsonl':14,
 'shared-adapter-v2-en-fr--design-workflow-refinement-v1-en-fr--independent.eval.jsonl':8,
 'shared-adapter-v2-en-fr--facturation-acceptance-en-fr--test.eval.jsonl':66,
 'shared-adapter-v2-en-fr--facturation-refinement-v1-en-fr--independent.eval.jsonl':8,
 'shared-adapter-v2-en-fr--management-projet-v1-en-fr--test.eval.jsonl':50,
 'shared-adapter-v2-en-fr--management-projet-v2-en-fr--independent.eval.jsonl':14,
 'shared-adapter-v2-en-fr--management-projet-v3-en-fr--independent.eval.jsonl':26,
 'shared-adapter-v2-en-fr--management-projet-v4-en-fr--independent.eval.jsonl':20,
 'shared-adapter-v2-en-fr--management-projet-refinement-v1-en-fr--independent.eval.jsonl':8,
 'shared-adapter-v2-en-fr--management-projet-followup-v1-en-fr--independent.eval.jsonl':20,
 'facturation-refinement-v2-en-fr--independent.eval.jsonl':12,
 'management-projet-refinement-v2-en-fr--independent.eval.jsonl':10,
 'design-workflow-refinement-v2-en-fr--independent.eval.jsonl':12,
}


def assessment(count, arguments):
    return {'model_targets_passed':True, 'metrics':{'count':count,
        'counts':{'tool_correct':count,'structured_valid':count,'action_matches':count},
        'exact_arguments':{'count':arguments,'passed':arguments}}}


def fixture(root, step=1200):
    binding, plan, proofs, persist, artifacts = original_fixture(root)
    changed = {}
    for name, value in proofs.items():
        value = deepcopy(value)
        for key in ('step', 'selected_step'):
            if key in value:value[key] = step
        changed[name.replace('-900-', '-'+str(step)+'-')] = value
    proofs.clear(); proofs.update(changed)
    binding['base'] = binding['base'].replace('step-900', 'step-'+str(step))
    retained = ROOT / 'training/datasets/shared-v5r11-en-fr'
    manifest = json.loads((retained / 'manifest.json').read_text())
    binding['predecessor']['retained_data'] = str(retained)
    plan['retained_dataset'] = {'manifest_sha256':supervisor.file_sha(retained / 'manifest.json'),
                                'files':manifest['files']}
    proofs['validation-0-collect.json']['report'] = {
        'steps':2419,'dataset_sha256':manifest['files']['train.jsonl'],
        'validation_sha256':manifest['files']['valid.jsonl']}
    sets=[]
    for name, info in manifest['held_out'].items():
        name=Path(name).name
        if name=='controls.eval.jsonl':continue
        sets.append({'dataset':name,'assessment':assessment(info['count'],ARGUMENT_COUNTS[name])})
    proofs['acceptance.json'].update(assessment=assessment(438,334),sets=sets)
    proofs['fresh.json'].update(assessment=assessment(48,36),by_application={
        app:assessment(16,args) for app,args in
        [('facturation',14),('management_projet',10),('design_workflow',12)]})
    persist()
    return binding,plan,proofs,persist,artifacts


class R11PredecessorTests(unittest.TestCase):
    def check(self,binding,plan,artifacts):
        with patch.object(supervisor,'served_artifacts',return_value=artifacts):
            return supervisor.check_predecessor(binding,plan)

    def test_all_declared_changed_r11_checkpoints_can_pass(self):
        for step in supervisor.R11_CANDIDATES:
            with self.subTest(step=step),tempfile.TemporaryDirectory() as temp:
                b,p,_,_,a=fixture(Path(temp),step)
                self.assertEqual(self.check(b,p,a)['step'],step)

    def test_unfinished_unaccepted_baseline_and_undeclared_steps_reject(self):
        for key,value in [('phase','waiting_for_training'),('accepted',False),
                          ('regression_passed',False),('fresh_passed',False),
                          ('selected_step',0),('selected_step',900),('selected_step',True)]:
            with self.subTest(key=key,value=value),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                proofs['pipeline-state.json'][key]=value;persist()
                with self.assertRaises(ValueError):self.check(b,p,a)

    def test_r8_or_another_trained_curriculum_cannot_be_relabelled_r11(self):
        for mutation in ('steps','training_hash','validation_hash','retained_manifest','plan_stage'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                report=proofs['validation-0-collect.json']['report']
                if mutation=='steps':report['steps']=2339
                if mutation=='training_hash':report['dataset_sha256']='wrong'
                if mutation=='validation_hash':report['validation_sha256']='wrong'
                if mutation=='retained_manifest':b['predecessor']['retained_data']=str(Path(temp)/'retained')
                if mutation=='plan_stage':p['stage']='gestion_magasin'
                persist()
                with self.assertRaises(ValueError):self.check(b,p,a)

    def test_failed_app_cannot_hide_behind_true_flags_or_high_overall_score(self):
        for metric in ('action_matches','tool_correct','structured_valid','arguments'):
            with self.subTest(metric=metric),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                report=proofs['acceptance.json']
                selected=next(x for x in report['sets'] if 'facturation-acceptance' in x['dataset'])
                m=selected['assessment']['metrics'];total=report['assessment']['metrics']
                if metric=='arguments':
                    m['exact_arguments']['passed']-=5
                    total['exact_arguments']['passed']-=5
                else:
                    amount=2 if metric=='structured_valid' else 6
                    m['counts'][metric]-=amount;total['counts'][metric]-=amount
                persist()
                with self.assertRaisesRegex(ValueError,'Per-application acceptance target'):
                    self.check(b,p,a)

    def test_fresh_action_and_argument_failures_reject_even_with_true_flags(self):
        for metric in ('action_matches','arguments'):
            with self.subTest(metric=metric),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                fresh=proofs['fresh.json']
                m=fresh['by_application']['facturation']['metrics'];total=fresh['assessment']['metrics']
                if metric=='arguments':
                    m['exact_arguments']['passed']-=1;total['exact_arguments']['passed']-=1
                else:
                    m['counts'][metric]-=1;total['counts'][metric]-=1
                persist()
                with self.assertRaisesRegex(ValueError,'Per-application acceptance target'):
                    self.check(b,p,a)

    def test_missing_duplicate_and_wrong_count_regressions_reject(self):
        for mutation in ('missing','duplicate','case_count','argument_count'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                sets=proofs['acceptance.json']['sets']
                if mutation=='missing':sets.pop()
                if mutation=='duplicate':sets[-1]=deepcopy(sets[0])
                if mutation=='case_count':sets[0]['assessment']['metrics']['count']-=1
                if mutation=='argument_count':sets[0]['assessment']['metrics']['exact_arguments']={'count':47,'passed':47}
                persist()
                with self.assertRaises(ValueError):self.check(b,p,a)

    def test_invalid_and_inconsistent_counts_reject(self):
        for value in (True,-1,float('nan'),999):
            with self.subTest(value=value),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                proofs['acceptance.json']['assessment']['metrics']['counts']['action_matches']=value
                persist()
                with self.assertRaises(ValueError):self.check(b,p,a)

    def test_proof_model_identity_and_worker_cleanup_remain_required(self):
        for mutation in ('proof','after','stop','base','served'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                b,p,proofs,persist,a=fixture(Path(temp))
                if mutation=='after':proofs['fresh-1200-after.json']['worker']='changed'
                if mutation=='stop':proofs['fresh-1200-stop.json']['stopped_workers']=2
                if mutation=='base':b['base']=b['base'].replace('step-1200','step-600')
                if mutation=='served':a={'changed':True}
                persist()
                if mutation=='proof':
                    (Path(b['predecessor']['evidence_root'])/'pipeline-state.json').write_text('{}')
                with self.assertRaises(ValueError):self.check(b,p,a)

class RunExistingBehaviorAgainstR11:
    def setUp(self):
        replacement=patch.object(shared_tests,'supervisor',supervisor)
        replacement.start()
        self.addCleanup(replacement.stop)


class R11NumericalTests(RunExistingBehaviorAgainstR11, shared_tests.NumericalTests):
    pass


class R11IsolationTests(RunExistingBehaviorAgainstR11, shared_tests.IsolationTests):
    pass


class R11SupervisorFlowTests(RunExistingBehaviorAgainstR11, shared_tests.SupervisorFlowTests):
    pass


class R11SourceAdmissionTests(RunExistingBehaviorAgainstR11, shared_tests.SourceAdmissionTests):
    pass


if __name__=='__main__':
    unittest.main()
