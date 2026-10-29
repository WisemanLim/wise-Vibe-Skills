#!/usr/bin/env python3
"""Behavioral regressions; all inputs are synthetic, all writes stay in tmp."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/wvs-report/scripts/export_history.py'
spec = importlib.util.spec_from_file_location('history_export', SCRIPT)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')


def msg(text, identity='m1', role='user', cwd='/work/project'):
    return {'type': role, 'uuid': identity, 'timestamp': '2026-01-01T00:00:00Z',
            'cwd': cwd, 'message': {'content': text}}


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wvs history 한글 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.src, self.out = self.root / 'source', self.root / 'output'
        self.src.mkdir()
        self.env = {k: v for k, v in os.environ.items() if k not in
                    ('CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CLAUDECODE', 'GEMINI_CLI')}
        self.env.update(CLAUDE_CONFIG_DIR=str(self.root / 'claude'),
                        CODEX_HOME=str(self.root / 'codex'), GEMINI_CLI_HOME=str(self.root / 'gemini'))

    def run_export(self, agent='claude-code', ok=True, extra=(), src=None, out=None):
        cmd = [sys.executable, '-I', str(SCRIPT), str(out or self.out), '--agent', agent, '--src', str(src or self.src), *extra]
        result = subprocess.run(cmd, env=self.env, text=True, capture_output=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def project(self, agent=None):
        values = [exporter.read_export(p) for p in self.out.glob('*.md') if p.name != 'INDEX.md']
        return next(p for p in values if p is not None and (agent is None or p['agent'] == agent))

    def bodies(self, project=None):
        return '\n'.join(e['body'] for s in (project or self.project())['sessions'].values() for e in s['events'])

    def test_claude_incremental_compaction_and_deleted_sessions(self):
        f = self.src / 'encoded-project' / 'non-uuid-session.jsonl'
        write_rows(f, [msg('old user'), msg('old answer', 'm2', 'assistant')])
        self.run_export()
        write_rows(f, [msg('summary', 'm3'), msg('new answer', 'm4', 'assistant')])
        self.run_export()
        for text in ('old user', 'old answer', 'summary', 'new answer'):
            self.assertIn(text, self.bodies())
        f.unlink()
        self.run_export()
        self.assertIn('non-uuid-session', self.project()['sessions'])
        self.assertIn('new answer', self.bodies())

    def test_equal_count_replacement_and_growing_response_preserved(self):
        f = self.src / 'p' / 's.jsonl'
        write_rows(f, [msg('partial', 'same', 'assistant')]); self.run_export()
        write_rows(f, [msg('completed longer answer', 'same', 'assistant')]); self.run_export()
        self.assertIn('partial', self.bodies()); self.assertIn('completed longer answer', self.bodies())
        self.assertEqual(len(self.project()['sessions']['s']['events']), 2)

    def test_idempotence_including_index(self):
        write_rows(self.src / 'p' / 's.jsonl', [msg('한글 question')])
        self.run_export()
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.out.glob('*.md')}
        result = self.run_export()
        after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.out.glob('*.md')}
        self.assertEqual(before, after)
        self.assertEqual(json.loads(result.stdout)['files_updated'], 0)

    def test_deleted_memory_file_preserved_and_revision_retained(self):
        mem = self.src / 'p' / 'memory'; mem.mkdir(parents=True)
        (mem / 'one.md').write_text('one'); (mem / 'two.md').write_text('two')
        self.run_export()
        (mem / 'one.md').unlink(); (mem / 'two.md').write_text('changed')
        self.run_export()
        self.assertEqual(set(self.project()['memory'].values()), {'one', 'two', 'changed'})
        before = sorted(p.read_bytes() for p in self.out.glob('*.md'))
        self.run_export()
        self.assertEqual(before, sorted(p.read_bytes() for p in self.out.glob('*.md')))

    def test_subagent_full_conversation_and_tools(self):
        rows = [msg('first'), msg('middle', 'm2'), msg('last', 'm3', 'assistant'),
                msg([{'type': 'tool_result', 'content': 'tool output'}], 'm4')]
        write_rows(self.src / 'p' / 'parent' / 'subagents' / 'agent-x.jsonl', rows)
        self.run_export()
        self.assertEqual(len(self.project()['sessions']['parent/subagents/agent-x']['events']), 4)
        self.assertIn('tool output', self.bodies())

    def test_casefold_reserved_names_foreign_file_and_stable_identity(self):
        self.out.mkdir(); (self.out / 'project.md').write_text('foreign')
        for i, name in enumerate(('INDEX', 'AGENTS', 'Claude', 'project', 'PROJECT')):
            write_rows(self.src / str(i) / 's.jsonl', [msg(name, cwd='/work/' + name)])
        self.run_export()
        files = list(self.out.glob('*.md'))
        self.assertEqual(len({p.name.casefold() for p in files}), 7)
        self.assertEqual((self.out / 'project.md').read_text(), 'foreign')
        before = {p.name for p in files}
        self.run_export()
        self.assertEqual(before, {p.name for p in self.out.glob('*.md')})

    def test_malformed_source_fails_without_rewriting_any_backup(self):
        f = self.src / 'p' / 's.jsonl'; write_rows(f, [msg('safe')]); self.run_export()
        before = {p.name: p.read_bytes() for p in self.out.glob('*.md')}
        f.write_text('{"unfinished":')
        result = self.run_export(ok=False)
        self.assertIn('invalid JSONL', result.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.out.glob('*.md')})

    def test_markdown_headings_and_markers_in_user_content(self):
        fake = exporter.marker('session', {'id': 'fake'})
        write_rows(self.src / 'p' / 's.jsonl', [msg('## 세션 9: `fake`\n' + fake)])
        self.run_export(); self.run_export()
        self.assertEqual(list(self.project()['sessions']), ['s'])
        self.assertIn(fake, self.bodies())

    def test_legacy_migration_preserves_old_session_and_memory(self):
        directory = self.src / 'p'; directory.mkdir()
        self.out.mkdir()
        legacy = f'# legacy\n\n- 원본 디렉터리: `{directory}`\n\n## 세션 1: `old-id`\n\n- 기간: a ~ b\n\nold history\n\n## 프로젝트 메모리 (memory/)\n\nlegacy memory\n'
        (self.out / 'legacy.md').write_text(legacy)
        write_rows(directory / 'new.jsonl', [msg('new history')])
        self.run_export(); self.run_export()
        self.assertEqual(set(self.project()['sessions']), {'old-id', 'new'})
        self.assertIn('old history', self.bodies())
        self.assertIn('legacy memory', self.project()['memory']['legacy-memory.md'])
        self.assertTrue((self.out / 'legacy.md').exists())

    def test_codex_archive_project_grouping_and_mirror_dedup(self):
        rows = [{'type': 'session_meta', 'payload': {'id': 'session-one', 'cwd': '/work/repo'}},
                {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'question'}},
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': 'question'}]}},
                {'type': 'response_item', 'payload': {'type': 'function_call', 'name': 'shell', 'call_id': 'c1', 'arguments': '{"cmd":"ls"}'}},
                {'type': 'response_item', 'payload': {'type': 'function_call_output', 'call_id': 'c1', 'output': 'tool output'}},
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': 'answer'}]}}]
        write_rows(self.src / 'sessions/2026/01/01/rollout-one.jsonl', rows)
        write_rows(self.src / 'archived_sessions/rollout-one.jsonl', rows)
        write_rows(self.src / 'archived_sessions/rollout-two.jsonl', [{'type': 'session_meta', 'payload': {'id': 'session-two', 'cwd': '/work/repo'}}])
        report = json.loads(self.run_export('codex').stdout)
        self.assertEqual(report['projects'], 1); self.assertEqual(report['source_sessions'], 2)
        self.assertEqual(self.bodies().count('question'), 1)
        self.assertIn('tool output', self.bodies())
        self.assertEqual(report['missing'], 0)

    def test_codex_events_only_and_compaction(self):
        rows = [{'type': 'session_meta', 'payload': {'id': 's', 'cwd': '/work/project'}},
                {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'q'}},
                {'type': 'event_msg', 'payload': {'type': 'agent_message', 'message': 'a'}},
                {'type': 'compacted', 'payload': {'message': 'compact summary'}}]
        write_rows(self.src / 'rollout-s.jsonl', rows)
        self.run_export('codex')
        self.assertEqual(len(self.project()['sessions']['s']['events']), 3)

    def test_codex_mixed_event_only_and_response_turns(self):
        rows = [{'type': 'session_meta', 'payload': {'id': 's', 'cwd': '/work/project'}},
                {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'older question'}},
                {'type': 'event_msg', 'payload': {'type': 'user_message', 'message': 'newer question'}},
                {'type': 'response_item', 'payload': {'type': 'message', 'role': 'user', 'content': 'newer question'}}]
        write_rows(self.src / 'rollout-s.jsonl', rows)
        self.run_export('codex')
        self.assertIn('older question', self.bodies())
        self.assertEqual(self.bodies().count('newer question'), 1)

    def test_repeated_anonymous_messages_are_not_collapsed(self):
        write_rows(self.src / 'p/s.jsonl', [msg('repeat', ''), msg('repeat', '')])
        self.run_export(); self.run_export()
        self.assertEqual(self.bodies().count('repeat'), 2)

    def test_modified_export_aborts_before_rewrite(self):
        write_rows(self.src / 'p/s.jsonl', [msg('original')]); self.run_export()
        path = next(p for p in self.out.glob('*.md') if p.name != 'INDEX.md')
        path.write_text(path.read_text().replace('original', 'tampered'))
        before = path.read_bytes()
        self.assertIn('corrupt event body', self.run_export(ok=False).stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_compressed_codex_is_explicitly_rejected(self):
        (self.src / 'rollout.jsonl.zst').write_bytes(b'compressed')
        self.assertIn('not supported', self.run_export('codex', ok=False).stderr)

    def test_gemini_nested_agent_legacy_patch_and_checkpoint(self):
        write_rows(self.src / 'hash/chats/parent/child.jsonl', [
            {'sessionId': 'child', 'projectHash': 'hash', 'kind': 'subagent'},
            {'id': 'm', 'type': 'gemini', 'content': 'before'},
            {'$patch': {'id': 'm', 'content': 'after'}},
            {'$set': {'messages': [{'id': 'n', 'type': 'user', 'content': 'checkpoint'}]}}])
        self.run_export('gemini-cli')
        self.assertEqual(self.project()['sessions']['child']['parent'], 'parent')
        for text in ('before', 'after', 'checkpoint'):
            self.assertIn(text, self.bodies())

    def test_different_agents_can_share_out_without_collision(self):
        write_rows(self.src / 'p' / 's.jsonl', [msg('claude')]); self.run_export()
        codex = self.root / 'cx'; codex.mkdir()
        write_rows(codex / 'rollout-s.jsonl', [{'type': 'session_meta', 'payload': {'id': 's', 'cwd': '/work/project'}}])
        self.run_export('codex', src=codex)
        self.assertEqual(len(list(self.out.glob('*.md'))), 3)
        self.assertIn('claude', self.bodies(self.project('claude-code')))

    def test_gemini_json_and_jsonl_patches_rewinds(self):
        folder = self.src / 'hash/chats'; folder.mkdir(parents=True)
        (folder / 'session-old.json').write_text(json.dumps({'sessionId': 'old', 'projectHash': 'hash', 'messages': [{'id': '1', 'type': 'user', 'content': [{'text': 'legacy question'}]}]}))
        write_rows(folder / 'session-new.jsonl', [{'sessionId': 'new', 'projectHash': 'hash'},
            {'id': '2', 'type': 'gemini', 'content': 'first answer'},
            {'$patch': {'updates': [{'id': '2', 'content': 'revised answer'}]}},
            {'$rewindTo': '2'}])
        self.run_export('gemini-cli')
        self.assertEqual(set(self.project()['sessions']), {'old', 'new'})
        for text in ('legacy question', 'first answer', 'revised answer', 'rewind'):
            self.assertIn(text, self.bodies())

    def test_auto_detect_and_unsupported_host_no_fallback(self):
        write_rows(self.src / 'p' / 's.jsonl', [msg('auto')])
        self.assertEqual(json.loads(self.run_export('auto').stdout)['agent'], 'claude-code')
        self.run_export('cursor', ok=False, out=self.root / 'unsupported')
        self.assertFalse((self.root / 'unsupported').exists())
        with patch.dict(os.environ, self.env, clear=True):
            with self.assertRaisesRegex(ValueError, 'cannot uniquely'):
                exporter.detect()

    def test_missing_source_and_output_inside_source_refused(self):
        self.run_export(src=self.root / 'absent', ok=False)
        self.assertFalse(self.out.exists())
        self.run_export(out=self.src / 'nested', ok=False)
        self.assertFalse((self.src / 'nested').exists())

    def test_hook_preserves_siblings_and_quotes_shell_metacharacters(self):
        cfg = self.root / 'claude'; cfg.mkdir()
        settings = cfg / 'settings.json'
        legacy = {'type': 'command', 'command': f'(nohup python -I "{SCRIPT}" >.export.log &)'}
        foreign = {'type': 'command', 'command': 'echo keep-export_history.py'}
        original = {'permissions': {'allow': ['Read']}, 'hooks': {'SessionEnd': [{'matcher': 'clear', 'hooks': [legacy, foreign]}], 'Stop': [{'hooks': [foreign]}]}}
        settings.write_text(json.dumps(original))
        target = self.root / "out ' $(touch INJECTED)"
        self.run_export(extra=('--install-hook',), out=target)
        data = json.loads(settings.read_text())
        self.assertEqual(data['hooks']['SessionEnd'][0], {'matcher': 'clear', 'hooks': [foreign]})
        command = data['hooks']['SessionEnd'][1]['hooks'][0]['command']
        self.assertIn("'\"'\"'", command)
        self.assertIn('--agent claude-code', command)
        self.run_export(extra=('--install-hook',), out=target)
        self.assertEqual(data, json.loads(settings.read_text()))
        self.run_export(extra=('--uninstall-hook',))
        final = json.loads(settings.read_text())
        self.assertEqual(final['hooks']['Stop'], original['hooks']['Stop'])
        self.assertEqual(final['permissions'], original['permissions'])
        self.assertEqual(final['hooks']['SessionEnd'][0]['hooks'], [foreign])

    def test_non_claude_hook_refused_without_settings_write(self):
        self.run_export('codex', extra=('--install-hook',), ok=False)
        self.assertFalse((self.root / 'claude/settings.json').exists())

    @unittest.skipIf(os.name == 'nt', 'POSIX flock integration')
    def test_concurrent_export_refused(self):
        import fcntl
        self.out.mkdir()
        with (self.out / '.export.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertIn('another export', self.run_export(ok=False).stderr)
        self.run_export()

    def test_custom_environment_roots(self):
        with patch.dict(os.environ, self.env, clear=True):
            roots = exporter.locations()
            self.assertEqual(roots['codex'][0], self.root / 'codex')
            self.assertEqual(roots['claude-code'][0], self.root / 'claude/projects')
            self.assertEqual(roots['gemini-cli'][0], self.root / 'gemini/.gemini/tmp')


if __name__ == '__main__':
    unittest.main()
