"""MLX onbellek siniri: yalniz Mac yolu, kilit icinde temizlik, hata dikteyi bozmaz."""
import ast
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import Mock

import numpy as np


SOURCE = Path(__file__).resolve().parents[2] / "dev/dictation.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"))


def load(*names, **extra):
    ns = dict(np=np, log=Mock(), threading=threading, time=time, _diagnostic_event=Mock(), transcribe_lock=threading.Lock(),
              IS_MAC=True, USE_MLX=True, SAMPLE_RATE=16000, MODEL_SIZE="turbo", DEVICE="mlx",
              MLX_MODEL_REPO="repo", MLX_LECTURE_MODEL_REPO="repo", MLX_CACHE_LIMIT_BYTES=64 << 20,
              INITIAL_PROMPT="fixed", mx=Mock(), mlx_whisper=Mock(), _has_speech=lambda audio: True,
              _whisper_context=lambda context: ("fixed", "hints"), _clean_transcription=lambda t: t,
              _strip_known_artifacts=lambda t, **kw: t, _dedupe_repeated_segments=lambda t, **kw: t)
    ns.update(extra)
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ns)
    return ns


class MlxCacheTests(unittest.TestCase):
    def setUp(self):
        self.ns = load("_release_mlx_cache", "load_model", "quick_transcribe", "_transcribe_audio_path",
                       _vad_prefilter=lambda audio, sampling_rate: (audio, None), LECTURE_AGGRESSIVE_CLEANUP=False,
                       _finalize_segments=lambda segments, aggressive: (segments, "Merhaba"))
        self.calls = []
        self.lock_seen = []
        self.ns["mx"].set_cache_limit.side_effect = lambda limit: self.calls.append(("limit", limit))
        def clear():
            self.calls.append(("clear",))
            self.lock_seen.append(self.ns["transcribe_lock"].locked())
        self.ns["mx"].clear_cache.side_effect = clear
        def transcribe(*args, **kwargs):
            self.calls.append(("transcribe",))
            return dict(text="Merhaba", segments=[])
        self.ns["mlx_whisper"].transcribe.side_effect = transcribe

    def test_load_sets_limit_before_warmup_then_clears(self):
        self.ns["load_model"]()
        self.assertEqual(self.calls, [("limit", 64 << 20), ("transcribe",), ("clear",)])
        self.assertEqual(self.lock_seen, [True])

    def test_dictation_clears_inside_lock_after_transcribe(self):
        self.assertEqual(self.ns["quick_transcribe"](np.ones(1600)), "Merhaba")
        self.assertEqual(self.calls, [("transcribe",), ("clear",)])
        self.assertEqual(self.lock_seen, [True])

    def test_file_path_clears_inside_lock_after_transcribe(self):
        self.assertEqual(self.ns["_transcribe_audio_path"](np.ones(1600))[0], "Merhaba")
        self.assertEqual(self.calls, [("transcribe",), ("clear",)])
        self.assertEqual(self.lock_seen, [True])

    def test_failed_transcribe_still_clears(self):
        self.ns["mlx_whisper"].transcribe.side_effect = RuntimeError("gpu")
        self.assertEqual(self.ns["quick_transcribe"](np.ones(1600)), "")
        self.assertEqual(self.calls, [("clear",)])

    def test_clear_failure_keeps_transcript(self):
        self.ns["mx"].clear_cache.side_effect = RuntimeError("metal")
        self.assertEqual(self.ns["quick_transcribe"](np.ones(1600)), "Merhaba")
        self.ns["log"].warning.assert_called_once()

    def test_windows_path_never_touches_mlx(self):
        whisper = Mock()
        whisper.transcribe.return_value = ([], None)
        ns = load("quick_transcribe", "_release_mlx_cache", IS_MAC=False, USE_MLX=False, model=whisper)
        ns["quick_transcribe"](np.ones(1600))
        whisper.transcribe.assert_called_once()
        ns["mx"].clear_cache.assert_not_called()
        ns["mlx_whisper"].transcribe.assert_not_called()


if __name__ == "__main__":
    unittest.main()
