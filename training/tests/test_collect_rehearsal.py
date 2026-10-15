"""Synthetic transport regression tests; no model, server or network use."""
import base64
import json
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'training/scripts'))
import collect_rehearsal as collector
from rehearsal_comparison import compare_pairs
from test_rehearsal_comparison import requests, events


def wire(event_list=None, done=True):
    data = b''.join(b'data: ' + json.dumps(event).encode() + b'\r\n\r\n'
                    for event in (events() if event_list is None else event_list))
    return data + (b'data: [DONE]\r\n\r\n' if done else b'')


class CollectorTests(unittest.TestCase):
    def collect(self, chunks, *, status=200, content_type='text/event-stream; charset=utf-8'):
        response = Mock()
        response.status = status
        response.length = None
        response.isclosed.return_value = False
        response.getheader.return_value = content_type
        response.read1.side_effect = [*chunks, b'']
        connection = Mock()
        connection.getresponse.return_value = response
        with patch.object(collector.http.client, 'HTTPConnection', return_value=connection):
            result = collector.collect_one(requests()[0], ('127.0.0.1', 12345, '/v1/chat/completions'), timeout=90)
        self.assertTrue(connection.close.called)
        self.assertTrue(response.close.called)
        return result, connection

    def test_exact_sent_body_and_raw_wire_are_preserved(self):
        raw = wire()
        result, connection = self.collect([raw])
        body = connection.request.call_args.kwargs['body']
        self.assertEqual(body, collector.request_json(requests()[0]['payload']).encode())
        self.assertEqual(result['request_sha256'], collector.digest(body))
        self.assertEqual(base64.b64decode(result['response_body_base64']), raw)
        self.assertEqual(result['response_body_sha256'], collector.digest(raw))
        self.assertEqual(result['events'], events())
        self.assertTrue(result['sse_done'])
        self.assertIsNone(result['transport_error'])
        self.assertTrue(compare_pairs(requests()[:1], [result])['pairs'][0]['same_valid_action'])

    def test_sent_tool_schema_order_matches_the_rendered_input(self):
        _, connection = self.collect([wire()])
        sent = json.loads(connection.request.call_args.kwargs['body'])
        original = requests()[0]['payload']
        # JSON object equality hides ordering changes that alter the model prompt.
        self.assertEqual(json.dumps(sent['tools']), json.dumps(original['tools']))

    def test_saved_request_preserves_tool_schema_order(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'replay'
            def send(request, address, timeout):
                saved = json.loads((output / 'requests.json').read_text())[0]
                self.assertEqual(json.dumps(saved['payload']['tools']),
                                 json.dumps(request['payload']['tools']))
                return {'identity': collector.identity(request),
                        'request_sha256': request['request_sha256'],
                        'events': [], 'transport_error': 'MODEL_TIMEOUT'}
            with patch.object(collector.sys, 'platform', 'linux'), \
                 patch.dict(os.environ, {'CHAT_AI_TRAINING_SERVER': '1'}), \
                 patch.object(collector, 'collect_one', side_effect=send):
                collector.collect_replay(requests(), 'http://127.0.0.1:12345/chat/completions', output)

    def test_arbitrary_byte_chunks_and_multiline_events(self):
        raw = b': heartbeat\r\n\r\nevent: message\n'
        first = json.dumps(events()[0])
        raw += ('data: ' + first[:first.index(',') + 1] + '\ndata: ' +
                first[first.index(',') + 1:] + '\n\n').encode()
        raw += wire(events()[1:])
        result, _ = self.collect([bytes([byte]) for byte in raw])
        self.assertEqual(result['events'], events())
        self.assertIsNone(result['transport_error'])

    def test_clean_eof_without_done_is_compatible(self):
        result, _ = self.collect([wire(done=False).rstrip(b'\r\n'), b''])
        self.assertFalse(result['sse_done'])
        self.assertIsNone(result['transport_error'])
        self.assertTrue(compare_pairs(requests()[:1], [result])['pairs'][0]['same_valid_action'])

    def test_missing_finish_stays_failure(self):
        result, _ = self.collect([wire(events(finish=None))])
        self.assertIsNone(result['transport_error'])
        self.assertFalse(compare_pairs(requests()[:1], [result])['pairs'][0]['same_valid_action'])

    def test_partial_events_survive_timeout_without_retry(self):
        prefix = wire(events()[:2], done=False)
        result, connection = self.collect([prefix, TimeoutError()])
        self.assertEqual(result['events'], events()[:2])
        self.assertEqual(base64.b64decode(result['response_body_base64']), prefix)
        self.assertEqual(result['transport_error'], 'MODEL_TIMEOUT')
        self.assertEqual(connection.request.call_count, 1)

    def test_malformed_utf8_json_and_trailing_data_fail_with_raw_evidence(self):
        for raw in (b'data: \xff\n\n', b'data: {bad}\n\n',
                    wire() + b'data: {}\n\n', b'junk\n\n'):
            with self.subTest(raw=raw):
                result, _ = self.collect([raw])
                self.assertEqual(result['transport_error'], 'INVALID_SSE')
                self.assertEqual(base64.b64decode(result['response_body_base64']), raw)

    def test_size_limit_does_not_accept_valid_prefix(self):
        raw = wire(done=False) + b'x' * 500000
        result, _ = self.collect([raw])
        self.assertEqual(result['transport_error'], 'RESPONSE_LIMIT')
        self.assertFalse(compare_pairs(requests()[:1], [result])['pairs'][0]['same_valid_action'])

    def test_http_errors_redirects_and_wrong_content_type_fail(self):
        for status, mime, error in ((500, 'application/json', 'HTTP_STATUS'),
                                   (302, 'text/event-stream', 'HTTP_STATUS'),
                                   (200, 'application/json', 'INVALID_CONTENT_TYPE')):
            with self.subTest(status=status, mime=mime):
                raw = b'{"error":"synthetic failure"}'
                result, connection = self.collect([raw], status=status, content_type=mime)
                self.assertEqual(base64.b64decode(result['response_body_base64']), raw)
                self.assertEqual(result['transport_error'], error)
                self.assertEqual(connection.request.call_count, 1)

    def test_late_data_after_done_is_independent_of_chunk_boundary(self):
        for chunks in ([wire() + b'data: {}\n\n'], [wire(), b'data: {}\n\n']):
            result, _ = self.collect(chunks)
            self.assertEqual(result['transport_error'], 'INVALID_SSE')
            self.assertFalse(compare_pairs(requests()[:1], [result])['pairs'][0]['same_valid_action'])

    def test_incomplete_http_body_retains_partial_bytes(self):
        prefix = wire(events()[:2], done=False)
        result, _ = self.collect([prefix, collector.http.client.IncompleteRead(b'partial')])
        self.assertEqual(base64.b64decode(result['response_body_base64']), prefix + b'partial')
        self.assertEqual(result['read_error'], 'INCOMPLETE_READ')
        self.assertEqual(result['transport_error'], 'TRANSPORT_ERROR')

    def test_connection_and_read_errors_are_retained(self):
        result, _ = self.collect([OSError('synthetic')])
        self.assertEqual(result['transport_error'], 'TRANSPORT_ERROR')
        connection = Mock()
        connection.request.side_effect = OSError('synthetic')
        with patch.object(collector.http.client, 'HTTPConnection', return_value=connection):
            result = collector.collect_one(requests()[0], ('127.0.0.1', 12345, '/chat/completions'), timeout=90)
        self.assertEqual(result['transport_error'], 'TRANSPORT_ERROR')
        self.assertTrue(connection.close.called)

    def test_real_http_framing_distinguishes_complete_and_truncated_bodies(self):
        body = wire()
        for missing in (0, 10):
            stream = io.BytesIO(b'HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\n'
                                + ('Content-Length: %d\r\nConnection: close\r\n\r\n' %
                                   (len(body) + missing)).encode() + body)
            socket = Mock()
            socket.makefile.return_value = stream
            def settimeout(value):
                if stream.closed:
                    raise OSError('closed socket')
            socket.settimeout.side_effect = settimeout
            response = collector.http.client.HTTPResponse(socket)
            response.begin()
            connection = Mock()
            connection.sock = socket
            connection.getresponse.return_value = response
            with patch.object(collector.http.client, 'HTTPConnection', return_value=connection):
                result = collector.collect_one(requests()[0], ('127.0.0.1', 12345, '/chat/completions'), timeout=90)
            self.assertEqual(base64.b64decode(result['response_body_base64']), body)
            pair = compare_pairs(requests()[:1], [result])['pairs'][0]
            if missing:
                self.assertEqual(result['transport_error'], 'TRANSPORT_ERROR')
                self.assertFalse(pair['same_valid_action'])
            else:
                self.assertIsNone(result['transport_error'])
                self.assertTrue(pair['same_valid_action'])

    def test_total_deadline_failure_preserved(self):
        response, connection = Mock(), Mock()
        response.status = 200
        response.length = None
        response.isclosed.return_value = False
        response.getheader.return_value = 'text/event-stream'
        response.read1.return_value = wire()
        connection.getresponse.return_value = response
        with patch.object(collector.http.client, 'HTTPConnection', return_value=connection), \
             patch.object(collector.time, 'monotonic', side_effect=[0, 1, 2, 91, 92]):
            result = collector.collect_one(requests()[0], ('127.0.0.1', 12345, '/chat/completions'), timeout=90)
        self.assertEqual(result['transport_error'], 'MODEL_TIMEOUT')

    def test_endpoint_rejects_credentials_external_dns_and_paths(self):
        for value in ('https://127.0.0.1:12345/v1/chat/completions',
                      'http://localhost:12345/v1/chat/completions',
                      'http://example.invalid:12345/v1/chat/completions',
                      'http://192.0.2.1:12345/v1/chat/completions',
                      'http://user:secret@127.0.0.1:12345/v1/chat/completions',
                      'http://127.0.0.1:12345/v1/chat/completions?key=test',
                      'http://127.0.0.1:12345/other', 'http://127.0.0.1/v1/chat/completions'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                collector.endpoint_address(value)
        self.assertEqual(collector.endpoint_address('http://[::1]:12345/chat/completions'),
                         ('::1', 12345, '/chat/completions'))

    def test_server_guard_and_changed_payload_prevent_network(self):
        with patch.object(collector.sys, 'platform', 'darwin'), patch.object(collector, 'collect_one') as send:
            with self.assertRaisesRegex(ValueError, 'server-only'):
                collector.collect_replay(requests(), 'unused', 'unused')
            send.assert_not_called()
        changed = requests()[0]
        changed['payload']['temperature'] = 1
        with patch.object(collector.http.client, 'HTTPConnection') as network:
            with self.assertRaisesRegex(ValueError, 'payload'):
                collector.collect_one(changed, ('127.0.0.1', 12345, '/chat/completions'), timeout=90)
            network.assert_not_called()

    def test_collection_persists_before_sending_and_stops_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'replay'
            def send(request, address, timeout):
                self.assertEqual(json.loads((output / 'requests.json').read_text()), requests())
                return {'identity': collector.identity(request), 'request_sha256': request['request_sha256'],
                        'events': [], 'transport_error': 'MODEL_TIMEOUT'}
            with patch.object(collector.sys, 'platform', 'linux'), \
                 patch.dict(os.environ, {'CHAT_AI_TRAINING_SERVER': '1'}), \
                 patch.object(collector, 'collect_one', side_effect=send) as mocked:
                report = collector.collect_replay(requests(), 'http://127.0.0.1:12345/chat/completions', output)
            self.assertEqual(mocked.call_count, 1)
            self.assertEqual(len((output / 'responses.jsonl').read_text().splitlines()), 1)
            self.assertFalse(report['transport_complete'])
            self.assertFalse(report['model_accepted'])
            self.assertNotIn('comparison', report)

    def test_complete_collection_still_cannot_authorize_training(self):
        with tempfile.TemporaryDirectory() as directory:
            def send(request, address, timeout):
                return {'identity': collector.identity(request), 'request_sha256': request['request_sha256'],
                        'events': events(), 'transport_error': None}
            with patch.object(collector.sys, 'platform', 'linux'), \
                 patch.dict(os.environ, {'CHAT_AI_TRAINING_SERVER': '1'}), \
                 patch.object(collector, 'collect_one', side_effect=send):
                report = collector.collect_replay(requests(), 'http://127.0.0.1:12345/chat/completions',
                                                  Path(directory) / 'replay')
            self.assertTrue(report['transport_complete'])
            self.assertFalse(report['full_training_authorized'])
            self.assertEqual(report['comparison']['by_split']['train']['same_valid_action'], 1)

    def test_duplicate_requests_and_invalid_timeouts_rejected_before_io(self):
        with patch.object(collector.sys, 'platform', 'linux'), \
             patch.dict(os.environ, {'CHAT_AI_TRAINING_SERVER': '1'}), \
             patch.object(collector, 'collect_one') as send:
            for inputs, timeout in ((requests() * 2, 90), ([], 90), (requests(), True),
                                    (requests(), float('nan')), (requests(), 0)):
                with self.subTest(), self.assertRaises(ValueError):
                    collector.collect_replay(inputs, 'http://127.0.0.1:12345/chat/completions', 'unused', timeout=timeout)
            send.assert_not_called()


if __name__ == '__main__':
    unittest.main()
