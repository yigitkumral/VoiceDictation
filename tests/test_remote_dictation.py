"""Vault uzak dikte ucu: istek denetimi, PCM cevrimi ve dikte akisi sahte model/temizlikle sinanir."""
import http.client
from http.server import ThreadingHTTPServer
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np

from remote_dictation import make_handler, pcm_to_float, target_from_query
from test_dictation import load


class RequestTests(unittest.TestCase):
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

    def post(self, path, body=b"", host=None, header=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.putrequest("POST", path, skip_host=True)
        conn.putheader("Host", host or f"127.0.0.1:{self.port}")
        if header:
            conn.putheader("X-Vault-Dikte", "1")
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
        self.assertEqual((len(audio), pane, machine), (3200, "w12:p3V", "mac"))
        self.assertEqual(self.post("/hazirla?pane=w12:p3V")[0], 200)
        self.prepare.assert_called_once_with("w12:p3V", None)
        self.assertEqual(self.post("/dikte?pane=w1:p1", b"")[0], 413)
        self.assertEqual(self.post("/dikte?pane=w1:p1;x", pcm)[0], 400)
        self.assertEqual(self.post("/baska", pcm)[0], 404)


class RemoteDictateTests(unittest.TestCase):
    def namespace(self, key):
        stop = threading.Event()
        ns = load("_remote_dictate")
        ns.update(SAMPLE_RATE=16000, _remote_lock=threading.Lock(),
                  _remote_state=dict(key=key, selection={"pane_id": "w1:p1"}, stop=stop),
                  remote_cache=SimpleNamespace(request=Mock(return_value={"status": "conversation", "words": 7, "text": "x"})),
                  quick_transcribe=Mock(return_value="ham metin"), _cleanup_text=Mock(return_value="temiz metin"),
                  cleanup_stats=SimpleNamespace(value={"status": "accepted", "backend": "CUDA0"}),
                  _write_timing=Mock())
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

        ns, _ = self.namespace(("w9:p9", None))
        ns["_remote_dictate"](np.zeros(16000, dtype=np.float32), "w1:p1", None)
        self.assertEqual(ns["quick_transcribe"].call_args.kwargs["context"], "")

    def test_short_audio_is_empty(self):
        ns, _ = self.namespace(None)
        text, _ = ns["_remote_dictate"](np.zeros(1000, dtype=np.float32), None, None)
        self.assertEqual(text, "")
        ns["quick_transcribe"].assert_not_called()
        self.assertEqual(ns["_write_timing"].call_args.args[0]["status"], "empty")


if __name__ == "__main__":
    unittest.main()
