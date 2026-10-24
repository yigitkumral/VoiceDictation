"""Olcum dosyasi kullanici metni ve hedef bilgisi tasimaz."""
import ast
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]


class TimingTests(unittest.TestCase):
    def test_whitelist_drops_text_and_records_stage_times(self):
        node = next(n for n in ast.parse((ROOT / 'dictation.py').read_text(encoding='utf-8')).body
                    if isinstance(n, ast.FunctionDef) and n.name == '_write_timing')
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as folder:
            destination = Path(folder) / 'metrics' / 'dictation.jsonl'
            ns = dict(os=os, json=json, time=time, timing_lock=threading.Lock(),
                      TIMING_FILE=str(destination), log=Mock())
            exec(compile(ast.Module(body=[node], type_ignores=[]), 'dictation.py', 'exec'), ns)
            ns['_write_timing'](dict(total_ms=1500, whisper_ms=300, cleanup_ms=900, paste_ms=300,
                                     status='pasted', cleanup_status='accepted', cleanup_backend='CUDA0', text='PRIVATE',
                                     window='PRIVATE', input_chars=30))
            row = json.loads(destination.read_text())
            self.assertNotIn('PRIVATE', destination.read_text())
            self.assertEqual(row['total_ms'], 1500)
            self.assertEqual(row['cleanup_status'], 'accepted')
            self.assertEqual(row['cleanup_backend'], 'CUDA0')
            self.assertIn('1.5', ns['last_timing_summary'])
            ns['_write_timing'](dict(status='PRIVATE', cleanup_status='PRIVATE', cleanup_backend='PRIVATE', total_ms='PRIVATE'))
            self.assertNotIn('PRIVATE', destination.read_text())


if __name__ == '__main__':
    unittest.main()
