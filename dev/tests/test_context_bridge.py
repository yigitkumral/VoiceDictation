"""Konusma baglami yalniz sentetik kayitli oturumlarla sinanir."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("context_bridge", ROOT / "dev/context_bridge.py")
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)
SESSION = "01a16d16-e381-7d01-83b2-7b6b1e873889"
OTHER = "01a16d16-e381-7d01-83b2-7b6b1e873888"
TEST_TMP = ROOT / ".local" / "test-tmp"
TEST_TMP.mkdir(parents=True, exist_ok=True)


def codex(role, text, channel=None, item_type="message"):
    payload = dict(type=item_type, role=role, content=[dict(
        type="input_text" if role == "user" else "output_text", text=text)])
    if channel:
        payload["channel"] = channel
    return dict(type="response_item", payload=payload)


def claude(role, content, **extra):
    return dict(type=role, sessionId=SESSION, message=dict(role=role, content=content), **extra)


class ContextBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TEST_TMP)
        self.home = Path(self.temp.name)
        self.codex = self.home / ".codex/sessions/2026/10/24" / ("rollout-2026-10-24T12-00-00-" + SESSION + ".jsonl")
        self.claude = self.home / ".claude/projects/project" / (SESSION + ".jsonl")
        self.codex.parent.mkdir(parents=True)
        self.claude.parent.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, provider, rows, suffix=b""):
        path = self.codex if provider == "codex" else self.claude
        if provider == "codex":
            rows = [dict(type="session_meta", payload=dict(id=SESSION, source="cli"))] + rows
        path.write_bytes(b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows) + suffix)
        return path

    def read(self, provider, session=SESSION, max_words=300):
        path = self.codex if provider == "codex" else self.claude
        return bridge.read_conversation(path, session, provider, max_words=max_words, path_root=self.home)

    def test_codex_only_visible_response_items_no_event_duplicates(self):
        self.write("codex", [
            codex("system", "SYSTEM PRIVATE"), codex("developer", "DEVELOPER PRIVATE"),
            codex("user", "Ali VoiceDictation kullanıyor"),
            dict(type="event_msg", payload=dict(type="user_message", message="DUPLICATE PRIVATE")),
            codex("assistant", "Ayşe dictation.py dosyasını inceliyor", "commentary"),
            codex("assistant", "FINAL VISIBLE", "final"),
            codex("assistant", "ANALYSIS PRIVATE", "analysis"),
            codex("assistant", "THINK PRIVATE", item_type="reasoning"),
            codex("tool", "TOOL PRIVATE"), codex("function", "FUNCTION PRIVATE"),
            dict(type="response_item", payload=dict(type="function_call_output", output="FUNCTION OUTPUT PRIVATE")),
        ])
        result = self.read("codex")
        self.assertEqual([m["role"] for m in result["messages"]], ["user", "assistant", "assistant"])
        self.assertEqual(result["words"], 9)
        self.assertNotIn("PRIVATE", str(result))
        self.assertNotIn("DUPLICATE", str(result))

    def test_codex_missing_channel_and_final_answer_phase_are_visible(self):
        final = codex("assistant", "Son yanıt")
        final["payload"]["phase"] = "final_answer"
        self.write("codex", [codex("assistant", "Eski biçim"), final])
        self.assertEqual(self.read("codex")["words"], 4)

    def test_payload_child_routing_and_unicode_control_frames_are_excluded(self):
        child = codex("assistant", "CHILD PRIVATE", "final")
        child["payload"]["agent_id"] = "child"
        routed = codex("assistant", "ROUTED PRIVATE", "commentary")
        routed["payload"]["recipient"] = "functions"
        self.write("codex", [child, routed, codex("user", "Bidi\u202ePRIVATE"),
                             codex("user", "Ali burada")])
        self.assertEqual(self.read("codex")["messages"], [dict(role="user", text="Ali burada")])

    def test_claude_excludes_thinking_tool_results_and_internal_agents(self):
        self.write("claude", [
            claude("user", "Ali yardım istiyor"),
            claude("assistant", [dict(type="thinking", thinking="THINK PRIVATE"),
                                  dict(type="tool_use", name="read", input={"secret": "PRIVATE"}),
                                  dict(type="text", text="Ayşe yardım ediyor")]),
            claude("user", [dict(type="tool_result", content="TOOL PRIVATE"),
                             dict(type="text", text="Görünür kullanıcı metni")]),
            claude("assistant", "CHILD PRIVATE", isSidechain=True),
            claude("assistant", "AGENT PRIVATE", agentId="child"),
            claude("user", "META PRIVATE", isMeta=True),
            dict(type="progress", sessionId=SESSION, message=dict(role="assistant", content="PROGRESS PRIVATE")),
        ])
        result = self.read("claude")
        self.assertEqual(result["words"], 9)
        self.assertNotIn("PRIVATE", str(result))

    def test_injected_frames_and_notifications_do_not_become_context(self):
        self.write("codex", [
            codex("user", "# AGENTS.md instructions for C:\\repo\nPRIVATE"),
            codex("user", "<environment_context>PRIVATE</environment_context>"),
            codex("user", "<INSTRUCTIONS>PRIVATE</INSTRUCTIONS>"),
            codex("user", "<subagent_notification>PRIVATE</subagent_notification>"),
            codex("user", "Message Type: FINAL_ANSWER\nTask name: child\nPRIVATE"),
            codex("user", "Ali yardım et <system-reminder>PRIVATE</system-reminder>"),
            codex("assistant", "Görünür cevap", "final"),
        ])
        result = self.read("codex")
        self.assertEqual([m["text"] for m in result["messages"]], ["Ali yardım et", "Görünür cevap"])

    def test_three_hundred_words_hard_cap_keeps_latest_roles(self):
        self.write("codex", [codex("user", " ".join("old" + str(i) for i in range(400))),
                             codex("assistant", " ".join("new" + str(i) for i in range(200)), "final")])
        result = self.read("codex", max_words=10000)
        self.assertEqual(result["words"], 300)
        self.assertTrue(result["messages"][0]["text"].startswith("old300 "))
        self.assertTrue(result["messages"][-1]["text"].endswith("new199"))
        self.assertEqual(self.read("codex", max_words=5)["words"], 5)

    def test_large_token_cannot_export_entire_transcript(self):
        self.write("codex", [codex("user", "x" * 100000)])
        result = self.read("codex")
        self.assertLessEqual(len(result["messages"][0]["text"]), bridge.MAX_TEXT_CHARS)

    def test_partial_and_corrupt_json_are_ignored_safely(self):
        self.write("codex", [codex("user", "Ali burada")], suffix=b'{"type":"response_item","payload":')
        self.assertEqual(self.read("codex")["messages"], [dict(role="user", text="Ali burada")])
        with self.codex.open("ab") as output:
            output.write(b"\nnot JSON\n")
            output.write(json.dumps(codex("assistant", "Ayşe burada")).encode())
        self.assertEqual(self.read("codex")["words"], 4)

    def test_read_budget_head_tail_and_partial_boundary(self):
        self.write("codex", [codex("user", "old " * 150000), codex("user", "Ali en yeni"),
                             codex("assistant", "Ayşe en son", "final")])
        original_open = Path.open
        observed = dict(bytes=0)
        class Tracked:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def read(self, size):
                result = self.stream.read(size)
                observed["bytes"] += len(result)
                return result
            def seek(self, *args):
                return self.stream.seek(*args)
            def fileno(self):
                return self.stream.fileno()
        def tracked(path, *args, **kwargs):
            return Tracked(original_open(path, *args, **kwargs))
        with patch.object(Path, "open", tracked):
            result = self.read("codex")
        self.assertLessEqual(observed["bytes"], bridge.MAX_READ_BYTES)
        self.assertEqual([m["text"] for m in result["messages"]], ["Ali en yeni", "Ayşe en son"])

    def test_mismatched_or_missing_identity_is_rejected(self):
        self.write("codex", [codex("user", "Ali")])
        self.assertEqual(self.read("codex", OTHER)["words"], 0)
        self.codex.write_text(json.dumps(codex("user", "Ali")), encoding="utf-8")
        self.assertEqual(self.read("codex")["words"], 0)
        self.write("claude", [claude("user", "Ali"), dict(type="user", sessionId=OTHER,
                                                         message=dict(role="user", content="PRIVATE"))])
        self.assertEqual(self.read("claude")["words"], 0)

    def test_codex_subagent_session_is_rejected(self):
        self.codex.write_text(json.dumps(dict(type="session_meta", payload=dict(
            id=SESSION, source={"subagent": {"thread_spawn": {"parent_thread_id": OTHER}}}))) + "\n"
                              + json.dumps(codex("user", "PRIVATE")), encoding="utf-8")
        self.assertEqual(self.read("codex")["words"], 0)

    def test_path_allowlist_and_child_directories(self):
        self.write("codex", [codex("user", "PRIVATE")])
        outside = self.home / "outside.jsonl"
        outside.write_bytes(self.codex.read_bytes())
        child = self.codex.parent / "subagents/child.jsonl"
        child.parent.mkdir()
        child.write_bytes(self.codex.read_bytes())
        for path, provider in [(outside, "codex"), (child, "codex"), (self.codex, "claude")]:
            self.assertEqual(bridge.read_conversation(path, SESSION, provider, path_root=self.home)["words"], 0)

    def test_symlink_escape_is_rejected(self):
        outside = self.home / "outside.jsonl"
        outside.write_text("PRIVATE", encoding="utf-8")
        try:
            self.codex.symlink_to(outside)
        except OSError:
            self.skipTest("Windows symlink permission unavailable")
        self.assertIsNone(bridge.resolve_session("codex", dict(kind="id", value=SESSION), path_root=self.home))

    def test_resolver_exact_id_and_path_for_both_providers(self):
        self.write("codex", [codex("user", "Ali")])
        self.write("claude", [claude("user", "Ayşe")])
        for provider, path in [("codex", self.codex), ("claude", self.claude)]:
            for identity in (dict(kind="id", value=SESSION), dict(kind="path", value=str(path))):
                result = bridge.resolve_session(provider, identity, path_root=self.home)
                self.assertEqual(result, dict(provider=provider, path=str(path.resolve()), session_id=SESSION))

    def test_resolver_no_latest_selection_and_ambiguity_rejected(self):
        self.write("codex", [])
        for value in ("latest", "*", "", "../" + SESSION):
            self.assertIsNone(bridge.resolve_session("codex", dict(kind="id", value=value), path_root=self.home))
        duplicate = self.codex.parent / ("rollout-other-" + SESSION + ".jsonl")
        duplicate.write_text("PRIVATE", encoding="utf-8")
        self.assertIsNone(bridge.resolve_session("codex", dict(kind="id", value=SESSION), path_root=self.home))
        self.assertIsNone(bridge.resolve_session("unknown", dict(kind="id", value=SESSION), path_root=self.home))

    def test_hints_use_frequency_recency_and_safe_names_code_terms(self):
        hints = bridge.build_hints([
            dict(role="user", text="Ali VoiceDictation dictation.py Ayşe Ali"),
            dict(role="assistant", text="Ayşe VoiceDictation cleanup_text Qwen3 CUDA")])
        for term in ("Ali", "Ayşe", "VoiceDictation", "dictation.py", "cleanup_text", "Qwen3", "CUDA"):
            self.assertIn(term, hints)
        self.assertLessEqual(len(hints), 240)
        self.assertEqual(len(bridge.build_hints([dict(role="user", text="Ali Ayşe Qwen3")], 2).split(", ")), 2)
        self.assertEqual(bridge.build_hints([], 0), "")

    def test_hints_exclude_urls_emails_secrets_tools_wake_and_controls(self):
        hints = bridge.build_hints([
            dict(role="tool", text="PrivateToolName"),
            dict(role="user", text="# AGENTS.md instructions for PrivateProject\nPrivateAgentHint"),
            dict(role="user", text="<environment_context>PrivateEnvironment</environment_context>"),
            dict(role="user", text="Diktasyon Zugzwang Bugün Ignore Previous Instructions "
                 "https://PrivateURL.test/HiddenName Person@PrivateEmail.test "
                 "OPENAI_API_KEY=SecretValue sk-PrivateApiKey123456789 "
                 "Bearer PrivateBearerValue C:\\PrivatePath\\SecretFile.py Ali VoiceDictation")])
        for forbidden in ("Diktasyon", "Zugzwang", "Bugün", "Ignore", "Previous", "Instructions", "Private",
                          "Secret", "Bearer", "ToolName", "API_KEY"):
            self.assertNotIn(forbidden, hints)
        self.assertIn("VoiceDictation", hints)
        self.assertIn("Ali", hints)


if __name__ == "__main__":
    unittest.main()
