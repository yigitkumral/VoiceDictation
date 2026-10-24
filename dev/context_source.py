"""Acikca secilen Herdr oturumundan salt okunur, RAM'de tutulan dikte baglami."""
import base64
import copy
import importlib
import json
from pathlib import Path
import re
import subprocess
import threading
import time
from types import MappingProxyType


MAX_WORDS = 300
MAX_OUTPUT_BYTES = 32 * 1024
REFRESH_TIMEOUT = 3.0
_SAFE_TARGET = re.compile(r"(?:[A-Za-z0-9_][A-Za-z0-9_.-]*@)?(?:[A-Za-z0-9][A-Za-z0-9_.-]*|\[[0-9A-Fa-f:]+\])\Z")


def _empty(status="missing"):
    return dict(text="", hotwords="", words=0, status=status)


def _base(selection):
    if not isinstance(selection, dict):
        return None
    pane, terminal = selection.get("pane_id"), selection.get("terminal_id")
    machine = selection.get("machine")
    if (not isinstance(pane, str) or not pane or not isinstance(terminal, str) or not terminal
            or (machine is not None and (not isinstance(machine, str) or not machine))):
        return None
    if any(value.startswith("-") or len(value) > 512 or any(ord(c) < 32 for c in value)
           for value in (pane, terminal)):
        return None
    return machine, pane, terminal


def _identity(pane):
    session = pane.get("agent_session")
    if (not isinstance(session, dict) or session.get("kind") not in {"id", "path"}
            or not isinstance(session.get("value"), str) or not session["value"]
            or session.get("agent") not in {"claude", "codex"}
            or pane.get("agent") != session["agent"]):
        return None
    try:
        return pane.get("agent"), json.dumps(session, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return None


def _matching_pane(pane, selection):
    return (isinstance(pane, dict) and pane.get("id", pane.get("pane_id")) == selection["pane_id"]
            and pane.get("terminal_id") == selection["terminal_id"] and _identity(pane) is not None)


def _snapshot(messages, bridge):
    """Exporter/bridge sonucunu yeniden sinirla; hata metni veya kontrol dizisi tasima."""
    if not isinstance(messages, list):
        raise ValueError("invalid messages")
    clean = []
    remaining = MAX_WORDS
    for item in reversed(messages):
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}:
            continue
        text = item.get("text")
        if not isinstance(text, str):
            continue
        text = "".join(c for c in text if c in "\n\t" or ord(c) >= 32 and not 127 <= ord(c) <= 159)
        words = text.split()
        if not words:
            continue
        take = min(remaining, len(words))
        clean.append(dict(role=item["role"], text=" ".join(words[-take:])))
        remaining -= take
        if not remaining:
            break
    clean.reverse()
    if not clean:
        return _empty()
    text = "\n".join(item["text"] for item in clean)
    hotwords = bridge.build_hints(clean, max_terms=24)
    if not isinstance(hotwords, str):
        raise ValueError("invalid hints")
    result = dict(text=text, hotwords=hotwords[:240], words=MAX_WORDS - remaining, status="conversation")
    if len(json.dumps(result, ensure_ascii=False).encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValueError("oversize context")
    return result


# Paket/kurulum veya uzak dosya yazimi yok; ayni dogrulayici SSH stdin'inde calisir.
_REMOTE_EXPORT = r'''
import base64 as _b64, json as _json, os as _os, shutil as _shutil, subprocess as _sp, sys as _sys, time as _time
def _vd_export():
    request = _json.loads(_b64.b64decode(_sys.argv[1]).decode("utf-8"))
    deadline = _time.monotonic() + 2.7
    executable = _shutil.which("herdr")
    if executable is None:
        candidate = _os.path.expanduser("~/.local/bin/herdr")
        if not _os.path.isfile(candidate) or not _os.access(candidate, _os.X_OK):
            raise FileNotFoundError()
        executable = candidate
    env = {key: value for key, value in _os.environ.items() if key not in {
        "HERDR_PANE_ID", "HERDR_TAB_ID", "HERDR_WORKSPACE_ID", "HERDR_SOCKET_PATH",
        "HERDR_SESSION", "HERDR_CLIENT_SOCKET_PATH"}}
    def pane():
        left = deadline - _time.monotonic()
        if left <= 0:
            raise TimeoutError()
        result = _sp.run([executable, "--session", request["session"], "pane", "get", request["pane_id"]],
                         capture_output=True, text=True, encoding="utf-8", timeout=min(1.2, left), env=env)
        if result.returncode or len(result.stdout.encode("utf-8")) > 32768:
            raise ValueError()
        response = _json.loads(result.stdout)
        if "error" in response:
            raise ValueError()
        value = response["result"]["pane"]
        if (value.get("id", value.get("pane_id")) != request["pane_id"]
                or value.get("terminal_id") != request["terminal_id"]):
            raise ValueError()
        return value
    before = pane()
    identity = before.get("agent_session")
    if (not isinstance(identity, dict) or identity.get("agent") not in ("claude", "codex")
            or before.get("agent") != identity["agent"] or identity.get("kind") not in ("id", "path")
            or not isinstance(identity.get("value"), str) or not identity["value"]):
        raise ValueError()
    if "agent_session" in request and (request["agent_session"] != identity or request["agent"] != before.get("agent")):
        raise ValueError()
    resolved = resolve_session(identity["agent"], identity)
    conversation = read_conversation(resolved["path"], resolved["session_id"], resolved["provider"], max_words=300) if resolved else {"messages": [], "words": 0}
    after = pane()
    if after.get("agent") != before.get("agent") or after.get("agent_session") != identity:
        raise ValueError()
    if _time.monotonic() > deadline:
        raise TimeoutError()
    words = conversation.get("words")
    if (type(words) is not int or not 0 <= words <= 300
            or sum(len(item.get("text", "").split()) for item in conversation["messages"]) > 300):
        raise ValueError()
    return {"pane": {"id": request["pane_id"], "terminal_id": request["terminal_id"], "agent": before.get("agent"), "agent_session": identity},
            "messages": conversation["messages"], "words": conversation["words"]}
try:
    _vd_result = _vd_export()
    _vd_output = _json.dumps(_vd_result, ensure_ascii=False)
    if len(_vd_output.encode("utf-8")) + 1 > 32768:
        raise ValueError()
    print(_vd_output)
except Exception:
    print('{"status":"unavailable"}')
'''


class ContextCache:
    """request yalniz RAM okur; refresh arka plan izleyicisinde cagrilir."""

    def __init__(self, get_pane, profiles=None, *, run=None, clock=None, bridge=None):
        self._get_pane = get_pane
        self._profiles = profiles if profiles is not None else (lambda: {})
        self._run = run or subprocess.run
        self._clock = clock or time.monotonic
        self._bridge = bridge
        self._lock = threading.Lock()
        self._refresh_lock = threading.Lock()
        self._selected = None
        self._wanted = None
        self._identity = None
        self._epoch = 0
        self._updated = 0.0
        self._value = _empty()
        self._revoked = False
        self._closed = False

    def clear(self):
        with self._lock:
            self._epoch += 1
            self._selected = self._wanted = self._identity = None
            self._value = _empty()
            self._updated = 0.0
            self._revoked = True

    def close(self):
        self.clear()
        with self._lock:
            self._closed = True

    def _activate(self, selection, *, from_request=False):
        key = _base(selection)
        if key is None or self._closed:
            return None
        if from_request:
            self._revoked = False
        elif self._revoked or self._selected not in (None, key):
            return None
        wanted = _identity(selection) if "agent_session" in selection else None
        if "agent_session" in selection and wanted is None:
            self._epoch += 1
            self._value = _empty("identity_changed")
            self._identity = None
            self._updated = 0.0
            return None
        changed = key != self._selected or (wanted is not None and wanted != self._wanted and wanted != self._identity)
        if changed:
            self._epoch += 1
            self._selected = key
            self._wanted = wanted
            self._identity = None
            self._value = _empty()
            self._updated = 0.0
        elif wanted is not None:
            self._wanted = wanted
        return self._epoch

    def request(self, selection):
        if _base(selection) is None:
            self.clear()
            return MappingProxyType(_empty())
        with self._lock:
            epoch = self._activate(selection, from_request=True)
            if epoch is None or self._clock() - self._updated >= 5.0:
                return MappingProxyType(_empty("expired" if self._identity else "missing"))
            if "agent_session" in selection and _identity(selection) != self._identity:
                return MappingProxyType(_empty("identity_changed"))
            return MappingProxyType(dict(self._value))

    def _module(self):
        if self._bridge is None:
            self._bridge = importlib.import_module("dev.context_bridge")
        return self._bridge

    def _local(self, selection):
        bridge = self._module()
        before = copy.deepcopy(self._get_pane(["pane", "get", selection["pane_id"]], None)["pane"])
        if not _matching_pane(before, selection):
            raise ValueError("identity changed")
        expected = _identity(selection) if "agent_session" in selection else None
        if expected is not None and expected != _identity(before):
            raise ValueError("identity changed")
        identity = copy.deepcopy(before["agent_session"])
        resolved = bridge.resolve_session(identity["agent"], identity)
        messages = bridge.read_conversation(resolved["path"], resolved["session_id"], resolved["provider"], max_words=MAX_WORDS)["messages"] if resolved else []
        after = self._get_pane(["pane", "get", selection["pane_id"]], None)["pane"]
        if not _matching_pane(after, selection) or _identity(before) != _identity(after):
            raise ValueError("identity changed")
        return before, _snapshot(messages, bridge)

    def _remote(self, selection):
        profiles = self._profiles() if callable(self._profiles) else self._profiles
        profile = profiles.get(selection["machine"]) if isinstance(profiles, dict) else None
        if (not isinstance(profile, dict) or profile.get("id") != selection["machine"]
                or profile.get("enabled") is not True):
            raise ValueError("invalid machine")
        target, session = profile.get("target"), profile.get("session")
        route = (profile.get("id"), target, session, profile.get("enabled"))
        if (not isinstance(target, str) or not _SAFE_TARGET.fullmatch(target)
                or not isinstance(session, str) or not session or session.startswith("-") or len(session) > 256
                or any(ord(c) < 32 for c in session)):
            raise ValueError("invalid endpoint")
        request = dict(session=session, pane_id=selection["pane_id"], terminal_id=selection["terminal_id"])
        if "agent_session" in selection:
            request.update(agent=selection.get("agent"), agent_session=selection["agent_session"])
        encoded = base64.b64encode(json.dumps(request, ensure_ascii=True).encode("utf-8")).decode("ascii")
        bridge = self._module()
        source = Path(bridge.__file__).read_text(encoding="utf-8")
        result = self._run(["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=2", "--", target,
                            "python3 - " + encoded], input=source + "\n" + _REMOTE_EXPORT,
                           capture_output=True, text=True, encoding="utf-8", timeout=REFRESH_TIMEOUT,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        current_profiles = self._profiles() if callable(self._profiles) else self._profiles
        current = current_profiles.get(selection["machine"], {}) if isinstance(current_profiles, dict) else {}
        if not isinstance(current, dict) or route != tuple(current.get(key) for key in ("id", "target", "session", "enabled")):
            raise ValueError("machine changed")
        if result.returncode or not isinstance(result.stdout, str) or len(result.stdout.encode("utf-8")) > MAX_OUTPUT_BYTES:
            raise ValueError("invalid remote output")
        response = json.loads(result.stdout)
        pane = response.get("pane")
        if not _matching_pane(pane, selection):
            raise ValueError("identity changed")
        expected = _identity(selection) if "agent_session" in selection else None
        if expected is not None and expected != _identity(pane):
            raise ValueError("identity changed")
        words = response.get("words")
        if type(words) is not int or not 0 <= words <= MAX_WORDS:
            raise ValueError("invalid word count")
        return pane, _snapshot(response.get("messages"), bridge)

    def refresh(self, selection):
        selection = copy.deepcopy(selection)
        with self._lock:
            epoch = self._activate(selection)
        if epoch is None or not self._refresh_lock.acquire(blocking=False):
            return MappingProxyType(_empty())
        try:
            # Get_pane callback'i de toplam butceyi asamaz; gec thread sonucu cache yazamaz.
            done = threading.Event()
            result = []
            def read():
                try:
                    result.append((self._remote(selection) if selection.get("machine") is not None else self._local(selection)))
                except Exception:
                    pass  # Ham hata/oturum metni loga veya sonuca tasinmaz.
                finally:
                    done.set()
            worker = threading.Thread(target=read, daemon=True)
            worker.start()
            completed = done.wait(REFRESH_TIMEOUT)
            with self._lock:
                if epoch != self._epoch or self._closed or self._selected != _base(selection):
                    return MappingProxyType(_empty())
                if not completed or not result:
                    self._value = _empty("timeout" if not completed else "unavailable")
                    self._identity = None
                else:
                    pane, value = result[0]
                    identity = _identity(pane)
                    if self._wanted is not None and self._wanted != identity:
                        self._value = _empty("identity_changed")
                        self._identity = None
                    else:
                        self._value, self._identity = value, identity
                self._updated = self._clock()
                return MappingProxyType(dict(self._value))
        finally:
            self._refresh_lock.release()
