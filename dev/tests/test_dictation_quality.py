"""Tur 1 dikte kalitesi: yalniz AST ve sentetik metin, daemon/model baslatilmaz."""
import ast
from pathlib import Path
import re
import threading
import unittest
from unittest.mock import Mock

import numpy as np

from test_cleanup_v3 import load_cleanup
import test_dictation
import test_remote_dictation


ROOT = Path(__file__).resolve().parents[2]


def load_text_filters():
    tree = ast.parse((ROOT / 'dev/dictation.py').read_text(encoding='utf-8'))
    constants = {'_HALLUCINATION_RE', '_ARTIFACT_RE', '_ENGLISH_HALLUC_RE', '_WORD_CORRECTIONS'}
    functions = {'_clean_transcription', '_strip_known_artifacts', '_apply_word_corrections'}
    body = [node for node in tree.body
            if (isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) in constants)
            or (isinstance(node, ast.FunctionDef) and node.name in functions)]
    ns = dict(re=re)
    exec(compile(ast.Module(body=body, type_ignores=[]), 'dictation.py', 'exec'), ns)
    return ns


class TextQualityTests(unittest.TestCase):
    def setUp(self):
        self.ns = load_text_filters()
        self.clean = self.ns['_clean_transcription']
        self.text = 'Bugün önce dosyayı aç sonra testleri çalıştır ve sonucu birlikte kontrol edelim'

    def test_long_dictation_keeps_meaningful_terminal_punctuation(self):
        for suffix in ('.', '?', '!', '…', '?!', '...', ''):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.clean(self.text + suffix), self.text + suffix)

    def test_long_dictation_removes_leading_and_trailing_junk(self):
        for suffix in (',', ';', ':', ' ,;: ', '? ,;: '):
            with self.subTest(suffix=suffix):
                expected = self.text + ('?' if '?' in suffix else '')
                self.assertEqual(self.clean('...?! ,: ' + self.text + suffix), expected)

    def test_short_dictation_and_file_terminal_punctuation_policy_stays_the_same(self):
        self.assertEqual(self.clean('Merhaba dünya?'), 'Merhaba dünya?')
        self.assertEqual(self.ns['_strip_known_artifacts'](self.text + '?'), self.text)

    def test_complete_outro_is_removed_including_verb_and_punctuation(self):
        for verb in ('ederim', 'ederiz'):
            for punctuation in ('.', '?!', '…', ''):
                outro = 'İzlediğiniz için teşekkür ' + verb + punctuation
                with self.subTest(outro=outro):
                    self.assertEqual(self.ns['_ARTIFACT_RE'].sub('', outro), '')
                    self.assertEqual(self.clean(outro), '')
                    self.assertEqual(self.clean(self.text + '. ' + outro), self.text + '.')
                    self.assertEqual(self.ns['_strip_known_artifacts'](self.text + '. ' + outro), self.text)

    def test_real_thanks_outside_outro_is_kept(self):
        for text in ('Yardımın için teşekkür ederim.', 'Teşekkür ederiz.',
                     self.text + ', yardımın için teşekkür ederim.'):
            with self.subTest(text=text):
                self.assertEqual(self.clean(text), text)
                self.assertIsNone(self.ns['_ARTIFACT_RE'].search(text))

    def test_punctuation_survives_cleanup_rejection_and_oversize_fallback(self):
        ns = load_cleanup()
        text = self.clean(self.text + '?')
        ns['_cleanup_available'] = lambda: False
        self.assertEqual(ns['_cleanup_text'](text), text)
        long_text = self.clean(('ayrıntıları inceleyelim ' * 65) + '?')
        self.assertGreater(len(long_text), 1200)
        self.assertTrue(ns['_cleanup_text'](long_text).endswith('?'))
        self.assertEqual(ns['cleanup_stats'].value, {'status': 'oversize'})
        ready = threading.Event()
        ready.set()
        process = Mock()
        process.poll.return_value = None
        ns.update(_cleanup_available=lambda: True,
                  _cleanup_server=dict(ready=ready, process=process),
                  _cleanup_request=Mock(return_value=dict(content=self.text + '.')))
        self.assertEqual(ns['_cleanup_text'](text), text)
        self.assertEqual(ns['cleanup_stats'].value, {'status': 'rejected', 'reason': 'question'})


class ReasonPropagationTests(unittest.TestCase):
    def test_desktop_timing_and_diagnostic_receive_reason_only_on_rejection(self):
        fixture = test_dictation.RecordingTests()
        for status, reason in (('rejected', 'question'), ('accepted', None), ('oversize', None)):
            with self.subTest(status=status):
                fixture.setUp()
                ns = fixture.ns
                ns['cleanup_stats'].value = {'status': status}
                if reason:
                    ns['cleanup_stats'].value['reason'] = reason
                ns['sm'].force(ns['State'].PROCESSING)
                fixture.finish()
                timings = ns['_write_timing'].call_args.args[0]
                self.assertEqual(timings, ns['_finish_diagnostic'].call_args.args[0])
                self.assertEqual(timings['status'], 'pasted')
                self.assertEqual(timings.get('cleanup_reason'), reason)
                if reason is None:
                    self.assertNotIn('cleanup_reason', timings)

    def test_remote_timing_and_diagnostic_receive_reason_only_on_rejection(self):
        fixture = test_remote_dictation.RemoteDictateTests()
        for status, reason in (('rejected', 'quote'), ('accepted', None), ('not_ready', None)):
            with self.subTest(status=status):
                ns, _ = fixture.namespace(('w1:p1', None))
                ns['cleanup_stats'].value = {'status': status}
                if reason:
                    ns['cleanup_stats'].value['reason'] = reason
                ns['_remote_dictate'](np.zeros(16000, dtype=np.float32), 'w1:p1', None)
                timings = ns['_write_timing'].call_args.args[0]
                self.assertEqual(timings, ns['_finish_diagnostic'].call_args.args[0])
                self.assertEqual(timings.get('cleanup_reason'), reason)
                if reason is None:
                    self.assertNotIn('cleanup_reason', timings)


if __name__ == '__main__':
    unittest.main()
