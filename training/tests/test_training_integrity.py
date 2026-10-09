import json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'training/scripts'))
sys.path.insert(0,str(ROOT/'runtime/colibri/c'))
from training_schedule import complete_epoch_order
from semantic_loss import semantic_token_weights
from text_lora import text_target_regex
from training_contracts import CLARIFICATION_DESCRIPTION
from openai_server import parse_qwen_tool_calls, _qwen_parameter_schema

class IntegrityTests(unittest.TestCase):
    def test_clarification_description_matches_real_provider(self):
        import ast
        tree=ast.parse((ROOT/'src/chat_ai_assistant/provider.py').read_text())
        found=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Dict):
                values={key.value:value.value for key,value in zip(node.keys,node.values) if isinstance(key,ast.Constant) and isinstance(value,ast.Constant)}
                if values.get('name')=='clarify':found.append(values.get('description'))
        self.assertEqual(found,[CLARIFICATION_DESCRIPTION])
    def test_semantic_weights_preserve_syntax_and_prompt_mask(self):
        prompt='prompt\n'
        target='<tool_call>\n<function=find>\n<parameter=limit>\n2\n</parameter>\n</function>\n</tool_call>EOS'
        text=prompt+target
        # Character tokens make the overlap expectation independently inspectable.
        weights=semantic_token_weights(text,len(prompt),[(i,i+1) for i in range(len(text))],len(prompt),4)
        for value in ['find','limit','2']:
            start=target.index(value)
            self.assertEqual(weights[start:start+len(value)],[4]*len(value))
        self.assertEqual(weights[-3:],[1,1,1])
        self.assertEqual(weights[:11],[1]*11)
        self.assertEqual(semantic_token_weights(text,len(prompt),[(i,i+1) for i in range(len(text))],len(prompt),1),[1]*len(target))
        with self.assertRaises(ValueError):semantic_token_weights(text,len(prompt),[],len(prompt),4)
        with self.assertRaises(ValueError):semantic_token_weights(text,len(prompt),[(0,1)],0,float('nan'))
    def test_text_adapter_regex_keeps_vision_out(self):
        import re
        regex=text_target_regex(24,24)
        for i in range(24):
            self.assertTrue(re.fullmatch(regex,'model.language_model.layers.'+str(i)+'.linear_attn.in_proj_qkv'))
        self.assertIsNone(re.fullmatch(regex,'model.visual.blocks.23.mlp.up_proj'))
        self.assertIsNone(re.fullmatch(regex,'model.language_model.layers.24.mlp.up_proj'))
        with self.assertRaises(ValueError):text_target_regex(24,25)
    def test_complete_imbalanced_coverage_and_reshuffle(self):
        rows=[{'application':app} for app,n in [('facturation',410),('management_projet',82),('design_workflow',122)] for _ in range(n)]
        first=complete_epoch_order(rows)
        self.assertEqual(sorted(first),list(range(len(rows))))
        self.assertEqual(first,complete_epoch_order(rows))
        self.assertNotEqual(first,complete_epoch_order(rows,epoch=1))
        # Every quarter retains all three applications, even with imbalanced sizes.
        for offset in range(0,len(rows)-154,154):
            self.assertEqual({rows[i]['application'] for i in first[offset:offset+154]}, {'facturation','management_projet','design_workflow'})
    def test_compound_numeric_types_and_required_keys(self):
        tools=[{'type':'function','function':{'name':'search','parameters':{'oneOf':[{'type':'object','properties':{'resource':{'const':r},'limit':{'type':'integer'},'archived':{'type':'boolean'}},'required':['resource','limit']} for r in ['article','invoice']]}}}]
        text='<tool_call>\n<function=search>\n<parameter=resource>\narticle\n</parameter>\n<parameter=limit>\n2\n</parameter>\n<parameter=archived>\nfalse\n</parameter>\n</function>\n</tool_call>'
        _,calls=parse_qwen_tool_calls(text,tools)
        self.assertEqual(json.loads(calls[0]['function']['arguments']),{'resource':'article','limit':2,'archived':False})
        _,calls=parse_qwen_tool_calls(text.replace('<parameter=limit>\n2\n</parameter>\n',''),tools)
        self.assertEqual(calls,[])
    def test_nested_object_combinators_and_invalid_numeric_text(self):
        tools=[{'function':{'name':'find','parameters':{'allOf':[{'properties':{'resource':{'type':'string'}},'required':['resource']},{'anyOf':[{'properties':{'limit':{'type':'integer'}},'required':['limit']},{'properties':{'limit':{'type':'integer'}},'required':['limit']}]}]}}}]
        text='<tool_call>\n<function=find>\n<parameter=resource>\narticle\n</parameter>\n<parameter=limit>\n2\n</parameter>\n</function>\n</tool_call>'
        _,calls=parse_qwen_tool_calls(text,tools)
        self.assertEqual(json.loads(calls[0]['function']['arguments']),{'resource':'article','limit':2})
        _,calls=parse_qwen_tool_calls(text.replace('\n2\n','\ntwo\n'),tools)
        self.assertEqual(calls,[])
    def test_untyped_conjunction_preserves_integer(self):
        tools=[{'function':{'name':'find','parameters':{'properties':{'limit':{'type':'integer'}},'allOf':[{'properties':{'limit':{'minimum':1}}}]}}}]
        text='<tool_call>\n<function=find>\n<parameter=limit>\n2\n</parameter>\n</function>\n</tool_call>'
        _,calls=parse_qwen_tool_calls(text,tools)
        self.assertEqual(json.loads(calls[0]['function']['arguments']),{'limit':2})
        self.assertIsInstance(json.loads(calls[0]['function']['arguments'])['limit'],int)
    def test_numeric_conjunction_narrows_to_integer(self):
        tools=[{'function':{'name':'find','parameters':{'allOf':[{'properties':{'limit':{'type':'number'}}},{'properties':{'limit':{'type':'integer'}}}]}}}]
        text='<tool_call>\n<function=find>\n<parameter=limit>\n2\n</parameter>\n</function>\n</tool_call>'
        _,calls=parse_qwen_tool_calls(text,tools)
        self.assertIsInstance(json.loads(calls[0]['function']['arguments'])['limit'],int)
        properties,_=_qwen_parameter_schema(tools[0]['function']['parameters'])
        self.assertEqual(properties['limit'],{'type':'integer'})
    def test_strings_and_conflicting_union_types_are_not_guessed(self):
        tools=[{'function':{'name':'find','parameters':{'oneOf':[{'properties':{'code':{'type':'string'},'mixed':{'type':'string'}}},{'properties':{'code':{'type':'string'},'mixed':{'type':'integer'}}}]}}}]
        text='<tool_call>\n<function=find>\n<parameter=code>\n0012\n</parameter>\n<parameter=mixed>\n12\n</parameter>\n</function>\n</tool_call>'
        _,calls=parse_qwen_tool_calls(text,tools)
        self.assertEqual(json.loads(calls[0]['function']['arguments']),{'code':'0012','mixed':'12'})
if __name__=='__main__':unittest.main()
