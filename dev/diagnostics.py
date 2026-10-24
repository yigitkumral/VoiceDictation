"""Dikte tanisi: izinli ayrintilari arka planda yerel JSONL'ye yazar."""
import datetime
import hashlib
import json
from pathlib import Path
import queue
import threading
import uuid


class DiagnosticWriter:
    def __init__(self, directory, sources):
        self.directory = Path(directory)
        digest = hashlib.sha256()
        for source in sources:
            digest.update(Path(source).read_bytes())
        self.build = digest.hexdigest()[:16]
        self.run_id = uuid.uuid4().hex
        self.dropped = 0
        self.errors = 0
        self._queue = queue.Queue(maxsize=128)
        self._closed = False
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._write, daemon=True, name='dictation-diagnostics')
        self._worker.start()

    def submit(self, record):
        with self._lock:
            if self._closed:
                self.dropped += 1
                return False
            record = dict(record, schema=1, build=self.build, run_id=self.run_id)
            try:
                self._queue.put_nowait(record)
                return True
            except queue.Full:
                self.dropped += 1
                return False

    def _write(self):
        while True:
            record = self._queue.get()
            try:
                if record is None:
                    return
                self.directory.mkdir(parents=True, exist_ok=True)
                day = datetime.datetime.now().strftime('%Y-%m-%d')
                with (self.directory / (day + '.jsonl')).open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
            except (OSError, TypeError, ValueError):
                self.errors += 1
            finally:
                self._queue.task_done()

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        try:
            self._queue.put(None, timeout=1)
        except queue.Full:
            self.dropped += 1
            return
        self._worker.join(timeout=2)
