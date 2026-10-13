"""Context changes must change the expected target without relaxing access."""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_selection_contrasts import (ROOT, NOW, BARE, context, state, generate,
    current_request, function, digest, ordinal_target_matches)
from jsonschema import validate

class SelectionContrastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder=ROOT/'training/datasets/selection-contrasts-v1-en-fr'
        cls.manifest=json.loads((cls.folder/'manifest.json').read_text())
        cls.parent=ROOT/'training/datasets/shared-v5r6-en-fr'
        cls.sources=list(map(json.loads,(cls.parent/'train.jsonl').read_text().splitlines()))
        cls.rows=list(map(json.loads,(cls.folder/'train.jsonl').read_text().splitlines()))
        cls.aliases=cls.manifest['native_aliases']

    def test_exact_reconstruction_and_parent_binding(self):
        m=self.manifest
        self.assertEqual(digest(self.parent/'manifest.json'),m['parent_manifest_sha256'])
        self.assertEqual(digest(self.parent/'train.jsonl'),m['source_training_sha256'])
        self.assertEqual(digest(ROOT/'training/scripts/prepare_selection_contrasts.py'),m['generator_sha256'])
        self.assertEqual(digest(self.folder/'train.jsonl'),m['files']['train.jsonl'])
        rows,proof=generate(self.sources,self.aliases)
        self.assertEqual(rows,self.rows);self.assertEqual(proof,m['provenance'])
        self.assertEqual(len(rows),96);self.assertEqual(len({p['source_index'] for p in proof}),36)

    def test_native_ordinal_guard_agrees_for_every_expected_target(self):
        for row,proof in zip(self.rows,self.manifest['provenance']):
            source=self.sources[proof['source_index']];args=function(source)['arguments'];ctx=context(row)
            if proof['kind']=='rebound':identifier=function(row)['arguments']['identifier']
            else:identifier=args['identifier']
            with self.subTest(source=proof['source_index'],kind=proof['kind']):
                self.assertIs(ordinal_target_matches(current_request(row),args['resource'],identifier,state(ctx),NOW,self.aliases),proof['kind']=='rebound')
                if proof['kind']!='rebound':
                    self.assertEqual(function(row)['name'],'clarify')
                    self.assertEqual(function(row)['arguments']['reason'],'missing_details')

    def test_preserves_request_values_permissions_and_other_context(self):
        allowed={'previous_result_type','previous_result_count','previous_result_identifiers'}
        for row,proof in zip(self.rows,self.manifest['provenance']):
            original=self.sources[proof['source_index']]
            self.assertEqual(row['messages'][1],original['messages'][1])
            self.assertEqual({k:v for k,v in context(row).items() if k not in allowed},
                             {k:v for k,v in context(original).items() if k not in allowed})
            self.assertEqual(row['messages'][0]['content'].split('Trusted context: ',1)[0],
                             original['messages'][0]['content'].split('Trusted context: ',1)[0])
            if proof['kind']=='rebound':
                a=deepcopy(function(row));b=deepcopy(function(original))
                self.assertNotEqual(a['arguments'].pop('identifier'),b['arguments'].pop('identifier'))
                self.assertEqual(a,b)

    def test_schema_and_tool_availability_match_context(self):
        for row,proof in zip(self.rows,self.manifest['provenance']):
            original=self.sources[proof['source_index']];expected_tools=deepcopy(original['tools'])
            if proof['kind']=='missing_selection':expected_tools=[t for t in expected_tools if t['function']['name']!='previous_results']
            self.assertEqual(row['tools'],expected_tools)
            target=function(row)
            offered={t['function']['name']:t['function']['parameters'] for t in row['tools']}
            validate(target['arguments'],offered[target['name']])

    def test_languages_and_counterfactual_counts(self):
        counts=Counter(function(r)['arguments'].get('language') for r in self.rows if function(r)['name']=='clarify')
        self.assertEqual(counts,{'en':30,'fr':30})
        self.assertEqual(Counter(p['kind'] for p in self.manifest['provenance']),{'rebound':36,'missing_selection':36,'out_of_range':24})

    def test_incorrect_source_target_cannot_generate_examples(self):
        row=deepcopy(self.sources[self.manifest['provenance'][0]['source_index']])
        function(row)['arguments']['identifier']=2147483647
        with self.assertRaises(ValueError):generate([row],self.aliases)
        row=deepcopy(self.sources[self.manifest['provenance'][0]['source_index']])
        row['messages'][1]['content']='Change customer ID 4451: City “SYN-Test”.'
        with self.assertRaises(ValueError):generate([row],self.aliases)

if __name__=='__main__':unittest.main()
