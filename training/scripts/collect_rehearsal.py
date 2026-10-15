"""Exact loopback SSE collection for a bound, isolated server rehearsal worker.

The caller owns export/worker attestation and resource admission. This module
never starts services, loads weights, retries requests or authorizes training.
"""
import base64
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import sys
import time
from urllib.parse import urlsplit

from rehearsal_comparison import compare_pairs, request_json
from audit_training_inputs import digest, encoded

MAX_RESPONSE_BYTES = 500000


def endpoint_address(endpoint):
    url = urlsplit(endpoint)
    if (url.scheme != 'http' or url.username or url.password or url.query or url.fragment
            or url.path not in ('/v1/chat/completions', '/chat/completions')
            or not url.hostname or url.port is None):
        raise ValueError('Replay requires an explicit loopback chat endpoint')
    # Literal addresses only: no DNS, proxy or redirect route out of the worker.
    if not ipaddress.ip_address(url.hostname).is_loopback or not 1 <= url.port <= 65535:
        raise ValueError('Replay requires an explicit loopback chat endpoint')
    return url.hostname, url.port, url.path


class EventStream:
    def __init__(self):
        self.pending = b''
        self.data = []
        self.events = []
        self.done = False

    def dispatch(self):
        if not self.data:
            return
        raw = b'\n'.join(self.data)
        self.data = []
        if raw == b'[DONE]':
            self.done = True
        else:
            self.events.append(json.loads(raw.decode('utf-8')))

    def line(self, line):
        line = line.removesuffix(b'\r')
        if self.done:
            if line.strip():
                raise ValueError('Data after DONE')
            return
        if not line:
            self.dispatch()
        elif line.startswith(b'data:'):
            self.data.append(line[5:].removeprefix(b' '))
        elif line.startswith(b':') or line.split(b':', 1)[0] in (b'event', b'id', b'retry'):
            pass
        else:
            raise ValueError('Unexpected stream line')

    def feed(self, chunk):
        self.pending += chunk
        while b'\n' in self.pending:
            line, self.pending = self.pending.split(b'\n', 1)
            self.line(line)

    def finish(self):
        # The native provider accepts a final data line without a blank separator.
        if self.pending:
            self.line(self.pending)
            self.pending = b''
        self.dispatch()


def identity(request):
    return {key: request['reference'][key] for key in
            ('split', 'row_index', 'input_sha256', 'prompt_sha256')}


def collect_one(request, address, *, timeout):
    body = request_json(request['payload']).encode('utf-8')
    if digest(body) != request['request_sha256'] or len(body) > 48000:
        raise ValueError('Changed or oversized replay payload')
    result = {'identity': identity(request), 'request_sha256': digest(body),
              'events': [], 'sse_done': False, 'transport_error': None,
              'http_status': None, 'content_type': None}
    stream, raw = EventStream(), bytearray()
    started = time.monotonic()
    deadline = started + timeout
    connection = http.client.HTTPConnection(address[0], address[1], timeout=timeout)
    response = None
    try:
        connection.request('POST', address[2], body=body,
                           headers={'Content-Type': 'application/json',
                                    'Accept': 'text/event-stream', 'Connection': 'close'})
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        # Keep the socket reference: HTTPConnection clears .sock on Connection: close.
        connection.sock.settimeout(remaining)
        sock = connection.sock
        response = connection.getresponse()
        result['http_status'] = response.status
        result['content_type'] = response.getheader('Content-Type', '').split(';', 1)[0].strip().lower()
        if response.status != 200:
            result['transport_error'] = 'HTTP_STATUS'
        elif result['content_type'] != 'text/event-stream':
            result['transport_error'] = 'INVALID_CONTENT_TYPE'
        while True:
            if response.isclosed():
                if response.length not in (None, 0):
                    raise http.client.IncompleteRead(b'', response.length)
                if result['transport_error'] is None:
                    stream.finish()
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            sock.settimeout(remaining)
            chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - len(raw)))
            raw.extend(chunk)
            if time.monotonic() > deadline:
                raise TimeoutError()
            if not chunk:
                if response.length not in (None, 0):
                    raise http.client.IncompleteRead(b'', response.length)
                if result['transport_error'] is None:
                    stream.finish()
                break
            if len(raw) > MAX_RESPONSE_BYTES:
                result['transport_error'] = result['transport_error'] or 'RESPONSE_LIMIT'
                break
            if result['transport_error'] is None:
                stream.feed(chunk)
        if stream.done and stream.pending.strip():
            raise ValueError('Trailing data after DONE')
    except TimeoutError:
        result['transport_error'] = result['transport_error'] or 'MODEL_TIMEOUT'
        result['read_error'] = 'MODEL_TIMEOUT'
    except http.client.IncompleteRead as exc:
        raw.extend(exc.partial[:MAX_RESPONSE_BYTES + 1 - len(raw)])
        result['transport_error'] = result['transport_error'] or 'TRANSPORT_ERROR'
        result['read_error'] = 'INCOMPLETE_READ'
    except (OSError, http.client.HTTPException):
        result['transport_error'] = result['transport_error'] or 'TRANSPORT_ERROR'
        result['read_error'] = 'TRANSPORT_ERROR'
    except (ValueError, UnicodeError):
        result['transport_error'] = result['transport_error'] or 'INVALID_SSE'
    finally:
        if response is not None:
            response.close()
        connection.close()
    result.update(events=stream.events, sse_done=stream.done,
                  response_body_base64=base64.b64encode(raw).decode('ascii'),
                  response_body_sha256=digest(bytes(raw)),
                  duration_seconds=round(time.monotonic() - started, 6))
    return result


def collect_replay(requests, endpoint, output, *, timeout=90):
    """Persist exact requests before sequential replay; stop on any transport error."""
    if sys.platform != 'linux' or os.environ.get('CHAT_AI_TRAINING_SERVER') != '1':
        raise ValueError('Rehearsal replay is server-only')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 600:
        raise ValueError('Invalid replay timeout')
    address = endpoint_address(endpoint)
    # Admission before any network I/O, including binding to each original input.
    if not requests or len({encoded(identity(item)) for item in requests}) != len(requests):
        raise ValueError('Empty or duplicate replay requests')
    placeholders = [{'identity': identity(item), 'request_sha256': item['request_sha256'],
                     'events': []} for item in requests]
    compare_pairs(requests, placeholders)
    for item in requests:
        if len(request_json(item['payload']).encode('utf-8')) > 48000:
            raise ValueError('Oversized replay request')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'requests.json').write_text(request_json(requests) + '\n')
    responses = []
    with (output / 'responses.jsonl').open('x') as log:
        for request in requests:
            response = collect_one(request, address, timeout=timeout)
            responses.append(response)
            log.write(encoded(response) + '\n')
            log.flush()
            if response['transport_error']:
                break
    complete = len(responses) == len(requests) and not any(item['transport_error'] for item in responses)
    report = {'status': 'REPLAY COLLECTED' if complete else 'REPLAY INTERRUPTED',
              'transport_complete': complete, 'model_accepted': False,
              'full_training_authorized': False, 'requests': len(requests), 'responses': len(responses)}
    if complete:
        report['comparison'] = compare_pairs(requests, responses)
    (output / 'collection.json').write_text(encoded(report) + '\n')
    return report
