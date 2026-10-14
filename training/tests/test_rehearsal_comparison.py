"""Exact replay tests with synthetic messages and events; no weights or inference."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import rehearsal_comparison as comparison


def row():
    return {'application': 'facturation',
        'messages': [{'role': 'system', 'content': 'synthetic'},
            {'role': 'user', 'content': 'find the synthetic item'},
            {'role': 'assistant', 'tool_calls': [{'function': {
                'name': 'find', 'arguments': {'limit': 1}}}]}],
        'tools': [
            {'type': 'function', 'function': {'name': 'find', 'parameters': {
                'type': 'object', 'properties': {'limit': {'type': 'integer'}},
                'required': ['limit'], 'additionalProperties': False}}},
            {'type': 'function', 'function': {'name': 'clarify', 'parameters': {
                'type': 'object', 'properties': {'reason': {'type': 'string'}},
                'required': ['reason'], 'additionalProperties': False}}}]}


def reference(split='train'):
    value = row()
    return {'split': split, 'row_index': 0, 'application': value['application'],
        'input_sha256': comparison.digest(comparison.model_input_key(value).encode()),
        'prompt_sha256': comparison.digest(b'prompt'), 'prompt_tokens': 7704,
        'action': comparison.target(value), 'schema_valid': True, 'parse_error': None,
        'capture_contract': 'qwen36-stop-filter-v1', 'reply': 'synthetic',
        'served_reply': 'synthetic', 'matched_stop': None}


def evidence():
    return {'plan': {'settings': {'max_seq_length': 8192}},
        'rows': {'train': [row()], 'valid': [row()]},
        'captures': {'after': [reference('train'), reference('valid')]}}


def requests():
    return comparison.replay_requests(evidence(), lambda *a, **kw: 'prompt',
        SimpleNamespace(encode=lambda *a, **kw: list(range(7704))), 'candidate')


def events(arguments='{"limit":1}', finish='tool_calls'):
    return [
        {'model': 'candidate', 'choices': [{'index': 0, 'delta': {'role': 'assistant'}, 'finish_reason': None}]},
        {'model': 'candidate', 'choices': [{'index': 0, 'delta': {
            'tool_calls': [{'index': 0, 'function': {'name': 'find', 'arguments': arguments[:5]}}]},
            'finish_reason': None}]},
        {'model': 'candidate', 'choices': [{'index': 0, 'delta': {
            'tool_calls': [{'index': 0, 'function': {'arguments': arguments[5:]}}]},
            'finish_reason': finish}]},
        {'model': 'candidate', 'choices': [], 'usage': {'prompt_tokens': 7704, 'completion_tokens': 20}}]


def responses():
    return [{'identity': {key: request['reference'][key] for key in (
        'split', 'row_index', 'input_sha256', 'prompt_sha256')},
        'request_sha256': request['request_sha256'],
        'events': events(), 'sse_done': True} for request in requests()]


class ComparisonTests(unittest.TestCase):
    def test_exact_messages_tools_and_clamped_budget(self):
        seen = []
        def render(messages, **kwargs):
            seen.append((messages, kwargs))
            return 'prompt'
        result = comparison.replay_requests(evidence(), render,
            SimpleNamespace(encode=lambda *a, **kw: list(range(7704))), 'candidate')
        self.assertEqual(len(result), 2)
        for request in result:
            payload = request['payload']
            self.assertEqual(payload['tools'], row()['tools'])
            self.assertEqual(payload['messages'], row()['messages'][:-1])
            self.assertEqual(payload['max_tokens'], 488)
            self.assertEqual(sum(tool['function']['name'] == 'clarify' for tool in payload['tools']), 1)
        self.assertEqual(seen[0][1]['tools'], row()['tools'])

    def test_prompt_and_tokenizer_drift_rejected(self):
        for renderer, tokenizer in (
            (lambda *a, **kw: 'changed', SimpleNamespace(encode=lambda *a, **kw: list(range(7704)))),
            (lambda *a, **kw: 'prompt', SimpleNamespace(encode=lambda *a, **kw: [1]))):
            with self.subTest(), self.assertRaisesRegex(ValueError, 'prompt or tokenizer'):
                comparison.replay_requests(evidence(), renderer, tokenizer, 'candidate')

    def test_fragmented_calls_keep_raw_arguments_and_usage(self):
        observed = comparison.parse_events(events(), row()['tools'], 'candidate')
        self.assertEqual(observed['action'], {'name': 'find', 'arguments': {'limit': 1}})
        self.assertTrue(observed['schema_valid'])
        self.assertEqual(observed['finish_reason'], 'tool_calls')
        self.assertEqual(observed['usage']['completion_tokens'], 20)

    def test_wrong_model_unknown_tool_multiple_calls_and_bad_schema_fail(self):
        variants = []
        wrong_model = events()
        wrong_model[-1]['model'] = 'other'
        variants.append(wrong_model)
        unknown_tool = events()
        unknown_tool[1]['choices'][0]['delta']['tool_calls'][0]['function']['name'] = 'delete_all'
        variants.append(unknown_tool)
        multiple = events()
        multiple[1]['choices'][0]['delta']['tool_calls'].append(
            {'index': 1, 'function': {'name': 'find', 'arguments': '{"limit":1}'}})
        variants.extend((multiple, events('{"limit":true}'), events('{invalid')))
        for variant in variants:
            with self.subTest(events=variant):
                observed = comparison.parse_events(variant, row()['tools'], 'candidate')
                self.assertFalse(observed['schema_valid'])
                self.assertIsNone(observed['action'])
                self.assertIsNotNone(observed['error'])

    def test_missing_length_or_late_termination_fail(self):
        late = events()
        late.append(events()[1])
        for variant in (events(finish=None), events(finish='length'), late):
            with self.subTest():
                self.assertFalse(comparison.parse_events(variant, row()['tools'], 'candidate')['schema_valid'])

    def test_malformed_events_are_retained_as_failures(self):
        variants = [None, [], 'not an object',
            {'model': 'candidate', 'choices': {}},
            {'model': 'candidate', 'choices': [None]},
            {'model': 'candidate', 'choices': [{'index': False, 'delta': {}}]},
            {'model': 'candidate', 'choices': [{'index': 0, 'delta': None}]},
            {'model': 'candidate', 'choices': [{'index': 0, 'delta': {'tool_calls': [None]}}]}]
        for event in variants:
            with self.subTest(event=event):
                result = comparison.parse_events([event], row()['tools'], 'candidate')
                self.assertFalse(result['schema_valid'])
                self.assertIsNotNone(result['error'])

    def test_default_arguments_are_not_normalized(self):
        req = requests()
        resp = responses()
        resp[0]['events'] = events('{"limit":10}')
        report = comparison.compare_pairs(req, resp)
        self.assertFalse(report['pairs'][0]['same_valid_action'])
        self.assertTrue(report['pairs'][0]['correct_to_incorrect'])
        self.assertTrue(report['pairs'][1]['same_valid_action'])
        self.assertFalse(report['model_accepted'])
        self.assertFalse(report['full_training_authorized'])

    def test_clarification_arguments_remain_structured(self):
        variant = events('{"reason":"missing_date"}')
        variant[1]['choices'][0]['delta']['tool_calls'][0]['function']['name'] = 'clarify'
        observed = comparison.parse_events(variant, row()['tools'], 'candidate')
        self.assertEqual(observed['action'], {'name': 'clarify', 'arguments': {'reason': 'missing_date'}})

    def test_clean_eof_after_finish_and_transport_failures_match_provider(self):
        resp = responses()
        resp[0]['sse_done'] = False
        resp[1]['transport_error'] = 'MODEL_TIMEOUT'
        report = comparison.compare_pairs(requests(), resp)
        self.assertEqual(len(report['pairs']), 2)
        self.assertIsNone(report['pairs'][0]['colibri']['error'])
        self.assertFalse(report['pairs'][0]['colibri']['sse_done'])
        self.assertTrue(report['pairs'][0]['same_valid_action'])
        self.assertEqual(report['pairs'][1]['colibri']['error'], 'MODEL_TIMEOUT')
        self.assertEqual(report['by_split']['train']['correct_to_incorrect'], 0)
        self.assertEqual(report['by_split']['valid']['correct_to_incorrect'], 1)

    def test_two_failed_calls_are_not_agreement(self):
        req, resp = requests(), responses()
        req[0]['reference'].update(schema_valid=False, parse_error='ValueError', action=None)
        resp[0]['events'] = events('{invalid')
        report = comparison.compare_pairs(req, resp)
        self.assertFalse(report['pairs'][0]['same_valid_action'])
        self.assertFalse(report['pairs'][0]['correct_to_incorrect'])

    def test_missing_reordered_or_substituted_cases_reject(self):
        req, resp = requests(), responses()
        for variant in (resp[:-1], list(reversed(resp))):
            with self.subTest(), self.assertRaises(ValueError):
                comparison.compare_pairs(req, variant)
        resp[0]['identity']['prompt_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            comparison.compare_pairs(req, resp)

    def test_sent_payload_changes_reject(self):
        for mutate in (
                lambda payload: payload['messages'][1].update(content='changed'),
                lambda payload: payload.update(max_tokens=1),
                lambda payload: payload.update(temperature=1),
                lambda payload: payload['tools'].reverse()):
            req, resp = requests(), responses()
            mutate(req[0]['payload'])
            with self.subTest(), self.assertRaisesRegex(ValueError, 'payload differs'):
                comparison.compare_pairs(req, resp)
        req, resp = requests(), responses()
        resp[0]['request_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'payload differs'):
            comparison.compare_pairs(req, resp)

    def test_invalid_or_mismatched_usage_never_counts_as_agreement(self):
        for usage in ({'prompt_tokens': 1, 'completion_tokens': 20},
                      {'prompt_tokens': 7704, 'completion_tokens': -100},
                      {'prompt_tokens': 7704, 'completion_tokens': 489},
                      {'prompt_tokens': True, 'completion_tokens': 20},
                      {'prompt_tokens': 7704, 'completion_tokens': 20, 'total_tokens': 1},
                      {}):
            req, resp = requests(), responses()
            resp[0]['events'][-1]['usage'] = usage
            with self.subTest(usage=usage):
                report = comparison.compare_pairs(req, resp)
                self.assertFalse(report['pairs'][0]['same_valid_action'])
                self.assertIsNotNone(report['pairs'][0]['colibri']['error'])
        req, resp = requests(), responses()
        resp[0]['events'].pop()
        self.assertFalse(comparison.compare_pairs(req, resp)['pairs'][0]['same_valid_action'])

    def test_wrong_fragment_types_and_changing_call_ids_fail(self):
        for mutation in ('false_content', 'call_id', 'call_type', 'argument_type'):
            variant = events()
            first = variant[1]['choices'][0]['delta']
            second = variant[2]['choices'][0]['delta']
            if mutation == 'false_content':
                first['content'] = False
            elif mutation == 'call_id':
                first['tool_calls'][0]['id'] = 'a'
                second['tool_calls'][0]['id'] = 'b'
            elif mutation == 'call_type':
                second['tool_calls'][0]['type'] = 'changed'
            else:
                second['tool_calls'][0]['function']['arguments'] = None
            with self.subTest(mutation=mutation):
                self.assertFalse(comparison.parse_events(variant, row()['tools'], 'candidate')['schema_valid'])

    def test_capture_evidence_and_adapter_changes_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'data'
            data.mkdir()
            rehearsal = root / 'rehearsal'
            rehearsal.mkdir()
            adapter = rehearsal / 'disposable-adapter'
            adapter.mkdir()
            (adapter / 'adapter_model.safetensors').write_bytes(b'synthetic placeholder')
            payload = (json.dumps(row()) + '\n').encode()
            for split in ('train', 'valid'):
                (data / (split + '.jsonl')).write_bytes(payload)
            (data / 'manifest.json').write_text('{}')
            plan = {'capture_contract': 'qwen36-stop-filter-v1',
                'chat_stop_policy': {'sequences': ['<|im_end|>', '<|im_start|>'], 'ignore_leading': False},
                'audit': {'manifest_sha256': comparison.digest(b'{}'),
                'input_sha256': {split: comparison.digest(payload) for split in ('train', 'valid')},
                'rehearsal': {'row_indices': [0]}}, 'captures': {'train': [0], 'valid': [0]}}
            captured = [reference('train'), reference('valid')]
            (rehearsal / 'plan.json').write_text(json.dumps(plan))
            (rehearsal / 'steps.jsonl').write_text('{"step":1}\n')
            for phase in ('before', 'after'):
                (rehearsal / (phase + '.json')).write_text(json.dumps(captured))
                (rehearsal / (phase + '.events.jsonl')).write_text(
                    ''.join(json.dumps(item) + '\n' for item in captured))
            complete = {'model_accepted': False, 'export_compared': False,
                'full_training_may_resume_from_this_adapter': False, 'saved_adapter_matches_live': True,
                'frozen_parameters_unchanged': True,
                'evidence_sha256': {name: comparison.digest((rehearsal / name).read_bytes())
                    for name in comparison.EVIDENCE_FILES},
                'disposable_adapter': comparison.fingerprint(adapter, adapter.glob('*'))}
            (rehearsal / 'complete.json').write_text(json.dumps(complete))
            result = comparison.load_captures(rehearsal, data)
            self.assertEqual(result['captures']['after'], captured)
            # Even a self-consistent older capture must not silently bypass the fix.
            for altered in ('plan', 'record'):
                with self.subTest(altered=altered):
                    if altered == 'plan':
                        plan.pop('capture_contract')
                    else:
                        captured[0].pop('served_reply')
                    (rehearsal / 'plan.json').write_text(json.dumps(plan))
                    for phase in ('before', 'after'):
                        (rehearsal / (phase + '.json')).write_text(json.dumps(captured))
                        (rehearsal / (phase + '.events.jsonl')).write_text(
                            ''.join(json.dumps(item) + '\n' for item in captured))
                    complete['evidence_sha256'] = {name: comparison.digest((rehearsal / name).read_bytes())
                        for name in comparison.EVIDENCE_FILES}
                    (rehearsal / 'complete.json').write_text(json.dumps(complete))
                    with self.assertRaisesRegex(ValueError, 'stop contract|filtered serving evidence'):
                        comparison.load_captures(rehearsal, data)
                    plan['capture_contract'] = 'qwen36-stop-filter-v1'
                    captured[0]['served_reply'] = 'synthetic'
            (adapter / 'extra.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'adapter changed'):
                comparison.load_captures(rehearsal, data)
            (adapter / 'extra.json').unlink()
            (rehearsal / 'after.json').write_text('[]')
            with self.assertRaisesRegex(ValueError, 'evidence changed'):
                comparison.load_captures(rehearsal, data)


if __name__ == '__main__':
    unittest.main()
