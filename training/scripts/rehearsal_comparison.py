"""Exact rehearsal replay helpers, without model loading or service management.

The server controller owns export provenance and live worker attestation. These
helpers verify capture evidence and preserve raw SSE objects for paired diagnosis.
They never execute business tools, normalize arguments, or grant model acceptance.
"""
import json

from jsonschema import validate, ValidationError

from audit_training_inputs import digest, encoded, model_input_key, target
from attest_colibri import fingerprint

EVIDENCE_FILES = ('plan.json', 'before.json', 'after.json', 'steps.jsonl',
                  'before.events.jsonl', 'after.events.jsonl')


def load_captures(rehearsal, data):
    complete = json.loads((rehearsal / 'complete.json').read_text())
    if (complete.get('model_accepted') is not False or complete.get('export_compared') is not False or
            complete.get('full_training_may_resume_from_this_adapter') is not False or
            complete.get('saved_adapter_matches_live') is not True or
            complete.get('frozen_parameters_unchanged') is not True):
        raise ValueError('Incomplete numerical rehearsal evidence')
    if set(complete['evidence_sha256']) != set(EVIDENCE_FILES):
        raise ValueError('Incomplete rehearsal evidence inventory')
    payloads = {}
    for name in EVIDENCE_FILES:
        payloads[name] = (rehearsal / name).read_bytes()
        if digest(payloads[name]) != complete['evidence_sha256'][name]:
            raise ValueError('Rehearsal evidence changed')
    adapter = rehearsal / 'disposable-adapter'
    proof = complete['disposable_adapter']
    if fingerprint(adapter, [path for path in adapter.rglob('*') if path.is_file()]) != proof:
        raise ValueError('Disposable adapter changed')
    plan = json.loads(payloads['plan.json'])
    if (plan.get('capture_contract') != 'qwen36-stop-filter-v1' or
            plan.get('chat_stop_policy') != {
                'sequences': ['<|im_end|>', '<|im_start|>'], 'ignore_leading': False}):
        raise ValueError('Rehearsal lacks the pinned serving stop contract')
    if digest((data / 'manifest.json').read_bytes()) != plan['audit']['manifest_sha256']:
        raise ValueError('Dataset manifest changed')
    rows = {}
    for split in ('train', 'valid'):
        payload = (data / (split + '.jsonl')).read_bytes()
        if digest(payload) != plan['audit']['input_sha256'][split]:
            raise ValueError('Capture dataset changed')
        rows[split] = [json.loads(line) for line in payload.splitlines()]
    if set(plan['captures']) != {'train', 'valid'}:
        raise ValueError('Capture split inventory changed')
    selected = [(split, index) for split in ('train', 'valid') for index in plan['captures'][split]]
    if not selected or len(selected) != len(set(selected)):
        raise ValueError('Empty or duplicate capture selection')
    if not set(plan['captures']['train']) <= set(plan['audit']['rehearsal']['row_indices']):
        raise ValueError('Training capture was not rehearsed')
    captures = {}
    for phase in ('before', 'after'):
        captured = json.loads(payloads[phase + '.json'])
        events = [json.loads(line) for line in payloads[phase + '.events.jsonl'].splitlines()]
        if captured != events or [(item['split'], item['row_index']) for item in captured] != selected:
            raise ValueError('Capture coverage differs from the frozen plan')
        for item in captured:
            if (item.get('capture_contract') != plan['capture_contract'] or
                    not isinstance(item.get('reply'), str) or
                    not isinstance(item.get('served_reply'), str) or
                    'matched_stop' not in item or
                    item['matched_stop'] not in (None, *plan['chat_stop_policy']['sequences'])):
                raise ValueError('Capture lacks filtered serving evidence')
            split, index = item['split'], item['row_index']
            if type(index) is not int or index < 0 or index >= len(rows[split]):
                raise ValueError('Invalid capture row index')
            row = rows[split][index]
            if (item['application'] != row['application'] or
                    item['input_sha256'] != digest(model_input_key(row).encode())):
                raise ValueError('Capture input identity changed')
        captures[phase] = captured
    return {'plan': plan, 'complete': complete, 'rows': rows, 'captures': captures}


def replay_requests(evidence, renderer, tokenizer, model_id):
    """Use the original tool inventory directly; do not call provider.choose()."""
    requests = []
    context = evidence['plan']['settings']['max_seq_length']
    if context != 8192 or not isinstance(model_id, str) or not model_id:
        raise ValueError('Unexpected replay model or context')
    for reference in evidence['captures']['after']:
        row = evidence['rows'][reference['split']][reference['row_index']]
        prompt = renderer(row['messages'][:-1], tools=row['tools'],
                          enable_thinking=False, add_generation_prompt=True)
        token_ids = tokenizer.encode(prompt, add_special_tokens=False)
        if (digest(prompt.encode()) != reference['prompt_sha256'] or
                len(token_ids) != reference['prompt_tokens']):
            raise ValueError('Replay prompt or tokenizer differs from the rehearsal')
        budget = min(512, context - len(token_ids))
        if budget < 1:
            raise ValueError('No generation room')
        payload = {'model': model_id, 'messages': row['messages'][:-1], 'tools': row['tools'],
                   'tool_choice': 'auto', 'stream': True, 'stream_options': {'include_usage': True},
                   'temperature': 0, 'max_tokens': budget, 'enable_thinking': False,
                   'chat_template_kwargs': {'enable_thinking': False}}
        if len(json.dumps(payload).encode()) > 48000:
            raise ValueError('Replay exceeds the native provider request limit')
        requests.append({'reference': reference, 'target': target(row), 'payload': payload,
                         'request_sha256': digest(encoded(payload).encode())})
    return requests


def parse_events(events, offered, model_id, *, prompt_tokens=None, max_tokens=None):
    """Retain streamed objects outside this parser; return schema-valid raw actions."""
    calls, usage, content, finished, error = {}, {}, '', None, None
    definitions = {tool['function']['name']: tool['function']['parameters'] for tool in offered}
    if len(definitions) != len(offered):
        raise ValueError('Duplicate offered tool')
    try:
        for event in events:
            if not isinstance(event, dict):
                raise ValueError('Invalid streamed event')
            if event.get('error'):
                raise ValueError('Server reported an error')
            if event.get('model') != model_id:
                raise ValueError('Unexpected replay model')
            if event.get('usage') is not None:
                if not isinstance(event['usage'], dict):
                    raise ValueError('Invalid usage object')
                usage = event['usage']
                if any(type(usage.get(key)) is not int or usage[key] < 0
                       for key in ('prompt_tokens', 'completion_tokens')):
                    raise ValueError('Invalid token usage')
                if 'total_tokens' in usage and (type(usage['total_tokens']) is not int or
                        usage['total_tokens'] != usage['prompt_tokens'] + usage['completion_tokens']):
                    raise ValueError('Invalid total token usage')
                if prompt_tokens is not None and usage['prompt_tokens'] != prompt_tokens:
                    raise ValueError('Served prompt token count differs')
                if max_tokens is not None and usage['completion_tokens'] > max_tokens:
                    raise ValueError('Served completion exceeded the replay budget')
            choices = event.get('choices', [])
            if not isinstance(choices, list) or len(choices) > 1:
                raise ValueError('Multiple response choices')
            for choice in choices:
                if not isinstance(choice, dict) or type(choice.get('index')) is not int or choice['index'] != 0:
                    raise ValueError('Unexpected response choice')
                delta = choice.get('delta', {})
                if not isinstance(delta, dict) or not isinstance(delta.get('tool_calls', []), list):
                    raise ValueError('Invalid response delta')
                if delta.get('content') is not None and not isinstance(delta['content'], str):
                    raise ValueError('Invalid text delta')
                if delta.get('role') is not None and delta['role'] != 'assistant':
                    raise ValueError('Invalid role delta')
                meaningful = bool(delta.get('content') or delta.get('tool_calls'))
                if finished is not None and (meaningful or choice.get('finish_reason') is not None):
                    raise ValueError('Response continued after termination')
                content += delta.get('content') or ''
                for call in delta.get('tool_calls', []):
                    if not isinstance(call, dict) or not isinstance(call.get('function', {}), dict):
                        raise ValueError('Invalid tool-call fragment')
                    index = call.get('index')
                    if type(index) is not int or index < 0:
                        raise ValueError('Invalid tool-call index')
                    function = call.get('function', {})
                    part = calls.setdefault(index, {'name': '', 'arguments': ''})
                    if 'id' in call:
                        if not isinstance(call['id'], str) or not call['id'] or (
                                'id' in part and part['id'] != call['id']):
                            raise ValueError('Tool-call identity changed')
                        part['id'] = call['id']
                    if 'type' in call and call['type'] != 'function':
                        raise ValueError('Invalid tool-call type')
                    if any(not isinstance(function[key], str) for key in ('name', 'arguments') if key in function):
                        raise ValueError('Invalid tool-call function fragment')
                    part['name'] += function.get('name', '')
                    part['arguments'] += function.get('arguments', '')
                if choice.get('finish_reason') is not None:
                    finished = choice['finish_reason']
        if finished not in ('tool_calls', 'stop'):
            return {'action': None, 'schema_valid': False, 'error': 'INCOMPLETE_RESPONSE',
                    'finish_reason': finished, 'content': content, 'usage': usage}
        if prompt_tokens is not None and not usage:
            raise ValueError('Missing replay usage evidence')
        if len(calls) != 1:
            raise ValueError('Exactly one tool call is required')
        function = next(iter(calls.values()))
        action = {'name': function['name'], 'arguments': json.loads(function['arguments'])}
        if action['name'] not in definitions:
            raise ValueError('Tool was not offered')
        validate(action['arguments'], definitions[action['name']])
        return {'action': action, 'schema_valid': True, 'error': None,
                'finish_reason': finished, 'content': content, 'usage': usage}
    except (KeyError, TypeError, ValueError, ValidationError) as exc:
        error = type(exc).__name__
    return {'action': None, 'schema_valid': False, 'error': error,
            'finish_reason': finished, 'content': content, 'usage': usage}


def compare_pairs(requests, responses):
    """Return diagnostics, not acceptance scores; never count two failures as agreement."""
    if len(requests) != len(responses):
        raise ValueError('Replay omitted or added captures')
    pairs = []
    for request, response in zip(requests, responses):
        reference = request['reference']
        identity = {key: reference[key] for key in ('split', 'row_index', 'input_sha256', 'prompt_sha256')}
        if response['identity'] != identity:
            raise ValueError('Replay capture identity or order changed')
        payload = request['payload']
        payload_hash = digest(encoded(payload).encode())
        if payload_hash != request['request_sha256'] or payload_hash != response['request_sha256']:
            raise ValueError('Sent replay payload differs from the frozen request')
        actual_input = encoded({'messages': payload['messages'], 'tools': payload['tools']})
        if digest(actual_input.encode()) != reference['input_sha256']:
            raise ValueError('Replay payload differs from the captured model input')
        result = parse_events(response['events'], payload['tools'], payload['model'],
            prompt_tokens=reference['prompt_tokens'], max_tokens=payload['max_tokens'])
        # Native provider accepts clean EOF after a terminal finish reason.
        # Missing DONE alone is metadata, not a model failure.
        result['sse_done'] = response.get('sse_done')
        if response.get('transport_error'):
            result.update(action=None, schema_valid=False, error=response['transport_error'])
        hf_valid = reference['schema_valid'] and reference['parse_error'] is None
        hf_match = hf_valid and encoded(reference['action']) == encoded(request['target'])
        replay_match = result['schema_valid'] and encoded(result['action']) == encoded(request['target'])
        pairs.append({**identity, 'application': reference['application'],
            'hf_action': reference['action'], 'colibri': result,
            'same_valid_action': bool(hf_valid and result['schema_valid'] and
                                      encoded(reference['action']) == encoded(result['action'])),
            'hf_matches_development_target': bool(hf_match),
            'colibri_matches_development_target': bool(replay_match),
            'correct_to_incorrect': bool(hf_match and not replay_match)})
    return {'status': 'PAIRED DIAGNOSTICS; EXPORT AND WORKER ATTESTATION REQUIRED',
            'model_accepted': False, 'full_training_authorized': False, 'pairs': pairs,
            'by_split': {split: {
                'count': sum(pair['split'] == split for pair in pairs),
                'same_valid_action': sum(pair['split'] == split and pair['same_valid_action'] for pair in pairs),
                'correct_to_incorrect': sum(pair['split'] == split and pair['correct_to_incorrect'] for pair in pairs)}
                for split in ('train', 'valid')},
            'limitations': [
                'Caller must attest real export, runtime, tokenizer and live worker before and after replay.',
                'Streamed API tool calls do not prove raw generated-token parity.',
                'BF16, FP32 merge, FP16 export and dense int8 serving may produce different actions.',
                'Training and development captures are not model acceptance cases.']}
