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
from logging.handlers import TimedRotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, "dictation.log")

log = logging.getLogger("dictation")
log.setLevel(logging.DEBUG)

# Dosya handler — gunluk rotate, tum gecmis saklanir
_fh = TimedRotatingFileHandler(
    _LOG_FILE, when="midnight", interval=1,
    backupCount=0,  # 0 = sinirsiz, hicbir log silinmez
    encoding="utf-8",
)
_fh.suffix = "%Y-%m-%d"  # dictation.log.2026-03-15
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

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
LECTURE_MODEL_SIZE = "turbo"  # Toplanti/ders/dosya transkripti icin (turbo = large-v3-turbo)
MLX_MODEL_REPO = "mlx-community/whisper-turbo"
MLX_LECTURE_MODEL_REPO = "mlx-community/whisper-turbo"

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

# Lecture live (VAD-bazli anlik transcribe)
LIVE_SILENCE_DURATION = 1.5    # 1.5sn sessizlik = cumle sonu, transcribe et
LIVE_MIN_CHUNK_SECONDS = 3.0   # bu kadar olmadan transcribe etme (cok kisa chunk gurultu)
LIVE_MAX_CHUNK_SECONDS = 25.0  # bu kadar olduysa zorla bol (hizli konusmaci icin)

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

_WAV_RECORDING = _make_wav([(520, 150), (780, 150)], 0.05)
_WAV_SENT = _make_wav([(880, 120), (880, 120)], 0.05)
_WAV_ERROR = _make_wav([(280, 250)], 0.05)

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
_last_audio_callback = 0  # watchdog icin son callback zamani
model = None
speech_detected = False
last_speech_time = 0
listen_speech_detected = False
listen_last_speech_time = 0
wake_word_enabled = False  # Anahtar kelime (Zugzwang) varsayilan kapali, tray'den acilabilir
current_modifiers = set()
should_quit = threading.Event()
_last_hotkey_tap = 0  # double-tap icin son basma zamani
_hotkey_press_start = 0.0  # long-press reset icin baslangic zamani
_long_press_timer = None  # long-press timer
_long_press_fired = False  # timer tetiklendi mi
LONG_PRESS_RESET = 1.25  # 1.25 saniye basili tutma = reset
_gui = None  # GUI referansi

# --- LECTURE / FILE MODE STATE ---
# RAM-only: ses dosyasi DISKE YAZILMIYOR. Sadece bellekte chunk'lar tutulur,
# kayit bitince transcribe edilir ve buffer temizlenir.
lecture_active = False
lecture_audio_chunks = []                     # tum kayit (numpy chunk listesi) - RAM
lecture_audio_chunks_lock = threading.Lock()
lecture_start_time = 0.0
lecture_lock = threading.Lock()

# Live transcribe (VAD-bazli, anlik MD'ye append)
lecture_live_buffer = []                      # cumle bazli flush icin numpy chunks
lecture_live_buffer_lock = threading.Lock()
lecture_live_md_path = None                   # canli MD dosyasi
lecture_live_speech_detected = False          # bu chunk'ta konusma algilandi mi
lecture_live_last_speech_time = 0.0           # son konusma zamani (silence olcumu icin)


# --- MINI GUI (sag ust kose) ---

def _do_reset():
    """Durumu sifirla — hangi state'te olursa olsun LISTENING'e don."""
    global speech_detected, listen_speech_detected
    with audio_lock:
        audio_frames.clear()
    with listen_lock:
        listen_frames.clear()
    speech_detected = False
    listen_speech_detected = False
    sm.force(State.LISTENING)
    sound_error()
    log.info("[RESET] Kullanici tarafindan sifirlandi.")


def start_gui():
    """macOS menu bar icon ile durum gosterimi."""
    if IS_MAC:
        _start_menubar_gui()
    else:
        _start_tray_gui()


def _start_menubar_gui():
    """macOS menu bar uygulamasi (rumps) — tam ekranda da gorunur."""
    import rumps

    _state_icons = {
        State.LISTENING:  "🟢",
        State.RECORDING:  "🔴",
        State.PROCESSING: "🟡",
        State.COOLDOWN:   "⚪",
    }
    _state_labels = {
        State.LISTENING:  "Hazır",
        State.RECORDING:  "Kayıt...",
        State.PROCESSING: "İşliyor...",
        State.COOLDOWN:   "Bekleme",
    }

    class VDMenuBar(rumps.App):
        def __init__(self):
            super().__init__("VD", title="🟢", quit_button=None)
            self._wake_item = rumps.MenuItem(
                "🗣️ Anahtar Kelime: Açık", callback=self.on_toggle_wake
            )
            self._lecture_item = rumps.MenuItem(
                "🎙 Toplantı Kaydı Başlat", callback=self.on_lecture_toggle
            )
            self._file_item = rumps.MenuItem(
                "📁 Ses dosyasını dök...", callback=self.on_pick_file
            )
            self.menu = [
                rumps.MenuItem("Durum: Hazır", callback=None),
                None,  # separator
                self._lecture_item,
                self._file_item,
                None,
                self._wake_item,
                rumps.MenuItem("↺ Sıfırla", callback=self.on_reset),
                None,
                rumps.MenuItem("Çıkış", callback=self.on_quit),
            ]
            self._status_item = self.menu["Durum: Hazır"]

        @rumps.timer(0.3)
        def update_status(self, _):
            if lecture_active:
                self.title = "🟣"
                self._status_item.title = "Durum: Toplantı Kaydı"
                self._lecture_item.title = "⏹ Toplantı Kaydını Durdur"
            else:
                state = sm.state
                icon = _state_icons.get(state, "⚪")
                label = _state_labels.get(state, "?")
                self.title = icon
                self._status_item.title = f"Durum: {label}"
                self._lecture_item.title = "🎙 Toplantı Kaydı Başlat"
            self._wake_item.title = f"🗣️ Anahtar Kelime: {'Açık' if wake_word_enabled else 'Kapalı'}"
            if should_quit.is_set():
                rumps.quit_application()

        def on_toggle_wake(self, _):
            global wake_word_enabled
            wake_word_enabled = not wake_word_enabled
            state = "ACIK" if wake_word_enabled else "KAPALI"
            log.info(f"[WAKE] Anahtar kelime: {state}")

        def on_lecture_toggle(self, _):
            if lecture_active:
                threading.Thread(target=stop_lecture_recording, daemon=True).start()
            else:
                threading.Thread(target=start_lecture_recording, daemon=True).start()

        def on_pick_file(self, _):
            threading.Thread(target=_pick_file_and_transcribe, daemon=True).start()

        def on_reset(self, _):
            _do_reset()

        def on_quit(self, _):
            should_quit.set()
            rumps.quit_application()

    VDMenuBar().run()


def _start_tray_gui():
    """Windows icin sistem tepsisi (pystray) — macOS menu bar karsiligi."""
    import pystray
    from PIL import Image, ImageDraw

    _state_colors = {
        State.LISTENING:  (0, 255, 136),   # yesil
        State.RECORDING:  (255, 68, 68),    # kirmizi
        State.PROCESSING: (255, 170, 0),    # sari
        State.COOLDOWN:   (136, 136, 136),  # gri
    }
    _LECTURE_COLOR = (170, 70, 255)  # mor — toplanti/ders modu
    _state_labels = {
        State.LISTENING:  "Hazır",
        State.RECORDING:  "Kayıt...",
        State.PROCESSING: "İşliyor...",
        State.COOLDOWN:   "Bekleme",
    }

    def make_icon(color):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=color)
        return img

    def on_reset(icon, item):
        _do_reset()

    def on_toggle_wake(icon, item):
        global wake_word_enabled
        wake_word_enabled = not wake_word_enabled
        state = "ACIK" if wake_word_enabled else "KAPALI"
        log.info(f"[WAKE] Anahtar kelime: {state}")

    def on_lecture_toggle(icon, item):
        if lecture_active:
            threading.Thread(target=stop_lecture_recording, daemon=True).start()
        else:
            threading.Thread(target=start_lecture_recording, daemon=True).start()
        try:
            icon.update_menu()
        except Exception:
            pass

    def on_pick_file(icon, item):
        threading.Thread(target=_pick_file_and_transcribe, daemon=True).start()

    def on_quit(icon, item):
        should_quit.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: (f"Durum: 🟣 Toplantı Kaydı" if lecture_active
                          else f"Durum: {_state_labels.get(sm.state, '?')}"),
            None, enabled=False,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: ("⏹  Toplantı Kaydını Durdur" if lecture_active
                          else "🎙  Toplantı Kaydı Başlat"),
            on_lecture_toggle,
        ),
        pystray.MenuItem("📁 Ses dosyasını dök...", on_pick_file),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda item: f"🗣️ Anahtar Kelime: {'Açık' if wake_word_enabled else 'Kapalı'}",
            on_toggle_wake,
            checked=lambda item: wake_word_enabled,
        ),
        pystray.MenuItem("↺ Sıfırla", on_reset),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Çıkış", on_quit),
    )

    icon = pystray.Icon("VoiceDictation", make_icon((0, 255, 136)), "VD: Hazır", menu)

    # Cift-tik destegi: icon olusturulduktan SONRA _message_handlers'i patch ediyoruz.
    # pystray WM_LBUTTONDBLCLK (0x0203) mesajini yoksayar; biz WM_LBUTTONUP (0x0202)
    # zamanlama ile algiliyoruz: 400ms icinde iki tik = cift tik = reset.
    # Ayni zamanda WM_LBUTTONDBLCLK mesaji gelirse de reset yapiyoruz.
    try:
        from pystray._util import win32 as _pw32util
        _WM_LBUTTONUP = 0x0202
        _WM_LBUTTONDBLCLK = 0x0203
        _DBLCLICK_MS = 0.4
        _last_lbuttonup = [0.0]
        _WM_NOTIFY_KEY = _pw32util.WM_NOTIFY
        _orig_handler = icon._message_handlers.get(_WM_NOTIFY_KEY)

        def _dblclick_notify(wparam, lparam):
            if lparam == _WM_LBUTTONUP:
                now = time.time()
                if now - _last_lbuttonup[0] < _DBLCLICK_MS:
                    _last_lbuttonup[0] = 0.0
                    threading.Thread(target=_do_reset, daemon=True).start()
                else:
                    _last_lbuttonup[0] = now
            elif lparam == _WM_LBUTTONDBLCLK:
                _last_lbuttonup[0] = 0.0
                threading.Thread(target=_do_reset, daemon=True).start()
            elif _orig_handler:
                _orig_handler(wparam, lparam)

        icon._message_handlers[_WM_NOTIFY_KEY] = _dblclick_notify
        log.debug("[Tray] Cift-tik instance patch uygulandi.")
    except Exception as e:
        log.warning(f"[Tray] Cift-tik patch basarisiz: {e}")

    def update_loop():
        last_state = None
        last_lecture = False
        while not should_quit.is_set():
            state = sm.state
            cur_lecture = lecture_active
            if state != last_state or cur_lecture != last_lecture:
                if cur_lecture:
                    color = _LECTURE_COLOR
                    label = "Toplantı Kaydı"
                else:
                    color = _state_colors.get(state, (136, 136, 136))
                    label = _state_labels.get(state, "?")
                icon.icon = make_icon(color)
                icon.title = f"VD: {label}"
                try:
                    icon.update_menu()
                except Exception:
                    pass
                last_state = state
                last_lecture = cur_lecture
            time.sleep(0.3)
        icon.stop()

    threading.Thread(target=update_loop, daemon=True).start()

    global _gui
    _gui = icon
    icon.run()


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


# Bilinen halusinasyon kaliplari
_HALLUCINATION_RE = re.compile(
    r"^[\s!.?,;:]+$"                          # sadece noktalama
    r"|^Apa\.?$"                              # Apa.
    r"|^Okay\.?\s*$"                          # Okay.
    r"|^Beep\.?\s*$"                          # Beep.
    r"|^Donama\.?\s*$"                        # Donama.
    r"|Abone ol"                              # YouTube CTA
    , re.IGNORECASE
)

# Temizlenebilir halusinasyon artiklari (uzun metinlerden cikarilir, kisa metinleri filtreler)
_ARTIFACT_RE = re.compile(
    r"Altyaz[ıi]\s*M\.?[A-Z]\.?[A-Z]?\.?"   # Altyazı M.K., Altyazı M.D.D.
    r"|İzlediğiniz için teşekkür\w*"          # YouTube outro
    r"|Abone ol\w*"                           # YouTube CTA
    , re.IGNORECASE
)

# MLX-whisper sessizlikte urettigi Ingilizce baslangic halusinasyonlari
_ENGLISH_HALLUC_RE = re.compile(
    r"^(Thank you\.?\s*|Hold on[^.]*\.\s*|Beep\.?\s*|Come on\.?\s*|"
    r"Okay\.?\s*|Please\b[^.]*\.\s*|Let me[^.]*\.\s*|"
    r"So[,.]?\s+|Well[,.]?\s+|And\s+the\s+)"
    , re.IGNORECASE
)


def _is_hallucination(text):
    """Kisa metinler icin strict halusinasyon filtresi (wake word listener icin)."""
    if not text:
        return True
    if _HALLUCINATION_RE.search(text):
        return True
    if _ARTIFACT_RE.search(text) and len(text.split()) < 10:
        return True
    # Tekrar eden kelime tespiti
    words = text.split()
    if len(words) >= 5:
        from collections import Counter
        counts = Counter(words)
        most_common_word, most_common_count = counts.most_common(1)[0]
        if most_common_count / len(words) > 0.6:
            return True
    return False


def _clean_transcription(text):
    """Transcribe sonucunu temizle: halusinasyon artiklari cikar, gercek icerigi koru.

    - Kisa metinlerde (<10 kelime) strict filtreleme
    - Uzun metinlerde artiklari temizleyip gercek metni kurtarir
    - Ingilizce baslangic halusinasyonlarini cikarir
    """
    if not text:
        return ""

    # 1) Ingilizce baslangic halusinasyonlarini temizle
    cleaned = _ENGLISH_HALLUC_RE.sub("", text).strip()
    if not cleaned:
        return ""

    # 2) Kisa metin: strict filtre
    words = cleaned.split()
    if len(words) < 10:
        if _HALLUCINATION_RE.search(cleaned):
            return ""
        if _ARTIFACT_RE.search(cleaned):
            return ""
        # Tekrar kontrolu
        if len(words) >= 5:
            from collections import Counter
            counts = Counter(words)
            if counts.most_common(1)[0][1] / len(words) > 0.6:
                return ""
        return cleaned

    # 3) Uzun metin: tekrar kontrolu (esik yuksek tutulur, gercek icerik korunur)
    from collections import Counter
    counts = Counter(words)
    most_word, most_count = counts.most_common(1)[0]
    ratio = most_count / len(words)
    # 20+ kelimede sadece %75+ tekrar halusinasyon sayilir (gercek konusmada tekrar normal)
    if len(words) >= 20 and ratio > 0.75:
        return ""
    # 10-19 kelimede %65+ tekrar halusinasyon
    elif len(words) < 20 and ratio > 0.65:
        return ""

    # 4) Uzun metin: artiklari temizle ama gercek icerigi koru
    cleaned = _ARTIFACT_RE.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^[\s.,;:!?]+|[\s.,;:!?]+$", "", cleaned)
    if not cleaned or len(cleaned.split()) < 3:
        return ""
    return cleaned


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
            text = result.get("text", "").strip()
        else:
            segments, _ = model.transcribe(
                audio_data, language="tr", initial_prompt=INITIAL_PROMPT,
                beam_size=1, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300),
            )
            text = " ".join(seg.text.strip() for seg in segments)

    cleaned = _clean_transcription(text)
    if not cleaned:
        log.debug(f"[FILTRE] Halusinasyon filtrelendi ({len(text.split())} kelime): {text[:80]}...")
        return ""
    if cleaned != text:
        log.debug(f"[TEMIZLIK] '{text[:40]}...' -> '{cleaned[:40]}...'")
    return cleaned


# --- LECTURE / FILE TRANSCRIBE ---

def _get_desktop_path():
    """Cross-platform masaustu yolu."""
    return os.path.join(os.path.expanduser("~"), "Desktop")


def _get_lectures_dir():
    """Masaustunde 'VoiceDictation_Lectures' klasorunu garantile.
    NOT: ses dosyasi diske yazilmiyor (RAM-only); sadece transkript MD'leri burada."""
    base = os.path.join(_get_desktop_path(), "VoiceDictation_Lectures")
    os.makedirs(base, exist_ok=True)
    return base


def _transcribe_audio_path(audio, beam_size=5):
    """Dosya yolu VEYA numpy array'inden transkript al (faster-whisper / MLX).
    (text, segments) doner."""
    if isinstance(audio, str):
        label = os.path.basename(audio)
    else:
        label = f"RAM buffer ({len(audio)/SAMPLE_RATE:.0f}sn)"
    log.info(f"[TRANSCRIBE] Calisiyor: {label}")
    t0 = time.time()
    if IS_MAC and USE_MLX:
        result = mlx_whisper.transcribe(
            audio, path_or_hf_repo=MLX_LECTURE_MODEL_REPO,
            language="tr", initial_prompt=INITIAL_PROMPT,
        )
        text = result.get("text", "").strip()
        segments = [
            {"start": float(s.get("start", 0.0)),
             "end": float(s.get("end", 0.0)),
             "text": s.get("text", "").strip()}
            for s in result.get("segments", [])
        ]
    else:
        if model is None:
            raise RuntimeError("Model henuz yuklenmedi (load_model cagir).")
        with transcribe_lock:
            segs, _info = model.transcribe(
                audio, language="tr", initial_prompt=INITIAL_PROMPT,
                beam_size=beam_size, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            segments = []
            for s in segs:
                segments.append({
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": s.text.strip(),
                })
        text = " ".join(s["text"] for s in segments).strip()
    elapsed = time.time() - t0
    log.info(f"[TRANSCRIBE] Tamamlandi ({elapsed:.0f}sn islem, {len(segments)} segment).")
    return text, segments


def _format_seconds(total):
    total = int(total)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}sa {m}dk {s}sn"
    if m > 0:
        return f"{m}dk {s}sn"
    return f"{s}sn"


def _segments_to_paragraphs(segments, target_seconds=30):
    """Segmentleri ~target_seconds uzunlugunda paragraflara grupla."""
    paragraphs = []
    cur = []
    cur_start = None
    for seg in segments:
        if not cur:
            cur_start = seg["start"]
        cur.append(seg["text"])
        if seg["end"] - cur_start >= target_seconds:
            paragraphs.append((cur_start, " ".join(cur).strip()))
            cur = []
            cur_start = None
    if cur and cur_start is not None:
        paragraphs.append((cur_start, " ".join(cur).strip()))
    return paragraphs


def _write_lecture_markdown(md_path, segments, audio_duration, source_path, header_title="Toplanti / Ders Transkripti"):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    paragraphs = _segments_to_paragraphs(segments, target_seconds=30)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {header_title}\n\n")
        f.write(f"- **Tarih:** {timestamp}\n")
        f.write(f"- **Ses suresi:** {_format_seconds(audio_duration)}\n")
        f.write(f"- **Model:** {LECTURE_MODEL_SIZE} ({DEVICE})\n")
        f.write(f"- **Kaynak:** `{source_path}`\n\n")
        f.write("---\n\n")
        if paragraphs:
            for start_sec, paragraph in paragraphs:
                m = int(start_sec // 60); s = int(start_sec % 60)
                f.write(f"**[{m:02d}:{s:02d}]** {paragraph}\n\n")
        else:
            f.write("_(Konusma algilanamadi.)_\n")


def transcribe_file_to_markdown(audio_path, output_dir=None, header_title=None):
    """Dis ses dosyasini transkripte et, Markdown olarak yanına ve Desktop'a yaz.

    output_dir verilmezse: ses dosyasi ile ayni klasore + Desktop/VoiceDictation_Lectures'e iki kopya.
    Donus: olusan ana .md yolu (basarisizsa None).
    """
    if not os.path.isfile(audio_path):
        log.error(f"[FILE] Dosya bulunamadi: {audio_path}")
        return None
    try:
        text, segments = _transcribe_audio_path(audio_path, beam_size=5)
    except Exception as e:
        log.error(f"[FILE] Transcribe hatasi: {e}", exc_info=True)
        return None

    if not segments and not text:
        log.warning("[FILE] Transkript bos.")
        return None

    audio_dur = max((s["end"] for s in segments), default=0.0)
    title = header_title or "Ses Dosyasi Transkripti"
    base_name = os.path.splitext(os.path.basename(audio_path))[0]

    primary_md = os.path.splitext(audio_path)[0] + ".md"
    try:
        _write_lecture_markdown(primary_md, segments, audio_dur, audio_path, header_title=title)
        log.info(f"[FILE] Yazildi: {primary_md}")
    except Exception as e:
        log.error(f"[FILE] Yazma hatasi (kaynak yaninda): {e}")
        primary_md = None

    # Masaustu kopyasi (her zaman)
    try:
        base = _get_lectures_dir()
        desktop_md = os.path.join(base, base_name + ".md")
        _write_lecture_markdown(desktop_md, segments, audio_dur, audio_path, header_title=title)
        log.info(f"[FILE] Masaustu kopyasi: {desktop_md}")
        if primary_md is None:
            primary_md = desktop_md
    except Exception as e:
        log.error(f"[FILE] Masaustu kopya hatasi: {e}")

    return primary_md


def _copy_path_to_clipboard(path):
    """Dosya yolunu clipboard'a kopyala (editor acilamadiginda kullanici manuel acsin)."""
    try:
        pyperclip.copy(path)
        log.info("[EDITOR] Dosya yolu clipboard'a kopyalandi.")
    except Exception as e:
        log.error(f"[EDITOR] Clipboard'a yazilamadi: {e}")


def _open_in_editor(path):
    """Cross-platform editor opener. Sirayla denenir:

       1. ENV var: VOICEDICTATION_EDITOR (kullanici override)
          - "none" -> hicbir editor acma, sadece path'i clipboard'a koy
          - diger -> verilen komutu calistir (orn. "notepad++", "obsidian", "subl")
       2. VS Code (PATH'te 'code' veya 'code.cmd' varsa)
       3. Sistem default (Windows: os.startfile, macOS: open, Linux: xdg-open)
       4. Hicbiri olmazsa clipboard fallback
    """
    import shutil

    # 1) ENV override
    custom = os.environ.get("VOICEDICTATION_EDITOR", "").strip()
    if custom:
        if custom.lower() == "none":
            log.info(f"[EDITOR] VOICEDICTATION_EDITOR=none -> manuel acmak gerekecek: {path}")
            _copy_path_to_clipboard(path)
            return
        try:
            if IS_WIN:
                flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                subprocess.Popen(f'{custom} "{path}"', shell=True, creationflags=flags)
            else:
                subprocess.Popen([custom, path])
            log.info(f"[EDITOR] {custom} ile acildi: {path}")
            return
        except Exception as e:
            log.warning(f"[EDITOR] {custom} acilamadi, fallback'e geciliyor: {e}")

    # 2) VS Code (PATH'te varsa)
    code_cmd = shutil.which("code") or (shutil.which("code.cmd") if IS_WIN else None)
    if code_cmd:
        try:
            if IS_WIN:
                flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                subprocess.Popen(f'code "{path}"', shell=True, creationflags=flags)
            else:
                subprocess.Popen(["code", path])
            log.info(f"[EDITOR] VS Code ile acildi: {path}")
            log.info("[EDITOR] Markdown preview: Ctrl+K V (yan panel) veya Ctrl+Shift+V (yeni tab)")
            return
        except Exception as e:
            log.warning(f"[EDITOR] VS Code acilamadi: {e}")

    # 3) Sistem default (Markdown association ne ise — Notepad/Typora/Obsidian/...)
    try:
        if IS_WIN:
            os.startfile(path)
        elif IS_MAC:
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        log.info(f"[EDITOR] Sistem default ile acildi: {path}")
        return
    except Exception as e:
        log.warning(f"[EDITOR] Sistem default acilamadi: {e}")

    # 4) Hicbiri olmadi -> clipboard fallback
    log.warning(f"[EDITOR] Hicbir editor acilamadi. Manuel ac: {path}")
    _copy_path_to_clipboard(path)


def _init_live_md(md_path, source_label):
    """Canli MD dosyasini header'la initialize et."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Toplanti / Ders — CANLI Transkript\n\n")
        f.write(f"- **Baslangic:** {timestamp}\n")
        f.write(f"- **Mod:** Canli (turbo, beam=1, cumle sonlarinda)\n")
        f.write(f"- **Ses kaynagi:** {source_label}\n")
        f.write("- _Final transkript kayit bitince ayri dosyada yazilacak (paragraf yapisi + segment timestamp)._\n\n")
        f.write("---\n\n")


def _append_live_paragraph(md_path, offset_sec, text):
    """Canli MD'ye timestamp'li paragraf ekle."""
    m = int(offset_sec // 60); s = int(offset_sec % 60)
    try:
        with open(md_path, "a", encoding="utf-8") as f:
            f.write(f"**[{m:02d}:{s:02d}]** {text}\n\n")
    except Exception as e:
        log.error(f"[LIVE] MD yazma hatasi: {e}")


def _live_transcribe_loop(md_path):
    """Lecture aktifken: VAD ile cumle sonlarinda transcribe et, MD'ye append et.

    Tetiklenme:
      - Buffer >= LIVE_MIN_CHUNK_SECONDS VE son konusmadan >= LIVE_SILENCE_DURATION gecti
      - Ya da buffer >= LIVE_MAX_CHUNK_SECONDS (zorla bolme)
    """
    global lecture_live_buffer, lecture_live_speech_detected, lecture_live_last_speech_time
    log.info("[LIVE] Loop basladi.")
    while not should_quit.is_set():
        time.sleep(0.3)
        if not lecture_active:
            break

        with lecture_live_buffer_lock:
            buf_count = len(lecture_live_buffer)
        # 100ms blok varsayimi (audio_callback blocksize = SAMPLE_RATE*0.1)
        buf_seconds = buf_count * 0.1
        if buf_seconds < LIVE_MIN_CHUNK_SECONDS:
            continue

        silence_elapsed = time.time() - lecture_live_last_speech_time
        force_flush = buf_seconds >= LIVE_MAX_CHUNK_SECONDS
        sentence_end = (
            lecture_live_speech_detected
            and silence_elapsed >= LIVE_SILENCE_DURATION
        )
        if not (force_flush or sentence_end):
            continue

        with lecture_live_buffer_lock:
            if not lecture_live_buffer:
                continue
            frames = list(lecture_live_buffer)
            lecture_live_buffer.clear()
        # speech bayragini sifirla; bir sonraki chunk icin yeni konusma beklenir
        lecture_live_speech_detected = False

        # Bu chunk'in offset'i: simdi - lecture_start - chunk_uzunlugu
        chunk_seconds = len(frames) * 0.1
        offset_now = (time.time() - lecture_start_time) - chunk_seconds
        offset_sec = max(0.0, offset_now)

        try:
            audio = np.concatenate(frames, axis=0).flatten()
            text = quick_transcribe(audio)
            if not text:
                log.debug(f"[LIVE] Bos chunk (offset={offset_sec:.0f}sn, sure={chunk_seconds:.0f}sn)")
                continue
            log.info(f"[LIVE] [{int(offset_sec//60):02d}:{int(offset_sec%60):02d}] {text[:80]}{'...' if len(text)>80 else ''}")
            _append_live_paragraph(md_path, offset_sec, text)
        except Exception as e:
            log.error(f"[LIVE] Transcribe hatasi: {e}", exc_info=True)

    # Lecture bitti — kalan buffer'i da flush et (varsa)
    with lecture_live_buffer_lock:
        if lecture_live_buffer:
            frames = list(lecture_live_buffer)
            lecture_live_buffer.clear()
        else:
            frames = []
    if frames:
        chunk_seconds = len(frames) * 0.1
        if chunk_seconds >= 1.0:  # cok kisa olani atla
            offset_now = (time.time() - lecture_start_time) - chunk_seconds
            offset_sec = max(0.0, offset_now)
            try:
                audio = np.concatenate(frames, axis=0).flatten()
                text = quick_transcribe(audio)
                if text:
                    log.info(f"[LIVE] (final flush) [{int(offset_sec//60):02d}:{int(offset_sec%60):02d}] {text[:80]}")
                    _append_live_paragraph(md_path, offset_sec, text)
            except Exception as e:
                log.error(f"[LIVE] Final flush hatasi: {e}")
    log.info("[LIVE] Loop bitti.")


def start_lecture_recording():
    """Tray menusunden cagrilir: RAM-only kayit baslat, live MD olustur, VS Code'da ac.
    DISKE SES YAZILMIYOR — tum ses bellekte tutulur, kayit bitince transcribe edilip silinir."""
    global lecture_active, lecture_start_time, lecture_live_md_path
    global lecture_live_speech_detected, lecture_live_last_speech_time
    with lecture_lock:
        if lecture_active:
            log.warning("[LECTURE] Zaten kayitta.")
            return False
        try:
            base_dir = _get_lectures_dir()
            ts = time.strftime("%Y-%m-%d_%H-%M-%S")
            # Live MD
            lecture_live_md_path = os.path.join(base_dir, f"{ts}_LIVE.md")
            _init_live_md(lecture_live_md_path, "RAM-only — diske ses dosyasi YAZILMIYOR")
            # Buffer / VAD reset
            with lecture_audio_chunks_lock:
                lecture_audio_chunks.clear()
            with lecture_live_buffer_lock:
                lecture_live_buffer.clear()
            lecture_live_speech_detected = False
            lecture_live_last_speech_time = time.time()
            lecture_start_time = time.time()
            lecture_active = True
        except Exception as e:
            log.error(f"[LECTURE] Baslatma hatasi: {e}", exc_info=True)
            sound_error()
            return False

    sound_recording()
    log.info("[LECTURE] Toplanti kaydi basladi (RAM-only, diske ses yazilmiyor)")
    log.info(f"[LECTURE] Canli MD: {lecture_live_md_path}")

    # Live transcribe thread'i baslat
    threading.Thread(
        target=lambda: _live_transcribe_loop(lecture_live_md_path), daemon=True
    ).start()

    # Editor'da canli dosyayi ac (VS Code > sistem default > clipboard fallback)
    _open_in_editor(lecture_live_md_path)

    return True


def stop_lecture_recording():
    """Tray menusunden cagrilir: RAM buffer'i transcribe et, sonra bellegi temizle."""
    global lecture_active, lecture_live_md_path
    with lecture_lock:
        if not lecture_active:
            return False
        live_md = lecture_live_md_path
        duration = time.time() - lecture_start_time
        lecture_active = False  # bu live_loop'un sonunu tetikler
        lecture_live_md_path = None

    # Audio chunks'i bir snapshot'a al ve buffer'i hemen temizle (RAM hassasligi)
    with lecture_audio_chunks_lock:
        chunks = list(lecture_audio_chunks)
        lecture_audio_chunks.clear()

    log.info(f"[LECTURE] Kayit durduruldu ({_format_seconds(duration)}). Final transcribe RAM uzerinden basliyor...")
    sound_sent()

    def _bg(chunks_local, live_md_local, duration_local):
        try:
            if not chunks_local:
                log.warning("[LECTURE] Audio buffer bos, final pass atlandi.")
                return
            audio_data = np.concatenate(chunks_local, axis=0).flatten()
            # RAM kullanimi: chunks_local'i hemen birak
            chunks_local = None

            text, segments = _transcribe_audio_path(audio_data, beam_size=5)
            # Transcribe sonrasi audio_data'yi da birak
            audio_data = None

            if not segments and not text:
                log.warning("[LECTURE] Final transkript bos.")
                sound_error()
                return
            audio_dur = max((s["end"] for s in segments), default=duration_local)
            base = _get_lectures_dir()
            md_name = (
                os.path.basename(live_md_local).replace("_LIVE.md", ".md")
                if live_md_local else
                f"{time.strftime('%Y-%m-%d_%H-%M-%S')}.md"
            )
            md_path = os.path.join(base, md_name)
            _write_lecture_markdown(
                md_path, segments, audio_dur,
                "(RAM-only — diske ses dosyasi yazilmadi)",
                header_title="Toplanti / Ders Transkripti",
            )
            log.info(f"[LECTURE] Final transcript yazildi: {md_path}")
            if live_md_local and os.path.isfile(live_md_local):
                try:
                    with open(live_md_local, "a", encoding="utf-8") as f:
                        f.write(f"\n---\n\n_**Final transkript hazir:** `{md_path}` (paragraf yapili, beam=5 ile)._\n")
                except Exception:
                    pass
            sound_sent()
        except Exception as e:
            log.error(f"[LECTURE] Final transcribe hatasi: {e}", exc_info=True)
            sound_error()

    threading.Thread(target=_bg, args=(chunks, live_md, duration), daemon=True).start()
    return True


def _pick_file_and_transcribe():
    """Tray menusunden cagrilir: tkinter dosya secici ac, secileni transcribe et."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        path = filedialog.askopenfilename(
            title="Transkripte edilecek ses dosyasini sec",
            filetypes=[
                ("Ses dosyalari", "*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.wma *.opus"),
                ("Video (sesi cikarilir)", "*.mp4 *.mov *.mkv *.avi *.webm"),
                ("Tum dosyalar", "*.*"),
            ],
        )
        try:
            root.destroy()
        except Exception:
            pass
        if not path:
            log.info("[FILE] Secim iptal edildi.")
            return
        log.info(f"[FILE] Secildi: {path}")
        sound_recording()
        result = transcribe_file_to_markdown(path)
        if result:
            sound_sent()
        else:
            sound_error()
    except Exception as e:
        log.error(f"[FILE] Picker hatasi: {e}", exc_info=True)
        sound_error()


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
    global _last_audio_callback

    _last_audio_callback = time.time()
    level = np.abs(indata).mean()

    # Lecture mode: RAM-only — diske ses YAZMIYORUZ. Iki paralel buffer:
    #   1) full-duration chunks → final pass icin
    #   2) live buffer → cumle bazli VAD flush
    if lecture_active:
        global lecture_live_speech_detected, lecture_live_last_speech_time
        chunk = indata.copy()
        with lecture_audio_chunks_lock:
            lecture_audio_chunks.append(chunk)
        with lecture_live_buffer_lock:
            lecture_live_buffer.append(chunk)
        if level > SILENCE_THRESHOLD:
            lecture_live_speech_detected = True
            lecture_live_last_speech_time = time.time()

    state = sm.state

    if state == State.RECORDING:
        with audio_lock:
            audio_frames.append(indata.copy())
        if level > SILENCE_THRESHOLD:
            speech_detected = True
            last_speech_time = time.time()

    elif state == State.LISTENING and wake_word_enabled:
        with listen_lock:
            listen_frames.append(indata.copy())
        if level > SILENCE_THRESHOLD:
            listen_speech_detected = True
            listen_last_speech_time = time.time()


# --- CORE ACTIONS ---

def do_start_recording():
    """LISTENING -> RECORDING gecisi. Basarisizsa False doner."""
    global audio_frames, speech_detected, last_speech_time

    if lecture_active:
        log.debug("[REC] Lecture mode aktif, dictation kayit baslatilmadi.")
        return False

    if not sm.transition(State.LISTENING, State.RECORDING):
        return False

    # Listen buffer'daki sesi kayda aktar — sadece son 3 saniye (arka plan birikmesi onlenir)
    with listen_lock:
        all_frames = list(listen_frames)
        listen_frames.clear()
    max_carry_frames = int(SAMPLE_RATE / (SAMPLE_RATE * 0.1) * 1)  # ~1 saniye (10 frame)
    carry_over = all_frames[-max_carry_frames:] if len(all_frames) > max_carry_frames else all_frames
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
        msg = extract_message(text) if (wake_word_enabled and has_wake_word(text)) else text
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

        if wake_word_enabled and has_wake_word(text):
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

    _consecutive_empty = 0  # arka arkaya bos/filtreli sonuc sayaci
    _backoff_time = 0.1     # bekleme suresi (halusinasyon dongusunu kirma)

    while not should_quit.is_set():
        time.sleep(_backoff_time)

        if not wake_word_enabled:
            continue

        if lecture_active:
            # Lecture sirasinda wake word listener bekler
            _consecutive_empty = 0
            _backoff_time = 0.5
            continue

        if sm.state != State.LISTENING:
            _consecutive_empty = 0
            _backoff_time = 0.1
            continue

        # Buffer boyut siniri: maksimum 30 saniye tut (arka plan birikmesini onle)
        _max_listen_frames = int(SAMPLE_RATE / (SAMPLE_RATE * 0.1) * 30)  # ~30sn = 300 frame
        with listen_lock:
            if len(listen_frames) > _max_listen_frames:
                listen_frames[:] = listen_frames[-_max_listen_frames:]

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
            # Bos sonuc — backoff artir (gereksiz transcribe'i azalt)
            _consecutive_empty += 1
            _backoff_time = min(2.0, 0.1 * (2 ** _consecutive_empty))
            continue

        # Basarili transcribe — backoff sifirla
        _consecutive_empty = 0
        _backoff_time = 0.1

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
    if lecture_active:
        log.debug("[HOTKEY] Lecture mode aktif, F13 yoksayildi.")
        return
    state = sm.state
    if state == State.RECORDING:
        do_stop_and_send()
    elif state == State.LISTENING:
        do_start_recording()
    # PROCESSING veya COOLDOWN'daysa hicbir sey yapma


# --- PYNPUT LISTENER ---



_reset_cooldown_until = 0.0  # reset sonrasi bounce engelleme

def _long_press_trigger():
    """Timer tetiklendi — 1.25sn doldu, hemen reset at."""
    global _long_press_fired, _hotkey_press_start, _reset_cooldown_until
    _long_press_fired = True
    _hotkey_press_start = 0.0
    _reset_cooldown_until = time.time() + 0.8  # 800ms cooldown
    log.info(f"[RESET] Long-press algilandi ({LONG_PRESS_RESET}sn)")
    _do_reset()


def on_press(key):
    global _last_hotkey_tap, _hotkey_press_start, _long_press_timer, _long_press_fired

    if _suppress_hotkey:
        return  # paste_and_send sirasinda hotkey'leri yoksay

    # Reset sonrasi bounce engelleme
    if time.time() < _reset_cooldown_until:
        return

    if HOTKEY_RECORD_MODIFIERS:
        if key == HOTKEY_RECORD and HOTKEY_RECORD_MODIFIERS.issubset(current_modifiers):
            if _hotkey_press_start == 0.0 and not _long_press_fired:
                _hotkey_press_start = time.time()
                _long_press_fired = False
                _long_press_timer = threading.Timer(LONG_PRESS_RESET, _long_press_trigger)
                _long_press_timer.daemon = True
                _long_press_timer.start()
            return
    else:
        if key == HOTKEY_RECORD:
            if _hotkey_press_start == 0.0 and not _long_press_fired:
                _hotkey_press_start = time.time()
                _long_press_fired = False
                _long_press_timer = threading.Timer(LONG_PRESS_RESET, _long_press_trigger)
                _long_press_timer.daemon = True
                _long_press_timer.start()
            if IS_MAC and hasattr(sys.modules[__name__], 'DOUBLE_TAP_INTERVAL'):
                return
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
    global _last_hotkey_tap, _hotkey_press_start, _long_press_timer, _long_press_fired

    # Hotkey release: timer tetiklendiyse (reset oldu) hicbir sey yapma, yoksa toggle
    is_hotkey = False
    if HOTKEY_RECORD_MODIFIERS:
        is_hotkey = (key == HOTKEY_RECORD and HOTKEY_RECORD_MODIFIERS.issubset(current_modifiers))
    else:
        is_hotkey = (key == HOTKEY_RECORD)

    if is_hotkey:
        # Timer'i iptal et (henuz tetiklenmediyse)
        if _long_press_timer:
            _long_press_timer.cancel()
            _long_press_timer = None
        _hotkey_press_start = 0.0
        if _long_press_fired:
            # Reset zaten oldu, toggle yapma
            _long_press_fired = False
            return
        # Kisa basma — normal toggle
        if _suppress_hotkey:
            return
        if IS_MAC and hasattr(sys.modules[__name__], 'DOUBLE_TAP_INTERVAL'):
            now = time.time()
            if now - _last_hotkey_tap < DOUBLE_TAP_INTERVAL:
                _last_hotkey_tap = 0
                toggle_recording()
            else:
                _last_hotkey_tap = now
            return
        toggle_recording()
        return

    if key in (pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r, pynput_kb.Key.ctrl):
        current_modifiers.discard(pynput_kb.Key.ctrl)
    elif key in (pynput_kb.Key.alt_l, pynput_kb.Key.alt_r, pynput_kb.Key.alt, pynput_kb.Key.alt_gr):
        current_modifiers.discard(pynput_kb.Key.alt)
    elif key in (pynput_kb.Key.cmd_l, pynput_kb.Key.cmd_r, pynput_kb.Key.cmd):
        current_modifiers.discard(pynput_kb.Key.cmd)


# --- MAIN ---

def _run_headless_transcribe(file_path):
    """--transcribe FILE: GUI/audio stream baslatmadan tek seferlik transcribe."""
    print("=" * 55)
    print("  Voice Dictation - Tek Seferlik Transkript")
    print("=" * 55)
    print(f"  Kaynak : {file_path}")
    print(f"  Model  : {LECTURE_MODEL_SIZE} ({DEVICE})")
    print("=" * 55)
    log.info(f"[HEADLESS] Transcribe basliyor: {file_path}")

    if not os.path.isfile(file_path):
        print(f"\n[HATA] Dosya bulunamadi: {file_path}")
        log.error(f"[HEADLESS] Dosya bulunamadi: {file_path}")
        return 1

    load_model()

    out = transcribe_file_to_markdown(file_path)
    if out:
        print(f"\n[OK] Transkript yazildi: {out}")
        return 0
    print("\n[HATA] Transcribe basarisiz.")
    return 1


def main():
    global audio_stream

    import argparse
    parser = argparse.ArgumentParser(prog="dictation", add_help=True,
                                     description="Voice Dictation - Whisper STT")
    parser.add_argument("--transcribe", metavar="FILE", default=None,
                        help="Headless: ses dosyasini transkripte et ve cik")
    args, _unknown = parser.parse_known_args()

    if args.transcribe:
        sys.exit(_run_headless_transcribe(args.transcribe))

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

    def start_audio_stream():
        global audio_stream, _last_audio_callback
        audio_stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS,
            dtype="float32", callback=audio_callback,
            blocksize=int(SAMPLE_RATE * 0.1),
        )
        audio_stream.start()
        _last_audio_callback = time.time()

    start_audio_stream()

    def audio_watchdog():
        """Uyku/hibernate sonrasi audio stream'i yeniden baslat."""
        global _last_audio_callback
        while not should_quit.is_set():
            time.sleep(3)
            if _last_audio_callback and time.time() - _last_audio_callback > 5:
                log.warning("[WATCHDOG] Audio stream yanitlamiyor, yeniden baslatiliyor...")
                try:
                    audio_stream.stop()
                    audio_stream.close()
                except Exception:
                    pass
                try:
                    start_audio_stream()
                    log.info("[WATCHDOG] Audio stream yeniden baslatildi.")
                    # Kayit durumundaysa LISTENING'e don
                    if sm.state == State.RECORDING:
                        log.warning("[WATCHDOG] Kayit iptal edildi (stream kesildi).")
                        sound_error()
                        sm.force(State.LISTENING)
                except Exception as e:
                    log.error(f"[WATCHDOG] Stream baslatilamadi: {e}")

    threading.Thread(target=audio_watchdog, daemon=True).start()
    threading.Thread(target=wake_word_listener, daemon=True).start()

    log.info("[HAZIR] Dinliyorum...\n"
             "   Baslat: F13 (sniper) veya \"Zugzwang\" de\n"
             "   Durdur: F13 (tekrar) veya \"Zugzwang\" de\n"
             f"   Cikmak icin: {quit_combo}")

    # pynput listener'i thread'de baslat (macOS'ta tkinter main thread olmali)
    _pynput_listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
    _pynput_listener.start()

    # GUI main thread'de calis (macOS gereksinimi)
    start_gui()  # bloklayici — should_quit olunca root.destroy() ile cikar

    _pynput_listener.stop()
    log.info("Kapatiliyor...")
    audio_stream.stop()
    audio_stream.close()
    log.info("Kapatildi.")


if __name__ == "__main__":
    main()
