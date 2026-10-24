"""Vault uzak dikte ucu: istek denetimi, PCM cevrimi ve dikte akisi sahte model/temizlikle sinanir."""
import http.client
from http.server import ThreadingHTTPServer
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np

from dev.remote_dictation import make_handler, pcm_to_float, target_from_query, client_from_headers
from test_dictation import load


class RequestTests(unittest.TestCase):
    def test_client_metadata_is_bounded_and_unknown_without_headers(self):
        self.assertEqual(client_from_headers({})['device_type'], 'unknown')
        value = client_from_headers({'X-Vault-Device-Type': 'ipad',
                                     'X-Vault-Client-Id': 'synthetic-device-1',
                                     'X-Vault-Request-Id': 'request-123'})
        self.assertEqual(value['device_type'], 'ipad')
        self.assertEqual(value['client_id'], 'synthetic-device-1')
        bad = client_from_headers({'X-Vault-Device-Type': 'invented',
                                   'X-Vault-Client-Id': 'x' * 100,
                                   'X-Vault-Request-Id': 'unsafe/value'})
        self.assertEqual(bad['device_type'], 'unknown')
        self.assertNotIn('client_id', bad)
        self.assertNotIn('request_id', bad)

    def test_pcm_and_target_validation(self):
        audio = pcm_to_float(np.array([0, 16384, -32768], dtype="<i2").tobytes())
        self.assertEqual(audio.dtype, np.float32)
        self.assertEqual(audio.tolist(), [0.0, 0.5, -1.0])
        for bad in (b"", b"\x00"):
            with self.assertRaises(ValueError):
                pcm_to_float(bad)
        self.assertEqual(target_from_query("pane=w12:p3V&makine=mac"), ("w12:p3V", "mac"))
        self.assertEqual(target_from_query(""), (None, None))
        for bad in ("pane=w1:p1;id", "pane=w1:p1&makine=Mac", "makine=a%20b"):
            with self.assertRaises(ValueError):
                target_from_query(bad)


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.dictate = Mock(return_value=("merhaba dunya", {"total_ms": 5}))
        self.prepare = Mock()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), None)
        self.port = self.server.server_address[1]
        self.server.RequestHandlerClass = make_handler(self.dictate, self.prepare, self.port)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def post(self, path, body=b"", host=None, header=True, client_headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.putrequest("POST", path, skip_host=True)
        conn.putheader("Host", host or f"127.0.0.1:{self.port}")
        if header:
            conn.putheader("X-Vault-Dikte", "1")
        for name, value in (client_headers or {}).items():
            conn.putheader(name, value)
        conn.putheader("Content-Length", str(len(body)))
        conn.endheaders(body)
        response = conn.getresponse()
        data = json.loads(response.read() or b"{}")
        conn.close()
        return response.status, data

    def test_only_local_host_with_header(self):
        pcm = np.zeros(1600, dtype="<i2").tobytes()
        self.assertEqual(self.post("/dikte?pane=w1:p1", pcm, header=False)[0], 403)
        self.assertEqual(self.post("/dikte?pane=w1:p1", pcm, host="kotu.example")[0], 403)
        self.dictate.assert_not_called()

    def test_dictate_and_prepare(self):
        pcm = (np.ones(3200, dtype="<i2") * 100).tobytes()
        status, data = self.post("/dikte?pane=w12:p3V&makine=mac", pcm)
        self.assertEqual((status, data["metin"]), (200, "merhaba dunya"))
        audio, pane, machine = self.dictate.call_args.args
        self.assertEqual(self.dictate.call_args.kwargs['client']['channel'], 'vault')
        self.assertEqual((len(audio), pane, machine), (3200, "w12:p3V", "mac"))
        self.assertEqual(self.post("/hazirla?pane=w12:p3V")[0], 200)
        self.prepare.assert_called_once_with("w12:p3V", None)
        self.assertEqual(self.post("/dikte?pane=w1:p1", b"")[0], 413)
        self.assertEqual(self.post("/dikte?pane=w1:p1;x", pcm)[0], 400)
        self.assertEqual(self.post("/baska", pcm)[0], 404)

    def test_client_headers_reach_callback_without_raw_agent_or_ip(self):
        pcm = np.zeros(1600, dtype='<i2').tobytes()
        status, _ = self.post('/dikte', pcm, client_headers={
            'X-Vault-Device-Type': 'iphone', 'X-Vault-Client-Id': 'browser-profile-1',
            'X-Vault-Request-Id': 'request-id-1', 'User-Agent': 'not-for-logging',
            'X-Forwarded-For': '192.0.2.1'})
        self.assertEqual(status, 200)
        self.assertEqual(self.dictate.call_args.kwargs['client'], {
            'channel': 'vault', 'device_type': 'iphone', 'evidence': 'client_reported',
            'client_id': 'browser-profile-1', 'request_id': 'request-id-1'})


class RemoteDictateTests(unittest.TestCase):
    def test_machine_slug_matches_vault_and_collisions_are_rejected(self):
        ns = load('_remote_selection')
        ns.update(_remote_profiles=Mock(return_value={'one': {'id': 'one', 'label': 'Macbook-Pro'}}),
                  _herdr_json=Mock(return_value={'pane': {'terminal_id': 'term-1'}}))
        result = ns['_remote_selection']('w1:p1', 'macbook-pro')
        self.assertEqual(result['machine'], 'one')
        ns['_herdr_json'].assert_called_once_with(['pane', 'get', 'w1:p1'], 'one')
        ns['_remote_profiles'].return_value['two'] = {'id': 'two', 'label': 'Macbook Pro'}
        with self.assertRaises(ValueError):
            ns['_remote_selection']('w1:p1', 'macbook-pro')

    def namespace(self, key):
        stop = threading.Event()
        ns = load("_remote_dictate")
        ns.update(SAMPLE_RATE=16000, _remote_lock=threading.Lock(),
                  _remote_state=dict(key=key, selection={"pane_id": "w1:p1"}, stop=stop),
                  remote_cache=SimpleNamespace(request=Mock(return_value={"status": "conversation", "words": 7, "text": "x"})),
                  quick_transcribe=Mock(return_value="ham metin"), _cleanup_text=Mock(return_value="temiz metin"),
                  cleanup_stats=SimpleNamespace(value={"status": "accepted", "backend": "CUDA0"}),
                  _write_timing=Mock(), _start_diagnostic=Mock(return_value='trace'),
                  _diagnostic_event=Mock(), _finish_diagnostic=Mock())
        return ns, stop

    def test_uses_warm_context_only_for_same_pane_and_never_pastes(self):
        ns, stop = self.namespace(("w1:p1", None))
        text, timings = ns["_remote_dictate"](np.zeros(16000, dtype=np.float32), "w1:p1", None)
        self.assertEqual(text, "temiz metin")
        self.assertTrue(stop.is_set())
        self.assertEqual(ns["quick_transcribe"].call_args.kwargs["context"]["words"], 7)
        self.assertEqual(timings["context_words"], 7)
        row = ns["_write_timing"].call_args.args[0]
        self.assertEqual((row["status"], row["source"]), ("returned", "vault"))
        self.assertNotIn("pyperclip", ns)
        ns['_finish_diagnostic'].assert_called_once()
        self.assertEqual(ns['_start_diagnostic'].call_args.args[1]['client']['channel'], 'vault')

        ns, _ = self.namespace(("w9:p9", None))
        ns["_remote_dictate"](np.zeros(16000, dtype=np.float32), "w1:p1", None)
        self.assertEqual(ns["quick_transcribe"].call_args.kwargs["context"], "")

    def test_short_audio_is_empty(self):
        ns, _ = self.namespace(None)
        text, _ = ns["_remote_dictate"](np.zeros(1000, dtype=np.float32), None, None)
        self.assertEqual(text, "")
        ns["quick_transcribe"].assert_not_called()
        self.assertEqual(ns["_write_timing"].call_args.args[0]["status"], "empty")

    def test_remote_trace_retains_client_target_context_and_failure(self):
        ns, _ = self.namespace(("w1:p1", None))
        helpers = load('_remote_dictate', '_start_diagnostic', '_finish_diagnostic', '_diagnostic_event', '_diagnostic_window')
        for name, value in ns.items():
            if name not in {'_remote_dictate', '_start_diagnostic', '_finish_diagnostic', '_diagnostic_event', '_diagnostic_window'}:
                helpers[name] = value
        ns = helpers
        writer = Mock(dropped=0, errors=0)
        ns.update(diagnostic_state=threading.local(), diagnostic_writer=writer)
        client = {'channel': 'vault', 'device_type': 'iphone', 'client_id': 'synthetic-1'}
        ns['_remote_dictate'](np.zeros(16000, dtype=np.float32), 'w1:p1', None, client=client)
        row = writer.submit.call_args.args[0]
        self.assertEqual(row['source']['client'], client)
        self.assertEqual(row['stages']['context']['used']['words'], 7)
        self.assertEqual(row['stages']['remote_target']['pane_id'], 'w1:p1')
        self.assertEqual(row['stages']['remote_result']['text'], 'temiz metin')
        self.assertIsNone(ns['diagnostic_state'].trace)
        ns['quick_transcribe'].side_effect = RuntimeError('synthetic')
        ns['_remote_dictate'](np.zeros(16000, dtype=np.float32), 'w1:p1', None, client=client)
        self.assertEqual(writer.submit.call_args.args[0]['timings']['status'], 'error')
        self.assertIsNone(ns['diagnostic_state'].trace)


if __name__ == "__main__":
    unittest.main()
