"""file_queue birim testleri (model/GPU yok). Calistirma:
    venv\\Scripts\\python -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import file_queue as fq  # noqa: E402

JOB_ID = "a" * 64
SR = 16000


class Audio(list):
    """numpy gerektirmeyen sahte ses: sadece uzunluk onemli."""


def job_file(root, job_id, audio):
    os.makedirs(os.path.join(root, "jobs"), exist_ok=True)
    with open(os.path.join(root, "jobs", f"{job_id}.json"), "w", encoding="utf-8") as f:
        json.dump({"v": 1, "id": job_id, "audio": audio}, f)


def result(root, job_id):
    with open(os.path.join(root, "done", f"{job_id}.json"), encoding="utf-8") as f:
        return json.load(f)


def run(decode=None, transcribe=None, has_speech=lambda a: True, is_noise=lambda t: False, max_seconds=600):
    return lambda job: fq.transcribe_job(
        job, decode=decode or (lambda p: Audio([0] * SR * 2)),
        transcribe=transcribe or (lambda a: ("Merhaba", [{"start": 0, "end": 2, "avg_logprob": -0.2,
                                                           "no_speech_prob": 0.01}])),
        has_speech=has_speech, is_noise=is_noise, max_seconds=max_seconds, sample_rate=SR)


class TranscribeJobTests(unittest.TestCase):
    job = {"audio": "x.ogg"}

    def test_done_with_confidence(self):
        out = run()(self.job)
        self.assertEqual(out["status"], "done")
        self.assertEqual(out["text"], "Merhaba")
        self.assertFalse(out["lowConfidence"])

    def test_low_confidence(self):
        segs = [{"start": 0, "end": 2, "avg_logprob": -1.1, "no_speech_prob": 0.2}]
        self.assertTrue(run(transcribe=lambda a: ("Belki", segs))(self.job)["lowConfidence"])
        segs = [{"start": 0, "end": 2, "avg_logprob": -0.3, "no_speech_prob": 0.7}]
        self.assertTrue(run(transcribe=lambda a: ("Belki", segs))(self.job)["lowConfidence"])

    def test_broken_file(self):
        def broken(path):
            raise ValueError("invalid data")
        self.assertEqual(run(decode=broken)(self.job), {"status": "failed", "error": "decode-failed"})

    def test_silence_and_noise_do_not_reach_model(self):
        called = []
        spy = lambda a: called.append(1) or ("x", [])
        self.assertEqual(run(has_speech=lambda a: False, transcribe=spy)(self.job)["status"], "no-speech")
        self.assertEqual(run(decode=lambda p: Audio([0] * 100), transcribe=spy)(self.job)["status"], "no-speech")
        self.assertEqual(called, [])
        self.assertEqual(run(transcribe=lambda a: ("", []))(self.job)["status"], "no-speech")
        self.assertEqual(run(is_noise=lambda t: True)(self.job)["status"], "no-speech")

    def test_too_long(self):
        out = run(decode=lambda p: Audio([0] * SR * 11), max_seconds=10)(self.job)
        self.assertEqual(out["status"], "too-long")


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "queue")
        self.audio = os.path.join(self.tmp.name, "voice.ogg")
        with open(self.audio, "wb") as f:
            f.write(b"OggS")

    def tearDown(self):
        self.tmp.cleanup()

    def serve(self, handle, is_busy=lambda: False, until=None):
        stop = threading.Event()
        thread = threading.Thread(target=fq.serve, args=(self.root, handle),
                                  kwargs=dict(should_stop=stop, is_busy=is_busy, poll_seconds=0.05), daemon=True)
        thread.start()
        deadline = time.time() + 5
        while time.time() < deadline and not (until or (lambda: False))():
            time.sleep(0.02)
        stop.set()
        thread.join(5)
        self.assertFalse(thread.is_alive())

    def done_exists(self, job_id=JOB_ID):
        return lambda: os.path.exists(os.path.join(self.root, "done", f"{job_id}.json"))

    def test_job_processed_once_and_worker_info_removed(self):
        calls = []
        job_file(self.root, JOB_ID, self.audio)
        self.serve(lambda job: calls.append(job["audio"]) or {"status": "done", "text": "Tamam"},
                   until=self.done_exists())
        self.assertEqual(calls, [self.audio])
        self.assertEqual(result(self.root, JOB_ID)["status"], "done")
        self.assertFalse(os.listdir(os.path.join(self.root, "jobs")))
        self.assertFalse(os.listdir(os.path.join(self.root, "work")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "worker.json")))
        self.assertTrue(os.path.exists(self.audio), "kaynak ses tasinmamali/silinmemeli")

    def test_invalid_and_missing_jobs_fail_without_model(self):
        other = "b" * 64
        job_file(self.root, JOB_ID, os.path.join(self.tmp.name, "missing.ogg"))
        job_file(self.root, other, "relative.ogg")
        with open(os.path.join(self.root, "jobs", "not-a-job.json"), "w") as f:
            f.write("{}")
        self.serve(lambda job: self.fail("model cagrilmamali"),
                   until=lambda: self.done_exists()() and self.done_exists(other)())
        self.assertEqual(result(self.root, JOB_ID)["error"], "audio-missing")
        self.assertEqual(result(self.root, other)["error"], "audio-missing")
        self.assertTrue(os.path.exists(os.path.join(self.root, "jobs", "not-a-job.json")))

    def test_waits_while_user_dictates(self):
        busy = threading.Event()
        busy.set()
        started = []
        job_file(self.root, JOB_ID, self.audio)

        def handle(job):
            started.append(busy.is_set())
            return {"status": "done", "text": "x"}

        threading.Timer(0.4, busy.clear).start()
        self.serve(handle, is_busy=busy.is_set, until=self.done_exists())
        self.assertEqual(started, [False])

    def test_interrupted_work_is_not_rerun(self):
        os.makedirs(os.path.join(self.root, "work"), exist_ok=True)
        with open(os.path.join(self.root, "work", f"{JOB_ID}.json"), "w") as f:
            json.dump({"v": 1, "id": JOB_ID, "audio": self.audio}, f)
        self.serve(lambda job: self.fail("yarim is tekrar calismamali"), until=self.done_exists())
        self.assertEqual(result(self.root, JOB_ID)["error"], "interrupted")

    def test_handler_crash_becomes_failed_result(self):
        job_file(self.root, JOB_ID, self.audio)

        def crash(job):
            raise RuntimeError("cuda")
        self.serve(crash, until=self.done_exists())
        self.assertEqual(result(self.root, JOB_ID)["error"], "transcribe-failed")

    def test_stop_while_busy_releases_job(self):
        job_file(self.root, JOB_ID, self.audio)
        claimed = lambda: os.path.exists(os.path.join(self.root, "work", f"{JOB_ID}.json"))
        self.serve(lambda job: self.fail("mesgulken baslamamali"), is_busy=lambda: True, until=claimed)
        self.assertTrue(os.path.exists(os.path.join(self.root, "jobs", f"{JOB_ID}.json")))


if __name__ == "__main__":
    unittest.main()
