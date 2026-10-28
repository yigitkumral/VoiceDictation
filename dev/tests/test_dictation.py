"""Daemon import edilmeden gercek fonksiyonlari sahte I/O ile sinar."""
import ast
import concurrent.futures
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import tempfile
import threading
import time
from enum import Enum
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np


SOURCE = Path(__file__).resolve().parents[2] / "dev/dictation.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))
TEMP_DIR = Path(__file__).resolve().parents[2] / ".local" / "test-tmp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def load(*names):
    """Modul import'u log/model/klavye olusturdugundan yalniz secilen AST'yi yukle."""
    ns = dict(_diagnostic_event=Mock(), _diagnostic_destination=Mock(),
              _start_diagnostic=Mock(return_value="a" * 32), _finish_diagnostic=Mock(),
              MODEL_SIZE="test", DEVICE="test", CLEANUP_MODEL="test.gguf", os=os, re=re, time=time, threading=threading, json=json, subprocess=subprocess,
              tempfile=tempfile, np=np, Enum=Enum, log=Mock(), IS_WIN=True, IS_MAC=False,
              wake_word_string="diktasyon", _cancel_windows_hotkey=Mock())
    for node in TREE.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ns)
    return ns


class FileAndTextTests(unittest.TestCase):
    def test_atomic_paths_never_reuse_existing_file(self):
        f = load("_unique_path")["_unique_path"]
        with tempfile.TemporaryDirectory(dir=TEMP_DIR) as folder:
            original = Path(folder, "meeting.wav")
            original.write_bytes(b"precious")
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                paths = list(pool.map(lambda _: f(folder, "meeting", ".wav"), range(40)))
            self.assertEqual(len(set(paths)), 40)
            self.assertTrue(all(Path(p).exists() for p in paths))
            self.assertEqual(original.read_bytes(), b"precious")

    def test_dedupe_updates_segments_without_eating_meaningful_repeats(self):
        ns = load("_dedupe_segment_runs", "_finalize_segments", "_segments_to_paragraphs")
        ns.update(_FILLER_RE=re.compile(r"^(?:E+e*|Ee+|Hı+m?|Mı+m?|Aa+|Ah+)$", re.I),
                  _drop_low_confidence_segments=lambda s: (s, 0),
                  _strip_known_artifacts=lambda t: t, _apply_word_corrections=lambda t: t)
        def segments(word, n):
            return [dict(start=i, end=i + 1, text=word) for i in range(n)]
        clean, text = ns["_finalize_segments"](segments("Eee.", 3))
        self.assertEqual(text, "Eee.")
        self.assertEqual(ns["_segments_to_paragraphs"](clean), [(0, "Eee.")])
        clean, text = ns["_finalize_segments"](segments("Evet.", 5))
        self.assertEqual(len(clean), 5)
        clean, text = ns["_finalize_segments"](segments("Evet.", 5), aggressive=True)
        self.assertEqual(len(clean), 1)
        self.assertEqual(clean[0]["end"], 5)

    def test_unchanged_segments_keep_word_timestamps(self):
        ns = load("_dedupe_segment_runs")
        ns["_FILLER_RE"] = re.compile("Eee")
        original = [dict(text="Merhaba. Nasılsın?", words=[{"word": "Merhaba"}], start=0, end=3)]
        self.assertIs(ns["_dedupe_segment_runs"](original), original)

class CleanupTests(unittest.TestCase):
    def test_conservative_cleanup_acceptance(self):
        f = load("_accept_cleanup", "_cleanup_rejection_reason")["_accept_cleanup"]
        self.assertTrue(f("Eee bugün dosyayı açalım.", "Bugün dosyayı açalım."))
        self.assertTrue(f("Toplantı salı, hayır çarşamba günü olacak.", "Toplantı çarşamba günü olacak."))
        for original, changed in [
            ("Evet evet evet katılıyorum.", "Evet katılıyorum."),
            ("Dosyayı silme.", "Dosyayı sil."),
            ("Dosyayı silme, hayır sil.", "Dosyayı sil."),
            ("Toplantı 25 Ekim saat 13.", "Toplantı 26 Ekim saat 13."),
            ("Saat 13.30 için gel.", "Saat 13 30 için gel."),
            ("Ali bugün gelecek.", "Bugün gelecek."),
            ("Bugün çalışalım.", "Bugün çalışalım ve dosyaları silelim."),
            ("Merhaba dünya.", ""),
        ]:
            with self.subTest(original=original):
                self.assertFalse(f(original, changed))

    def test_timeout_preserves_original_and_removes_prompt(self):
        ns = load("_cleanup_text", "_accept_cleanup")
        ready = threading.Event()
        ready.set()
        process = Mock()
        process.poll.return_value = None
        with tempfile.TemporaryDirectory(dir=TEMP_DIR) as folder:
            ns.update(cleanup_enabled=True, _cleanup_available=lambda: True, CLEANUP_TEMP_DIR=folder,
                      cleanup_lock=threading.Lock(), cleanup_stats=threading.local(),
                      _cleanup_server_lock=threading.RLock(),
                      _cleanup_server=dict(ready=ready, process=process), _cleanup_prompt=lambda t: t,
                      _cleanup_request=Mock(side_effect=TimeoutError()))
            self.assertEqual(ns["_cleanup_text"]("Eee bugün çalışalım."), "Eee bugün çalışalım.")
            self.assertEqual(ns["cleanup_stats"].value["status"], "timeout")
            self.assertEqual(os.listdir(folder), [])

    def test_missing_model_does_not_start_process(self):
        ns = load("_cleanup_text")
        ns.update(cleanup_enabled=True, _cleanup_available=lambda: False, cleanup_stats=threading.local())
        with patch.object(subprocess, "run") as run:
            self.assertEqual(ns["_cleanup_text"]("Merhaba."), "Merhaba.")
            run.assert_not_called()


class RecordingTests(unittest.TestCase):
    def setUp(self):
        self.ns = ns = load("State", "StateMachine", "_do_reset", "_recording_valid",
                            "_finish_dictation", "_finish_recording", "_send_final", "do_stop_and_send")
        ns.update(recording_lock=threading.RLock(), audio_lock=threading.Lock(), listen_lock=threading.Lock(),
                  audio_frames=[np.ones(16000)], listen_frames=[], _recording_id=1,
                  _recording_source=(1, 2, "title", "app"), _recording_context="project",
                  should_quit=SimpleNamespace(is_set=lambda: False, wait=lambda _: False),
                  SAMPLE_RATE=16000, wake_word_enabled=False,
                  sound_error=Mock(), sound_sent=Mock(), pyperclip=SimpleNamespace(copy=Mock()),
                  paste_only=Mock(return_value=True),
                  _delivery_notice=Mock(),
                  _write_timing=Mock(), cleanup_stats=threading.local(),
                  _cleanup_text=lambda t: t, quick_transcribe=Mock(return_value="Merhaba"))
        ns["sm"] = ns["StateMachine"]()
        ns["sm"].force(ns["State"].PROCESSING)

    def finish(self):
        ns = self.ns
        ns["_finish_dictation"](1, list(ns["audio_frames"]), "project", ns["_recording_source"])

    def test_reset_during_transcription_prevents_send(self):
        ns = self.ns
        def transcribe(*args, **kwargs):
            ns["_do_reset"]()
            return "Should never send"
        ns["quick_transcribe"] = transcribe
        self.finish()
        ns["pyperclip"].copy.assert_not_called()
        ns["paste_only"].assert_not_called()
        self.assertEqual(ns["sm"].state, ns["State"].LISTENING)

    def test_old_final_does_not_reset_new_recording(self):
        ns = self.ns
        def transcribe(*args, **kwargs):
            ns["_do_reset"]()
            ns["sm"].force(ns["State"].RECORDING)
            ns["audio_frames"].append(np.ones(1600))
            return "Stale"
        ns["quick_transcribe"] = transcribe
        self.finish()
        self.assertEqual(ns["sm"].state, ns["State"].RECORDING)
        self.assertEqual(len(ns["audio_frames"]), 1)
        ns["pyperclip"].copy.assert_not_called()

    def test_clipboard_failure_returns_to_listening(self):
        ns = self.ns
        ns["pyperclip"].copy.side_effect = RuntimeError("busy")
        self.finish()
        self.assertEqual(ns["sm"].state, ns["State"].LISTENING)
        self.assertEqual(ns["audio_frames"], [])

    def test_changed_focus_receives_completed_text(self):
        focus = self.ns["_foreground_window"] = Mock(return_value=(9, 10, "New focus", "new.exe"))
        self.ns["_same_target"] = Mock(side_effect=AssertionError("Odak dogrulamasi yapilmamali"))
        self.finish()
        self.ns["pyperclip"].copy.assert_called_once_with("Merhaba")
        self.ns["paste_only"].assert_called_once()
        focus.assert_not_called()

    def test_cleanup_cancellation_prevents_clipboard_and_paste(self):
        ns = self.ns
        def cleanup(text):
            ns["_do_reset"]()
            return "Gecikmis sonuc"
        ns["_cleanup_text"] = cleanup
        self.finish()
        ns["pyperclip"].copy.assert_not_called()
        ns["paste_only"].assert_not_called()

    def test_final_preserves_cleanup_paragraphs(self):
        ns = self.ns
        ns["_cleanup_text"] = Mock(return_value="İlk paragraf.\n\nİkinci paragraf.")
        self.finish()
        ns["_cleanup_text"].assert_called_once_with("Merhaba")
        ns["pyperclip"].copy.assert_called_once_with("İlk paragraf.\n\nİkinci paragraf.")
        ns["paste_only"].assert_called_once()

    def test_final_uses_context_prepared_by_source_worker(self):
        ready = threading.Event()
        ready.set()
        self.ns["_recording_source"] = dict(ready=ready, context="source project")
        self.finish()
        self.assertEqual(self.ns["quick_transcribe"].call_args.kwargs["context"], "source project")

    def test_unready_context_does_not_block_final_transcription(self):
        event = Mock()
        event.wait.return_value = False
        self.ns["_recording_source"] = dict(ready=event, context="stale")
        self.finish()
        event.wait.assert_called_once_with(.15)
        self.assertEqual(self.ns["quick_transcribe"].call_args.kwargs["context"], "")
        self.ns["paste_only"].assert_called_once()

    def test_full_audio_and_context_used_and_only_one_send(self):
        self.finish()
        ns = self.ns
        ns["quick_transcribe"].assert_called_once()
        self.assertEqual(len(ns["quick_transcribe"].call_args.args[0]), 16000)
        self.assertEqual(ns["quick_transcribe"].call_args.kwargs["context"], "project")
        ns["pyperclip"].copy.assert_called_once_with("Merhaba")
        ns["paste_only"].assert_called_once()

    def test_final_reports_stage_times_without_content(self):
        self.finish()
        metrics = self.ns["_write_timing"].call_args.args[0]
        self.assertEqual(metrics["status"], "pasted")
        for key in ("context_wait_ms", "whisper_ms", "cleanup_ms", "paste_ms", "total_ms"):
            self.assertGreaterEqual(metrics[key], 0)
        self.assertEqual(metrics["audio_seconds"], 1)
        self.assertNotIn("Merhaba", str(metrics))

    def test_paste_never_presses_enter(self):
        ns = load("paste_only")
        keys = Mock()
        ns.update(paste_controller=keys, MODIFIER="ctrl", PASTE_KEY="v",
                  pynput_kb=SimpleNamespace(Key=SimpleNamespace(enter="enter")))
        valid = Mock(return_value=True)
        with patch.object(time, "sleep"):
            self.assertTrue(ns["paste_only"](valid))
        self.assertNotIn(unittest.mock.call("enter"), keys.press.call_args_list)

    def test_mac_denied_permission_keeps_clipboard_without_claiming_paste(self):
        ns = self.ns
        ns.update(IS_MAC=True, _mac_keyboard_access=Mock(return_value=False))
        status = ns['_send_final']('Merhaba.', 1)
        self.assertEqual(status, 'permission_denied')
        ns['pyperclip'].copy.assert_called_once_with('Merhaba.')
        ns['paste_only'].assert_not_called()
        ns['sound_sent'].assert_not_called()
        ns['_delivery_notice'].assert_called_once()

    def test_mac_granted_permission_uses_existing_paste(self):
        ns = self.ns
        ns.update(IS_MAC=True, _mac_keyboard_access=Mock(return_value=True))
        self.assertEqual(ns['_send_final']('Merhaba.', 1), 'pasted')
        ns['paste_only'].assert_called_once()
        ns['sound_sent'].assert_not_called()  # bitis tonu durdurmada calar

    def test_stop_claims_recording_once_without_blocking_keyboard(self):
        ns = self.ns
        ns["sm"].force(ns["State"].RECORDING)
        with patch.object(threading, "Thread") as worker:
            ns["do_stop_and_send"](expected_id=0)
            worker.assert_not_called()
            ns["sound_sent"].assert_not_called()
            ns["do_stop_and_send"](expected_id=1)
            ns["do_stop_and_send"](expected_id=1)
            worker.assert_called_once()
            ns["sound_sent"].assert_called_once()
            worker.return_value.start.assert_called_once()
        self.assertEqual(ns["sm"].state, ns["State"].PROCESSING)


class RecordingWakeTests(unittest.TestCase):
    def test_provisional_start_captures_without_sound_or_decoder_worker(self):
        ns = load("State", "StateMachine", "do_start_recording", "_announce_recording")
        source = {"window": None}
        ns.update(sm=ns["StateMachine"](), lecture_active=False, _recording_id=0,
                  recording_lock=threading.RLock(), listen_lock=threading.Lock(),
                  audio_lock=threading.Lock(), listen_frames=["recent audio"], audio_frames=[],
                  _capture_context_source=Mock(return_value=source), sound_recording=Mock(),
                  stop_word_checker=Mock())
        with patch.object(threading, "Thread") as worker:
            self.assertTrue(ns["do_start_recording"](provisional=True))
            self.assertEqual(ns["sm"].state, ns["State"].RECORDING)
            self.assertEqual(ns["audio_frames"], ["recent audio"])
            ns["sound_recording"].assert_not_called()
            worker.assert_not_called()
            ns["_announce_recording"](ns["_recording_id"], source)
            ns["sound_recording"].assert_called_once()
            worker.assert_called_once_with(target=ns["stop_word_checker"], args=(1, source), daemon=True)

    def setup_loop(self):
        ns = load("State", "StateMachine", "_recording_valid", "stop_word_checker")
        ns.update(_recording_id=7, _capture_context=Mock(return_value="project"),
                  recording_lock=threading.RLock(), audio_lock=threading.Lock(),
                  audio_frames=[np.ones(1600)] * 200,
                  should_quit=SimpleNamespace(is_set=lambda: False, wait=Mock(side_effect=[False, True])),
                  speech_detected=True, last_speech_time=time.time() - 1, NO_SPEECH_TIMEOUT=30,
                  STOP_CHECK_SILENCE=.35, wake_word_enabled=False,
                  quick_transcribe=Mock(return_value="Diktasyon"),
                  has_wake_word=Mock(return_value=True), do_stop_and_send=Mock())
        ns["sm"] = ns["StateMachine"]()
        ns["sm"].force(ns["State"].RECORDING)
        return ns

    def test_no_recording_stt_when_wake_is_disabled(self):
        ns = self.setup_loop()
        source = dict(context="", ready=threading.Event())
        ns["stop_word_checker"](7, source)
        ns["quick_transcribe"].assert_not_called()
        ns["_capture_context"].assert_called_once_with(source)
        self.assertEqual(source["context"], "project")
        self.assertTrue(source["ready"].is_set())
        self.assertEqual(ns["_recording_context"], "project")
        self.assertEqual(len(ns["audio_frames"]), 200)

    def test_wake_stt_is_bounded_and_requests_full_final(self):
        ns = self.setup_loop()
        ns["wake_word_enabled"] = True
        ns["stop_word_checker"](7, None)
        ns["quick_transcribe"].assert_called_once()
        self.assertEqual(len(ns["quick_transcribe"].call_args.args[0]), 120 * 1600)
        self.assertEqual(ns["quick_transcribe"].call_args.kwargs["context"], "")
        self.assertEqual(len(ns["audio_frames"]), 200)
        ns["do_stop_and_send"].assert_called_once_with(expected_id=7)

    def test_wake_stt_waits_for_silence(self):
        ns = self.setup_loop()
        ns.update(wake_word_enabled=True, last_speech_time=time.time())
        ns["stop_word_checker"](7, None)
        ns["quick_transcribe"].assert_not_called()

    def test_wake_result_after_recording_stops_cannot_request_another_final(self):
        ns = self.setup_loop()
        ns["wake_word_enabled"] = True
        def transcribe(*args, **kwargs):
            ns["sm"].force(ns["State"].PROCESSING)
            return "Diktasyon"
        ns["quick_transcribe"] = transcribe
        ns["stop_word_checker"](7, None)
        ns["do_stop_and_send"].assert_not_called()

    def test_context_worker_releases_final_waiter_after_stop(self):
        ns = self.setup_loop()
        ns["sm"].force(ns["State"].PROCESSING)
        source = dict(context="", ready=threading.Event())
        ns["stop_word_checker"](7, source)
        self.assertTrue(source["ready"].is_set())
        self.assertEqual(source["context"], "project")
        ns["quick_transcribe"].assert_not_called()


class ModelCallTests(unittest.TestCase):
    def test_cancelled_waiter_never_starts_whisper(self):
        ns = load("quick_transcribe", "_whisper_context")
        ns.update(_has_speech=lambda audio: True, transcribe_lock=threading.Lock(), model=Mock())
        self.assertEqual(ns["quick_transcribe"](np.ones(1600), valid=lambda: False), "")
        ns["model"].transcribe.assert_not_called()

    def test_dynamic_terms_are_passed_to_hotwords(self):
        ns = load("quick_transcribe", "_whisper_context")
        ns.update(_has_speech=lambda audio: True, transcribe_lock=threading.Lock(), IS_MAC=False,
                  INITIAL_PROMPT="fixed", model=Mock(), _clean_transcription=lambda t: t,
                  _strip_known_artifacts=lambda t: t, _dedupe_repeated_segments=lambda t, **kw: t)
        ns["model"].transcribe.return_value = ([SimpleNamespace(text="Merhaba")], None)
        self.assertEqual(ns["quick_transcribe"](np.ones(1600), context="project, branch"), "Merhaba")
        self.assertEqual(ns["model"].transcribe.call_args.kwargs["hotwords"], "project, branch")
        self.assertFalse(ns["model"].transcribe.call_args.kwargs["condition_on_previous_text"])


if __name__ == "__main__":
    unittest.main()
