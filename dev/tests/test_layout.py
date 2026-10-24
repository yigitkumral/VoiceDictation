"""Birlesik yerlesimde baslatici, veri ve ortam yollari."""
import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'dev' / 'dictation.py'


class LayoutTests(unittest.TestCase):
    def test_launchers_use_package_and_local_environment(self):
        for name in ('start.vbs', 'start.bat', 'start.sh'):
            text = (ROOT / 'dev' / 'scripts' / name).read_text(encoding='utf-8')
            self.assertIn('-m dev.dictation', text)
            self.assertIn('.local', text)
        self.assertFalse((ROOT / 'dictation.py').exists())

    def test_data_and_runtime_paths_use_local_tree(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        names = {'SOURCE_DIR', 'BASE_DIR', 'DATA_DIR', 'LOCAL_DIR', '_LOG_DIR'}
        nodes = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)]
        ns = {'os': os, '__file__': str(SOURCE)}
        with patch.dict(os.environ, {}, clear=True):
            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)
        self.assertEqual(Path(ns['BASE_DIR']), ROOT)
        self.assertEqual(Path(ns['DATA_DIR']), ROOT / '.local' / 'data')
        self.assertEqual(Path(ns['_LOG_DIR']), ROOT / '.local' / 'logs')

    def test_env_is_loaded_from_local(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_load_env_file')
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / '.local').mkdir()
            (base / '.local' / '.env').write_text('VD_LAYOUT_TEST=root\n', encoding='utf-8')
            ns = {'os': os, '__file__': str(base / 'dev' / 'dictation.py')}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), ns)
            with patch.dict(os.environ, {}, clear=True):
                ns['_load_env_file']()
                self.assertEqual(os.environ['VD_LAYOUT_TEST'], 'root')
