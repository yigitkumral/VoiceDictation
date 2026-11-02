"""Daemon sinyal kapanisi: gercek surec ve gercek sinyal; model yerine sahte alt surec."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


SOURCE = Path(__file__).resolve().parents[2] / "dev/dictation.py"
TEMP_DIR = Path(__file__).resolve().parents[2] / ".local" / "test-tmp"

# Baslatici nohup ve & ile SIGHUP/SIGINT'i yok sayili devreder; harness ayni kosulda baslar.
HARNESS = r"""
import ast, logging, os, signal, subprocess, sys, threading, time
source, pid_file, mode = sys.argv[1:4]
names = {"_close_owned_resources", "_exit_on_signal", "_install_exit_signals", "_stop_cleanup_server",
         "_terminate_cleanup_process", "_remove_daemon_pid"}
child = subprocess.Popen(["sleep", "300"])
worker = threading.Thread(target=lambda: None)
worker.start()
ns = dict(os=os, signal=signal, subprocess=subprocess, threading=threading, logging=logging, time=time,
          log=logging.getLogger("harness"), IS_WIN=False, should_quit=threading.Event(),
          _signal_exit=threading.Event(), mac_trackpad=None,
          diagnostic_writer=None, _PID_FILE=pid_file, _cleanup_server_lock=threading.RLock(),
          _cleanup_server=dict(stop=threading.Event(), ready=threading.Event(), process=child, thread=worker),
          EXIT_SIGNAL_TIMEOUT=0.2 if mode == "hang" else 15)
for node in ast.parse(open(source, encoding="utf-8").read()).body:
    if isinstance(node, ast.FunctionDef) and node.name in names:
        exec(compile(ast.Module(body=[node], type_ignores=[]), source, "exec"), ns)
if mode == "hang":
    ns["_close_owned_resources"] = lambda: time.sleep(60)
ns["_install_exit_signals"]()
open(pid_file, "w").write(str(os.getpid()))
print(child.pid, flush=True)
threading.Event().wait()
"""


def ignore_like_launcher():
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


@unittest.skipIf(sys.platform == "win32", "POSIX sinyalleri")
class ExitSignalTests(unittest.TestCase):
    def start(self, mode):
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.TemporaryDirectory(dir=TEMP_DIR)
        self.addCleanup(tmp.cleanup)
        self.pid_file = Path(tmp.name) / "dictation.pid"
        process = subprocess.Popen([sys.executable, "-B", "-c", HARNESS, str(SOURCE), str(self.pid_file), mode],
                                   stdout=subprocess.PIPE, text=True, preexec_fn=ignore_like_launcher)
        self.addCleanup(process.stdout.close)
        child = int(process.stdout.readline())
        def reap():
            for pid in (process.pid, child):
                if alive(pid):
                    os.kill(pid, signal.SIGKILL)
            process.wait()
        self.addCleanup(reap)
        return process, child

    def test_each_signal_stops_child_and_removes_pid(self):
        for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            with self.subTest(signal=signum.name):
                process, child = self.start("normal")
                self.assertTrue(alive(child))
                self.assertTrue(self.pid_file.exists())
                process.send_signal(signum)
                self.assertEqual(process.wait(timeout=10), 128 + signum)
                self.assertFalse(alive(child))
                self.assertFalse(self.pid_file.exists())

    def test_hung_close_still_exits_after_timeout(self):
        process, _child = self.start("hang")
        started = time.monotonic()
        process.send_signal(signal.SIGTERM)
        self.assertEqual(process.wait(timeout=10), 128 + signal.SIGTERM)
        self.assertLess(time.monotonic() - started, 5)

    def test_menubar_cannot_race_signal_cleanup(self):
        # Ikisi de gercek Mac kabulunde bulundu: zamanlayici Cocoa'yi temizlikten once sonlandiriyor,
        # rumps SIGINT'i kendi isleyicisine aliyordu. GUI test ortaminda acilamadigi icin kaynak denetlenir.
        text = SOURCE.read_text(encoding="utf-8")
        self.assertIn("if should_quit.is_set() and not _signal_exit.is_set():", text)
        self.assertIn("AppHelper.installMachInterrupt = lambda: None", text)
        self.assertLess(text.index("_signal_exit.set()"), text.index("should_quit.set()\n    failsafe"))


if __name__ == "__main__":
    unittest.main()
