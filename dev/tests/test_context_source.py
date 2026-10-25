"""Baglam cache ve SSH exporter yalniz sentetik oturum/transport ile sinanir."""
import base64
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dev import context_source as source


class ContextCacheTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.selection = dict(machine=None, pane_id="pane-a", terminal_id="term-a")
        self.session = dict(source="synthetic", agent="claude", kind="id", value="session-a")
        self.pane = dict(id="pane-a", terminal_id="term-a", agent="claude", agent_session=self.session)
        self.api = Mock(side_effect=lambda args, machine: dict(pane=copy.deepcopy(self.pane)))
        self.bridge = SimpleNamespace(__file__=str(Path(source.__file__)),
            resolve_session=Mock(return_value=dict(provider="claude", path="/synthetic/exact-session.jsonl", session_id="session-a")),
            read_conversation=Mock(return_value=dict(messages=[dict(role="user", text="Atelier Widget açalım."),
                                                              dict(role="assistant", text="Widget hazır.")], words=5)),
            build_hints=Mock(return_value="Atelier, Widget"))
        self.profiles = dict(mac=dict(id="mac", label="Mac", target="synthetic@host.test", session="remote-session", enabled=True, selected=False))
        self.run = Mock()
        self.cache = source.ContextCache(self.api, lambda: self.profiles, run=self.run,
                                         bridge=self.bridge, clock=lambda: self.now)

    def identity_selection(self):
        return dict(self.selection, agent=self.pane["agent"], agent_session=copy.deepcopy(self.pane["agent_session"]))

    def test_request_does_not_perform_io_and_snapshot_is_immutable(self):
        self.assertEqual(self.cache.request(self.selection)["status"], "missing")
        self.api.assert_not_called()
        self.bridge.resolve_session.assert_not_called()
        result = self.cache.refresh(self.selection)
        self.assertEqual(result["status"], "conversation")
        self.assertEqual(result["words"], 5)
        self.assertEqual(result["hotwords"], "Atelier, Widget")
        self.assertEqual(result["text"], "Atelier Widget açalım.\nWidget hazır.")
        self.assertNotIn("user:", result["text"])
        self.assertNotIn("assistant:", result["text"])
        with self.assertRaises(TypeError):
            result["text"] = "mutated"
        self.assertEqual(self.cache.request(self.identity_selection())["text"], result["text"])
        self.assertEqual(self.api.call_args_list, [call(["pane", "get", "pane-a"], None)] * 2)
        self.bridge.resolve_session.assert_called_once_with("claude", self.session)
        self.bridge.read_conversation.assert_called_once_with("/synthetic/exact-session.jsonl", "session-a", "claude", max_words=300)

    def test_cache_expires_at_five_seconds_without_refresh_io(self):
        self.cache.refresh(self.selection)
        count = self.api.call_count
        self.now += 4.99
        self.assertEqual(self.cache.request(self.selection)["status"], "conversation")
        self.now += .02
        self.assertEqual(self.cache.request(self.selection)["status"], "expired")
        self.assertEqual(self.api.call_count, count)

    def test_same_pane_new_terminal_or_agent_session_invalidates_immediately(self):
        self.cache.refresh(self.selection)
        changed = dict(self.selection, terminal_id="replacement")
        self.assertEqual(self.cache.request(changed)["text"], "")
        self.cache.request(self.selection)
        self.cache.refresh(self.selection)
        changed = self.identity_selection()
        changed["agent_session"]["source"] = "changed-source"
        self.assertEqual(self.cache.request(changed)["text"], "")

    def test_changed_before_after_identity_discards_conversation(self):
        for change in (dict(id="other-pane"), dict(terminal_id="other-terminal"), dict(agent="codex"),
                       dict(agent_session=dict(self.session, value="other-session")),
                       dict(agent_session=dict(self.session, source="other-source"))):
            with self.subTest(change=change):
                self.cache.clear()
                self.cache.request(self.selection)
                self.api.side_effect = [dict(pane=self.pane), dict(pane=dict(self.pane, **change))]
                self.assertEqual(self.cache.refresh(self.selection)["text"], "")
                self.assertEqual(self.cache.request(self.selection)["text"], "")

    def test_wrong_initial_terminal_or_unresolved_identity_never_reads_session(self):
        for change in (dict(terminal_id="other-terminal"), dict(agent_session=None),
                       dict(agent_session=dict(self.session, kind="unknown"))):
            with self.subTest(change=change):
                self.api.side_effect = lambda *args: dict(pane=dict(self.pane, **change))
                self.assertEqual(self.cache.refresh(self.selection)["text"], "")
                self.bridge.resolve_session.assert_not_called()

    def test_invalid_explicit_identity_revokes_existing_snapshot(self):
        self.cache.refresh(self.selection)
        changed = dict(self.selection, agent="claude", agent_session=None)
        self.assertEqual(self.cache.request(changed)["text"], "")
        self.assertEqual(self.cache.request(self.selection)["text"], "")

    def test_missing_exact_session_never_falls_back_to_another_file(self):
        self.bridge.resolve_session.return_value = None
        self.assertEqual(self.cache.refresh(self.selection)["status"], "missing")
        self.bridge.read_conversation.assert_not_called()
        self.assertEqual(self.api.call_count, 2)

    def test_limit_keeps_latest_three_hundred_words(self):
        self.bridge.read_conversation.return_value = dict(messages=[dict(role="user", text=" ".join(f"w{i}" for i in range(400)))], words=400)
        result = self.cache.refresh(self.selection)
        self.assertEqual(result["words"], 300)
        self.assertEqual(result["text"].split()[0], "w100")
        self.assertEqual(result["text"].split()[-1], "w399")

    def test_failed_refresh_drops_old_content_without_exposing_error_text(self):
        self.cache.refresh(self.selection)
        self.bridge.read_conversation.side_effect = RuntimeError("PRIVATE_TRANSCRIPT")
        result = self.cache.refresh(self.selection)
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("PRIVATE", str(dict(result)))
        self.assertEqual(result["text"], "")

    def test_clear_and_source_change_drop_inflight_results(self):
        for revoke in (lambda: self.cache.clear(), lambda: self.cache.request(dict(self.selection, pane_id="new-pane"))):
            with self.subTest(revoke=revoke):
                self.cache.clear()
                self.cache.request(self.selection)
                entered, release = threading.Event(), threading.Event()
                original = self.bridge.read_conversation.return_value
                def read(*args, **kwargs):
                    entered.set()
                    release.wait(2)
                    return original
                self.bridge.read_conversation.side_effect = read
                result = []
                worker = threading.Thread(target=lambda: result.append(self.cache.refresh(self.selection)))
                worker.start()
                try:
                    self.assertTrue(entered.wait(2))
                    before = time.monotonic()
                    self.assertEqual(self.cache.request(self.selection)["text"], "")
                    self.assertLess(time.monotonic() - before, .2)
                    revoke()
                finally:
                    release.set()
                    worker.join(2)
                self.assertFalse(worker.is_alive())
                self.assertEqual(result[0]["text"], "")

    def test_total_timeout_drops_late_worker_result(self):
        entered, release = threading.Event(), threading.Event()
        def read(*args, **kwargs):
            entered.set()
            release.wait(2)
            return dict(messages=[dict(role="user", text="Late private words")], words=3)
        self.bridge.read_conversation.side_effect = read
        try:
            with patch.object(source, "REFRESH_TIMEOUT", .05):
                result = self.cache.refresh(self.selection)
            self.assertTrue(entered.is_set())
            self.assertEqual(result["status"], "timeout")
            release.set()
            self.assertEqual(self.cache.request(self.selection)["text"], "")
        finally:
            release.set()

    def test_close_prevents_later_request_or_refresh_reads(self):
        self.cache.refresh(self.selection)
        self.cache.close()
        count = self.api.call_count
        self.assertEqual(self.cache.request(self.selection)["text"], "")
        self.assertEqual(self.cache.refresh(self.selection)["text"], "")
        self.assertEqual(self.api.call_count, count)

    def remote(self, **changes):
        self.selection["machine"] = "mac"
        response = dict(pane=self.pane, messages=self.bridge.read_conversation.return_value["messages"], words=5)
        response.update(changes)
        self.run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps(response))
        return self.cache.refresh(self.selection)

    def test_remote_uses_exact_profile_safe_base64_and_portable_stdin(self):
        self.assertEqual(self.remote()["status"], "conversation")
        args = self.run.call_args.args[0]
        self.assertEqual(args[:8], ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=2", "--", "synthetic@host.test"])
        self.assertTrue(args[8].startswith("python3 - "))
        request = json.loads(base64.b64decode(args[8].split()[-1]))
        self.assertEqual(request, dict(session="remote-session", pane_id="pane-a", terminal_id="term-a"))
        options = self.run.call_args.kwargs
        self.assertEqual(options["timeout"], 3)
        self.assertFalse(options.get("shell", False))
        self.assertIn('executable, "--session", request["session"]', options["input"])
        self.api.assert_not_called()

    def test_remote_unsafe_or_unknown_profile_never_starts_ssh(self):
        for target in ("-oProxyCommand=evil", "host;echo leak", "user@host\nnext", "host$(command)"):
            with self.subTest(target=target):
                self.profiles["mac"]["target"] = target
                self.assertEqual(self.remote()["text"], "")
                self.run.assert_not_called()
        self.profiles["mac"]["target"] = "synthetic@host.test"
        self.profiles["mac"]["enabled"] = False
        self.assertEqual(self.remote()["text"], "")
        self.run.assert_not_called()
        self.profiles = dict(other=self.profiles["mac"])
        self.assertEqual(self.remote()["text"], "")
        self.run.assert_not_called()

    def test_remote_invalid_or_oversize_output_never_enters_cache(self):
        self.selection["machine"] = "mac"
        for output in ("not JSON", "x" * (32768 + 1), '{"status":"unavailable"}',
                       json.dumps(dict(pane=self.pane, messages=[], words=301))):
            with self.subTest(output_length=len(output)):
                self.run.return_value = SimpleNamespace(returncode=0, stdout=output)
                self.assertEqual(self.cache.refresh(self.selection)["text"], "")

    def test_remote_route_change_during_read_invalidates_result(self):
        self.selection["machine"] = "mac"
        def run(*args, **kwargs):
            self.profiles["mac"]["session"] = "replaced-session"
            return SimpleNamespace(returncode=0, stdout=json.dumps(dict(pane=self.pane, messages=[], words=0)))
        self.run.side_effect = run
        self.assertEqual(self.cache.refresh(self.selection)["status"], "unavailable")


class RemoteExporterTests(unittest.TestCase):
    def execute(self, before, after=None, executable="/synthetic/bin/herdr", fallback_exists=False, existing=None):
        request = dict(session="exact-remote-session", pane_id="pane-a", terminal_id="term-a")
        encoded = base64.b64encode(json.dumps(request).encode()).decode()
        ns = dict(resolve_session=Mock(return_value=dict(path="synthetic", session_id="session-a", provider="claude")),
                  read_conversation=Mock(return_value=dict(messages=[dict(role="user", text="Synthetic words")], words=2)))
        def result(pane):
            return SimpleNamespace(returncode=0, stdout=json.dumps(dict(result=dict(pane=pane))))
        with patch.object(sys, "argv", ["-", encoded]), \
                patch.object(shutil, "which", return_value=executable), \
                patch.object(os.path, "expanduser", **(dict(side_effect=lambda p: p) if existing else
                                                     dict(return_value="/synthetic/home/.local/bin/herdr"))), \
                patch.object(os.path, "isfile", **(dict(side_effect=lambda p: p == existing) if existing else
                                                 dict(return_value=fallback_exists))), \
                patch.object(os, "access", return_value=fallback_exists), \
                patch.object(subprocess, "run", side_effect=[result(before), result(after or before)]) as run:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(source._REMOTE_EXPORT, ns)
        return json.loads(output.getvalue()), ns, run

    def test_remote_exporter_verifies_both_panes_with_exact_session(self):
        pane = dict(id="pane-a", terminal_id="term-a", agent="claude",
                    agent_session=dict(agent="claude", kind="id", value="session-a", source="synthetic"))
        result, ns, run = self.execute(pane)
        self.assertEqual(result["words"], 2)
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(c.args[0] == ["/synthetic/bin/herdr", "--session", "exact-remote-session", "pane", "get", "pane-a"] for c in run.call_args_list))
        ns["resolve_session"].assert_called_once_with("claude", pane["agent_session"])

    def test_remote_exporter_drops_changed_session_without_raw_error(self):
        pane = dict(id="pane-a", terminal_id="term-a", agent="claude",
                    agent_session=dict(agent="claude", kind="id", value="session-a"))
        after = dict(pane, agent_session=dict(pane["agent_session"], value="other-session"))
        result, _, _ = self.execute(pane, after)
        self.assertEqual(result, dict(status="unavailable"))

    def test_remote_exporter_falls_back_to_known_user_binary(self):
        pane = dict(id="pane-a", terminal_id="term-a", agent="claude",
                    agent_session=dict(agent="claude", kind="id", value="session-a"))
        result, _, run = self.execute(pane, executable=None, fallback_exists=True)
        self.assertEqual(result["words"], 2)
        self.assertTrue(all(c.args[0][0] == "/synthetic/home/.local/bin/herdr" for c in run.call_args_list))

    def test_remote_exporter_finds_homebrew_binary_outside_ssh_path(self):
        # macOS etkilesimsiz SSH PATH'i /usr/bin:/bin; Homebrew herdr ancak acik yolla bulunur.
        pane = dict(id="pane-a", terminal_id="term-a", agent="claude",
                    agent_session=dict(agent="claude", kind="id", value="session-a"))
        result, _, run = self.execute(pane, executable=None, fallback_exists=True, existing="/opt/homebrew/bin/herdr")
        self.assertEqual(result["words"], 2)
        self.assertTrue(all(c.args[0][0] == "/opt/homebrew/bin/herdr" for c in run.call_args_list))

    def test_remote_exporter_missing_binary_does_not_read_any_session(self):
        result, ns, run = self.execute({}, executable=None)
        self.assertEqual(result, dict(status="unavailable"))
        run.assert_not_called()
        ns["resolve_session"].assert_not_called()

    def test_remote_exporter_removes_inherited_routing_environment(self):
        pane = dict(id="pane-a", terminal_id="term-a", agent="claude",
                    agent_session=dict(agent="claude", kind="id", value="session-a"))
        with patch.dict(os.environ, {"HERDR_SESSION": "wrong-session", "HERDR_SOCKET_PATH": "wrong-socket"}):
            _, _, run = self.execute(pane)
        for command in run.call_args_list:
            self.assertNotIn("HERDR_SESSION", command.kwargs["env"])
            self.assertNotIn("HERDR_SOCKET_PATH", command.kwargs["env"])


if __name__ == "__main__":
    unittest.main()
