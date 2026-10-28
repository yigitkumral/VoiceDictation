"""Kayitli Codex/Claude oturumundan sinirli, gorunur konusma baglami."""
import json
import os
from pathlib import Path
import re
import unicodedata
import uuid
from collections import Counter


MAX_READ_BYTES = 512 * 1024
MAX_WORDS = 300
MAX_TEXT_CHARS = 24000
_HEAD_BYTES = 64 * 1024


def _session_id(value):
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError):
        return None


def _provider_root(provider, path_root=None):
    home = Path.home() if path_root is None else Path(path_root)
    if provider == "codex":
        return (home / ".codex" / "sessions").resolve()
    if provider == "claude":
        return (home / ".claude" / "projects").resolve()
    return None


def _allowed_path(path, provider, path_root=None):
    root = _provider_root(provider, path_root)
    if root is None or not isinstance(path, (str, os.PathLike)):
        return None
    try:
        result = Path(path).resolve(strict=True)
        if (not result.is_relative_to(root) or not result.is_file()
                or result.suffix.lower() != ".jsonl"
                or any(part.lower() == "subagents" for part in result.relative_to(root).parts)):
            return None
        return result
    except (OSError, ValueError, RuntimeError):
        return None


def resolve_session(provider, identity, path_root=None):
    """Yalniz tam ID veya exact path; 'en yeni dosya' secimi ve icerik taramasi yok.

    path_root testlerde sahte home'dur. Donus None veya provider/path/session_id.
    """
    if not isinstance(identity, dict):
        return None
    kind, value = identity.get("kind"), identity.get("value")
    root = _provider_root(provider, path_root)
    if root is None or not isinstance(value, str):
        return None
    if kind == "id":
        session_id = _session_id(value)
        if session_id is None:
            return None
        pattern = "rollout-*" + session_id + ".jsonl" if provider == "codex" else "*/" + session_id + ".jsonl"
        try:
            paths = root.rglob(pattern) if provider == "codex" else root.glob(pattern)
            candidates = {allowed for path in paths
                          if (allowed := _allowed_path(path, provider, path_root)) is not None}
        except OSError:
            return None
        if len(candidates) != 1:
            return None
        path = candidates.pop()
    elif kind == "path":
        path = _allowed_path(value, provider, path_root)
        if path is None:
            return None
        match = re.search(r"([0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12})$", path.stem)
        session_id = _session_id(match[1]) if match else None
        if session_id is None:
            return None
        if provider == "codex" and not path.name.startswith("rollout-"):
            return None
        if provider == "claude" and path.stem.lower() != session_id:
            return None
    else:
        return None
    return dict(provider=provider, path=str(path), session_id=session_id)


def _json_rows(raw, discard_first=False, discard_last=False):
    lines = raw.splitlines(keepends=True)
    if discard_first and lines:
        lines = lines[1:]
    if discard_last and lines and not lines[-1].endswith((b"\n", b"\r")):
        lines = lines[:-1]
    result = []
    for line in lines:
        try:
            value = json.loads(line)
        except (ValueError, UnicodeError, RecursionError):
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _read_bounded(path):
    """Head+tail toplam en fazla 512KiB; buyuk dosyada head yalniz kimlik icin."""
    with path.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        if size <= MAX_READ_BYTES:
            rows = _json_rows(stream.read(size))
            return rows, rows
        head = _json_rows(stream.read(_HEAD_BYTES), discard_last=True)
        tail_size = MAX_READ_BYTES - _HEAD_BYTES
        stream.seek(size - tail_size)
        tail = _json_rows(stream.read(tail_size), discard_first=True)
        return head + tail, tail


def _visible_text(message, role, provider):
    if message.get("recipient") not in (None, "all", "user"):
        return ""
    channels = [message.get("channel"), message.get("phase")]
    if any(channel is not None and channel not in ("final", "commentary", "final_answer")
           for channel in channels):
        return ""
    content = message.get("content", "")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        accepted = ("text",) if provider == "claude" else (("input_text", "text") if role == "user"
                                                         else ("output_text", "text"))
        text = "\n".join(part["text"] for part in content
                         if isinstance(part, dict) and part.get("type") in accepted
                         and isinstance(part.get("text"), str))
    else:
        return ""
    stripped = text.lstrip()
    frame_prefixes = ("# AGENTS.md instructions", "<environment_context>", "<INSTRUCTIONS>",
                      "<skills_instructions>", "<permissions instructions>", "<collaboration_mode>",
                      "<local-command-caveat>", "<command-name>",
                      "This session is being continued from a previous conversation")
    if stripped.startswith(frame_prefixes):
        return ""
    if re.search(r"<(?:subagent_notification|agent_notification|collaboration)[>\s]", text, re.I):
        return ""
    if re.search(r"(?m)^Message Type: (?:NEW_TASK|MESSAGE|FINAL_ANSWER)\s*$", text):
        return ""
    # Sistem hatirlatmalari normal kullanici istegine eklenmis olabilir.
    text = re.sub(r"<system-reminder>[\s\S]*?(?:</system-reminder>|$)", "", text, flags=re.I)
    if any(unicodedata.category(char) in ("Cc", "Cf", "Cs") and char not in "\t\r\n" for char in text):
        return ""
    return text.strip()


def _trim_messages(messages, max_words):
    remaining = min(MAX_WORDS, max(0, int(max_words)))
    result = []
    for message in reversed(messages):
        if not remaining:
            break
        # Tek devasa token bile tum kaynak dosyayi ciktiya tasiyamaz.
        words = message["text"][-MAX_TEXT_CHARS:].split()
        selected = words[-remaining:]
        if selected:
            result.append(dict(role=message["role"], text=" ".join(selected)))
            remaining -= len(selected)
    result.reverse()
    total_chars = 0
    for message in reversed(result):
        available = max(0, MAX_TEXT_CHARS - total_chars)
        message["text"] = message["text"][-available:] if available else ""
        total_chars += len(message["text"])
    return [message for message in result if message["text"]]


def read_conversation(path, session_id, provider, max_words=300, path_root=None):
    """Kayitli oturumun yalniz son <=300 gorunur kelimesi; hatada bos sonuc."""
    empty = dict(messages=[], words=0)
    expected = _session_id(session_id)
    allowed = _allowed_path(path, provider, path_root)
    if expected is None or allowed is None:
        return empty
    try:
        identities, recent = _read_bounded(allowed)
        if provider == "codex":
            headers = [row.get("payload", {}) for row in identities if row.get("type") == "session_meta"]
            if not headers or any(not isinstance(header, dict)
                                  or _session_id(header.get("id")) != expected for header in headers):
                return empty
            for header in headers:
                source = header.get("source", "")
                if (isinstance(source, dict) and "subagent" in source
                        or isinstance(source, str) and "subagent" in source.lower()):
                    return empty
        else:
            found = [row["sessionId"] for row in identities if "sessionId" in row]
            if not found or any(_session_id(value) != expected for value in found):
                return empty
        messages = []
        for row in recent:
            if any(row.get(key) for key in ("isSidechain", "is_sidechain", "isMeta", "agentId", "agent_id")):
                continue
            if provider == "codex":
                if row.get("type") != "response_item":
                    continue
                message = row.get("payload")
                if not isinstance(message, dict) or message.get("type") != "message":
                    continue
            else:
                if row.get("type") not in ("user", "assistant") or _session_id(row.get("sessionId")) != expected:
                    continue
                message = row.get("message")
                if not isinstance(message, dict) or message.get("role") != row.get("type"):
                    continue
            role = message.get("role")
            if role not in ("user", "assistant"):
                continue
            if any(message.get(key) for key in ("isSidechain", "is_sidechain", "agentId", "agent_id")):
                continue
            if any(row.get(key) is not None and row[key] not in ("final", "commentary", "final_answer")
                   for key in ("channel", "phase")):
                continue
            text = _visible_text(message, role, provider)
            if text:
                messages.append(dict(role=role, text=text))
        messages = _trim_messages(messages, max_words)
        return dict(messages=messages, words=sum(len(message["text"].split()) for message in messages))
    except (OSError, ValueError, TypeError, OverflowError):
        return empty


def _fold(value):
    return value.replace("İ", "i").replace("I", "ı").casefold()


def build_hints(messages, max_terms=24):
    """Yakinlik+siklikla ozel ad/kod terimi; URL, sir, komut ve wake word yok."""
    if not isinstance(messages, list):
        return ""
    safe = []
    for message in messages:
        if (not isinstance(message, dict) or message.get("role") not in ("user", "assistant")
                or not isinstance(message.get("text"), str)
                or any(message.get(key) for key in ("isSidechain", "isMeta", "agentId", "agent_id"))):
            continue
        visible = _visible_text(dict(message, content=message["text"]), message["role"], "claude")
        if visible:
            safe.append(dict(role=message["role"], text=visible))
    text = " ".join(message["text"] for message in _trim_messages(safe, MAX_WORDS))
    text = re.sub(r"(?i)\b(?:https?://|www\.)\S+|\b[\w.+-]+@[\w.-]+\b", " ", text)
    text = re.sub(r"(?i)\b[\w-]*(?:api[_-]?key|token|password|secret|authorization|bearer|şifre|sifre)"
                  r"[\w-]*\s*[:=]?\s*[\"']?\S+", " ", text)
    text = re.sub(r"(?i)\b(?:sk-|ghp_|github_pat_|hf_)[A-Za-z0-9_-]+", " ", text)
    text = re.sub(r"(?:[A-Za-z]:[\\/]|(?<!\w)/)\S+|\b\S+/\S+\b", " ", text)
    stop = set(("bugün yarın dün şimdi önce sonra evet hayır tamam lütfen merhaba teşekkür "
                "ben sen biz siz onlar bunu şunu şöyle böyle burada orada için ile bir bu şu o "
                "yeni eski dosya dosyayı kod kodu proje projeyi çalıştır aç kapat yap yaz "
                "the this that these those please thanks hello ignore previous instructions "
                "system developer assistant user tool delete remove all files only output "
                "diktasyon diktation dictation token secret password authorization "
                "apikey api_key bearer true false none null").split())
    candidates = []
    for match in re.finditer(r"[^\W\d][\w]*(?:[._-][\w]+)*", text):
        term = match.group()
        key = _fold(term)
        if (not 3 <= len(term) <= 64 or key in stop or term.casefold() in stop
                or _session_id(term) is not None):
            continue
        if ((len(term) >= 24 or len(term) >= 16 and term.isalnum())
                and any(char.isdigit() for char in term)):
            continue
        codeish = any(char in term for char in "._-") or any(
            term[index - 1].islower() and char.isupper() for index, char in enumerate(term) if index)
        proper = term[0].isupper()
        if codeish or proper:
            candidates.append((key, term))
    counts = Counter(key for key, _ in candidates)
    last = {key: index for index, (key, _) in enumerate(candidates)}
    spelling = dict(candidates)
    limit = min(24, max(0, int(max_terms)))
    ordered = sorted(counts, key=lambda key: (counts[key] + 2 * last[key] / max(1, len(candidates) - 1),
                                             last[key]), reverse=True)
    chosen = []
    for key in ordered:
        value = spelling[key]
        if len(", ".join(chosen + [value])) <= 240:
            chosen.append(value)
        if len(chosen) == limit:
            break
    return ", ".join(chosen) if limit else ""
