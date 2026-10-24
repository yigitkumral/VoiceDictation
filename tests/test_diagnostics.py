"""Tani kayitlari yalniz sentetik icerikle sinanir."""
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from dev.diagnostics import DiagnosticWriter
from test_dictation import load
from test_cleanup_v3 import load_cleanup

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticTests(unittest.TestCase):
    def test_writer_keeps_content_and_build_and_survives_bad_record(self):
        with tempfile.TemporaryDirectory(dir=ROOT / '.local') as temp:
            writer = DiagnosticWriter(temp, [ROOT / 'dev/dictation.py'])
            self.assertTrue(writer.submit({'bad': object()}))
            self.assertTrue(writer.submit({'trace_id': 'synthetic', 'text': 'Example input'}))
            writer.close()
            rows = [json.loads(line) for p in Path(temp).glob('*.jsonl') for line in p.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['text'], 'Example input')
            self.assertEqual(rows[0]['build'], writer.build)
            self.assertEqual(writer.errors, 1)
            self.assertFalse(writer.submit({}))

    def test_source_destination_and_threads_are_not_confused(self):
        ns = load('_start_diagnostic', '_diagnostic_event', '_diagnostic_window',
                  '_diagnostic_destination', '_finish_diagnostic')
        writer = Mock(dropped=0, errors=0)
        ns.update(diagnostic_state=threading.local(), diagnostic_writer=writer,
                  herdr_targets=[dict(title='Source', pane_id='pane-1')],
                  _foreground_window=lambda: (3, 4, 'Destination', 'editor'))
        trace_id = ns['_start_diagnostic'](1, {'window': (1, 2, 'Source', 'terminal'),
                                             'herdr': {'pane_id': 'pane-1'}})
        thread = threading.Thread(target=lambda: ns['_diagnostic_event']('foreign', text='must not leak'))
        thread.start(); thread.join()
        ns['_diagnostic_destination']('paste_before')
        ns['_finish_diagnostic']({'status': 'pasted', 'trace_id': trace_id})
        row = writer.submit.call_args.args[0]
        self.assertEqual(row['source']['selection']['pane_id'], 'pane-1')
        self.assertEqual(row['stages']['paste_before']['window']['title'], 'Destination')
        self.assertIsNone(row['stages']['paste_before']['pane'])
        self.assertNotIn('foreign', row['stages'])
        self.assertIsNone(ns['diagnostic_state'].trace)

    def test_logged_whisper_prompt_is_the_one_sent_to_model(self):
        ns = load('quick_transcribe', '_whisper_context', '_diagnostic_event')
        state = threading.local(); state.trace = {'stages': {}}
        ns.update(diagnostic_state=state, _has_speech=lambda audio: True,
                  transcribe_lock=threading.Lock(), IS_MAC=False, INITIAL_PROMPT='fixed',
                  model=Mock(), _clean_transcription=lambda t: t + '.',
                  _strip_known_artifacts=lambda t: t, _dedupe_repeated_segments=lambda t, **kw: t)
        ns['model'].transcribe.return_value = ([SimpleNamespace(text='Synthetic text')], None)
        ns['quick_transcribe']([], context={'status': 'conversation', 'text': 'Example context', 'hotwords': 'AtlasBridge'})
        sent = ns['model'].transcribe.call_args.kwargs
        logged = state.trace['stages']
        self.assertEqual(sent['initial_prompt'], logged['whisper_request']['initial_prompt'])
        self.assertEqual(sent['hotwords'], logged['whisper_request']['hotwords'])
        self.assertEqual(logged['whisper_response']['raw_text'], 'Synthetic text')
        self.assertEqual(logged['whisper_filtered']['text'], 'Synthetic text.')

    def test_comparison_separates_build_and_machine_and_context(self):
        spec = importlib.util.spec_from_file_location('compare', ROOT / 'scripts/compare-dictation.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        rows = []
        for machine, build in [('local', 'v1'), ('remote', 'v1'), ('local', 'v2')]:
            rows.append(dict(build=build, source={'selection': {'machine': machine, 'pane_id': 'p1'}},
                             stages={'context': {'kind': 'general', 'reason': {'status': 'missing'}}},
                             timings={'total_ms': 100, 'status': 'pasted'}))
        self.assertEqual(len(module.summarize(rows)), 3)
        for device, client_id in [('iphone', 'device-a'), ('ipad', 'device-b'), ('iphone', 'device-c')]:
            rows.append(dict(build='v1', source={'selection': {'machine': 'local', 'pane_id': 'p1'},
                'client': {'channel': 'vault', 'device_type': device, 'client_id': client_id}},
                stages={'context': {'kind': 'general', 'reason': {'status': 'missing'}}},
                timings={'total_ms': 200, 'status': 'returned'}))
        groups = module.summarize(rows)
        self.assertEqual(len(groups), 6)
        self.assertEqual({g['client_id'] for g in groups if g['channel'] == 'vault'},
                         {'device-a', 'device-b', 'device-c'})

    def test_qwen_log_matches_request_and_keeps_rejected_candidate(self):
        diag = load('_diagnostic_event')
        state = threading.local(); state.trace = {'stages': {}}
        diag['diagnostic_state'] = state
        ns = load_cleanup()
        ready = threading.Event(); ready.set()
        process = Mock(); process.poll.return_value = None
        ns.update(_cleanup_available=lambda: True, _diagnostic_event=diag['_diagnostic_event'],
                  _cleanup_server={'ready': ready, 'process': process, 'backend': 'CUDA0'},
                  _cleanup_request=Mock(return_value={'content': 'Unrelated output', 'timings': {}}))
        self.assertEqual(ns['_cleanup_text']('Original sentence'), 'Original sentence')
        sent = ns['_cleanup_request'].call_args.args[2]
        self.assertEqual(state.trace['stages']['qwen_request']['prompt'], sent['prompt'])
        self.assertEqual(state.trace['stages']['qwen_response']['text'], 'Unrelated output')
        self.assertEqual(ns['cleanup_stats'].value['status'], 'rejected')


if __name__ == '__main__':
    unittest.main()
