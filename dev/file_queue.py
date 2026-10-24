"""Canli daemon'daki tek Whisper modeliyle dosya transkripsiyonu icin yerel dosya kuyrugu.

Neden: `--transcribe` daemon acikken reddedilir (ayni GPU'da ikinci model). Dis istemci
(orn. iFonzo WhatsApp hatti) ses dosyasi icin `jobs/<id>.json` birakir; daemon ayni
`transcribe_lock` ile isler ve `done/<id>.json` yazar.

Kurallar: pano/klavye yok, kaynak ses dosyasi tasinmaz/silinmez, MD yazilmaz,
transkript metni log'a yazilmaz. Sadece stdlib; model cagrilari disaridan verilir.

Protokol (v1):
  jobs/<id>.json  {"v":1, "id":"<hex>", "audio":"<mutlak yol>"}   istemci yazar (tmp + rename)
  work/<id>.json  daemon isi atomik rename ile sahiplenir
  done/<id>.json  {"v":1, "id", "status": done|no-speech|too-long|failed, ...}  istemci okur
  worker.json     {"v":1, "pid", ...}  daemon calisirken; cikista silinir
"""

import json
import os
import re
import time

PROTOCOL = 1
JOB_ID_RE = re.compile(r"^[0-9a-f]{16,128}$")
MAX_AUDIO_BYTES = 64 * 1024 * 1024
MIN_AUDIO_SECONDS = 0.3
# Dusuk guven isareti: sure agirlikli avg_logprob veya en yuksek no_speech_prob.
LOW_CONF_LOGPROB = -0.8
LOW_CONF_NO_SPEECH = 0.5


def queue_root(base_dir):
    return os.environ.get("VOICEDICTATION_QUEUE_DIR") or os.path.join(base_dir, ".local", "file-queue")


def _dirs(root):
    dirs = {name: os.path.join(root, name) for name in ("jobs", "work", "done")}
    for path in dirs.values():
        os.makedirs(path, exist_ok=True)
    return dirs


def _write_json(path, value):
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False)
    os.replace(tmp, path)


def _job_names(folder):
    return [n for n in os.listdir(folder) if n.endswith(".json") and JOB_ID_RE.match(n[:-5])]


def write_worker_info(root, **info):
    _dirs(root)
    _write_json(os.path.join(root, "worker.json"),
                {"v": PROTOCOL, "pid": os.getpid(), "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S"), **info})


def remove_worker_info(root):
    path = os.path.join(root, "worker.json")
    try:
        with open(path, encoding="utf-8") as f:
            owner = json.load(f).get("pid")
        if owner == os.getpid():
            os.remove(path)
    except (OSError, ValueError):
        pass


def recover_interrupted(root):
    """Onceki surecte yarim kalan isleri yeniden calistirmaz; 'interrupted' sonucuyla kapatir."""
    dirs = _dirs(root)
    for name in _job_names(dirs["work"]):
        done = os.path.join(dirs["done"], name)
        if not os.path.exists(done):
            _write_json(done, {"v": PROTOCOL, "id": name[:-5], "status": "failed", "error": "interrupted"})
        try:
            os.remove(os.path.join(dirs["work"], name))
        except OSError:
            pass


def claim_next(root):
    """En eski isi atomik rename ile sahiplen. Donus: (id, job) veya None."""
    dirs = _dirs(root)
    names = []
    for name in _job_names(dirs["jobs"]):
        try:
            names.append((os.path.getmtime(os.path.join(dirs["jobs"], name)), name))
        except OSError:
            continue
    for _mtime, name in sorted(names):
        work = os.path.join(dirs["work"], name)
        try:
            os.rename(os.path.join(dirs["jobs"], name), work)
        except OSError:
            continue
        try:
            with open(work, encoding="utf-8") as f:
                job = json.load(f)
        except (OSError, ValueError):
            job = {}
        return name[:-5], job if isinstance(job, dict) else {}
    return None


def release(root, job_id):
    """Kapanista baslamamis isi kuyruga geri koy (yeniden baslatmada kaybolmasin)."""
    dirs = _dirs(root)
    try:
        os.rename(os.path.join(dirs["work"], f"{job_id}.json"), os.path.join(dirs["jobs"], f"{job_id}.json"))
    except OSError:
        pass


def finish(root, job_id, result):
    dirs = _dirs(root)
    _write_json(os.path.join(dirs["done"], f"{job_id}.json"), {"v": PROTOCOL, "id": job_id, **result})
    try:
        os.remove(os.path.join(dirs["work"], f"{job_id}.json"))
    except OSError:
        pass


def validate_job(job_id, job):
    if job.get("v") != PROTOCOL or job.get("id") != job_id:
        return "invalid-job"
    audio = job.get("audio")
    if not isinstance(audio, str) or not os.path.isabs(audio) or not os.path.isfile(audio):
        return "audio-missing"
    size = os.path.getsize(audio)
    if size == 0:
        return "audio-empty"
    if size > MAX_AUDIO_BYTES:
        return "audio-too-large"
    return None


def transcribe_job(job, *, decode, transcribe, has_speech, is_noise, max_seconds, sample_rate=16000):
    """Tek ses dosyasini metne cevir. Model/filtre fonksiyonlari daemon'dan gelir.

    decode(path) -> float32 mono numpy; transcribe(audio) -> (text, segments) (final temizlik dahil).
    """
    try:
        audio = decode(job["audio"])
    except Exception:
        return {"status": "failed", "error": "decode-failed"}
    duration = round(len(audio) / sample_rate, 1)
    if duration > max_seconds:
        return {"status": "too-long", "durationSec": duration}
    if len(audio) < sample_rate * MIN_AUDIO_SECONDS or not has_speech(audio):
        return {"status": "no-speech", "durationSec": duration}
    text, segments = transcribe(audio)
    text = (text or "").strip()
    if not text or is_noise(text):
        return {"status": "no-speech", "durationSec": duration}
    weights = [max(0.01, float(s.get("end", 0)) - float(s.get("start", 0))) for s in segments]
    total = sum(weights) or 1.0
    avg_logprob = sum(float(s.get("avg_logprob", 0.0)) * w for s, w in zip(segments, weights)) / total
    max_no_speech = max((float(s.get("no_speech_prob", 0.0)) for s in segments), default=0.0)
    return {
        "status": "done",
        "text": text,
        "durationSec": duration,
        "segments": len(segments),
        "avgLogprob": round(avg_logprob, 3),
        "maxNoSpeechProb": round(max_no_speech, 3),
        "lowConfidence": avg_logprob < LOW_CONF_LOGPROB or max_no_speech > LOW_CONF_NO_SPEECH,
    }


def serve(root, handle, *, should_stop, is_busy=lambda: False, poll_seconds=1.0, log=None, **worker_info):
    """Daemon thread'i: kuyrugu sirayla isler. Kullanici kayit/isleme yaparken yeni ise baslamaz."""
    recover_interrupted(root)
    write_worker_info(root, **worker_info)
    if log:
        log.info(f"[QUEUE] Dosya kuyrugu hazir: {root}")
    try:
        while not should_stop.is_set():
            claimed = claim_next(root)
            if not claimed:
                should_stop.wait(poll_seconds)
                continue
            job_id, job = claimed
            error = validate_job(job_id, job)
            if error:
                finish(root, job_id, {"status": "failed", "error": error})
                if log:
                    log.warning(f"[QUEUE] {job_id[:12]} reddedildi: {error}")
                continue
            while is_busy() and not should_stop.is_set():
                should_stop.wait(0.25)
            if should_stop.is_set():
                release(root, job_id)
                break
            started = time.time()
            try:
                result = handle(job)
            except Exception as e:
                result = {"status": "failed", "error": "transcribe-failed"}
                if log:
                    log.error(f"[QUEUE] {job_id[:12]} transcribe hatasi: {type(e).__name__}")
            result["elapsedSec"] = round(time.time() - started, 1)
            finish(root, job_id, result)
            if log:
                log.info(f"[QUEUE] {job_id[:12]} -> {result['status']} ({result['elapsedSec']}sn)")
    finally:
        remove_worker_info(root)
