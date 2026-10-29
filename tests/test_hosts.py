#!/usr/bin/env python3
"""Installer routing contracts; this does not simulate the 14 agent runtimes."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = ('claude-code', 'claude-desktop', 'codex', 'cursor', 'gemini-cli', 'windsurf',
           'devin', 'opencode', 'antigravity', 'copilot-cli', 'commandcode', 'grok-build', 'omp', 'vscode')


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wvs hosts 한글 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        # Child processes only: never change the user's running environment.
        self.env = dict(os.environ, HOME=str(self.root), CLAUDE_CONFIG_DIR=str(self.root / 'claude custom'),
                        GEMINI_CLI_HOME=str(self.root / 'gemini custom'), CODEX_HOME=str(self.root / 'codex custom'))

    def call(self, command):
        result = subprocess.run(command, cwd=self.root, env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_all_client_routes_user_and_project(self):
        for client in CLIENTS:
            for scope in ('user', 'project'):
                with self.subTest(client=client, scope=scope):
                    args = ['--client', client, '--scope', scope, '--dry-run']
                    shell = self.call(['bash', str(ROOT / 'install.sh'), '--source', str(ROOT), *args])
                    node = self.call(['node', str(ROOT / 'bin/wise-vibe-skills.mjs'), 'install', *args])
                    a = [s.strip() for s in shell.splitlines() if s.startswith('  /')]
                    b = [s.strip() for s in node.splitlines() if s.startswith('  /')]
                    self.assertEqual(a, b)
                    if scope == 'project':
                        expected = [] if client == 'claude-desktop' else [str(self.root / ('.claude/skills' if client == 'claude-code' else '.agents/skills'))]
                    else:
                        base = {'claude-code': 'claude custom/skills', 'claude-desktop': 'claude custom/skills',
                                'gemini-cli': 'gemini custom/.agents/skills', 'antigravity': '.gemini/config/skills'}.get(client, '.agents/skills')
                        expected = [str(self.root / base)]
                    self.assertEqual(a, expected)
        self.assertFalse((self.root / '.agents').exists())
        self.assertFalse((self.root / 'claude custom').exists())

    def test_desktop_zip_contains_session_adapter(self):
        target = self.root / 'zips'
        self.call(['node', str(ROOT / 'bin/wise-vibe-skills.mjs'), 'zip', str(target)])
        with zipfile.ZipFile(target / 'wvs-report.zip') as archive:
            self.assertIsNone(archive.testzip())
            for name in ('export_history.py', 'history_sources.py'):
                self.assertIn('wvs-report/scripts/' + name, archive.namelist())


if __name__ == '__main__':
    unittest.main()
