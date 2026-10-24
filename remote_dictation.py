"""Uzak dikte ucu: iFonzo canli ajan grafi (Vault) iPhone/iPad'de kaydedilen sesi buraya yollar.

Yalniz 127.0.0.1'de dinler. Tek istemci ayni makinedeki Vault terminal koprusudur (iFonzo
memory/garden/tools/dikte.cjs); Tailscale kimlik denetimi orada yapilir. Ses 16 kHz mono 16-bit PCM
(ham, little-endian) gelir, bellekte kalir, diske yazilmaz; sonuc metni yanitla doner, yapistirma yoktur.
Tarayici sayfasinin bu uca dogrudan istek atmasi engellenir: X-Vault-Dikte basligi zorunludur (capraz site
on-ucus gerektirir) ve Host yalniz 127.0.0.1:<port> olabilir (DNS yeniden baglama).

POST /hazirla?pane=<id>[&makine=<etiket>]  kayit basinda: o pane'in sohbet baglamini isit (bos yanit)
POST /dikte?pane=<id>[&makine=<etiket>]    govde PCM; yanit {"metin": ..., "sureler": {...}}
"""
import json
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import numpy as np

PORT = 5190
SAMPLE_RATE = 16000
MAX_SECONDS = 300
_PANE = re.compile(r"w[0-9A-Za-z]+:p[0-9A-Za-z]+")
_MACHINE = re.compile(r"[a-z0-9-]{1,40}")


def pcm_to_float(raw):
    """16-bit PCM -> sounddevice ile ayni bicim (float32, -1..+1)."""
    if not raw or len(raw) % 2:
        raise ValueError("PCM uzunlugu gecersiz")
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def target_from_query(query):
    """(pane, makine etiketi); ikisi de istege bagli, bicim disi deger ValueError."""
    values = parse_qs(query)
    pane = (values.get("pane") or [""])[0] or None
    machine = (values.get("makine") or [""])[0] or None
    if pane is not None and not _PANE.fullmatch(pane):
        raise ValueError("pane gecersiz")
    if machine is not None and not _MACHINE.fullmatch(machine):
        raise ValueError("makine gecersiz")
    return pane, machine


def make_handler(dictate, prepare, port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # istek satiri loga girmez

        def _reply(self, code, body):
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if self.headers.get("Host") != f"127.0.0.1:{port}" or self.headers.get("X-Vault-Dikte") != "1":
                return self._reply(403, {"hata": "izin yok"})
            url = urlparse(self.path)
            try:
                pane, machine = target_from_query(url.query)
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._reply(400, {"hata": "geçersiz istek"})
            if url.path == "/hazirla":
                if pane:
                    prepare(pane, machine)
                return self._reply(200, {})
            if url.path != "/dikte":
                return self._reply(404, {"hata": "yol yok"})
            if not 0 < length <= SAMPLE_RATE * 2 * MAX_SECONDS:
                return self._reply(413, {"hata": "ses boş ya da çok uzun"})
            try:
                audio = pcm_to_float(self.rfile.read(length))
            except ValueError:
                return self._reply(400, {"hata": "ses biçimi geçersiz"})
            text, timings = dictate(audio, pane, machine)
            self._reply(200, {"metin": text, "sureler": timings})

    return Handler


def start_server(dictate, prepare, port=PORT, log=None):
    """Arka plan thread'inde baslatir; port doluysa dikte devam eder, yalniz uyari yazilir."""
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(dictate, prepare, port))
    except OSError as exc:
        if log:
            log.warning(f"[UZAK] Uzak dikte ucu acilamadi (127.0.0.1:{port}): {type(exc).__name__}")
        return None
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True, name="dictation-remote").start()
    if log:
        log.info(f"[UZAK] Uzak dikte ucu: http://127.0.0.1:{port}")
    return server
