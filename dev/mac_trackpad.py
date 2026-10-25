"""Ayni daemon icinde dort parmak -> F13 isleyicisi; ayri uygulama/izin yok."""
import ctypes
from pathlib import Path
import queue
import threading
import time


class Trackpad:
    def __init__(self, library_path, on_tap, log):
        self.enabled = False
        self.ready = False
        self.status = "kurulu degil"
        self._library = None
        self._events = queue.Queue(maxsize=8)
        self._stop = threading.Event()
        self._callback = ctypes.CFUNCTYPE(None)(self._enqueue)
        self._on_tap, self._log = on_tap, log
        self._worker = None
        self._last_report = 0
        self._dropped_full = 0
        self._dropped_stale = 0
        self._full_rejections = None
        # Hedef parmak sayisi modulden okunur; eski modulde sayi sorgusu yok ve uc parmaktir.
        self.fingers = 4
        if not Path(library_path).is_file():
            return
        try:
            lib = self._library = ctypes.CDLL(str(library_path))
            lib.vd_trackpad_start.argtypes = [type(self._callback)]
            lib.vd_trackpad_start.restype = ctypes.c_int
            lib.vd_trackpad_enable.argtypes = [ctypes.c_int]
            lib.vd_trackpad_enable.restype = None
            lib.vd_trackpad_stop.argtypes = []
            lib.vd_trackpad_stop.restype = None
            lib.vd_trackpad_counts.argtypes = [ctypes.POINTER(ctypes.c_ulong)] * 2
            lib.vd_trackpad_counts.restype = None
            lib.vd_trackpad_rejections.argtypes = [ctypes.POINTER(ctypes.c_ulong)]
            lib.vd_trackpad_rejections.restype = None
            fingers = getattr(lib, 'vd_trackpad_fingers', None)
            if fingers is None:
                self.fingers = 3
                log.warning("[TRACKPAD] Eski modul uc parmak bekliyor; dev/scripts/build-mac-trackpad.sh ile yeniden derle")
            else:
                fingers.argtypes = []
                fingers.restype = ctypes.c_int
                self.fingers = fingers()
            self._full_rejections = getattr(lib, 'vd_trackpad_full_rejections', None)
            if self._full_rejections is not None:
                self._full_rejections.argtypes = [ctypes.POINTER(ctypes.c_ulong)]
                self._full_rejections.restype = None
            result = lib.vd_trackpad_start(self._callback)
            if result:
                self.status = f"baslatilamadi ({result})"
                log.warning("[TRACKPAD] %s", self.status)
                return
            self.ready = True
            self._worker = threading.Thread(target=self._run, name="dictation-trackpad", daemon=True)
            self._worker.start()
            self.set_enabled(True)
        except (OSError, AttributeError):
            self.status = "modul yuklenemedi"
            log.warning("[TRACKPAD] %s", self.status)

    def _enqueue(self):
        if not self.enabled or self._stop.is_set():
            return
        try:
            self._events.put_nowait(time.monotonic())
        except queue.Full:
            self._dropped_full += 1

    def _run(self):
        while not self._stop.is_set():
            try:
                stamp = self._events.get(timeout=.1)
            except queue.Empty:
                continue
            age = time.monotonic() - stamp
            if self.enabled and not self._stop.is_set() and age < .2:
                try:
                    self._on_tap()
                    self._log.info("[TRACKPAD] %d parmak -> F13 isleyicisi (kuyruk=%.1f ms)", self.fingers, age * 1000)
                except Exception:
                    self._log.exception("[TRACKPAD] Hareket islenemedi")
            elif self.enabled and not self._stop.is_set() and age >= .2:
                self._dropped_stale += 1
                self._log.info("[TRACKPAD] Eski olay atlandi (kuyruk=%.1f ms)", age * 1000)

    def set_enabled(self, enabled):
        if not self.ready or self._stop.is_set():
            return
        self.enabled = bool(enabled)
        self._library.vd_trackpad_enable(int(self.enabled))
        while True:
            try:
                self._events.get_nowait()
            except queue.Empty:
                break
        self.status = "acik" if self.enabled else "kapali"
        self._log.info("[TRACKPAD] %s (daemon icinde)", self.status)

    def counts(self):
        if not self.ready:
            return 0, 0
        frames, taps = ctypes.c_ulong(), ctypes.c_ulong()
        self._library.vd_trackpad_counts(ctypes.byref(frames), ctypes.byref(taps))
        if time.monotonic() - self._last_report > 30:
            self._last_report = time.monotonic()
            rejected = (ctypes.c_ulong * 7)()
            self._library.vd_trackpad_rejections(rejected)
            self._log.info("[TRACKPAD] frame=%d tap=%d red(hareket,parmak,sure,modifier,gec_parmak,veri)=%s",
                           frames.value, taps.value, list(rejected)[1:])
            full = (ctypes.c_ulong * 7)()
            if self._full_rejections is not None:
                self._full_rejections(full)
            self._log.info("[TRACKPAD] %d_parmak_red=%s kuyruk_dolu=%d kuyruk_eski=%d", self.fingers,
                           list(full)[1:] if self._full_rejections is not None else 'bilinmiyor',
                           self._dropped_full, self._dropped_stale)
        return frames.value, taps.value

    def close(self):
        self.enabled = False
        self._stop.set()
        if self.ready:
            self._library.vd_trackpad_stop()
            self.ready = False
        if self._worker:
            self._worker.join(timeout=1)
