"""Kaynak tasinmasi baslaticiyi ve kalici veri yollarini degistirmemeli."""
import ast
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'dev' / 'dictation.py'


class LayoutTests(unittest.TestCase):
    def test_existing_launcher_dispatches_without_loading_models(self):
        with patch('runpy.run_module') as run:
            runpy.run_path(str(ROOT / 'dictation.py'), run_name='__main__')
        run.assert_called_once_with('dev.dictation', run_name='__main__')

    def test_data_and_runtime_paths_stay_at_repo_root(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        names = {'SOURCE_DIR', 'BASE_DIR', 'DATA_DIR', 'LOCAL_DIR', '_LOG_DIR'}
        nodes = [n for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in names for t in n.targets)]
        ns = {'os': os, '__file__': str(SOURCE)}
        with patch.dict(os.environ, {}, clear=True):
            exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), ns)
        self.assertEqual(Path(ns['BASE_DIR']), ROOT)
        self.assertEqual(Path(ns['DATA_DIR']), ROOT / 'data')
        self.assertEqual(Path(ns['_LOG_DIR']), ROOT / '.local' / 'logs')

    def test_env_is_loaded_from_root(self):
        tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_load_env_file')
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / '.env').write_text('VD_LAYOUT_TEST=root\n', encoding='utf-8')
            ns = {'os': os, '__file__': str(base / 'dev' / 'dictation.py')}
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), 'exec'), ns)
            with patch.dict(os.environ, {}, clear=True):
                ns['_load_env_file']()
                self.assertEqual(os.environ['VD_LAYOUT_TEST'], 'root')
