"""F13 hareketlerini sahte saat/timer/klavye ile, gercek tus gondermeden sinar."""
import ast
from enum import Enum
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).resolve().parents[1] / "dictation.py"


class FakeTimer:
    created = None

    def __init__(self, interval, function, args=(), kwargs=None):
        self.interval, self.function, self.args = interval, function, args
        self.kwargs = kwargs or {}
        self.cancelled = False
        self.daemon = False
        self.created.append(self)

    def start(self):
        pass

    def cancel(self):
        self.cancelled = True

    def fire(self, force=False):
        if force or not self.cancelled:
            return self.function(*self.args, **self.kwargs)


class WindowsHotkeyTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        self.timers = []
        FakeTimer.created = self.timers
        key_names = ("f13", "caps_lock", "enter", "ctrl", "ctrl_l", "ctrl_r", "alt",
                     "alt_l", "alt_r", "alt_gr", "cmd", "cmd_l", "cmd_r", "shift", "shift_l", "shift_r")
        keys = SimpleNamespace(**{key: key for key in key_names})
        ns = self.ns = dict(Enum=Enum, log=Mock(), IS_MAC=False,
                            _start_diagnostic=Mock(), _finish_diagnostic=Mock(), _diagnostic_destination=Mock(),
                            threading=SimpleNamespace(Timer=FakeTimer),
                            time=SimpleNamespace(time=lambda: self.now, monotonic=lambda: self.now),
                            pynput_kb=SimpleNamespace(Key=keys), paste_controller=Mock(),
                            HOTKEY_RECORD="f13", HOTKEY_RECORD_MODIFIERS=set(), current_modifiers=set(),
                            should_quit=threading.Event(), lecture_active=False, _suppress_hotkey=False,
                            _reset_cooldown_until=0, _recording_id=1,
                            _last_hotkey_tap=0, _hotkey_press_start=0, _long_press_timer=None,
                            _long_press_fired=False, _hotkey_tap_count=0, _pending_toggle_timer=None,
                            LONG_PRESS_RESET=1.25, F13_DOUBLE_TAP_INTERVAL=.25,
                            recording_lock=threading.RLock(), _f13_lock=threading.RLock(),
                            _f13_modifiers_down=set(),
                            _f13_gesture=dict(generation=0, press_generation=0, down=False, pending=None,
                                              timer=None, hold_timer=None, press_state=None, blocked_until=0),
                            audio_lock=threading.Lock(), listen_lock=threading.Lock(),
                            audio_frames=[], listen_frames=[], sound_error=Mock(), _recording_source=None,
                            _announce_recording=Mock())
        names = {"State", "StateMachine", "_cancel_windows_hotkey", "_windows_modifier", "_send_enter", "_windows_single_tap",
                 "_discard_windows_recording", "_confirm_windows_recording",
                 "_windows_long_press", "_windows_hotkey_press", "_windows_hotkey_release", "_do_reset",
                 "_long_press_trigger", "on_press", "on_release", "_delayed_toggle"}
        for node in ast.parse(SOURCE.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(SOURCE), "exec"), ns)
        # StateMachine gercek threading.Lock kullanir; timer'lar sahte kalir.
        ns["threading"].Lock = threading.Lock
        ns["sm"] = ns["StateMachine"]()
        self.window = (10, 20, "Input", "editor.exe")
        ns["_foreground_window"] = Mock(side_effect=lambda: self.window)
        def start(provisional=False):
            ns["_recording_id"] += 1
            ns["sm"].force(ns["State"].RECORDING)
            ns["audio_frames"][:] = ["captured from first press"]
            return True
        ns["do_start_recording"] = Mock(side_effect=start)
        ns["do_stop_and_send"] = Mock(side_effect=lambda: ns["sm"].force(ns["State"].PROCESSING))

    def tap(self, gap=0):
        self.now += gap
        self.ns["on_press"]("f13")
        self.now += .02
        self.ns["on_release"]("f13")

    def timer(self, function):
        return next(t for t in reversed(self.timers) if t.function is self.ns[function])

    def no_enter(self):
        self.ns["paste_controller"].press.assert_not_called()

    def test_first_press_records_immediately_and_tone_waits_250ms(self):
        self.ns["on_press"]("f13")
        self.ns["do_start_recording"].assert_called_once_with(provisional=True)
        self.assertEqual(self.ns["sm"].state, self.ns["State"].RECORDING)
        self.ns["_announce_recording"].assert_not_called()
        self.now += .02
        self.ns["on_release"]("f13")
        timer = self.timer("_windows_single_tap")
        self.assertEqual(timer.interval, .25)
        self.now += .25
        timer.fire()
        self.ns["_announce_recording"].assert_called_once()
        self.ns["do_start_recording"].assert_called_once()
        self.no_enter()

    def test_double_short_release_discards_silent_recording_and_sends_one_enter(self):
        self.tap()
        pending = self.timer("_windows_single_tap")
        self.tap(.1)
        self.assertTrue(pending.cancelled)
        pending.fire(force=True)
        self.ns["paste_controller"].press.assert_called_once_with("enter")
        self.ns["paste_controller"].release.assert_called_once_with("enter")
        self.ns["_announce_recording"].assert_not_called()
        self.ns["do_stop_and_send"].assert_not_called()
        self.assertEqual(self.ns["sm"].state, self.ns["State"].LISTENING)
        self.assertEqual(self.ns["audio_frames"], [])

    def test_second_hold_cancels_start_and_long_hold_resets(self):
        self.tap()
        pending = self.timer("_windows_single_tap")
        self.now += .1
        self.ns["on_press"]("f13")
        pending.fire(force=True)
        self.ns["_announce_recording"].assert_not_called()
        self.timer("_windows_long_press").fire()
        self.ns["sound_error"].assert_called_once()
        self.ns["on_release"]("f13")
        pending.fire(force=True)
        self.ns["_announce_recording"].assert_not_called()
        self.no_enter()

    def test_late_timer_cannot_extend_double_tap_window(self):
        self.tap()
        old = self.timer("_windows_single_tap")
        self.tap(.4)
        old.fire(force=True)
        self.ns["_announce_recording"].assert_called_once()
        self.ns["do_stop_and_send"].assert_called_once()
        self.no_enter()

    def test_confirmation_keeps_audio_captured_before_tone(self):
        self.tap()
        self.ns["audio_frames"].append("first spoken word")
        self.timer("_windows_single_tap").fire()
        self.assertEqual(self.ns["audio_frames"], ["captured from first press", "first spoken word"])
        self.ns["_announce_recording"].assert_called_once()

    def test_long_second_press_past_double_interval_confirms_existing_recording(self):
        self.tap()
        old = self.timer("_windows_single_tap")
        self.now += .1
        self.ns["on_press"]("f13")
        self.now += .4
        self.ns["on_release"]("f13")
        old.fire(force=True)
        self.no_enter()
        self.ns["_announce_recording"].assert_called_once()
        self.timer("_windows_single_tap").fire()
        self.ns["do_start_recording"].assert_called_once()
        self.ns["_announce_recording"].assert_called_once()

    def test_delayed_hold_timer_cannot_turn_long_release_into_enter(self):
        self.tap()
        self.ns["on_press"]("f13")
        self.now += 1.3
        self.ns["on_release"]("f13")
        self.ns["sound_error"].assert_called_once()
        for timer in list(self.timers):
            timer.fire(force=True)
        self.no_enter()
        self.ns["_announce_recording"].assert_not_called()

    def test_recording_stop_is_immediate_and_following_tap_never_sends_enter(self):
        for transition in ("PROCESSING", "COOLDOWN", "LISTENING"):
            with self.subTest(transition=transition):
                self.ns["_cancel_windows_hotkey"]()
                self.ns["sm"].force(self.ns["State"].RECORDING)
                self.ns["do_stop_and_send"].reset_mock()
                self.tap()
                self.ns["do_stop_and_send"].assert_called_once()
                self.ns["sm"].force(getattr(self.ns["State"], transition))
                self.tap(.1)
                self.no_enter()
                self.assertIsNone(self.ns["_f13_gesture"]["pending"])
                self.now += 1

    def test_cooldown_allows_new_explicit_double_tap_after_stop_guard(self):
        self.ns["sm"].force(self.ns["State"].RECORDING)
        self.tap()
        self.ns["sm"].force(self.ns["State"].COOLDOWN)
        self.tap(.4)
        self.tap(.1)
        self.ns["paste_controller"].press.assert_called_once_with("enter")

    def test_single_cooldown_tap_does_not_start_recording_after_becoming_idle(self):
        self.ns["sm"].force(self.ns["State"].COOLDOWN)
        self.tap()
        self.ns["sm"].force(self.ns["State"].LISTENING)
        self.timer("_windows_single_tap").fire()
        self.ns["do_start_recording"].assert_not_called()
        self.no_enter()

    def test_processing_taps_do_not_turn_into_enter_after_becoming_idle(self):
        self.ns["sm"].force(self.ns["State"].PROCESSING)
        self.tap()
        self.ns["on_press"]("f13")
        self.ns["sm"].force(self.ns["State"].LISTENING)
        self.ns["on_release"]("f13")
        self.no_enter()
        self.ns["do_start_recording"].assert_not_called()

    def test_focus_change_between_taps_cancels_both_enter_and_recording(self):
        self.tap()
        self.window = (11, 21, "Other input", "other.exe")
        self.tap(.1)
        for timer in list(self.timers):
            timer.fire(force=True)
        self.no_enter()
        self.ns["_announce_recording"].assert_not_called()

    def test_focus_is_rechecked_immediately_before_enter(self):
        self.ns["_foreground_window"].side_effect = [self.window, self.window, (11, 21, "Other", "other.exe")]
        self.tap()
        self.tap(.1)
        self.no_enter()

    def test_missing_focus_never_sends_enter(self):
        self.window = None
        self.tap()
        self.tap(.1)
        self.no_enter()

    def test_title_change_in_same_window_does_not_cancel_double_tap(self):
        self.tap()
        self.window = (10, 20, "Edited title", "editor.exe")
        self.tap(.1)
        self.ns["paste_controller"].press.assert_called_once_with("enter")

    def test_modifier_or_unrelated_key_cancels_pending_gesture(self):
        for key in ("ctrl", "shift", "alt", "cmd", "x"):
            with self.subTest(key=key):
                self.ns["_cancel_windows_hotkey"]()
                self.ns["current_modifiers"].clear()
                self.tap()
                pending = self.timer("_windows_single_tap")
                self.ns["on_press"](key)
                pending.fire(force=True)
                self.tap(.1)
                self.no_enter()
                self.ns["_announce_recording"].assert_not_called()
                self.ns["on_release"](key)

    def test_held_modifier_prevents_gesture(self):
        self.ns["on_press"]("shift")
        self.tap()
        self.tap(.1)
        self.no_enter()
        self.ns["do_start_recording"].assert_not_called()

    def test_releasing_one_modifier_does_not_forget_other_physical_side(self):
        for left, right, modifier in (("ctrl_l", "ctrl_r", "ctrl"), ("shift_l", "shift_r", "shift")):
            with self.subTest(modifier=modifier):
                self.ns["on_press"](left)
                self.ns["on_press"](right)
                self.ns["on_release"](left)
                self.assertIn(modifier, self.ns["current_modifiers"])
                self.tap()
                self.tap(.1)
                self.no_enter()
                self.ns["do_start_recording"].assert_not_called()
                self.ns["on_release"](right)
                self.assertNotIn(modifier, self.ns["current_modifiers"])

    def test_modifier_pressed_during_reset_cooldown_still_blocks_enter_afterwards(self):
        self.ns["_reset_cooldown_until"] = self.now + .8
        self.ns["on_press"]("ctrl_l")
        self.now += 1
        self.tap()
        self.tap(.1)
        self.no_enter()
        self.ns["do_start_recording"].assert_not_called()

    def test_reset_cancels_pending_start_and_stale_hold_timer(self):
        self.tap()
        pending = self.timer("_windows_single_tap")
        hold = self.timer("_windows_long_press")
        self.ns["_do_reset"]()
        for timer in (pending, hold):
            timer.fire(force=True)
        self.ns["_announce_recording"].assert_not_called()
        self.ns["sound_error"].assert_called_once()
        self.no_enter()

    def test_cancelled_hold_callback_cannot_reset_a_new_press(self):
        self.tap()
        old_hold = self.timer("_windows_long_press")
        self.ns["on_press"]("f13")
        old_hold.fire(force=True)
        self.ns["sound_error"].assert_not_called()
        self.assertTrue(self.ns["_f13_gesture"]["down"])
        self.ns["on_release"]("f13")
        self.ns["paste_controller"].press.assert_called_once_with("enter")

    def test_shutdown_invalidates_pending_start_and_hold(self):
        self.tap()
        self.ns["should_quit"].set()
        self.ns["_cancel_windows_hotkey"]()
        for timer in list(self.timers):
            timer.fire(force=True)
        self.ns["_announce_recording"].assert_not_called()
        self.ns["sound_error"].assert_not_called()
        self.no_enter()

    def test_changed_record_id_or_state_invalidates_pending_start(self):
        self.tap()
        self.ns["_recording_id"] += 1
        self.timer("_windows_single_tap").fire()
        self.ns["_announce_recording"].assert_not_called()
        self.tap(1)
        self.ns["sm"].force(self.ns["State"].PROCESSING)
        self.timer("_windows_single_tap").fire()
        self.ns["_announce_recording"].assert_not_called()

    def test_key_repeat_and_unpaired_release_are_not_new_taps(self):
        self.ns["on_release"]("f13")
        self.ns["on_press"]("f13")
        self.ns["on_press"]("f13")
        self.assertEqual(len(self.timers), 1)
        self.ns["on_release"]("f13")
        self.ns["on_release"]("f13")
        self.timer("_windows_single_tap").fire()
        self.ns["do_start_recording"].assert_called_once()
        self.no_enter()

    def test_enter_transport_error_is_not_retried_and_key_is_released(self):
        self.ns["paste_controller"].press.side_effect = OSError("synthetic")
        self.tap()
        self.tap(.1)
        self.ns["paste_controller"].press.assert_called_once_with("enter")
        self.ns["paste_controller"].release.assert_called_once_with("enter")
        self.assertFalse(self.ns["_suppress_hotkey"])

    def test_suppressed_hotkey_cannot_send_or_start(self):
        self.ns["_suppress_hotkey"] = True
        self.tap()
        self.tap(.1)
        self.no_enter()
        self.ns["do_start_recording"].assert_not_called()

    def test_waiting_single_callback_cannot_win_after_second_press_cancels_it(self):
        self.tap()
        timer = self.timer("_windows_single_tap")
        entered = threading.Event()
        def callback():
            entered.set()
            timer.fire(force=True)
        with self.ns["recording_lock"]:
            worker = threading.Thread(target=callback)
            worker.start()
            self.assertTrue(entered.wait(2))
            self.tap(.1)
        worker.join(2)
        self.assertFalse(worker.is_alive())
        self.ns["_announce_recording"].assert_not_called()
        self.ns["paste_controller"].press.assert_called_once_with("enter")


class MacHotkeyTests(unittest.TestCase):
    def setUp(self):
        WindowsHotkeyTests.setUp(self)
        self.ns.update(IS_MAC=True, HOTKEY_RECORD="caps_lock", DOUBLE_TAP_INTERVAL=.4,
                       __name__="mac_test_fixture", toggle_recording=Mock(),
                       sys=SimpleNamespace(modules={"mac_test_fixture": SimpleNamespace(DOUBLE_TAP_INTERVAL=.4)}))
        self.ns["threading"].Thread = lambda target, daemon: SimpleNamespace(start=target)

    def tap(self):
        self.now += .1
        self.ns["on_press"]("caps_lock")
        self.ns["on_release"]("caps_lock")

    def test_idle_capslock_double_tap_toggles_without_enter(self):
        self.tap()
        self.ns["toggle_recording"].assert_not_called()
        self.tap()
        self.ns["toggle_recording"].assert_called_once()
        self.ns["paste_controller"].press.assert_not_called()
        self.assertEqual(self.timers, [])

    def test_recording_capslock_double_tap_keeps_existing_delay(self):
        self.ns["sm"].force(self.ns["State"].RECORDING)
        self.tap()
        self.tap()
        self.ns["toggle_recording"].assert_not_called()
        self.assertEqual(self.timers[-1].interval, .4)
        self.timers[-1].fire()
        self.ns["toggle_recording"].assert_called_once()
        self.ns["paste_controller"].press.assert_not_called()

    def test_recording_capslock_triple_tap_resets_and_cancels_toggle(self):
        self.ns["sm"].force(self.ns["State"].RECORDING)
        self.tap()
        self.tap()
        timer = self.timers[-1]
        self.tap()
        self.assertTrue(timer.cancelled)
        self.ns["sound_error"].assert_called_once()
        self.ns["toggle_recording"].assert_not_called()
        self.ns["paste_controller"].press.assert_not_called()


if __name__ == "__main__":
    unittest.main()
