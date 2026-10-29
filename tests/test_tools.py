#!/usr/bin/env python3
"""Exercise wvs against disposable files, without deployments or account access."""
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WVS = ROOT / 'skills/wvs-tools/scripts/wvs'


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wvs tools 한글 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def cli(self, *args, ok=True):
        result = subprocess.run(['bash', str(WVS), *map(str, args)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def test_clean_dry_run_then_remove_only_target(self):
        target = self.root / 'target'; target.mkdir()
        metadata, keep = target / '.DS_Store', target / 'keep.txt'
        metadata.write_text('temp'); keep.write_text('keep')
        self.cli('clean', '--dry-run', target)
        self.assertTrue(metadata.exists()); self.assertEqual(keep.read_text(), 'keep')
        self.cli('clean', '-y', target)
        self.assertFalse(metadata.exists()); self.assertEqual(keep.read_text(), 'keep')

    def test_bookmark_folder_global_and_dry_run(self):
        a = {'type': 'url', 'name': 'A', 'url': 'https://example.org/a'}
        data = {'roots': {'bookmark_bar': {'type': 'folder', 'children': [a, a,
                {'type': 'folder', 'name': 'nested', 'children': [a]}]}}}
        source = self.root / 'Bookmarks'; source.write_text(json.dumps(data))
        before = source.read_bytes()
        self.cli('bookmarks', '-i', source, '--dry-run')
        self.assertEqual(before, source.read_bytes())
        for mode, nested in [('folder', 1), ('global', 0)]:
            output = self.root / f'{mode}.json'
            self.cli('bookmarks', '-i', source, '-o', output, '--mode', mode)
            children = json.loads(output.read_text())['roots']['bookmark_bar']['children']
            self.assertEqual(len(children), 2)
            self.assertEqual(len(children[1]['children']), nested)
            self.assertEqual(before, source.read_bytes())

    def test_archive_dry_run(self):
        target = self.root / 'source'; target.mkdir(); (target / 'keep').write_text('keep')
        self.cli('archive', '--dry-run', target)
        self.assertFalse(list(self.root.glob('*.tar.gz')))
        self.assertTrue(target.exists())

    @unittest.skipUnless(shutil.which('gtar'), 'GNU tar required; tests never install system tools')
    def test_archive_contents_and_source_preservation(self):
        target = self.root / 'source'; target.mkdir()
        (target / 'keep.txt').write_text('contents'); (target / '.DS_Store').write_text('exclude')
        self.cli('archive', '-y', target)
        with tarfile.open(next(self.root.glob('*.tar.gz'))) as archive:
            self.assertTrue(any(n.endswith('keep.txt') for n in archive.getnames()))
            self.assertFalse(any(n.endswith('.DS_Store') for n in archive.getnames()))
        self.assertTrue((target / 'keep.txt').exists())

    def test_invalid_deploy_target_is_local_error(self):
        self.cli('deploy', 'invalid', ok=False)

    def test_gnu_tar_named_tar_needs_no_package_install(self):
        source = (WVS.parent / 'lib/archive-tgz.sh').read_text()
        functions = source.rsplit('main "$@"', 1)[0]
        # Stub only tool discovery and the installation boundary, keeping the
        # real resolver. A package installation attempt makes this test fail.
        probe = functions + '''
command_exists() { [ "$1" = tar ]; }
tar() { echo 'tar (GNU tar) 1.35'; }
install_gtar_linux() { return 99; }
ensure_tar linux || exit 99
[ "$TAR_CMD" = tar ]
'''
        result = subprocess.run(['bash'], input=probe, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pdf_dispatch_explicit_input_and_spaces(self):
        launcher = self.root / 'wvs'
        shutil.copy2(WVS, launcher)
        lib = self.root / 'lib'; lib.mkdir()
        for name in ('convert2pdf.sh', 'docx2pdf.sh'):
            (lib / name).write_text("#!/bin/bash\nprintf '%s\\n' \"$@\"\n")
        for args in (['--input=한글 report.md', '--cleanup'], ['-I', '한글 report.md', '-C'], ['한글 report.md', '-C']):
            result = subprocess.run(['bash', str(launcher), 'pdf', *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            passed = result.stdout.splitlines()
            self.assertIn('한글 report.md', passed)
            self.assertEqual(passed.count('-I'), 1)


if __name__ == '__main__':
    unittest.main()
