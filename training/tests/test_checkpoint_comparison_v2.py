"""Validate fallback comparison preparation without inference or model weights."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'training/scripts'))
from prepare_checkpoint_comparison_v2 import prepare, bind_completed_training, select_completed, STEPS
from model_acceptance import clarification_message

class FallbackComparisonTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.output=Path(self.folder.name)/'prepared'
        self.policy=prepare(self.output)
        self.rows=list(map(json.loads,(self.output/'validation.eval.jsonl').read_text().splitlines()))
        self.report={'steps':1969,'training_config':{'complete_epochs':1,'checkpoint_interval_steps':300,'validation_interval_steps':300},
                     'dataset_sha256':self.policy['training_sha256'],'validation_sha256':self.policy['source_validation_sha256'],
                     'steps_metrics':[{'step':n} for n in range(1,1970)],
                     'validation_history':[{'step':n,'loss':{'macro':.07+n/100000}} for n in STEPS]}
    def test_reconstructs_exact_existing_inputs_and_keeps_baseline_eligible(self):
        self.assertEqual(len(self.rows),275)
        self.assertEqual(len({r['scenario_group'] for r in self.rows}),222)
        self.assertEqual([r['step'] for r in bind_completed_training(self.policy,self.report)['candidates']],STEPS)
        with self.assertRaisesRegex(ValueError,'Never overwrite'):prepare(self.output)
    def test_rejects_partial_coverage_changed_data_and_missing_checkpoints(self):
        for kind in ('incomplete','changed_data','missing_validation','nan','wrong_schedule'):
            bad=deepcopy(self.report)
            if kind=='incomplete':bad['steps_metrics'].pop()
            elif kind=='changed_data':bad['dataset_sha256']='changed'
            elif kind=='missing_validation':bad['validation_history'].pop(0)
            elif kind=='nan':bad['validation_history'][0]['loss']['macro']=float('nan')
            else:bad['training_config']['validation_interval_steps']=600
            with self.subTest(kind=kind),self.assertRaises(ValueError):bind_completed_training(self.policy,bad)
    def cases(self):
        result={}
        for row in self.rows:
            expected=row['expected'];action={'tool':expected['tool'],'arguments':deepcopy(expected['arguments'])}
            if expected['tool']=='clarify':action={'tool':'clarify','message':clarification_message(**expected['arguments'])}
            result[row['id']]={key:row[key] for key in ('id','category','language','expected')}
            result[row['id']].update(action=action,tool_correct=True,arguments_correct=True,structured_valid=True)
        return result
    def test_actual_action_accuracy_outweighs_loss_and_requires_every_candidate(self):
        cases=self.cases();results={step:deepcopy(cases) for step in STEPS}
        item=next(r for r in self.rows if r['expected']['tool'] not in ('clarify','knowledge'))
        results[0][item['id']].update(action={'tool':'clarify','message':'unsupported'},tool_correct=False,arguments_correct=False)
        self.assertEqual(select_completed(self.policy,self.report,self.rows,results)['selected_step'],300)
        del results[600]
        with self.assertRaises(ValueError):select_completed(self.policy,self.report,self.rows,results)
    def test_changed_prompts_scoring_or_shortlist_reject(self):
        results={step:self.cases() for step in STEPS}
        for kind in ('prompt','scorer','shortlist'):
            policy=deepcopy(self.policy);rows=deepcopy(self.rows)
            if kind=='prompt':rows[0]['messages'][-1]['content']='changed'
            elif kind=='scorer':policy['script_sha256']='changed'
            else:policy['candidate_steps']=STEPS[1:]
            with self.subTest(kind=kind),self.assertRaises(ValueError):select_completed(policy,self.report,rows,results)
