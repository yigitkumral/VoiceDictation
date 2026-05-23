"""
Voice Dictation Tool — Whisper tabanli sesli yazim araci.

State Machine ile yonetilen birlesik kayit sistemi:
  Baslat: F13 (Windows sniper butonu) / Caps Lock x2 (macOS double-tap) VEYA "Diktasyon" (sesle)
  Durdur & Gonder: Ayni hotkey (toggle) VEYA "Diktasyon" (sesle, toggle)

Sessizlikte otomatik gonderme YOK — sen durdurana kadar kayit devam eder.
State gecisleri mutex ile korunur — race condition yok.

Cross-platform: Windows + macOS

Kullanim:
    cd voice-dictation
    # Windows:
    ./venv/Scripts/python dictation.py
    # macOS:
    ./venv/bin/python dictation.py

Cikis: Tray menusu / Menu bar -> Cikis
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
_PID_FILE = os.path.join(_LOG_DIR, "dictation.pid")


def _pid_alive(pid):
    """Cross-platform: verilen PID'in canli olup olmadigini kontrol et."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _read_daemon_pid():
    """PID dosyasini oku, canli ise PID'i don, degilse None."""
    if not os.path.isfile(_PID_FILE):
        return None
    try:
        with open(_PID_FILE, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
    except (ValueError, OSError):
        return None
    return pid if _pid_alive(pid) else None


def _write_daemon_pid():
    """Daemon baslarken PID'i yaz."""
    try:
        with open(_PID_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass


def _remove_daemon_pid():
    """Daemon kapanirken PID dosyasini sil (sadece bizim PID ise)."""
    try:
        if not os.path.isfile(_PID_FILE):
            return
        with open(_PID_FILE, "r", encoding="utf-8") as f:
            pid = int(f.read().strip())
        if pid == os.getpid():
            os.remove(_PID_FILE)
    except (OSError, ValueError):
        pass


def _load_env_file():
    """.env dosyasini yukle (basit KEY=VALUE parser, harici dep yok)."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass


_load_env_file()


def _get_hf_token():
    """HuggingFace token'i al (env veya .env)."""
    return (os.environ.get("HUGGINGFACE_TOKEN")
            or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGING_FACE_HUB_TOKEN"))


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

WAKE_WORD_DEFAULT = "diktasyon"
wake_word_string = WAKE_WORD_DEFAULT  # runtime'da degistirilebilir (tray menusunden)

# Sniper buton
HOTKEY_RECORD = pynput_kb.Key.f13
HOTKEY_RECORD_MODIFIERS = set()
if IS_MAC:
    HOTKEY_RECORD = pynput_kb.Key.caps_lock
    HOTKEY_RECORD_MODIFIERS = set()  # modifier yok, double-tap ile calisir
    DOUBLE_TAP_INTERVAL = 0.4  # 400ms icinde iki kez basarsa toggle

# Cikis hotkey'i kaldirildi: macOS'ta Cmd+Alt+Q sistem kisayoluyla cakisiyor
# (oturum kapatma). Cikis sadece tray menusunden yapilir.

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

# --- CIKTI DIZINLERI (23 Mayis 2026 yeni duzen) ---
# Birincil: G Drive'da Records altinda iki klasor.
#   VoiceDictation/: MD transkriptler (LIVE + final + --transcribe ciktilari)
#   RawRecords/:     islenen ses dosyalari (lecture WAV dump + dis dosyalardan tasinanlar)
# Drive yok / erisilemiyorsa: Desktop/VoiceDictation altinda ayni alt yapi (fallback).
# Hicbir dosya silinmez: lecture sesi WAV'a dumplenir, --transcribe ile gelen dosya TASINIR.
DRIVE_RECORDS_BASE = r"G:\Drive'ım\Records"
DRIVE_VOICEDICTATION_DIR = os.path.join(DRIVE_RECORDS_BASE, "VoiceDictation")
DRIVE_RAWRECORDS_DIR = os.path.join(DRIVE_RECORDS_BASE, "RawRecords")
FALLBACK_BASE = os.path.join(os.path.expanduser("~"), "Desktop", "VoiceDictation")
FALLBACK_VOICEDICTATION_DIR = os.path.join(FALLBACK_BASE, "VoiceDictation")
FALLBACK_RAWRECORDS_DIR = os.path.join(FALLBACK_BASE, "RawRecords")

# Sessizlik algilama
SILENCE_THRESHOLD = 0.008
STOP_CHECK_SILENCE = 0.35
LISTEN_SILENCE_DURATION = 0.5
NO_SPEECH_TIMEOUT = 30.0

# Lecture live (VAD-bazli anlik transcribe)
LIVE_SILENCE_DURATION = 0.8    # 0.8sn sessizlik = cumle sonu, transcribe et (dogal konusma araligi)
LIVE_MIN_CHUNK_SECONDS = 3.0   # bu kadar olmadan transcribe etme (cok kisa chunk gurultu)
LIVE_MAX_CHUNK_SECONDS = 12.0  # bu kadar olduysa zorla bol (surekli konusan icin akiskan canli yazim)
LECTURE_LIVE_BEAM_SIZE = 3     # lecture canli transcribe beam search (1=hizli/dusuk kalite, 5=yavas/yuksek)
# Lecture VAD esigi: cumle sonu sessizligini ayirt etmek icin SILENCE_THRESHOLD'dan yuksek tutulur.
# Mac dahili mikrofonu baseline 0.005-0.015 gurultu uretir; 0.025 konusma vs. fon gurultusu ayrimi yapar.
LECTURE_LIVE_VAD_THRESHOLD = 0.025

# Lecture final-pass temizlik (B2/B3 esikleri — 22 Mayis fix devami)
# Default False: gercek "evet evet evet" cevaplari korunur (CLAUDE.md kurali).
# --aggressive flag veya runtime override ile True yapilabilir.
LECTURE_AGGRESSIVE_CLEANUP = False
LECTURE_CONF_NO_SPEECH = 0.6        # nsp BU DEGER USTU + lp altta -> halusinasyon kabul edilir
LECTURE_CONF_LOGPROB = -1.0         # avg_logprob BU DEGER ALTI + nsp ustte -> halusinasyon
LECTURE_CONF_COMPRESSION = 2.4      # compression_ratio BU DEGER USTU -> ngram tekrar isareti (Whisper default)

INITIAL_PROMPT = (
    # NOT: Wake word ("Diktasyon") buraya KOYULMAZ — prompt'a eklenirse Whisper
    # belirsiz/kisa seslerde wake word'u hayal eder ve false-positive trigger atar.
    # Wake word algilama regex pattern'i ile yapilir, vocabulary boost'a gerek yok.
    "Claude, Claude Code, BMAD, API, commit, deploy, push, pull, "
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
wake_word_enabled = False  # Anahtar kelime (Diktasyon) varsayilan kapali, tray'den acilabilir
current_modifiers = set()
should_quit = threading.Event()
_last_hotkey_tap = 0  # double-tap icin son basma zamani
_hotkey_press_start = 0.0  # long-press reset icin baslangic zamani (Windows)
_long_press_timer = None  # long-press timer (Windows)
_long_press_fired = False  # timer tetiklendi mi (Windows)
LONG_PRESS_RESET = 1.25  # 1.25 saniye basili tutma = reset (Windows F13)
# macOS Caps Lock toggle key oldugu icin long-press calismaz; triple-tap kullanilir.
_hotkey_tap_count = 0  # macOS triple-tap sayaci
_pending_toggle_timer = None  # macOS: 2. tap sonrasi geciktirilmis toggle (3. tap iptal edebilsin)
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
lecture_live_thread = None                    # live transcribe thread handle (stop'ta join icin)


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
            # Toplanti submenu items
            self._lecture_item = rumps.MenuItem(
                "🎙 Toplantı Kaydı Başlat", callback=self.on_lecture_toggle
            )
            self._file_item = rumps.MenuItem(
                "📁 Ses dosyasını dök...", callback=self.on_pick_file
            )
            self._meet_item = rumps.MenuItem(
                "🎙 Meets Dictation (konuşmacı ayır)...", callback=self.on_meet_dictation
            )
            # Ayarlar submenu items
            self._wake_item = rumps.MenuItem(
                "🗣️ Anahtar Kelime Dinleme: Açık", callback=self.on_toggle_wake
            )
            self._wake_change_item = rumps.MenuItem(
                f"✏️  Anahtar Kelime: \"{wake_word_string}\" (değiştir...)",
                callback=self.on_change_wake_word,
            )
            # Submenu containers
            toplanti_submenu = rumps.MenuItem("🎤 Toplantı")
            toplanti_submenu.add(self._lecture_item)
            toplanti_submenu.add(self._file_item)
            toplanti_submenu.add(self._meet_item)

            ayarlar_submenu = rumps.MenuItem("⚙ Ayarlar")
            ayarlar_submenu.add(self._wake_item)
            ayarlar_submenu.add(self._wake_change_item)

            self.menu = [
                rumps.MenuItem("Durum: Hazır", callback=None),
                None,  # separator
                toplanti_submenu,
                ayarlar_submenu,
                None,
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
            self._wake_item.title = f"🗣️ Anahtar Kelime Dinleme: {'Açık' if wake_word_enabled else 'Kapalı'}"
            self._wake_change_item.title = f"✏️  Anahtar Kelime: \"{wake_word_string}\" (değiştir...)"
            if should_quit.is_set():
                rumps.quit_application()

        def on_toggle_wake(self, _):
            global wake_word_enabled
            wake_word_enabled = not wake_word_enabled
            state = "ACIK" if wake_word_enabled else "KAPALI"
            log.info(f"[WAKE] Anahtar kelime: {state}")

        def on_change_wake_word(self, _):
            # rumps Window ile string input alma (tkinter macOS thread sorunlu)
            try:
                w = rumps.Window(
                    title="Anahtar Kelime Değiştir",
                    message=(
                        f"Mevcut: \"{wake_word_string}\"\n\n"
                        "Yeni anahtar kelime girin (boş = iptal).\n"
                        "Default 'diktasyon' için 'diktasyon' yazın."
                    ),
                    default_text=wake_word_string,
                    ok="Kaydet",
                    cancel="İptal",
                    dimensions=(320, 24),
                )
                response = w.run()
                if response.clicked and response.text and response.text.strip():
                    set_wake_word(response.text.strip())
            except Exception as e:
                log.error(f"[WAKE] Dialog hatasi: {e}", exc_info=True)

        def on_lecture_toggle(self, _):
            if lecture_active:
                threading.Thread(target=stop_lecture_recording, daemon=True).start()
            else:
                threading.Thread(target=start_lecture_recording, daemon=True).start()

        def on_pick_file(self, _):
            threading.Thread(target=_pick_file_and_transcribe, daemon=True).start()

        def on_meet_dictation(self, _):
            threading.Thread(target=_pick_file_and_meet_dictate, daemon=True).start()

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

    def on_meet_dictation(icon, item):
        threading.Thread(target=_pick_file_and_meet_dictate, daemon=True).start()

    def on_change_wake_word(icon, item):
        threading.Thread(target=_prompt_change_wake_word, daemon=True).start()

    def on_quit(icon, item):
        should_quit.set()
        icon.stop()

    # Submenu: Toplanti
    toplanti_menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: ("⏹  Toplantı Kaydını Durdur" if lecture_active
                          else "🎙  Toplantı Kaydı Başlat"),
            on_lecture_toggle,
        ),
        pystray.MenuItem("📁 Ses dosyasını dök...", on_pick_file),
        pystray.MenuItem("🎙 Meets Dictation (konuşmacı ayır)...", on_meet_dictation),
    )

    # Submenu: Ayarlar
    ayarlar_menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: f"🗣️ Anahtar Kelime Dinleme: {'Açık' if wake_word_enabled else 'Kapalı'}",
            on_toggle_wake,
            checked=lambda item: wake_word_enabled,
        ),
        pystray.MenuItem(
            lambda item: f"✏️  Anahtar Kelime: \"{wake_word_string}\" (değiştir...)",
            on_change_wake_word,
        ),
    )

    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: (f"Durum: 🟣 Toplantı Kaydı" if lecture_active
                          else f"Durum: {_state_labels.get(sm.state, '?')}"),
            None, enabled=False,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🎤 Toplantı", toplanti_menu),
        pystray.MenuItem("⚙ Ayarlar", ayarlar_menu),
        pystray.Menu.SEPARATOR,
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
        return _apply_word_corrections(cleaned)

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
    return _apply_word_corrections(cleaned)


def _strip_known_artifacts(text):
    """Lecture/file path icin GUVENLI artifact temizleyici.
    `_clean_transcription`'in aksine tekrar tespiti YAPMAZ (gercek "evet evet" cevaplarini koru).
    Sadece bilinen YouTube dataset kaliplarini siler (Altyazi M.K., izlediginiz icin...).
    """
    if not text:
        return ""
    cleaned = _ENGLISH_HALLUC_RE.sub("", text).strip()
    cleaned = _ARTIFACT_RE.sub("", cleaned).strip()
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"^[\s.,;:!?]+|[\s.,;:!?]+$", "", cleaned)
    return cleaned


def _vad_prefilter(audio, sampling_rate=SAMPLE_RATE, min_silence_ms=500):
    """MLX yolu icin Silero VAD on-filtresi.

    mlx-whisper'in dahili VAD'i yok — sessiz bolgeler dataset artifact'leriyle ("Altyazi M.K.",
    "Izlediginiz icin tesekkur...") dolar. faster-whisper'in vad_filter=True ile yaptigini
    manuel yapariz: konusma chunk'larini bul, audio'dan sessizligi kirp, MLX'e gonder, sonra
    segment timestamp'lerini orijinal zamana geri map'le.

    Donus: (filtered_audio, ts_map). Hicbir konusma yoksa (None, None).
    """
    try:
        from faster_whisper.vad import get_speech_timestamps, SpeechTimestampsMap, VadOptions
    except ImportError:
        log.warning("[VAD] faster_whisper.vad bulunamadi, on-filtre atlaniyor")
        return audio, None

    vad_opts = VadOptions(min_silence_duration_ms=min_silence_ms)
    chunks = get_speech_timestamps(audio, vad_opts, sampling_rate=sampling_rate)
    if not chunks:
        return None, None

    filtered = np.concatenate([audio[c["start"]:c["end"]] for c in chunks])
    ts_map = SpeechTimestampsMap(chunks, sampling_rate=sampling_rate)

    original_dur = len(audio) / sampling_rate
    filtered_dur = len(filtered) / sampling_rate
    log.info(
        f"[VAD] On-filtre: {original_dur:.0f}sn -> {filtered_dur:.0f}sn "
        f"({original_dur - filtered_dur:.0f}sn sessizlik kirpildi, {len(chunks)} konusma blogu)"
    )
    return filtered, ts_map


# Filler vocalization regex (B4): "Eee" / "Ee" / "Hım" / "Mım" / "Aa" / "Ah" tek-kelime segmentleri.
# 3+ kez ardarda tekrar ediyorsa tekillestirilecek. Module-level: her cagrida re.compile maliyeti olmasin.
_FILLER_RE = re.compile(r'^(?:E+e*|Ee+|Hı+m?|Mı+m?|Aa+|Ah+)$', re.IGNORECASE)


def _drop_low_confidence_segments(
    segments,
    no_speech_threshold=LECTURE_CONF_NO_SPEECH,
    logprob_threshold=LECTURE_CONF_LOGPROB,
    compression_threshold=LECTURE_CONF_COMPRESSION,
):
    """Whisper segment metadata'sina bakarak dusuk-guven veya tekrar-isareti segmentleri at (B3).

    AND mantigi: HEM no_speech_prob yuksek HEM avg_logprob dusukse halusinasyon kabul edilir
    (her ikisi de yetmezse segment kalir — iyi segmenti yanlislikla atmamak icin).
    compression_ratio esigi bagimsiz: ngram tekrari isareti (Whisper standart sinyali, default 2.4).

    Donus: (filtered_segments, dropped_count)."""
    filtered, dropped = [], 0
    for s in segments:
        nsp = float(s.get("no_speech_prob", 0.0))
        lp = float(s.get("avg_logprob", 0.0))
        cr = float(s.get("compression_ratio", 1.0))
        low_speech = nsp > no_speech_threshold and lp < logprob_threshold
        repeat_signal = cr > compression_threshold
        if low_speech or repeat_signal:
            dropped += 1
            log.debug(
                f"[CONF] Drop t={s.get('start', 0):.1f}-{s.get('end', 0):.1f}: "
                f"nsp={nsp:.2f} lp={lp:.2f} cr={cr:.2f} text='{s.get('text', '')[:40]}'"
            )
            continue
        filtered.append(s)
    return filtered, dropped


def _dedupe_repeated_segments(text, aggressive=False, max_consecutive=3):
    """Ardarda tekrar eden cumleleri tekillestir (B2/B4).

    - Filler vocalization (Eee/Hım/Aa/...) max_consecutive+ ardarda -> 1 ornek (her zaman).
    - aggressive=True: 1-2 kelimelik herhangi bir cumle 5+ kere ardarda -> 1 ornek.
      Default False -> gercek "evet evet evet" cevap korunur (CLAUDE.md kurali).

    Cumle bolme: . ! ? sonrasi BUYUK harfle baslayan kelime gerekir
    (Turkce kisaltma 'Md.', 'Dr.', '1.5sn' gibi sahte cumle bolmesini onler)."""
    if not text:
        return text
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÇĞİÖŞÜ])', text)
    out, i = [], 0
    while i < len(sentences):
        s = sentences[i].strip()
        run = 1
        while i + run < len(sentences) and sentences[i + run].strip().lower() == s.lower():
            run += 1
        core = s.rstrip('.!? ').strip()
        is_filler = bool(_FILLER_RE.match(core))
        is_short_spam = aggressive and len(core.split()) <= 2 and run >= 5
        if is_filler and run >= max_consecutive:
            out.append(s)
            i += run
            log.info(f"[DEDUPE] Filler '{core[:30]}' {run}x -> 1x")
        elif is_short_spam:
            out.append(s)
            i += run
            log.warning(f"[DEDUPE] Agresif: '{core[:30]}' {run}x -> 1x (LECTURE_AGGRESSIVE_CLEANUP=True)")
        else:
            out.append(s)
            i += 1
    return " ".join(out)


def _finalize_segments(segments, *, aggressive=False):
    """Final pass cikti segmentlerini son hale getir:
       low-confidence drop (B3) -> artifact strip -> word correction -> dedupe (B2/B4).
       Donus: (clean_segments, joined_text)."""
    segments, dropped_conf = _drop_low_confidence_segments(segments)
    if dropped_conf:
        log.info(f"[FINALIZE] {dropped_conf} dusuk-guven segment elendi (B3).")
    clean, dropped_art = [], 0
    for s in segments:
        t = _strip_known_artifacts(s["text"])
        if not t:
            dropped_art += 1
            continue
        s["text"] = _apply_word_corrections(t)
        clean.append(s)
    if dropped_art:
        log.info(f"[FINALIZE] {dropped_art} segment artifact filtresinde elendi.")
    text = " ".join(s["text"] for s in clean).strip()
    text = _apply_word_corrections(text)
    text = _dedupe_repeated_segments(text, aggressive=aggressive)
    return clean, text


def quick_transcribe(audio_data, beam_size=3):
    """Hizli transcribe (turbo). beam_size sadece faster-whisper'da kullanilir;
    mlx-whisper beam search'i henuz desteklemiyor (NotImplementedError) -> MLX
    path greedy decoding kullanir."""
    # Sessiz audio'yu transcribe etme (halusinasyon onleme)
    if not _has_speech(audio_data):
        return ""

    try:
        with transcribe_lock:
            if IS_MAC and USE_MLX:
                # MLX: beam_size gecme — mlx-whisper henuz desteklemiyor.
                # condition_on_previous_text=False: dictation kisa kayitlarda bile halusinasyon
                # zincirini onler (model kendi onceki ciktisini prompt'a sokarak tekrar etmesin).
                result = mlx_whisper.transcribe(
                    audio_data, path_or_hf_repo=MLX_MODEL_REPO,
                    language="tr", initial_prompt=INITIAL_PROMPT,
                    condition_on_previous_text=False,
                )
                text = result.get("text", "").strip()
            else:
                # condition_on_previous_text=False (B1): faster-whisper default'u True; bu Tauron LIVE'da
                # "onun icin x11" zincirleme tekrarinin acik sebebiydi. MLX'te zaten False, parite saglandi.
                segments, _ = model.transcribe(
                    audio_data, language="tr", initial_prompt=INITIAL_PROMPT,
                    beam_size=beam_size, vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=300),
                    condition_on_previous_text=False,
                )
                text = " ".join(seg.text.strip() for seg in segments)
    except Exception as e:
        log.error(f"[HATA] quick_transcribe basarisiz: {type(e).__name__}: {e}", exc_info=True)
        return ""

    cleaned = _clean_transcription(text)
    if cleaned:
        # B1: Lecture LIVE pass'inde "M.K." / "Izlediginiz icin tesekkur..." YouTube artifaktlarini sil.
        # Dictation kisa kayitlari icin de iyi davranis (false positive yok).
        cleaned = _strip_known_artifacts(cleaned)
    if cleaned:
        # B4: 3+ ardarda 'Eee/Hım' filler tekrarini tekillestir. aggressive=False -> gercek cevap korunur.
        cleaned = _dedupe_repeated_segments(cleaned, aggressive=False)
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


def _ensure_writable_dir(primary, fallback, label):
    """Primary dir'i kullanilabilir mi dene (mkdir + W_OK); olmazsa fallback'e duş.
    Drive (G:\\) gibi network mount'lar bagli degilse veya senkron sorun varsa fallback devreye girer."""
    try:
        os.makedirs(primary, exist_ok=True)
        if os.access(primary, os.W_OK):
            return primary
        raise PermissionError(f"{primary} yazilabilir degil")
    except OSError as e:
        log.warning(f"[FALLBACK] {label}: Drive kullanilamiyor ({type(e).__name__}: {e}); Desktop'a duser -> {fallback}")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def _get_voicedictation_dir():
    """Transkript MD'lerinin yazildigi klasor. Once Drive, olmazsa Desktop/VoiceDictation/VoiceDictation."""
    return _ensure_writable_dir(DRIVE_VOICEDICTATION_DIR, FALLBACK_VOICEDICTATION_DIR, "VoiceDictation")


def _get_rawrecords_dir():
    """Islenen ses dosyalarinin tasindigi/yazildigi klasor. Once Drive, olmazsa Desktop/VoiceDictation/RawRecords."""
    return _ensure_writable_dir(DRIVE_RAWRECORDS_DIR, FALLBACK_RAWRECORDS_DIR, "RawRecords")


def _get_lectures_dir():
    """[DEPRECATED 23 Mayis 2026] Eski isim; yeni VoiceDictation/RawRecords duzenine shim.
    Tum eski cagirilarin tek noktadan yonlenmesi icin korunuyor."""
    return _get_voicedictation_dir()


def _save_wav(audio_data, path, sample_rate=SAMPLE_RATE):
    """Float32 numpy array'i (sounddevice cikti formati, -1..+1) 16-bit PCM mono WAV olarak yaz."""
    import wave
    arr = np.asarray(audio_data).flatten()
    pcm = (np.clip(arr, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    return path


def _load_audio_via_afconvert(path, target_sr=SAMPLE_RATE):
    """macOS native: afconvert ile herhangi bir formati 16kHz mono PCM'e cevir, numpy array dondur.
    ffmpeg gerektirmez. m4a/aac/mp3/wav/aiff/caf/flac/alac/ogg desteklenir."""
    import subprocess, tempfile, wave as _wave
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", f"LEI16@{target_sr}", "-c", "1", path, tmp_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"afconvert basarisiz: {result.stderr.strip()}")
        with _wave.open(tmp_path, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return audio_np
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _transcribe_audio_path(audio, beam_size=5, word_timestamps=False):
    """Dosya yolu VEYA numpy array'inden transkript al (faster-whisper / MLX).
    (text, segments) doner. word_timestamps=True ise her segmentte 'words' alani da olur.

    macOS'ta dosya yolu gelirse afconvert ile pre-load edilir (ffmpeg gerekmez)."""
    if isinstance(audio, str):
        label = os.path.basename(audio)
        if IS_MAC:
            log.info(f"[TRANSCRIBE] afconvert ile yukleniyor: {label}")
            audio = _load_audio_via_afconvert(audio)
            label = f"{label} (decoded {len(audio)/SAMPLE_RATE:.0f}sn)"
    else:
        label = f"RAM buffer ({len(audio)/SAMPLE_RATE:.0f}sn)"
    log.info(f"[TRANSCRIBE] Calisiyor: {label}")
    t0 = time.time()
    if IS_MAC and USE_MLX:
        # On-VAD: mlx-whisper'in dahili VAD'i olmadigi icin sessiz bolgeler "Altyazi M.K." /
        # "Izlediginiz icin tesekkur..." dataset artifact'leri ile dolar (bkz. Hakan Hoca
        # 20 Mayis vakasi). Sessizligi VAD ile kirp, sonra segment timestamp'lerini
        # SpeechTimestampsMap ile orijinal zamana geri map'le.
        filtered_audio, ts_map = _vad_prefilter(audio, sampling_rate=SAMPLE_RATE)
        if filtered_audio is None:
            log.info("[TRANSCRIBE] VAD: hicbir konusma bulunamadi, transcribe atlaniyor.")
            return "", []

        # transcribe_lock zorunlu: MLX Metal command buffer'lari thread-safe degil.
        # Lecture LIVE chunk transcribe ile eszamanli calismalardan dolayi
        # MTLReleaseAssertionFailure -> SIGABRT crash oluyordu.
        # condition_on_previous_text=False: bir kez halusinasyon ciksa bile model kendi
        # ciktisini prompt'a sokarak tekrar etmesin (Hakan Hoca'da 70dk "Altyazi M.K."
        # zincirinin acik sebebi).
        with transcribe_lock:
            result = mlx_whisper.transcribe(
                filtered_audio, path_or_hf_repo=MLX_LECTURE_MODEL_REPO,
                language="tr", initial_prompt=INITIAL_PROMPT,
                word_timestamps=word_timestamps,
                condition_on_previous_text=False,
            )
            text = result.get("text", "").strip()
            segments = []
            for s in result.get("segments", []):
                start = float(s.get("start", 0.0))
                end = float(s.get("end", 0.0))
                # Sessizlik kirpilmissa: filtered-time -> orijinal-time
                if ts_map is not None:
                    start = ts_map.get_original_time(start)
                    end = ts_map.get_original_time(end, is_end=True)
                seg = {
                    "start": start,
                    "end": end,
                    "text": s.get("text", "").strip(),
                    # B3: Whisper segment metadata'si — _drop_low_confidence_segments bunlari okur.
                    "avg_logprob": float(s.get("avg_logprob", 0.0)),
                    "no_speech_prob": float(s.get("no_speech_prob", 0.0)),
                    "compression_ratio": float(s.get("compression_ratio", 1.0)),
                }
                if word_timestamps and s.get("words"):
                    seg["words"] = [
                        {"start": (ts_map.get_original_time(float(w.get("start", 0.0)))
                                   if ts_map is not None else float(w.get("start", 0.0))),
                         "end": (ts_map.get_original_time(float(w.get("end", 0.0)), is_end=True)
                                 if ts_map is not None else float(w.get("end", 0.0))),
                         "word": w.get("word", "")}
                        for w in s["words"]
                    ]
                segments.append(seg)
    else:
        if model is None:
            raise RuntimeError("Model henuz yuklenmedi (load_model cagir).")
        with transcribe_lock:
            segs, _info = model.transcribe(
                audio, language="tr", initial_prompt=INITIAL_PROMPT,
                beam_size=beam_size, vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                word_timestamps=word_timestamps,
            )
            segments = []
            for s in segs:
                seg = {
                    "start": float(s.start),
                    "end": float(s.end),
                    "text": s.text.strip(),
                    # B3: faster-whisper Segment metadata'si — _drop_low_confidence_segments okur.
                    "avg_logprob": float(s.avg_logprob),
                    "no_speech_prob": float(s.no_speech_prob),
                    "compression_ratio": float(s.compression_ratio),
                }
                if word_timestamps and s.words:
                    seg["words"] = [
                        {"start": float(w.start),
                         "end": float(w.end),
                         "word": w.word}
                        for w in s.words
                    ]
                segments.append(seg)
        text = " ".join(s["text"] for s in segments).strip()
    elapsed = time.time() - t0
    log.info(f"[TRANSCRIBE] Tamamlandi ({elapsed:.0f}sn islem, {len(segments)} segment).")

    # Final pass son temizlik (22 Mayis fix devami):
    #   B3 dusuk-guven segment dropout -> bilinen artifact strip -> word correction -> B2/B4 dedupe
    # aggressive=True ise 1-2 kelimelik 5+ tekrarlar da kirpilir (CLAUDE.md kurali geregi default kapali).
    segments, text = _finalize_segments(segments, aggressive=LECTURE_AGGRESSIVE_CLEANUP)
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
            f.write("_(Konusma algilanamadi.)_\n\n")
        f.write("---\n\n")
        f.write(f"_**Transkript tamamlandi.** Sure: {_format_seconds(audio_duration)} • Model: {LECTURE_MODEL_SIZE} ({DEVICE})_\n")


_voice_encoder = None


def _load_voice_encoder():
    """speechbrain ECAPA-TDNN konusmaci embedding modelini lazy-load et.
    Ilk seferde HF'den public model indirir (~24 MB, token GEREKMEZ, lisans yok).
    Sonraki tum cagrilar lokal cache'den, internet de gerekmez.
    Ses verisi asla disariya gitmez."""
    global _voice_encoder
    if _voice_encoder is not None:
        return _voice_encoder

    try:
        from speechbrain.inference.speaker import EncoderClassifier
        from speechbrain.utils.fetching import LocalStrategy
    except ImportError:
        try:
            from speechbrain.pretrained import EncoderClassifier  # eski API
            LocalStrategy = None
        except ImportError:
            raise RuntimeError(
                "speechbrain kurulu degil. Kurmak icin:\n"
                "  venv\\Scripts\\pip.exe install speechbrain scikit-learn"
            )

    # PyTorch CUDA olarak kurulmamis ise CPU'ya dus (uyari ile)
    try:
        import torch as _torch
        device = "cuda" if (DEVICE == "cuda" and _torch.cuda.is_available()) else "cpu"
        if DEVICE == "cuda" and not _torch.cuda.is_available():
            log.warning("[DIARIZE] PyTorch CUDA yok (CPU-only kurulmus), embedding CPU'da calisacak")
    except ImportError:
        device = "cpu"

    log.info("[DIARIZE] ECAPA-TDNN konusmaci modeli yukleniyor (lokal)...")
    t0 = time.time()
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "models", "spkrec-ecapa-voxceleb")

    # Windows'ta symlink admin/Developer Mode istiyor; COPY ile bypass
    kwargs = {
        "source": "speechbrain/spkrec-ecapa-voxceleb",
        "savedir": save_dir,
        "run_opts": {"device": device},
    }
    if LocalStrategy is not None:
        kwargs["local_strategy"] = LocalStrategy.COPY

    encoder = EncoderClassifier.from_hparams(**kwargs)
    log.info(f"[DIARIZE] Konusmaci modeli hazir ({time.time()-t0:.1f}sn, {device})")
    _voice_encoder = encoder
    return encoder


def _diarize_audio_sliding_window(audio, num_speakers,
                                   window_sec=1.2, stride_sec=0.5,
                                   silence_rms=0.005, batch_size=32,
                                   progress_callback=None):
    """Audio'yu sabit pencerelerle (Whisper'dan bagimsiz) diarize et.

    audio: float32 mono 16kHz numpy array
    num_speakers: int (kullanicidan)
    window_sec: her pencere uzunlugu (>= 1.5 onerilir)
    stride_sec: pencere ilerleme adimi (overlap = window - stride)
    silence_rms: sessizlik esigi (alti es kesilir)
    batch_size: embedding batch boyutu (CPU'da hizlandirir)

    Donus: [(start_sec, end_sec, SPEAKER_XX), ...] kronolojik turn listesi.
    Bu pyannote'un mantigi — speaker overlap'ini ve hizli turn'leri yakalar,
    Whisper segment sinirlarinda kismayan."""
    if num_speakers < 2:
        return [(0.0, len(audio) / SAMPLE_RATE, "SPEAKER_00")]

    encoder = _load_voice_encoder()
    import torch as _torch
    import numpy as _np
    from sklearn.cluster import AgglomerativeClustering

    win = int(window_sec * SAMPLE_RATE)
    stride = int(stride_sec * SAMPLE_RATE)
    total_dur = len(audio) / SAMPLE_RATE

    log.info(f"[DIARIZE] Sliding-window: {total_dur:.0f}sn audio, "
             f"window={window_sec}s, stride={stride_sec}s")
    t0 = time.time()

    # Pencereleri topla (sessiz olanlari atla)
    chunks = []
    window_times = []
    for s in range(0, len(audio) - win + 1, stride):
        e = s + win
        chunk = audio[s:e]
        rms = float(_np.sqrt(_np.mean(chunk * chunk)))
        if rms < silence_rms:
            continue
        chunks.append(chunk)
        window_times.append((s / SAMPLE_RATE, e / SAMPLE_RATE))

    if not chunks:
        log.warning("[DIARIZE] Hicbir konusma penceresi bulunamadi (audio tamamen sessiz?)")
        return [(0.0, total_dur, "SPEAKER_00")]

    log.info(f"[DIARIZE] {len(chunks)} pencere embed ediliyor (batch={batch_size})...")
    embeddings = []
    for bi in range(0, len(chunks), batch_size):
        batch = chunks[bi:bi + batch_size]
        batch_tensor = _torch.from_numpy(_np.stack(batch))
        try:
            with _torch.no_grad():
                emb = encoder.encode_batch(batch_tensor)
                # speechbrain encode_batch -> [B, 1, 192]; squeeze middle dim
                emb_np = emb.squeeze(1).cpu().numpy()
            for e in emb_np:
                embeddings.append(e)
        except Exception as ex:
            log.warning(f"[DIARIZE] Batch {bi} embed atlandi: {ex}")
            for _ in batch:
                embeddings.append(None)
        if progress_callback and bi % (batch_size * 4) == 0:
            done = min(bi + batch_size, len(chunks))
            progress_callback(done, len(chunks))

    # None'lari ve onlara denk gelen window_times'i temizle
    valid = [(e, t) for e, t in zip(embeddings, window_times) if e is not None]
    if not valid:
        log.error("[DIARIZE] Tum embedding'ler basarisiz oldu")
        return [(0.0, total_dur, "SPEAKER_00")]

    embs_arr = _np.vstack([v[0] for v in valid]).astype(_np.float32)
    times = [v[1] for v in valid]

    # Mean subtraction (channel/akustik etkisini azalt — pyannote da bunu yapar):
    # tum embedding'lerin ortalamasini cikar; geride 'konusmaciya ozel' yon kalir.
    # Bu olmadan ayni odadaki konusmacilar ortak channel'e yiglir.
    mean_emb = embs_arr.mean(axis=0, keepdims=True)
    embs_arr = embs_arr - mean_emb

    # L2 normalize (cosine icin)
    norms = _np.linalg.norm(embs_arr, axis=1, keepdims=True)
    embs_arr = embs_arr / _np.clip(norms, 1e-12, None)

    actual_k = min(num_speakers, len(embs_arr))
    log.info(f"[DIARIZE] AgglomerativeClustering (cosine, average, k={actual_k})")
    cluster_labels = AgglomerativeClustering(
        n_clusters=actual_k, metric="cosine", linkage="average",
    ).fit_predict(embs_arr)
    log.info(f"[DIARIZE] Cluster bitti ({time.time()-t0:.1f}sn)")

    # Ardisik ayni-konusmaci pencereleri 'turn'lere birlestir
    turns = []
    cur_label = None
    cur_start = None
    cur_end = None
    for (ws, we), lbl in zip(times, cluster_labels):
        lbl_name = f"SPEAKER_{int(lbl):02d}"
        if lbl_name != cur_label:
            if cur_label is not None:
                turns.append((cur_start, cur_end, cur_label))
            cur_label = lbl_name
            cur_start = ws
            cur_end = we
        else:
            cur_end = we
    if cur_label is not None:
        turns.append((cur_start, cur_end, cur_label))

    # Ayni konusmacinin yakin turn'lerini (kisa sessizlikle ayrilmis) birlestir
    merged = []
    for t in turns:
        if merged and t[2] == merged[-1][2] and t[0] - merged[-1][1] < 0.5:
            merged[-1] = (merged[-1][0], t[1], t[2])
        else:
            merged.append(t)

    # Cok kisa izole turn'leri komsuya as
    smoothed = []
    for i, t in enumerate(merged):
        dur = t[1] - t[0]
        if dur < 0.7 and 0 < i < len(merged) - 1 and merged[i-1][2] == merged[i+1][2]:
            # Komsular ayni speaker -> bu izole turn yanlislik
            continue
        smoothed.append(t)

    detected = sorted(set(t[2] for t in smoothed))
    log.info(f"[DIARIZE] {len(smoothed)} turn olustu, konusmacilar: {detected}")
    return smoothed


def _split_segments_by_diarization(whisper_segments, diarization_turns):
    """Whisper segmentlerini speaker turn sinirlarinda parçala.

    word_timestamps=True ile transcribe edilmisse her kelime tek tek atanir;
    yoksa segment seviyesinde majority-overlap kullanir.

    Donus: yeni segment listesi (her biri tek konusmaci, speaker_raw alanli)."""

    def speaker_at(time_point):
        for t_start, t_end, lbl in diarization_turns:
            if t_start <= time_point < t_end:
                return lbl
        # Hicbir turn'e dusmuyor -> en yakin turn'un speaker'i
        if not diarization_turns:
            return "SPEAKER_00"
        nearest = min(
            diarization_turns,
            key=lambda t: min(abs(t[0] - time_point), abs(t[1] - time_point)),
        )
        return nearest[2]

    new_segments = []
    for seg in whisper_segments:
        words = seg.get("words", [])

        if not words:
            # Fallback: overlap'i en cok olan speaker'i ata
            seg_overlap = {}
            for t_start, t_end, lbl in diarization_turns:
                ov = max(0.0, min(seg["end"], t_end) - max(seg["start"], t_start))
                if ov > 0:
                    seg_overlap[lbl] = seg_overlap.get(lbl, 0.0) + ov
            sp = (max(seg_overlap.items(), key=lambda x: x[1])[0]
                  if seg_overlap else speaker_at((seg["start"] + seg["end"]) / 2))
            new_segments.append({
                "start": seg["start"], "end": seg["end"],
                "text": seg["text"], "speaker_raw": sp,
            })
            continue

        # Word-level: her kelimeyi speaker turn'e ata, ayni speaker'a sahip ardisik
        # kelimeleri bir sub-segment'te grupla
        cur_speaker = None
        cur_words = []
        cur_start = None

        def flush_sub():
            if not cur_words or cur_speaker is None or cur_start is None:
                return
            text = " ".join(w["word"].strip() for w in cur_words).strip()
            if not text:
                return
            new_segments.append({
                "start": cur_start,
                "end": cur_words[-1]["end"],
                "text": text,
                "speaker_raw": cur_speaker,
            })

        for w in words:
            wt = (w["start"] + w["end"]) / 2
            w_sp = speaker_at(wt)
            if cur_speaker is None:
                cur_speaker = w_sp
                cur_start = w["start"]
                cur_words = [w]
            elif w_sp != cur_speaker:
                flush_sub()
                cur_speaker = w_sp
                cur_start = w["start"]
                cur_words = [w]
            else:
                cur_words.append(w)
        flush_sub()

    return new_segments


def _smooth_speaker_labels(segments, min_isolated_dur=2.0):
    """Cok kisa, etrafi ayni konusmaciyla cevrili 'izole' segmentleri komsuya as.

    Ornek: [Yigit, Hakan(0.5sn), Yigit] -> [Yigit, Yigit, Yigit]
    Cluster gurultusu sonucu olusan tek-segment yanlislamalari duzeltir."""
    if len(segments) < 3:
        return
    fixed = 0
    for i in range(1, len(segments) - 1):
        cur = segments[i].get("speaker_raw")
        prev = segments[i - 1].get("speaker_raw")
        nxt = segments[i + 1].get("speaker_raw")
        dur = segments[i]["end"] - segments[i]["start"]
        if cur != prev and cur != nxt and prev == nxt and dur < min_isolated_dur:
            segments[i]["speaker_raw"] = prev
            fixed += 1
    if fixed:
        log.info(f"[DIARIZE] Smoothing: {fixed} izole segment komsuya tasindi.")


def _apply_speaker_names(segments, speaker_names):
    """speaker_raw -> insan ismi eşlemesi uygula."""
    for s in segments:
        raw = s.get("speaker_raw", "SPEAKER_00")
        s["speaker"] = speaker_names.get(raw, raw)
    return segments


def transcribe_file_to_markdown(audio_path, output_dir=None, header_title=None):
    """Dis ses dosyasini transkripte et: MD'yi VoiceDictation/'a yaz, sesi RawRecords/'a TASI.

    23 Mayis 2026 duzeni: tek MD ciktisi (VoiceDictation altinda), ses dosyasi RawRecords'a
    tasinir (silinmez). output_dir verilirse MD oraya yazilir (ses tasimasi yine RawRecords).
    Donus: olusan .md yolu (basarisizsa None).
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

    # 1) Sesi RawRecords'a tasi (zaten icinde degilse). MD'de "Kaynak" yeni yolu gosterir.
    raw_dir = _get_rawrecords_dir()
    src_norm = os.path.normcase(os.path.abspath(audio_path))
    raw_norm = os.path.normcase(os.path.abspath(raw_dir))
    if src_norm.startswith(raw_norm + os.sep):
        final_audio_path = audio_path  # zaten RawRecords altinda
    else:
        dst = os.path.join(raw_dir, os.path.basename(audio_path))
        if os.path.exists(dst):
            stem, ext = os.path.splitext(os.path.basename(audio_path))
            dst = os.path.join(raw_dir, f"{stem}_{time.strftime('%Y%m%d_%H%M%S')}{ext}")
        try:
            import shutil
            shutil.move(audio_path, dst)
            log.info(f"[FILE] Ses tasindi: {audio_path} -> {dst}")
            final_audio_path = dst
        except Exception as e:
            log.error(f"[FILE] Ses tasinamadi ({type(e).__name__}: {e}); orijinal yerinde kaldi.")
            final_audio_path = audio_path

    # 2) MD'yi VoiceDictation/'a yaz (tek kopya).
    target_dir = output_dir or _get_voicedictation_dir()
    md_path = os.path.join(target_dir, base_name + ".md")
    try:
        _write_lecture_markdown(md_path, segments, audio_dur, final_audio_path, header_title=title)
        log.info(f"[FILE] MD yazildi: {md_path}")
        return md_path
    except Exception as e:
        log.error(f"[FILE] MD yazma hatasi: {e}")
        return None


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

    # 2) VS Code — Windows'ta code.cmd ONCELIKLI (Code.exe yeni bos window acar,
    # code.cmd ise mevcut instance'a dosyayi tab olarak ekler)
    if IS_WIN:
        code_cmd = shutil.which("code.cmd") or shutil.which("code")
    else:
        code_cmd = shutil.which("code")
    if code_cmd:
        try:
            # shell=False + direct path: PATHEXT siralamasi nedeniyle Code.exe'ye
            # dusulmesini onler. .cmd dosyasi shell=False ile dogrudan calismaz,
            # bu yuzden Windows'ta cmd /c kullaniyoruz.
            if IS_WIN:
                flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
                subprocess.Popen(["cmd", "/c", code_cmd, path], creationflags=flags)
            else:
                subprocess.Popen([code_cmd, path])
            log.info(f"[EDITOR] VS Code ile acildi: {path}")
            log.info(f"[EDITOR] (cli: {code_cmd})")
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
        f.write(f"- **Mod:** Canli (turbo, beam=3, cumle sonlarinda)\n")
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
            text = quick_transcribe(audio, beam_size=LECTURE_LIVE_BEAM_SIZE)
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
                text = quick_transcribe(audio, beam_size=LECTURE_LIVE_BEAM_SIZE)
                if text:
                    log.info(f"[LIVE] (final flush) [{int(offset_sec//60):02d}:{int(offset_sec%60):02d}] {text[:80]}")
                    _append_live_paragraph(md_path, offset_sec, text)
            except Exception as e:
                log.error(f"[LIVE] Final flush hatasi: {e}")
    log.info("[LIVE] Loop bitti.")


def _get_live_temp_dir():
    """LIVE.md icin gecici dizin (Drive'a yazilmaz, kayit bitince silinir).
    Windows: %LOCALAPPDATA%\\Temp\\voicedictation_live, Mac: /tmp/voicedictation_live."""
    import tempfile
    path = os.path.join(tempfile.gettempdir(), "voicedictation_live")
    os.makedirs(path, exist_ok=True)
    return path


def start_lecture_recording():
    """Tray menusunden cagrilir: lecture kaydi baslat. LIVE.md gecici dizine acilir
    (Drive'a yazilmaz, kayit bitince silinir). Final pass WAV+MD Drive'a yazilir."""
    global lecture_active, lecture_start_time, lecture_live_md_path
    global lecture_live_speech_detected, lecture_live_last_speech_time
    with lecture_lock:
        if lecture_active:
            log.warning("[LECTURE] Zaten kayitta.")
            return False
        try:
            ts = time.strftime("%Y-%m-%d_%H-%M-%S")
            # LIVE.md gecici dizine — kullanici canli izleyebilir ama Drive'a yazilmaz
            lecture_live_md_path = os.path.join(_get_live_temp_dir(), f"{ts}_LIVE.md")
            _init_live_md(lecture_live_md_path, "(canli izleme — bu LIVE dosyasi kayit bitince SILINIR)")
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
    log.info("[LECTURE] Toplanti kaydi basladi (canli LIVE gecici, kayit bitince WAV+MD Drive'a yazilir)")
    log.info(f"[LECTURE] Canli (gecici) MD: {lecture_live_md_path}")

    # Live transcribe thread'i baslat
    global lecture_live_thread
    lecture_live_thread = threading.Thread(
        target=lambda: _live_transcribe_loop(lecture_live_md_path), daemon=True
    )
    lecture_live_thread.start()

    # Editor'da canli dosyayi ac (kullanici LIVE'i takip eder)
    _open_in_editor(lecture_live_md_path)

    return True


def stop_lecture_recording():
    """Tray menusunden cagrilir: kayit ismi sor, WAV diske dok, final pass transcribe et,
    sonra gecici LIVE.md'yi sil."""
    global lecture_active, lecture_live_md_path, lecture_live_thread
    with lecture_lock:
        if not lecture_active:
            return False
        live_md = lecture_live_md_path
        duration = time.time() - lecture_start_time
        lecture_active = False  # live_loop'un sonunu tetikler
        lecture_live_md_path = None
        live_thread = lecture_live_thread
        lecture_live_thread = None

    # Live thread'in kendi final flush'ini tamamlamasini bekle (max 15sn).
    if live_thread is not None:
        live_thread.join(timeout=15.0)
        if live_thread.is_alive():
            log.warning("[LECTURE] Live thread 15sn icinde bitmedi, devam ediliyor.")

    # Audio chunks snapshot, buffer'i hemen bosalt (RAM hassasligi)
    with lecture_audio_chunks_lock:
        chunks = list(lecture_audio_chunks)
        lecture_audio_chunks.clear()

    chunk_count = len(chunks)
    total_samples = sum(len(c) for c in chunks) if chunks else 0
    audio_seconds = total_samples / SAMPLE_RATE if total_samples else 0
    log.info(f"[LECTURE] Buffer durumu: {chunk_count} chunk, {total_samples} sample (~{audio_seconds:.1f}sn ses)")
    log.info(f"[LECTURE] Kayit durduruldu ({_format_seconds(duration)}). Isim sorulur, sonra WAV+transcribe...")
    sound_sent()

    def _bg(chunks_local, live_md_local, duration_local):
        wav_path = None
        try:
            if not chunks_local:
                log.warning("[LECTURE] Audio buffer bos, final pass atlandi.")
                return

            # Kullanicidan dosya ismi al (cancel/bos -> timestamp default)
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            custom_name = _prompt_lecture_filename(timestamp)
            final_base = custom_name or timestamp
            log.info(f"[LECTURE] Kayit ismi: {final_base}"
                     f"{' (kullanici verdi)' if custom_name else ' (timestamp default)'}")

            audio_data = np.concatenate(chunks_local, axis=0).flatten()
            chunks_local = None

            # WAV dump -> RawRecords/<isim>.wav (kalici, silinmez)
            try:
                wav_path = os.path.join(_get_rawrecords_dir(), final_base + ".wav")
                _save_wav(audio_data, wav_path)
                log.info(f"[LECTURE] Ham ses kaydedildi: {wav_path} ({len(audio_data)/SAMPLE_RATE:.0f}sn)")
            except Exception as e:
                log.error(f"[LECTURE] WAV kaydedilemedi ({type(e).__name__}: {e}); transcribe yine devam ediyor.")
                wav_path = None

            text, segments = _transcribe_audio_path(audio_data, beam_size=5)
            audio_data = None

            if not segments and not text:
                log.warning("[LECTURE] Final transkript bos.")
                sound_error()
                return

            audio_dur = max((s["end"] for s in segments), default=duration_local)
            md_path = os.path.join(_get_voicedictation_dir(), final_base + ".md")
            _write_lecture_markdown(
                md_path, segments, audio_dur,
                wav_path or "(WAV diske yazilamadi — sadece transkript var)",
                header_title="Toplanti / Ders Transkripti",
            )
            log.info(f"[LECTURE] Final transcript yazildi: {md_path}")
        except Exception as e:
            log.error(f"[LECTURE] Final transcribe hatasi: {e}", exc_info=True)
            sound_error()
        finally:
            # Gecici LIVE.md'yi sil (kullanici icin gorsel feedback'ti, Drive'a yazilmiyor)
            if live_md_local and os.path.isfile(live_md_local):
                try:
                    os.remove(live_md_local)
                    log.info(f"[LECTURE] Gecici LIVE.md silindi: {live_md_local}")
                except Exception as e:
                    log.warning(f"[LECTURE] LIVE.md silinemedi ({type(e).__name__}: {e}): {live_md_local}")

    threading.Thread(target=_bg, args=(chunks, live_md, duration), daemon=True).start()
    return True


def _prompt_change_wake_word():
    """Tray menusunden cagrilir: tkinter input dialog ile yeni wake word al + uygula."""
    try:
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        new_word = simpledialog.askstring(
            "Anahtar Kelime Değiştir",
            f"Mevcut: \"{wake_word_string}\"\n\n"
            "Yeni anahtar kelime girin (boş bırakırsanız değişmez).\n"
            "Not: Whisper'ın sizin telaffuzunuzu nasıl yazdığına bağlı; "
            "tek heceli ya da yaygın olmayan kelimeler daha iyi yakalanır.\n"
            "Default 'diktasyon' geri yüklemek için 'diktasyon' yazın.",
            parent=root,
        )
        try:
            root.destroy()
        except Exception:
            pass
        if not new_word or not new_word.strip():
            log.info("[WAKE] Degisiklik iptal edildi (bos giris).")
            return
        if set_wake_word(new_word):
            log.info(f"[WAKE] Anahtar kelime guncellendi: '{wake_word_string}'")
    except Exception as e:
        log.error(f"[WAKE] Dialog hatasi: {e}", exc_info=True)


def _prompt_lecture_filename(default_name):
    """Cross-platform: lecture sonrasi kullanicidan dosya ismi al.
    Donus: temizlenmis isim (windows/mac gecersiz karakterler atilmis) veya None
    (iptal/bos -> caller timestamp default'a duser)."""
    raw = None
    if IS_MAC:
        raw = _prompt_lecture_filename_macos(default_name)
    else:
        # Windows: tkinter simpledialog (gizli root, modal askstring)
        try:
            import tkinter as tk
            from tkinter import simpledialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            raw = simpledialog.askstring(
                "Toplanti Kaydi - Dosya Adi",
                "Kayit ismi (Iptal/bos -> timestamp ismi kullanilir):",
                initialvalue=default_name,
                parent=root,
            )
            root.destroy()
        except Exception as e:
            log.error(f"[LECTURE] Windows isim dialog hatasi: {e}")
            return None
    if not raw or not raw.strip():
        return None
    safe = re.sub(r'[\\/:*?"<>|]', '_', raw.strip()).strip()
    return safe or None


def _prompt_lecture_filename_macos(default_name):
    """macOS native text input dialog. Bos veya iptal => None.
    Kullanici toplanti kaydina isim verir, MD dosyalari rename edilir."""
    import subprocess
    safe_default = default_name.replace('"', '').replace('\\', '')
    script = (
        f'set theResult to display dialog '
        f'"Toplanti kaydina isim ver (Iptal: timestamp ismi kalir):" '
        f'default answer "{safe_default}" '
        f'with title "Toplanti Kaydi - Dosya Adi" '
        f'buttons {{"Iptal", "Kaydet"}} default button "Kaydet"\n'
        f'text returned of theResult'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=600
        )
        if result.returncode != 0:
            return None  # user canceled
        return result.stdout.strip() or None
    except Exception as e:
        log.error(f"[LECTURE] Isim dialog hatasi: {e}")
        return None


def _pick_audio_file_macos():
    """macOS native AppleScript file picker (osascript). tkinter rumps ile main-thread
    cakismasi yapip GIL deadlock'a girdigi icin kullanilmiyor."""
    import subprocess
    script = (
        'set theFile to choose file with prompt '
        '"Transkripte edilecek ses dosyasini sec" '
        'of type {"wav","mp3","m4a","aac","flac","ogg","wma","opus","aif","aiff","caf","qta","mp4","mov","mkv","webm"}\n'
        'POSIX path of theFile'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            # Kullanici iptal ettiyse stderr'de "User canceled" / -128 olur
            return None
        return result.stdout.strip() or None
    except Exception as e:
        log.error(f"[FILE] osascript hatasi: {e}")
        return None


def _pick_file_and_transcribe():
    """Tray menusunden cagrilir: dosya secici ac, secileni transcribe et."""
    try:
        if IS_MAC:
            path = _pick_audio_file_macos()
        else:
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
                    ("Ses dosyalari", "*.wav *.mp3 *.m4a *.aac *.flac *.ogg *.wma *.opus *.qta *.aif *.aiff *.caf"),
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


# ---------- MEET DICTATION (file + diarization + names) ----------

def _show_meet_error(message):
    """Hata mesajini messagebox ile goster (Win + Mac). Sessiz hata olmasin."""
    try:
        if IS_MAC:
            safe = message.replace('"', '\\"').replace("\n", "\\n")
            subprocess.run(
                ["osascript", "-e",
                 f'display dialog "{safe}" with title "Meet Dictation - Hata" '
                 f'with icon stop buttons {{"Tamam"}} default button "Tamam"'],
                capture_output=True, text=True, timeout=60,
            )
        else:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            messagebox.showerror("Meet Dictation - Hata", message, parent=root)
            try:
                root.destroy()
            except Exception:
                pass
    except Exception as e:
        log.error(f"[MEET] Hata mesaji gosterilemedi: {e}")


def _ask_speaker_count_win():
    """Windows: tkinter ile konusmaci sayisi sor. None=iptal."""
    import tkinter as tk
    from tkinter import simpledialog
    root = tk.Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    try:
        count = simpledialog.askinteger(
            "Meet Dictation - Konusmaci Sayisi",
            "Bu kayitta kac konusmaci var?\n"
            "(Dogru sayi vermek diarization kalitesini artirir)",
            minvalue=1, maxvalue=20, initialvalue=2, parent=root,
        )
    finally:
        try:
            root.destroy()
        except Exception:
            pass
    return count


def _ask_speaker_count_macos():
    """macOS: AppleScript ile konusmaci sayisi sor. None=iptal."""
    script = (
        'set theCount to text returned of (display dialog '
        '"Bu kayitta kac konusmaci var? (Dogru sayi diarization kalitesini artirir)" '
        'default answer "2" with title "Meet Dictation - Konusmaci Sayisi")\n'
        'return theCount'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return None
        val = result.stdout.strip()
        return int(val) if val.isdigit() else None
    except Exception as e:
        log.error(f"[MEET] Konusmaci sayisi sorusu hatasi: {e}")
        return None


class _MeetProgressDialog:
    """Meet Dictation pipeline calistirilirken acik kalan progress penceresi.
    Pipeline ayri thread'de calisir, bu pencere main thread'de mainloop ile aktif.
    Thread-safe set_text() / finish() ile pipeline thread'i UI'i guvenli gunceller."""

    def __init__(self, title="Meet Dictation - Isleniyor"):
        import tkinter as tk
        from tkinter import ttk

        self.root = tk.Tk()
        self.root.title(title)
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass
        # Kapatma butonu devre dısı: pipeline iptal edilemez (Whisper interrupt yok)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)

        tk.Label(
            self.root, text="🎙  Meet Dictation Pipeline",
            font=("Arial", 12, "bold"),
        ).pack(pady=(20, 8), padx=30)

        self._step_label = tk.Label(
            self.root, text="Hazirlaniyor...",
            font=("Arial", 10), wraplength=440, justify="center",
        )
        self._step_label.pack(pady=6, padx=20)

        self._detail_label = tk.Label(
            self.root, text="",
            font=("Arial", 9), fg="#666", wraplength=440, justify="center",
        )
        self._detail_label.pack(pady=(0, 8), padx=20)

        self._bar = ttk.Progressbar(self.root, mode="indeterminate", length=420)
        self._bar.pack(pady=(4, 18), padx=20)
        self._bar.start(12)

        self.root.update_idletasks()
        w = max(self.root.winfo_reqwidth(), 480)
        h = max(self.root.winfo_reqheight(), 200)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.lift()

    def set_text(self, step, detail=""):
        """Thread-safe: pipeline thread'inden cagrilabilir."""
        try:
            self.root.after(0, lambda s=step, d=detail: (
                self._step_label.config(text=s),
                self._detail_label.config(text=d),
            ))
        except Exception:
            pass

    def finish(self):
        """Pencereyi kapat (thread-safe)."""
        try:
            self.root.after(0, self._do_finish)
        except Exception:
            pass

    def _do_finish(self):
        try:
            self._bar.stop()
            self.root.destroy()
        except Exception:
            pass

    def run(self):
        """mainloop — finish() cagrilana kadar blok eder."""
        try:
            self.root.mainloop()
        except Exception as e:
            log.error(f"[MEET] Progress mainloop hatasi: {e}")


def _pick_speaker_samples(speaker_labels, segments, audio, max_chunk_sec=10):
    """Her konusmaci icin temsili ornek sec: en uzun 1 segment + kisa metin snippet.
    Donus: {label: (snippet_text, audio_chunk, duration_sec)}"""
    samples = {}
    if not segments or audio is None:
        return samples
    for label in speaker_labels:
        segs = [s for s in segments if s.get("speaker_raw") == label]
        if not segs:
            continue
        # En uzun (en bilgilendirici) segment
        best = max(segs, key=lambda s: s["end"] - s["start"])
        snippet = best["text"].strip()
        if len(snippet) > 180:
            snippet = snippet[:177] + "..."
        start = int(best["start"] * SAMPLE_RATE)
        end = int(best["end"] * SAMPLE_RATE)
        max_samples = int(max_chunk_sec * SAMPLE_RATE)
        if end - start > max_samples:
            end = start + max_samples
        chunk = audio[start:end]
        samples[label] = (snippet, chunk, (end - start) / SAMPLE_RATE)
    return samples


def _ask_speaker_names_win(speaker_labels, segments=None, audio=None):
    """Windows: tkinter dialog. Her konusmaci icin Dinle butonu + isim girisi
    + alttaki scroll'lu canli on-izleme (isim yazinca tum transkriptte degisir).
    None=iptal, dict=isimler."""
    import tkinter as tk
    from tkinter import scrolledtext

    sorted_labels = sorted(speaker_labels)
    samples = _pick_speaker_samples(sorted_labels, segments, audio)
    entries = {}
    result = {}
    submitted = [False]

    # Her konusmaciya farkli renk (preview'da gorsel ayrim)
    palette = ["#1a73e8", "#d93025", "#188038", "#f9ab00", "#9334e6", "#e8710a"]
    colors = {lbl: palette[i % len(palette)] for i, lbl in enumerate(sorted_labels)}

    def stop_playback():
        try:
            sd.stop()
        except Exception:
            pass

    def make_play_handler(chunk):
        def handler():
            stop_playback()
            try:
                sd.play(chunk, SAMPLE_RATE)
            except Exception as e:
                log.error(f"[MEET] Ses oynatma hatasi: {e}")
        return handler

    root = tk.Tk()
    root.title("Meet Dictation - Konusmaci Isimleri")
    root.minsize(760, 640)
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    tk.Label(
        root,
        text=(f"{len(sorted_labels)} konusmaci tespit edildi.\n"
              f"Dinle veya alttaki on-izlemeyi oku, ismini gir — preview anlik degisir.\n"
              f"Ipucu: preview'da herhangi bir satira tikla -> o paragrafi dinle."),
        font=("Arial", 10, "bold"), justify="left",
    ).pack(pady=(12, 6), padx=16, anchor="w")

    # --- Per-speaker name entry rows ---
    name_frame = tk.Frame(root)
    name_frame.pack(padx=12, pady=4, fill="x")

    for label in sorted_labels:
        block = tk.LabelFrame(
            name_frame, text=f"  {label}  ", padx=10, pady=8,
            font=("Arial", 9, "bold"), fg=colors[label],
        )
        block.pack(fill="x", pady=4)

        row = tk.Frame(block)
        row.pack(fill="x")

        if label in samples:
            _snippet, chunk, dur = samples[label]
            tk.Button(
                row, text=f"▶ Dinle ({dur:.0f}sn)",
                command=make_play_handler(chunk), width=14,
            ).pack(side="left")

        tk.Label(row, text="  Bu kim?", anchor="w").pack(side="left", padx=(6, 4))
        entry = tk.Entry(row)
        entry.insert(0, label)
        entry.pack(side="left", fill="x", expand=True, ipady=2)
        entries[label] = entry

    # --- Live preview area (scrollable, full transcript) ---
    preview_frame = tk.LabelFrame(
        root, text="  Onizleme (isim yazinca canli guncellenir)  ",
        font=("Arial", 9, "bold"), padx=4, pady=4,
    )
    preview_frame.pack(padx=12, pady=8, fill="both", expand=True)

    text_widget = scrolledtext.ScrolledText(
        preview_frame, wrap="word",
        font=("Segoe UI", 9), height=18, padx=8, pady=6,
    )
    text_widget.pack(fill="both", expand=True)

    text_widget.tag_configure("ts", foreground="#888", font=("Segoe UI", 8))
    for lbl, color in colors.items():
        text_widget.tag_configure(f"sp_{lbl}", foreground=color, font=("Segoe UI", 9, "bold"))

    # Paragraf tag'leri: her redraw'da yeniden olusur, click handler tutar
    paragraph_chunks = {}      # tag_name -> audio numpy slice
    created_para_tags = []     # eski tag'leri silmek icin

    def make_paragraph_click_handler(chunk):
        def handler(_event):
            stop_playback()
            try:
                sd.play(chunk, SAMPLE_RATE)
            except Exception as e:
                log.error(f"[MEET] Paragraf oynatma hatasi: {e}")
        return handler

    def on_para_enter(_e):
        text_widget.config(cursor="hand2")

    def on_para_leave(_e):
        text_widget.config(cursor="")

    def redraw_preview(*_args):
        # Eski paragraf tag'lerini ve bindinglerini sil
        for t in created_para_tags:
            try:
                text_widget.tag_delete(t)
            except Exception:
                pass
        created_para_tags.clear()
        paragraph_chunks.clear()

        if not segments:
            text_widget.config(state="normal")
            text_widget.delete("1.0", "end")
            text_widget.insert("end", "(Segment yok)")
            text_widget.config(state="disabled")
            return

        text_widget.config(state="normal")
        try:
            scroll_pos = text_widget.yview()
        except Exception:
            scroll_pos = (0.0, 1.0)
        text_widget.delete("1.0", "end")

        current_raw = None
        para_start = None
        para_segs = []
        para_idx = [0]

        def flush():
            nonlocal current_raw, para_start, para_segs
            if not para_segs or current_raw is None:
                return
            m = int(para_start // 60); s = int(para_start % 60)
            entry = entries.get(current_raw)
            name = entry.get().strip() if entry else current_raw
            if not name:
                name = current_raw
            tag_sp = f"sp_{current_raw}" if f"sp_{current_raw}" in text_widget.tag_names() else None

            line_start = text_widget.index("end-1c")
            text_widget.insert("end", f"[{m:02d}:{s:02d}] ", "ts")
            if tag_sp:
                text_widget.insert("end", name, tag_sp)
            else:
                text_widget.insert("end", name)
            text_widget.insert("end", f": {' '.join(seg['text'] for seg in para_segs).strip()}\n\n")
            line_end = text_widget.index("end-2c")  # son \n\n haric

            # Bu paragraf icin tiklanabilir tag
            if audio is not None:
                tag_name = f"para_{para_idx[0]}"
                para_idx[0] += 1
                start_s = int(para_segs[0]["start"] * SAMPLE_RATE)
                end_s = int(para_segs[-1]["end"] * SAMPLE_RATE)
                end_s = min(end_s, len(audio))
                if end_s > start_s:
                    chunk = audio[start_s:end_s]
                    paragraph_chunks[tag_name] = chunk
                    text_widget.tag_add(tag_name, line_start, line_end)
                    text_widget.tag_bind(tag_name, "<Button-1>",
                                          make_paragraph_click_handler(chunk))
                    text_widget.tag_bind(tag_name, "<Enter>", on_para_enter)
                    text_widget.tag_bind(tag_name, "<Leave>", on_para_leave)
                    created_para_tags.append(tag_name)
            para_segs = []

        for seg in segments:
            raw = seg.get("speaker_raw", "?")
            if raw != current_raw:
                flush()
                current_raw = raw
                para_start = seg["start"]
                para_segs = []
            para_segs.append(seg)
        flush()

        try:
            text_widget.yview_moveto(scroll_pos[0])
        except Exception:
            pass
        text_widget.config(state="disabled")

    # Live update on every keystroke
    for entry in entries.values():
        entry.bind("<KeyRelease>", redraw_preview)

    redraw_preview()

    if sorted_labels:
        first_entry = entries[sorted_labels[0]]
        first_entry.select_range(0, "end")
        first_entry.icursor("end")
        first_entry.focus_force()

    def on_ok():
        stop_playback()
        for label, e in entries.items():
            v = e.get().strip()
            result[label] = v if v else label
        submitted[0] = True
        root.destroy()

    def on_cancel():
        stop_playback()
        root.destroy()

    btns = tk.Frame(root)
    btns.pack(pady=10)
    tk.Button(btns, text="Tamam", command=on_ok, width=12, default="active").pack(side="left", padx=6)
    tk.Button(btns, text="Iptal", command=on_cancel, width=12).pack(side="left", padx=6)
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    root.bind("<Escape>", lambda e: on_cancel())
    root.update_idletasks()
    w = max(root.winfo_reqwidth(), 760)
    h = max(root.winfo_reqheight(), 640)
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    root.lift()
    root.mainloop()

    return result if submitted[0] else None


def _ask_speaker_names_macos(speaker_labels, segments=None, audio=None):
    """macOS: her label icin sirayla AppleScript dialog. Varsa snippet'i prompta ekler.
    None=iptal, dict=isimler. Audio playback macOS'ta su an entegre degil."""
    sorted_labels = sorted(speaker_labels)
    samples = _pick_speaker_samples(sorted_labels, segments, audio)
    names = {}
    for label in sorted_labels:
        snippet_line = ""
        if label in samples:
            snippet, _chunk, _dur = samples[label]
            safe = snippet.replace('"', '\\"').replace("\n", " ")
            snippet_line = f"\\n\\nOrnek: \\\"{safe}\\\""
        script = (
            f'set theName to text returned of (display dialog '
            f'"{label} kim? (Or: Yigit, Hakan Hoca){snippet_line}" '
            f'default answer "{label}" with title "Meet Dictation - Isim")\n'
            f'return theName'
        )
        try:
            r = subprocess.run(
                ["osascript", "-e", script], capture_output=True, text=True, timeout=300
            )
            if r.returncode != 0:
                return None
            val = r.stdout.strip()
            names[label] = val if val else label
        except Exception as e:
            log.error(f"[MEET] Isim sorusu hatasi: {e}")
            return None
    return names


def _ask_speaker_count():
    return _ask_speaker_count_macos() if IS_MAC else _ask_speaker_count_win()


def _ask_speaker_names(speaker_labels, segments=None, audio=None):
    if IS_MAC:
        return _ask_speaker_names_macos(speaker_labels, segments, audio)
    return _ask_speaker_names_win(speaker_labels, segments, audio)


def _write_meet_dictation_markdown(md_path, segments, audio_duration, source_path, speaker_names):
    """Speaker-labelli Meet dictation MD. Ardisik ayni konusmaci segmentleri paragraf yapilir."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    names_list = sorted(set(speaker_names.values()))
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Meet Dictation\n\n")
        f.write(f"- **Tarih:** {timestamp}\n")
        f.write(f"- **Ses suresi:** {_format_seconds(audio_duration)}\n")
        f.write(f"- **Model:** {LECTURE_MODEL_SIZE} ({DEVICE}) + speechbrain diarization (lokal)\n")
        f.write(f"- **Konusmacilar:** {', '.join(names_list)}\n")
        f.write(f"- **Kaynak:** `{source_path}`\n\n")
        f.write("---\n\n")

        current_speaker = None
        current_paragraph = []
        current_start = None

        def flush():
            if current_paragraph and current_speaker is not None and current_start is not None:
                m = int(current_start // 60); s = int(current_start % 60)
                paragraph_text = " ".join(current_paragraph).strip()
                f.write(f"**[{m:02d}:{s:02d}] {current_speaker}:** {paragraph_text}\n\n")

        for seg in segments:
            speaker = seg.get("speaker", "?")
            if speaker != current_speaker:
                flush()
                current_speaker = speaker
                current_paragraph = []
                current_start = seg["start"]
            current_paragraph.append(seg["text"])
        flush()

        f.write("---\n\n")
        f.write(f"_**Transkript tamamlandi.** Sure: {_format_seconds(audio_duration)} • "
                f"Model: {LECTURE_MODEL_SIZE} ({DEVICE}) + speechbrain (lokal)_\n")


def _pick_file_and_meet_dictate():
    """Tray'den cagrilir: dosya sec -> diarize -> isimler -> transcribe -> MD (speaker-labelli)."""
    try:
        # 1) Dosya sec
        if IS_MAC:
            path = _pick_audio_file_macos()
        else:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            try:
                root.attributes("-topmost", True)
            except Exception:
                pass
            path = filedialog.askopenfilename(
                title="Meet kaydi sec (diarization + transcribe)",
                filetypes=[
                    ("Tum dosyalar", "*.*"),
                    ("Tum medya", "*.mp4 *.mov *.mkv *.avi *.webm *.wav *.mp3 *.m4a *.aac *.flac *.ogg *.opus"),
                ],
            )
            try:
                root.destroy()
            except Exception:
                pass

        if not path:
            log.info("[MEET] Secim iptal edildi.")
            return

        log.info(f"[MEET] Dosya secildi: {path}")
        sound_recording()

        # 2) Konusmaci sayisi sor (UI ilk; agir is sonra)
        num_speakers = _ask_speaker_count()
        if num_speakers is None:
            log.info("[MEET] Iptal (konusmaci sayisi).")
            return

        # 3-5) Heavy pipeline (decode + transcribe + cluster) ayri thread'de;
        #     UI'da progress window mainloop calisir, thread bittiginde kapanir.
        pipeline_state = {
            "audio": None, "segments": None, "error": None,
        }
        progress = _MeetProgressDialog()

        def _pipeline_worker():
            try:
                from faster_whisper.audio import decode_audio
                progress.set_text("📥 Ses dosyasi decode ediliyor...",
                                  f"{os.path.basename(path)}")
                log.info("[MEET] Audio decode ediliyor...")
                audio = decode_audio(path, sampling_rate=SAMPLE_RATE)
                pipeline_state["audio"] = audio
                audio_dur = len(audio) / SAMPLE_RATE
                log.info(f"[MEET] Audio: {audio_dur:.0f}sn")

                if audio_dur < 5.0:
                    pipeline_state["error"] = ("too_short", audio_dur, path)
                    return

                # Tahmini sureler: turbo+CUDA Whisper ~audio_dur/30 (word_timestamps +20%)
                est_whisper = max(5, int(audio_dur / 25))
                progress.set_text(
                    f"📝 Whisper transcribe (turbo, beam=5, word-level)...",
                    f"{int(audio_dur)}sn ses • Tahmini {est_whisper}sn",
                )
                t0 = time.time()
                _text, segments = _transcribe_audio_path(
                    audio, beam_size=5, word_timestamps=True,
                )
                log.info(f"[MEET] Whisper bitti ({time.time()-t0:.0f}sn, {len(segments)} segment)")

                if not segments:
                    pipeline_state["error"] = ("empty_segments",)
                    return

                # Sliding-window diarization — Whisper'dan bagimsiz konusmaci zaman cizelgesi
                est_diar = max(5, int(audio_dur * 0.3))  # CPU embed ~ ses*0.3
                progress.set_text(
                    f"🎯 Sliding-window diarization (k={num_speakers})...",
                    f"Audio boyunca 1.5sn pencere ile konusmaci cizelgesi cikariliyor • Tahmini {est_diar}sn",
                )
                t0 = time.time()
                try:
                    def _diar_progress(done, total):
                        progress.set_text(
                            f"🎯 Sliding-window diarization (k={num_speakers})...",
                            f"Embed: {done}/{total} pencere",
                        )
                    diarization_turns = _diarize_audio_sliding_window(
                        audio, num_speakers, progress_callback=_diar_progress,
                    )
                except RuntimeError as e:
                    pipeline_state["error"] = ("setup", str(e))
                    return
                log.info(f"[MEET] Diarization bitti ({time.time()-t0:.0f}sn, {len(diarization_turns)} turn)")

                # Whisper segmentlerini speaker turn sinirlarinda parcala
                progress.set_text(
                    "✂ Segmentler konusmaci sinirlarinda parcalaniyor...",
                    f"{len(segments)} Whisper segmenti / {len(diarization_turns)} speaker turn",
                )
                segments = _split_segments_by_diarization(segments, diarization_turns)
                _smooth_speaker_labels(segments, min_isolated_dur=1.5)
                pipeline_state["segments"] = segments
                log.info(f"[MEET] Split sonrasi: {len(segments)} segment")

                progress.set_text("✓ Tamamlandi. Isim dialog'u aciliyor...", "")
            except Exception as e:
                log.error(f"[MEET] Pipeline worker hatasi: {e}", exc_info=True)
                pipeline_state["error"] = ("exception", str(e))
            finally:
                progress.finish()

        worker = threading.Thread(target=_pipeline_worker, daemon=True)
        worker.start()
        progress.run()         # bloklayici — finish() cagrilana kadar
        worker.join(timeout=5) # thread'in tamamen bitmesini bekle

        # Hata kontrolu
        err = pipeline_state["error"]
        if err:
            kind = err[0]
            sound_error()
            if kind == "too_short":
                _, audio_dur, path_x = err
                _show_meet_error(
                    f"Bu dosya cok kisa/bos ({audio_dur:.1f}sn).\n\n"
                    f"Yanlis dosya secmis olabilir misin? Meet kayitlarinda bazen "
                    f"0 byte placeholder dosyalar olur; asil kayit '(1)' suffix'li olandir.\n\n"
                    f"Dosya: {os.path.basename(path_x)}"
                )
            elif kind == "empty_segments":
                _show_meet_error("Whisper transkripti bos. Audio dosyasinda konusma olmayabilir.")
            elif kind == "setup":
                _show_meet_error(err[1])
            else:
                _show_meet_error(f"Beklenmeyen hata:\n\n{err[1]}\n\nDetay: logs/dictation.log")
            return

        audio = pipeline_state["audio"]
        segments = pipeline_state["segments"]

        detected_labels = sorted(set(s.get("speaker_raw", "SPEAKER_00") for s in segments))
        log.info(f"[MEET] {len(detected_labels)} konusmaci cluster edildi: {detected_labels}")

        # 6) Isimleri sor (dialog'da her konusmaci icin snippet + Dinle butonu gosterilir)
        speaker_names = _ask_speaker_names(detected_labels, segments=segments, audio=audio)
        if speaker_names is None:
            log.info("[MEET] Iptal (isim girisi).")
            return

        # 7) İsimleri segmentlere uygula
        segments_with_speakers = _apply_speaker_names(segments, speaker_names)

        # 8) Markdown yaz (kaynak yaninda + Desktop kopyasi)
        base_name = os.path.splitext(os.path.basename(path))[0]
        primary_md = os.path.splitext(path)[0] + "_meet.md"
        try:
            _write_meet_dictation_markdown(
                primary_md, segments_with_speakers, audio_dur, path, speaker_names
            )
            log.info(f"[MEET] Yazildi: {primary_md}")
        except Exception as e:
            log.error(f"[MEET] Yazma hatasi (kaynak yaninda): {e}")
            primary_md = None

        try:
            base = _get_lectures_dir()
            desktop_md = os.path.join(base, base_name + "_meet.md")
            _write_meet_dictation_markdown(
                desktop_md, segments_with_speakers, audio_dur, path, speaker_names
            )
            log.info(f"[MEET] Masaustu kopyasi: {desktop_md}")
            if primary_md is None:
                primary_md = desktop_md
        except Exception as e:
            log.error(f"[MEET] Masaustu kopya hatasi: {e}")

        sound_sent()
        if primary_md:
            _open_in_editor(primary_md)

    except Exception as e:
        log.error(f"[MEET] Hata: {e}", exc_info=True)
        sound_error()
        _show_meet_error(f"Beklenmeyen hata:\n\n{e}\n\nDetay icin: logs/dictation.log")


# --- REGEX ---

# Default 'Diktasyon' regex'i: Whisper'in Turkce + Ingilizce kayma varyasyonlari
# (diktasyon, diktason, diktatsyon, diktasion, dictation, diction, diktoson, ...)
_DEFAULT_WAKE_RE = re.compile(
    r"\bdikta[st]+(?:yon|ion|on|sion)\b"   # diktasyon, diktason, diktatsyon, diktasion
    r"|\bdiktason\b"                         # diktason (yumusak)
    r"|\bdiktosyon\b|\bdiktoson\b"          # diktosyon, diktoson (rare)
    r"|\bdic?tat?ion\b"                      # dictation, diction, dictaion
    , re.IGNORECASE
)
# Aktif wake word regex'i (runtime'da set_wake_word ile degisir)
_WAKE_RE = _DEFAULT_WAKE_RE


# --- WHISPER KELIME DUZELTMELERI ---
# Whisper bazi (ozellikle Almanca/yabanci) kelimeleri turlu sekilde yazar.
# Asagidaki tablo transkript ciktisinda otomatik duzeltme uygular.
# Format: (regex_pattern, replacement) — pattern'lar IGNORECASE, kelime sinirli.

_WORD_CORRECTIONS = [
    # Zugzwang (Almanca satranc terimi): zooksvang, zooksvank, zugsvang, zuckswang,
    # zucksvang, zugswang, zoogzwang, zukzwang, zooks vank vb. -> Zugzwang
    # Whisper hem -ng hem -nk hem -ngk yazabilir, ortada bosluk birakabilir.
    (re.compile(r"\bz[ou]+[gcktsz]+\s*[vw]an[gk]+\b", re.IGNORECASE), "Zugzwang"),
]


def _apply_word_corrections(text):
    """Whisper'in yanlis transkribe ettigi bilinen kelimeleri duzeltir."""
    if not text:
        return text
    for pattern, replacement in _WORD_CORRECTIONS:
        text = pattern.sub(replacement, text)
    return text


def set_wake_word(new_word):
    """Tray menusunden cagrilir: yeni wake word'u aktif et, regex'i guncelle.

    Default 'diktasyon' icin genis Whisper varyasyon pattern korunur.
    Diger kelimeler icin basit kelime sinirli case-insensitive eslesme uretilir
    (Whisper varyasyonlarini yakalayamayabilir; gelistirici kullanicilar el ile
    regex pattern de girebilir, parantez/escape karakterleri olduğu gibi calisir).
    """
    global wake_word_string, _WAKE_RE
    new_word = (new_word or "").strip()
    if not new_word:
        log.warning("[WAKE] Bos wake word girildi, degisiklik atlandi.")
        return False
    wake_word_string = new_word.lower()
    if wake_word_string == WAKE_WORD_DEFAULT:
        _WAKE_RE = _DEFAULT_WAKE_RE
        log.info(f"[WAKE] Default '{WAKE_WORD_DEFAULT}' regex'i (genis Whisper varyasyonlari) aktif.")
    else:
        try:
            # Eger kullanici regex meta karakterleri kullanmadiysa basit eslesme;
            # advanced kullanicilar tam regex de girebilir (escape ihtiyaci yoksa)
            pattern = rf"\b{re.escape(wake_word_string)}\b"
            _WAKE_RE = re.compile(pattern, re.IGNORECASE)
            log.info(f"[WAKE] Yeni wake word: '{wake_word_string}' (basit kelime sinirli pattern)")
        except re.error as e:
            log.error(f"[WAKE] Regex compile hatasi: {e}, default'a donuluyor.")
            wake_word_string = WAKE_WORD_DEFAULT
            _WAKE_RE = _DEFAULT_WAKE_RE
            return False
    return True


def has_wake_word(text):
    return bool(_WAKE_RE.search(text))

def extract_message(text):
    """Ilk wake word oncesindeki mesaji cikar."""
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

    # Lecture mode: iki paralel buffer
    #   1) full-duration chunks → final pass + RawRecords/<isim>.wav diske
    #   2) live buffer → cumle bazli VAD flush, gecici LIVE.md (kayit bitince silinir)
    if lecture_active:
        global lecture_live_speech_detected, lecture_live_last_speech_time
        chunk = indata.copy()
        with lecture_audio_chunks_lock:
            lecture_audio_chunks.append(chunk)
        with lecture_live_buffer_lock:
            lecture_live_buffer.append(chunk)
        if level > LECTURE_LIVE_VAD_THRESHOLD:
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
    record_label = "F13" if IS_WIN else "Caps Lock x2"
    log.info(f"[REC] KAYIT BASLADI - {record_label} veya \"{wake_word_string.capitalize()}\" ile durdur")

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
    """Kayit sirasinda wake word'u (default: 'Diktasyon') stop word olarak arar."""
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
                # Sadece wake word soylenmis, mesaj yok — kaydi iptal et
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
                # Birden fazla match var ama arada mesaj yok (Whisper tekrar hatasi:
                # "Diktasyon Diktasyon"). Tek wake gibi davran, kayit baslat.
                log.info(f"[WAKE] \"{wake_word_string.capitalize()}\" algilandi (Whisper tekrar etti, tek event sayildi).")
                do_start_recording()
                continue

            log.info(f"[WAKE] \"{wake_word_string.capitalize()}\" algilandi!")
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
            # macOS: Caps Lock toggle key, long-press algilanamaz; tap-counting on_release'de.
            if not IS_MAC and _hotkey_press_start == 0.0 and not _long_press_fired:
                _hotkey_press_start = time.time()
                _long_press_fired = False
                _long_press_timer = threading.Timer(LONG_PRESS_RESET, _long_press_trigger)
                _long_press_timer.daemon = True
                _long_press_timer.start()
            return

    if key in (pynput_kb.Key.ctrl_l, pynput_kb.Key.ctrl_r, pynput_kb.Key.ctrl):
        current_modifiers.add(pynput_kb.Key.ctrl)
    elif key in (pynput_kb.Key.alt_l, pynput_kb.Key.alt_r, pynput_kb.Key.alt, pynput_kb.Key.alt_gr):
        current_modifiers.add(pynput_kb.Key.alt)
    elif key in (pynput_kb.Key.cmd_l, pynput_kb.Key.cmd_r, pynput_kb.Key.cmd):
        current_modifiers.add(pynput_kb.Key.cmd)


def _delayed_toggle():
    """macOS: 2. tap sonrasi 400ms gecikmeli toggle. 3. tap gelirse iptal edilir."""
    global _hotkey_tap_count, _last_hotkey_tap, _pending_toggle_timer
    _hotkey_tap_count = 0
    _last_hotkey_tap = 0
    _pending_toggle_timer = None
    toggle_recording()


def on_release(key):
    global _last_hotkey_tap, _hotkey_press_start, _long_press_timer, _long_press_fired
    global _hotkey_tap_count, _pending_toggle_timer

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
            # macOS Caps Lock: 2 tap = toggle, 3 tap = reset (DOUBLE_TAP_INTERVAL penceresi)
            now = time.time()
            if now - _last_hotkey_tap < DOUBLE_TAP_INTERVAL:
                _hotkey_tap_count += 1
            else:
                _hotkey_tap_count = 1
            _last_hotkey_tap = now

            if _hotkey_tap_count >= 3:
                # Triple-tap: bekleyen toggle varsa iptal et, reset at
                if _pending_toggle_timer:
                    _pending_toggle_timer.cancel()
                    _pending_toggle_timer = None
                _hotkey_tap_count = 0
                _last_hotkey_tap = 0
                log.info("[RESET] Triple-tap algilandi")
                threading.Thread(target=_do_reset, daemon=True).start()
            elif _hotkey_tap_count == 2:
                if sm.state == State.RECORDING:
                    # RECORDING: olasi 3. tap icin DOUBLE_TAP_INTERVAL kadar bekle
                    if _pending_toggle_timer:
                        _pending_toggle_timer.cancel()
                    _pending_toggle_timer = threading.Timer(DOUBLE_TAP_INTERVAL, _delayed_toggle)
                    _pending_toggle_timer.daemon = True
                    _pending_toggle_timer.start()
                else:
                    # LISTENING/PROCESSING/COOLDOWN: gecikmeden toggle
                    _hotkey_tap_count = 0
                    _last_hotkey_tap = 0
                    toggle_recording()
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

def _run_headless_transcribe(file_path, aggressive=False):
    """--transcribe FILE: GUI/audio stream baslatmadan tek seferlik transcribe.
    aggressive=True (B2): 1-2 kelimelik segment 5+ ardarda tekrar -> halusinasyon kabul edilip kirpilir.
    Default False — gercek 'evet evet evet' cevap senaryosu korunur."""
    if aggressive:
        global LECTURE_AGGRESSIVE_CLEANUP
        LECTURE_AGGRESSIVE_CLEANUP = True
        log.info("[FLAG] LECTURE_AGGRESSIVE_CLEANUP=True (--aggressive)")
    print("=" * 55)
    print("  Voice Dictation - Tek Seferlik Transkript")
    print("=" * 55)
    print(f"  Kaynak : {file_path}")
    print(f"  Model  : {LECTURE_MODEL_SIZE} ({DEVICE})")
    if aggressive:
        print(f"  Mod    : AGRESIF TEMIZLIK (5+ kisa tekrar -> kirp)")
    print("=" * 55)
    log.info(f"[HEADLESS] Transcribe basliyor: {file_path}")

    # Ayni anda calisan daemon varsa GPU/CUDA context cakismasi olur:
    # daemon'un transcribe'lari sessizce bos donmeye baslar.
    daemon_pid = _read_daemon_pid()
    if daemon_pid is not None:
        msg = (f"Daemon zaten calisiyor (PID {daemon_pid}). Ayni anda iki Whisper instance "
               f"GPU'da cakisir ve daemon bozulur. Once tray'den 'Cikis' ile daemon'u durdur.")
        print(f"\n[HATA] {msg}")
        log.error(f"[HEADLESS] {msg}")
        return 2

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
    parser.add_argument("--aggressive", action="store_true",
                        help="B2: 5+ ardarda kisa segment tekrari halusinasyon kabul edilip kirpilir "
                             "(gercek 'evet evet evet' cevaplari da kirpilabilir; default kapali).")
    args, _unknown = parser.parse_known_args()

    if args.transcribe:
        sys.exit(_run_headless_transcribe(args.transcribe, aggressive=args.aggressive))

    os_name = "macOS" if IS_MAC else "Windows"
    record_label = "F13 (sniper butonu)" if IS_WIN else "Caps Lock x2 (double-tap)"

    print("=" * 55)
    print("  Voice Dictation Tool - Whisper STT")
    print("=" * 55)
    print(f"  Platform     : {os_name}")
    print(f"  Toggle word  : \"{wake_word_string}\" (baslat + durdur)")
    print(f"  Sniper buton : {record_label} (toggle)")
    print(f"  Cikis        : Tray/Menu bar -> Cikis")
    print(f"  Model        : {MODEL_SIZE} ({DEVICE})")
    print(f"  Custom vocab : {len(INITIAL_PROMPT.split(','))} terim")
    print(f"  Log dosyasi  : {_LOG_FILE}")
    print("=" * 55)
    log.info(f"Baslatildi: {os_name}, model={MODEL_SIZE}, device={DEVICE}")

    # Ayni anda ikinci daemon baslarsa GPU'da cakisma olur. Stale PID dosyasi yoksay.
    existing_pid = _read_daemon_pid()
    if existing_pid is not None and existing_pid != os.getpid():
        log.error(f"Baska bir daemon zaten calisiyor (PID {existing_pid}). Cikiliyor.")
        print(f"\n[HATA] Baska bir daemon zaten calisiyor (PID {existing_pid}).")
        sys.exit(3)

    _write_daemon_pid()
    import atexit
    atexit.register(_remove_daemon_pid)

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
             f"   Baslat: {record_label} veya \"{WAKE_WORD_DEFAULT.capitalize()}\" de\n"
             f"   Durdur: {record_label} (tekrar) veya \"{WAKE_WORD_DEFAULT.capitalize()}\" de\n"
             f"   Cikmak icin: Tray/Menu bar -> Cikis")

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
