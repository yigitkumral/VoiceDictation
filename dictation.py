"""
Voice Dictation Tool — Whisper tabanli sesli yazim araci.

State Machine ile yonetilen birlesik kayit sistemi:
  Baslat: F13 (sniper butonu) VEYA "Zugzwang" (sesle)
  Durdur & Gonder: F13 (tekrar bas) VEYA "Zugzwang" (sesle, toggle)

Sessizlikte otomatik gonderme YOK — sen durdurana kadar kayit devam eder.
State gecisleri mutex ile korunur — race condition yok.

Cross-platform: Windows + macOS

Kullanim:
    cd voice-dictation
    # Windows:
    ./venv/Scripts/python dictation.py
    # macOS:
    ./venv/bin/python dictation.py

Cikis: Ctrl+Alt+Q (Windows) / Cmd+Alt+Q (macOS)
"""

import sys
import os
import time
import platform
import threading
import re
import logging
from enum import Enum

# Windows cp1254 encoding fix
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# --- PLATFORM ---
IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

# --- LOGGING ---
_LOG_DIR = os.path.dirname(os.path.abspath(__file__))
_LOG_FILE = os.path.join(_LOG_DIR, "dictation.log")

log = logging.getLogger("dictation")
log.setLevel(logging.DEBUG)

# Dosya handler — DEBUG seviyesinden itibaren her seyi yazar
_fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))

# Konsol handler — INFO seviyesinden itibaren
_ch = logging.StreamHandler(sys.stdout)
_ch.setLevel(logging.INFO)
_ch.setFormatter(logging.Formatter("%(message)s"))

log.addHandler(_fh)
log.addHandler(_ch)

# CUDA DLL'lerini PATH'e ekle (Windows + venv icin gerekli)
if IS_WIN:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    _nvidia_dir = os.path.join(_script_dir, "venv", "Lib", "site-packages", "nvidia")
    if os.path.isdir(_nvidia_dir):
        for _pkg in os.listdir(_nvidia_dir):
            _dll_dir = os.path.join(_nvidia_dir, _pkg, "bin")
            if os.path.isdir(_dll_dir):
                os.add_dll_directory(_dll_dir)
                os.environ["PATH"] = _dll_dir + os.pathsep + os.environ.get("PATH", "")

import io
import wave
import struct
import tempfile
import subprocess
import numpy as np
import sounddevice as sd
import pyperclip
if IS_WIN:
    import winsound
from pynput import keyboard as pynput_kb
## MLX vs faster-whisper gecis: True=mlx, False=faster-whisper
USE_MLX = IS_MAC  # macOS'ta MLX, Windows'ta faster-whisper
if IS_MAC and USE_MLX:
    import mlx_whisper
else:
    from faster_whisper import WhisperModel

# --- AYARLAR ---

WAKE_WORD = "zugzwang"

# Sniper buton
HOTKEY_RECORD = pynput_kb.Key.f13
HOTKEY_RECORD_MODIFIERS = set()
if IS_MAC:
    HOTKEY_RECORD = pynput_kb.Key.caps_lock
    HOTKEY_RECORD_MODIFIERS = set()  # modifier yok, double-tap ile calisir
    DOUBLE_TAP_INTERVAL = 0.4  # 400ms icinde iki kez basarsa toggle

HOTKEY_QUIT_MODIFIERS = {pynput_kb.Key.ctrl, pynput_kb.Key.alt}
if IS_MAC:
    HOTKEY_QUIT_MODIFIERS = {pynput_kb.Key.cmd, pynput_kb.Key.alt}
HOTKEY_QUIT_KEY = pynput_kb.KeyCode.from_char("q")

MODEL_SIZE = "turbo"
MLX_MODEL_REPO = "mlx-community/whisper-turbo"

# Platform-aware device secimi
def _detect_device():
    if IS_MAC and USE_MLX:
        return "mlx", "float16"
    if IS_WIN:
        try:
            import ctranslate2 as _ct2
            _types = _ct2.get_supported_compute_types("cuda")
            if "float16" in _types:
                return "cuda", "float16"
        except Exception:
            pass
    return "cpu", "int8"

DEVICE, COMPUTE_TYPE = _detect_device()

SAMPLE_RATE = 16000
CHANNELS = 1

# Sessizlik algilama
SILENCE_THRESHOLD = 0.008
STOP_CHECK_SILENCE = 0.35
LISTEN_SILENCE_DURATION = 0.5
NO_SPEECH_TIMEOUT = 30.0

INITIAL_PROMPT = (
    "Zugzwang, "
    "Claude, Claude Code, BMAD, Zugzwang, API, commit, deploy, push, pull, "
    "merge, branch, refactor, component, TypeScript, React, OpenClaw, PRD, "
    "MCP, sprint, story, pipeline, Winston, Amelia, workflow, endpoint, "
    "frontend, backend, repository, npm, Node.js, VS Code, extension, "
    "Anthropic, Sonnet, Opus, Haiku, token, prompt, agent, sub-agent, "
    "party mode, orchestrator, gateway, Tailscale, Parsec, Discord"
)


# --- STATE MACHINE ---

class State(Enum):
    LISTENING = "listening"     # Wake word bekliyor
    RECORDING = "recording"    # Aktif kayit
    PROCESSING = "processing"  # Transcribe + gonderim yapiliyor
    COOLDOWN = "cooldown"      # Gonderim sonrasi kisa bekleme


class StateMachine:
    """Thread-safe state machine. Tum gecisler tek mutex ile korunur."""

    def __init__(self):
        self._state = State.LISTENING
        self._lock = threading.Lock()

    @property
    def state(self):
        return self._state

    def transition(self, from_state, to_state):
        """Atomic state gecisi. Basarili ise True doner."""
        with self._lock:
            if isinstance(from_state, (list, tuple)):
                if self._state not in from_state:
                    return False
            else:
                if self._state != from_state:
                    return False
            self._state = to_state
            return True

    def force(self, to_state):
        """Zorla state degistir (hata durumlarinda)."""
        with self._lock:
            self._state = to_state


sm = StateMachine()


# --- SES GERI BILDIRIMI ---

def _make_wav(tones, volume=0.3, rate=22050):
    samples = []
    for freq, dur_ms in tones:
        n = int(rate * dur_ms / 1000)
        t = np.linspace(0, dur_ms / 1000, n, False)
        envelope = np.ones(n)
        fade = max(1, int(n * 0.15))
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
        samples.extend((volume * np.sin(2 * np.pi * freq * t) * envelope).tolist())

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        for s in samples:
            wf.writeframes(struct.pack("<h", int(s * 32767)))
    return buf.getvalue()

_WAV_RECORDING = _make_wav([(520, 150), (780, 150)], 0.25)
_WAV_SENT = _make_wav([(880, 120), (880, 120)], 0.25)
_WAV_ERROR = _make_wav([(280, 250)], 0.2)

def _play_wav(wav_data):
    """Cross-platform WAV playback."""
    if IS_WIN:
        winsound.PlaySound(wav_data, winsound.SND_MEMORY)
    elif IS_MAC:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(wav_data)
            tmp.close()
            subprocess.run(["afplay", tmp.name], check=False)
            os.unlink(tmp.name)
        except Exception:
            pass

def sound_recording():
    threading.Thread(target=lambda: _play_wav(_WAV_RECORDING), daemon=True).start()

def sound_sent():
    threading.Thread(target=lambda: _play_wav(_WAV_SENT), daemon=True).start()

def sound_error():
    threading.Thread(target=lambda: _play_wav(_WAV_ERROR), daemon=True).start()


# --- PASTE/SEND ---
PASTE_KEY = "v"
MODIFIER = pynput_kb.Key.cmd if IS_MAC else pynput_kb.Key.ctrl
paste_controller = pynput_kb.Controller()
_suppress_hotkey = False  # paste_and_send sirasinda hotkey'leri yoksay

def paste_and_send():
    global _suppress_hotkey
    _suppress_hotkey = True
    try:
        time.sleep(0.3)
        paste_controller.press(MODIFIER)
        paste_controller.press(PASTE_KEY)
        paste_controller.release(PASTE_KEY)
        paste_controller.release(MODIFIER)
        time.sleep(0.2)
        paste_controller.press(pynput_kb.Key.enter)
        paste_controller.release(pynput_kb.Key.enter)
    finally:
        time.sleep(0.1)
        _suppress_hotkey = False


# --- AUDIO STATE ---

audio_frames = []
listen_frames = []
audio_lock = threading.Lock()    # audio_frames koruma
listen_lock = threading.Lock()   # listen_frames koruma
transcribe_lock = threading.Lock()  # MLX GPU ayni anda tek transcribe
audio_stream = None
model = None
speech_detected = False
last_speech_time = 0
listen_speech_detected = False
listen_last_speech_time = 0
current_modifiers = set()
should_quit = threading.Event()
_last_hotkey_tap = 0  # double-tap icin son basma zamani


# --- MODEL ---

def load_model():
    global model
    log.info(f"[...] Model yukleniyor: {MODEL_SIZE} ({DEVICE})...")
    log.info("   (Ilk seferde model indirilecek, birkac dakika surebilir)")
    if IS_MAC and USE_MLX:
        # mlx-whisper: ilk transcribe'da model otomatik yuklenir, warm-up yapalim
        _dummy = np.zeros(SAMPLE_RATE, dtype=np.float32)
        mlx_whisper.transcribe(_dummy, path_or_hf_repo=MLX_MODEL_REPO, language="tr")
        log.info("[OK] Model hazir! (MLX — Apple Silicon GPU)")
    else:
        model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
        if DEVICE == "cuda":
            log.info("[...] GPU warm-up yapiliyor...")
            _dummy = np.zeros(SAMPLE_RATE, dtype=np.float32)
            list(model.transcribe(_dummy, language="tr")[0])
            log.info("[OK] GPU hazir!")
        else:
            log.info("[OK] Model hazir!")


def _has_speech(audio_data, threshold=SILENCE_THRESHOLD):
    """Audio verisinde konusma var mi kontrol et (peak-based)."""
    # Ortalama yerine: 100ms pencereler icinde en yuksek ortalamaya bak
    window = int(SAMPLE_RATE * 0.1)
    if len(audio_data) < window:
        return np.abs(audio_data).mean() > threshold
    # En az bir 100ms pencerede threshold'u asan ses varsa True
    for i in range(0, len(audio_data) - window, window):
        if np.abs(audio_data[i:i+window]).mean() > threshold:
            return True
    return False


def quick_transcribe(audio_data):
    # Sessiz audio'yu transcribe etme (halusinasyon onleme)
    if not _has_speech(audio_data):
        return ""

    with transcribe_lock:
        if IS_MAC and USE_MLX:
            result = mlx_whisper.transcribe(
                audio_data, path_or_hf_repo=MLX_MODEL_REPO,
                language="tr", initial_prompt=INITIAL_PROMPT,
            )
            return result.get("text", "").strip()
        else:
            segments, _ = model.transcribe(
                audio_data, language="tr", initial_prompt=INITIAL_PROMPT,
                beam_size=1, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300),
            )
            return " ".join(seg.text.strip() for seg in segments)


# --- REGEX ---

# Whisper varyasyonlari: Zugzwang, Zuckzwang, ZUXWANG, Zvank, Zook Zvank, vb.
_WAKE_RE = re.compile(
    r"\bzu[cgkx]+s?z?w?[ao]n?[gk]\b"  # Zugzwang, Zuckzwang, Zuxwang, Zukwank
    r"|\bzux\s*wang\b"                  # ZUXWANG
    r"|\bzugs?\s*wang\b"                # ZUGS WANG, ZUG WANG
    r"|\bzuck\s*zwang\b"                # ZUCK ZWANG
    r"|\bzuks?\s*wang\b"                # ZUK WANG
    r"|\bzugz?\s*wang\b"                # ZUGZ WANG
    r"|\bz[uü]k\s*z?v[ao]n[gk]\b"      # Zük Zvank, Zuk Vank
    r"|\bzo+k\s*z?v[ao]n[gk]\b"         # Zook Zvank
    r"|\bzvank\b"                        # Zvank (tam kelime, sadece bu form)
    , re.IGNORECASE
)

def has_wake_word(text):
    return bool(_WAKE_RE.search(text))

def extract_message(text):
    """Ilk 'zugzwang' oncesindeki mesaji cikar."""
    matches = list(_WAKE_RE.finditer(text))
    if matches:
        m = matches[0]  # ilk wake word'den onceki mesaj
        msg = text[:m.start()].strip().strip(".,;:!? ")
        return msg if msg else None
    return None


# --- AUDIO CALLBACK ---

def audio_callback(indata, frames, time_info, status):
    global speech_detected, last_speech_time
    global listen_speech_detected, listen_last_speech_time

    level = np.abs(indata).mean()
    state = sm.state

    if state == State.RECORDING:
        with audio_lock:
            audio_frames.append(indata.copy())
        if level > SILENCE_THRESHOLD:
            speech_detected = True
            last_speech_time = time.time()

    elif state == State.LISTENING:
        with listen_lock:
            listen_frames.append(indata.copy())
        if level > SILENCE_THRESHOLD:
            listen_speech_detected = True
            listen_last_speech_time = time.time()


# --- CORE ACTIONS ---

def do_start_recording():
    """LISTENING -> RECORDING gecisi. Basarisizsa False doner."""
    global audio_frames, speech_detected, last_speech_time

    if not sm.transition(State.LISTENING, State.RECORDING):
        return False

    # Listen buffer'daki sesi kayda aktar — mesajin basi kaybolmasin
    with listen_lock:
        carry_over = list(listen_frames)
        listen_frames.clear()
    with audio_lock:
        audio_frames.clear()
        audio_frames.extend(carry_over)

    speech_detected = bool(carry_over)
    last_speech_time = time.time()

    sound_recording()
    log.info("[REC] KAYIT BASLADI - F13 veya \"Zugzwang\" ile durdur")

    # Stop word checker baslat
    threading.Thread(target=stop_word_checker, daemon=True).start()
    return True


def do_send(msg):
    """RECORDING -> PROCESSING -> COOLDOWN -> LISTENING gecisi."""
    global _suppress_hotkey
    if not sm.transition(State.RECORDING, State.PROCESSING):
        return

    try:
        pyperclip.copy(msg)
        log.info(f"[OK] >> {msg}")
        sound_sent()
        paste_and_send()
        log.info("[GONDERILDI]")
    finally:
        sm.force(State.COOLDOWN)
        _suppress_hotkey = True  # Cooldown boyunca hotkey'leri bastir
        with listen_lock:
            listen_frames.clear()
        listen_speech_detected = False
        time.sleep(1.5)
        _suppress_hotkey = False
        sm.force(State.LISTENING)


def do_stop_and_send():
    """F13 ile durdurma: RECORDING -> transcribe -> send."""
    global _suppress_hotkey
    if not sm.transition(State.RECORDING, State.PROCESSING):
        return

    with audio_lock:
        frames_copy = list(audio_frames)

    if not frames_copy:
        log.warning("[!] Ses algilanamadi (buffer bos).")
        sound_error()
        sm.force(State.LISTENING)
        return

    log.info("[STOP] Durduruldu, transcribe ediliyor...")
    audio_data = np.concatenate(frames_copy, axis=0).flatten()
    log.debug(f"Audio buffer: {len(audio_data)} sample ({len(audio_data)/SAMPLE_RATE:.1f}sn)")

    # Cok kisa buffer'lari atla (0.3sn altinda anlamli ses olmaz)
    if len(audio_data) < SAMPLE_RATE * 0.3:
        log.warning("[!] Ses algilanamadi (buffer cok kisa).")
        sound_error()
        sm.force(State.LISTENING)
        return
    text = quick_transcribe(audio_data)

    if text:
        msg = extract_message(text) if has_wake_word(text) else text
        if not msg:
            msg = text

        pyperclip.copy(msg)
        log.info(f"[OK] >> {msg}")
        sound_sent()
        paste_and_send()
        log.info("[GONDERILDI]")
    else:
        log.warning("[!] Ses algilanamadi (transcribe bos).")
        sound_error()

    sm.force(State.COOLDOWN)
    _suppress_hotkey = True
    with listen_lock:
        listen_frames.clear()
    listen_speech_detected = False
    time.sleep(1.5)
    _suppress_hotkey = False
    sm.force(State.LISTENING)


# --- STOP WORD CHECKER ---

def stop_word_checker():
    """Kayit sirasinda 'Zugzwang' stop word'unu arar."""
    global speech_detected, last_speech_time
    last_check_frame_count = 0

    while sm.state == State.RECORDING and not should_quit.is_set():
        time.sleep(0.5)

        if sm.state != State.RECORDING:
            return  # State degisti, cik

        if not speech_detected:
            if time.time() - last_speech_time > NO_SPEECH_TIMEOUT:
                log.warning(f"[IPTAL] {int(NO_SPEECH_TIMEOUT)}sn konusma algilanamadi.")
                sound_error()
                sm.force(State.LISTENING)
                return
            continue

        elapsed = time.time() - last_speech_time
        if elapsed < STOP_CHECK_SILENCE:
            continue

        with audio_lock:
            current_frame_count = len(audio_frames)
        if current_frame_count <= last_check_frame_count:
            continue

        with audio_lock:
            if not audio_frames:
                continue
            frames_copy = list(audio_frames)

        last_check_frame_count = current_frame_count
        audio_data = np.concatenate(frames_copy, axis=0).flatten()
        log.debug("[...] Stop word kontrolu yapiliyor...")
        text = quick_transcribe(audio_data)

        if sm.state != State.RECORDING:
            return  # Transcribe sirasinda state degisti

        if not text:
            continue

        log.info(f"[CHECK] Duydum: {text}")

        if has_wake_word(text):
            msg = extract_message(text)
            if msg:
                do_send(msg)
                return
            else:
                # Sadece "Zugzwang" soylenmis, mesaj yok — kaydi iptal et
                log.info("[IPTAL] Sadece toggle word soylendi, mesaj yok.")
                sound_error()
                sm.force(State.COOLDOWN)
                listen_frames.clear()
                listen_speech_detected = False
                time.sleep(1.0)
                sm.force(State.LISTENING)
                return

        # Yeni konusma bekle
        speech_detected = False
        last_speech_time = time.time()


# --- WAKE WORD LISTENER ---

def wake_word_listener():
    global listen_frames, listen_speech_detected, listen_last_speech_time

    while not should_quit.is_set():
        time.sleep(0.1)

        if sm.state != State.LISTENING:
            continue

        if not listen_speech_detected:
            with listen_lock:
                if len(listen_frames) > int(SAMPLE_RATE / 1600 * 50):
                    listen_frames.clear()
            continue

        elapsed = time.time() - listen_last_speech_time
        if elapsed < LISTEN_SILENCE_DURATION:
            continue

        with listen_lock:
            if not listen_frames:
                continue
            frames_copy = list(listen_frames)
            listen_frames.clear()
        listen_speech_detected = False

        audio_data = np.concatenate(frames_copy, axis=0).flatten()

        if len(audio_data) < SAMPLE_RATE * 0.5:
            continue

        text = quick_transcribe(audio_data)
        if not text:
            continue

        log.debug(f"[LISTEN] Duydum: {text}")

        if has_wake_word(text):
            matches = list(_WAKE_RE.finditer(text))
            if len(matches) >= 2:
                msg = text[matches[0].end():matches[-1].start()].strip().strip(".,;:!? ")
                if msg:
                    log.info(f"[WAKE+STOP] >> {msg}")
                    sm.transition(State.LISTENING, State.PROCESSING)
                    pyperclip.copy(msg)
                    sound_sent()
                    paste_and_send()
                    log.info("[GONDERILDI]")
                    sm.force(State.COOLDOWN)
                    listen_frames.clear()
                    listen_speech_detected = False
                    time.sleep(1.0)
                    sm.force(State.LISTENING)
                continue

            log.info("[WAKE] \"Zugzwang\" algilandi!")
            do_start_recording()


# --- HOTKEY HANDLER ---

def toggle_recording():
    state = sm.state
    if state == State.RECORDING:
        do_stop_and_send()
    elif state == State.LISTENING:
        do_start_recording()
    # PROCESSING veya COOLDOWN'daysa hicbir sey yapma


# --- PYNPUT LISTENER ---

def on_press(key):
    global _last_hotkey_tap

    if _suppress_hotkey:
        return  # paste_and_send sirasinda hotkey'leri yoksay

    if HOTKEY_RECORD_MODIFIERS:
        if key == HOTKEY_RECORD and HOTKEY_RECORD_MODIFIERS.issubset(current_modifiers):
            toggle_recording()
            return
    else:
        if key == HOTKEY_RECORD:
            if IS_MAC and hasattr(sys.modules[__name__], 'DOUBLE_TAP_INTERVAL'):
                now = time.time()
                if now - _last_hotkey_tap < DOUBLE_TAP_INTERVAL:
                    _last_hotkey_tap = 0  # reset
                    toggle_recording()
                else:
                    _last_hotkey_tap = now
                return
            toggle_recording()
            return

    if key in (pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r, pynput_kb.Key.ctrl):
        current_modifiers.add(pynput_kb.Key.ctrl)
    elif key in (pynput_kb.Key.alt_l, pynput_kb.Key.alt_r, pynput_kb.Key.alt, pynput_kb.Key.alt_gr):
        current_modifiers.add(pynput_kb.Key.alt)
    elif key in (pynput_kb.Key.cmd_l, pynput_kb.Key.cmd_r, pynput_kb.Key.cmd):
        current_modifiers.add(pynput_kb.Key.cmd)

    if key == HOTKEY_QUIT_KEY and HOTKEY_QUIT_MODIFIERS.issubset(current_modifiers):
        log.info("[CIKIS] Ctrl+Alt+Q algilandi.")
        should_quit.set()
        return False


def on_release(key):
    if key in (pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r, pynput_kb.Key.ctrl):
        current_modifiers.discard(pynput_kb.Key.ctrl)
    elif key in (pynput_kb.Key.alt_l, pynput_kb.Key.alt_r, pynput_kb.Key.alt, pynput_kb.Key.alt_gr):
        current_modifiers.discard(pynput_kb.Key.alt)
    elif key in (pynput_kb.Key.cmd_l, pynput_kb.Key.cmd_r, pynput_kb.Key.cmd):
        current_modifiers.discard(pynput_kb.Key.cmd)


# --- MAIN ---

def main():
    global audio_stream

    os_name = "macOS" if IS_MAC else "Windows"
    quit_combo = "Cmd+Alt+Q" if IS_MAC else "Ctrl+Alt+Q"
    record_label = "F13 (sniper butonu)" if IS_WIN else "Caps Lock x2 (double-tap)"

    print("=" * 55)
    print("  Voice Dictation Tool - Whisper STT")
    print("=" * 55)
    print(f"  Platform     : {os_name}")
    print(f"  Toggle word  : \"{WAKE_WORD}\" (baslat + durdur)")
    print(f"  Sniper buton : {record_label} (toggle)")
    print(f"  Cikis        : {quit_combo}")
    print(f"  Model        : {MODEL_SIZE} ({DEVICE})")
    print(f"  Custom vocab : {len(INITIAL_PROMPT.split(','))} terim")
    print(f"  Log dosyasi  : {_LOG_FILE}")
    print("=" * 55)
    log.info(f"Baslatildi: {os_name}, model={MODEL_SIZE}, device={DEVICE}")

    load_model()

    audio_stream = sd.InputStream(
        samplerate=SAMPLE_RATE, channels=CHANNELS,
        dtype="float32", callback=audio_callback,
        blocksize=int(SAMPLE_RATE * 0.1),
    )
    audio_stream.start()

    threading.Thread(target=wake_word_listener, daemon=True).start()

    log.info("[HAZIR] Dinliyorum...\n"
             "   Baslat: F13 (sniper) veya \"Zugzwang\" de\n"
             "   Durdur: F13 (tekrar) veya \"Zugzwang\" de\n"
             f"   Cikmak icin: {quit_combo}")

    with pynput_kb.Listener(on_press=on_press, on_release=on_release) as listener:
        should_quit.wait()
        listener.stop()

    log.info("Kapatiliyor...")
    audio_stream.stop()
    audio_stream.close()
    log.info("Kapatildi.")


if __name__ == "__main__":
    main()
