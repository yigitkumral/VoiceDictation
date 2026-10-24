"""Mac trackpad ve ses: donanim gerektirmeyen yasam dongusu/hata testleri."""
import logging
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from dev.mac_trackpad import Trackpad
from test_dictation import load


class MacIntegrationTests(unittest.TestCase):
    def test_native_callback_dispatch_disable_and_close(self):
        lib = SimpleNamespace(**{name: Mock() for name in (
            'vd_trackpad_start', 'vd_trackpad_enable', 'vd_trackpad_stop', 'vd_trackpad_counts', 'vd_trackpad_rejections')})
        lib.vd_trackpad_start.return_value = 0
        event = threading.Event()
        on_tap = Mock(side_effect=event.set)
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[2] / '.local') as tmp:
            path = Path(tmp) / 'synthetic.dylib'; path.touch()
            with patch('dev.mac_trackpad.ctypes.CDLL', return_value=lib):
                trackpad = Trackpad(path, on_tap, logging.getLogger('test'))
                try:
                    self.assertTrue(trackpad.enabled)
                    callback = lib.vd_trackpad_start.call_args.args[0]
                    callback()
                    self.assertTrue(event.wait(1))
                    trackpad.set_enabled(False)
                    on_tap.reset_mock()
                    callback()
                    self.assertTrue(trackpad._events.empty())
                    on_tap.assert_not_called()
                    trackpad.close(); trackpad.close()
                    lib.vd_trackpad_stop.assert_called_once()
                    self.assertFalse(trackpad._worker.is_alive())
                finally:
                    trackpad.close()

    def test_missing_library_does_not_break_dictation(self):
        with patch('dev.mac_trackpad.ctypes.CDLL') as loader:
            trackpad = Trackpad('/does-not-exist-vd-test.dylib', Mock(), Mock())
            self.assertFalse(trackpad.ready)
            self.assertEqual(trackpad.counts(), (0, 0))
            trackpad.close()
            loader.assert_not_called()

    def test_mac_sound_uses_memory_and_reports_failure(self):
        ns = load('_play_wav')
        ns.update(IS_WIN=False, IS_MAC=True, log=Mock())
        sound = Mock()
        sound.play.return_value = True
        sound.isPlaying.return_value = False
        factory = Mock(); factory.alloc.return_value.initWithData_.return_value = sound
        data = Mock()
        with patch.dict('sys.modules', {'AppKit': SimpleNamespace(NSSound=factory),
                                        'Foundation': SimpleNamespace(NSData=data, NSDate=Mock(), NSRunLoop=Mock())}):
            ns['_play_wav'](b'synthetic-wav')
            data.dataWithBytes_length_.assert_called_once_with(b'synthetic-wav', 13)
            sound.play.assert_called_once()
            ns['log'].warning.assert_not_called()
            sound.play.return_value = False
            ns['_play_wav'](b'synthetic-wav')
            ns['log'].warning.assert_called_once()
