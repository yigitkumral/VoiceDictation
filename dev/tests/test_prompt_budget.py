"""Sohbet baglami STT token butcesine sigar; wake/special token tasinmaz."""
import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]


class ByteTokenizer:
    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens
        return SimpleNamespace(ids=list(text.encode('utf-8')))

    def decode(self, ids):
        return bytes(ids).decode('utf-8', errors='ignore')


class ByteListTokenizer:
    """mlx_whisper Tokenizer gibi: encode liste dondurur."""
    def encode(self, text):
        return list(text.encode('utf-8'))

    def decode(self, ids):
        return bytes(ids).decode('utf-8', errors='ignore')


class PromptBudgetTests(unittest.TestCase):
    def load(self, mac=False):
        ns = dict(re=re, model=SimpleNamespace(hf_tokenizer=ByteTokenizer()), IS_MAC=mac,
                  _mlx_tokenizer=lambda: ByteListTokenizer(),
                  INITIAL_PROMPT='Sabit teknik terimler.', wake_word_string='Diktasyon',
                  PERSONAL_HINTS='iFonzo')
        node = next(n for n in ast.parse((ROOT/'dev/dictation.py').read_text(encoding='utf-8')).body
                    if isinstance(n, ast.FunctionDef) and n.name == '_whisper_context')
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'dictation.py', 'exec'), ns)
        return ns['_whisper_context']

    def test_conversation_recent_tail_and_hints_share_bounded_budget(self):
        for mac in (False, True):
            prompt, hints = self.load(mac)(dict(status='conversation',
                text='eski ' * 300 + 'Yeni konu Qwen GPU.', hotwords='Qwen, CUDA, GPU, ' * 30))
            self.assertLessEqual(len(prompt.encode()), 160)
            self.assertLessEqual(len(hints.encode()), 40)
            self.assertTrue(prompt.endswith('Yeni konu Qwen GPU.'))
            self.assertTrue(hints.startswith('iFonzo, Qwen'))

    def test_wake_and_special_tokens_are_removed_from_both_inputs(self):
        prompt, hints = self.load()(dict(status='conversation',
            text='<|endoftext|> Diktasyon Qwen\x00 modeli', hotwords='Diktasyon, Qwen'))
        self.assertNotIn('Diktasyon', prompt + hints)
        self.assertNotIn('<|', prompt + hints)
        self.assertNotIn('\x00', prompt)

    def test_conversation_hints_always_carry_personal_names_once(self):
        load = self.load()
        self.assertEqual(load(dict(status='conversation', text='Merhaba', hotwords=''))[1], 'iFonzo')
        self.assertEqual(load(dict(status='conversation', text='Merhaba', hotwords='Herdr, iFonzo'))[1], 'Herdr, iFonzo')

    def test_missing_conversation_keeps_static_prompt(self):
        prompt, hints = self.load()('Project')
        self.assertEqual(prompt, 'Sabit teknik terimler.')
        self.assertEqual(hints, 'Project')


    def test_full_static_prompt_fits_real_whisper_token_budget(self):
        try:
            from mlx_whisper.tokenizer import get_tokenizer
        except ImportError:
            self.skipTest('mlx_whisper yok')
        tree = ast.parse((ROOT/'dev/dictation.py').read_text(encoding='utf-8'))
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and getattr(n.targets[0], 'id', None) == 'INITIAL_PROMPT')
        prompt = ast.literal_eval(node.value)
        tokenizer = get_tokenizer(multilingual=True, language='tr', task='transcribe')
        self.assertLessEqual(len(tokenizer.encode(prompt)), 160)
        self.assertIn('Herdr', prompt)
        self.assertIn('iFonzo', prompt)


class WordCorrectionTests(unittest.TestCase):
    def test_mac_diagnostic_misspellings_are_corrected_without_touching_real_words(self):
        tree = ast.parse((ROOT/'dev/dictation.py').read_text(encoding='utf-8'))
        body = [n for n in tree.body if (isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', None) == '_WORD_CORRECTIONS')
                or (isinstance(n, ast.FunctionDef) and n.name == '_apply_word_corrections')]
        ns = dict(re=re)
        exec(compile(ast.Module(body=body, type_ignores=[]), 'dictation.py', 'exec'), ns)
        fix = ns['_apply_word_corrections']
        self.assertEqual(fix("Herder'ı açtım, Herder tabi"), "Herdr'ı açtım, Herdr tabi")
        self.assertEqual(fix('Voice Daktation ve Voice Ductation'), 'VoiceDictation ve VoiceDictation')
        self.assertEqual(fix("B-MED'de shard"), "BMAD'de shard")
        self.assertEqual(fix('Tadayıcıyı başlat, tadayıcı'), 'Tarayıcıyı başlat, tarayıcı')
        self.assertEqual(fix('seninle sohbaya devam'), 'seninle sohbete devam')
        self.assertEqual(fix("iPhonezo'yu nasıl yazacak, iPhone zo ve ifonso"),
                         "iFonzo'yu nasıl yazacak, iFonzo ve iFonzo")
        self.assertEqual(fix('Ayfonzo, i-fonzo, iFonzo'), 'iFonzo, iFonzo, iFonzo')
        self.assertEqual(fix("Iphones o, iPhones o'yu, İfonzo"), "iFonzo, iFonzo'yu, iFonzo")
        self.assertEqual(fix('iPhonezlu, iPhonezu, iFonzu'), 'iFonzo, iFonzo, iFonzo')
        for word in ('şart değil', 'Tarayıcı', 'herhalde', 'VoiceDictation', 'iPhone', 'iPhone so', 'iPhone zor', 'iPhones oldu'):
            self.assertEqual(fix(word), word)


if __name__ == '__main__':
    unittest.main()
