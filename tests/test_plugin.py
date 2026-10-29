# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Gyccc0828 and contributors
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/codex-speed-overlay'


class PluginTests(unittest.TestCase):
    def test_hook_is_bounded_asynchronous_and_only_starts_or_resumes(self):
        group = json.loads((PLUGIN / 'hooks/hooks.json').read_text(encoding='utf-8'))['hooks']['SessionStart'][0]
        self.assertEqual(group['matcher'], '^(startup|resume)$')
        hook = group['hooks'][0]
        self.assertTrue(hook['async'])
        self.assertEqual(hook['timeout'], 3)
        self.assertIn('${PLUGIN_ROOT}', hook['command'])
        self.assertNotIn('dangerously-bypass-hook-trust', hook['command'])

    @unittest.skipUnless(os.name == 'nt', 'Windows Script Host required')
    def test_missing_runtime_exits_quietly(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'scripts').mkdir()
            script = root / 'scripts/start-overlay.vbs'
            shutil.copy2(PLUGIN / 'scripts/start-overlay.vbs', script)
            for runtime in (None, str(root / 'missing/pythonw.exe')):
                with self.subTest(runtime=runtime):
                    if runtime is not None:
                        (root / 'runtime-path.txt').write_text(runtime, encoding='utf-16')
                    result = subprocess.run(['cscript.exe', '//B', '//NoLogo', str(script)],
                                            capture_output=True, timeout=3)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b'', b''))


@unittest.skipUnless(os.name == 'nt', 'Windows GUI required')
class GuiTests(unittest.TestCase):
    def test_labels_are_consistent_and_close_stops_timer(self):
        from PyQt5 import QtCore, QtGui, QtWidgets
        sys.path.insert(0, str(PLUGIN / 'app'))
        loader = importlib.machinery.SourceFileLoader('overlay_test', str(PLUGIN / 'app/overlay.pyw'))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        window = module.Overlay()
        try:
            self.assertEqual((window.width(), window.height()), (282, 90))
            for label in (window.model, window.speed, window.status):
                label.ensurePolished()
                self.assertEqual(label.font().pixelSize(), 14)
                self.assertEqual(label.palette().color(QtGui.QPalette.WindowText).name(), '#111827')
            self.assertTrue(window.testAttribute(QtCore.Qt.WA_TranslucentBackground))
            window.close_button.click()
            self.assertTrue(window.stop.is_set())
            self.assertFalse(window.timer.isActive())
        finally:
            window.close()


if __name__ == '__main__':
    unittest.main()
