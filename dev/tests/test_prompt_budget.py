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


class PromptBudgetTests(unittest.TestCase):
    def load(self, mac=False):
        ns = dict(re=re, model=SimpleNamespace(hf_tokenizer=ByteTokenizer()), IS_MAC=mac,
                  INITIAL_PROMPT='Sabit teknik terimler.', wake_word_string='Diktasyon')
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
            self.assertTrue(hints.startswith('Qwen'))

    def test_wake_and_special_tokens_are_removed_from_both_inputs(self):
        prompt, hints = self.load()(dict(status='conversation',
            text='<|endoftext|> Diktasyon Qwen\x00 modeli', hotwords='Diktasyon, Qwen'))
        self.assertNotIn('Diktasyon', prompt + hints)
        self.assertNotIn('<|', prompt + hints)
        self.assertNotIn('\x00', prompt)

    def test_missing_conversation_keeps_static_prompt(self):
        prompt, hints = self.load()('Project')
        self.assertEqual(prompt, 'Sabit teknik terimler.')
        self.assertEqual(hints, 'Project')


if __name__ == '__main__':
    unittest.main()
