import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


scripts = Path(__file__).resolve().parents[1] / 'scripts'
spec = importlib.util.spec_from_file_location('step_entry', scripts / 'step_to_glb.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)


class ArtifactLayoutChecks(unittest.TestCase):
    def test_folder_names_do_not_imply_a_project_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            for folder in (root / 'glb', root / 'source' / 'glb', root / 'nested' / 'visuals'):
                with self.subTest(folder=folder):
                    self.assertEqual(entry.resolve_work_dir(folder), folder.parent / '_conversion_work')
            workspace = root / 'pipeline'
            self.assertEqual(entry.resolve_work_dir(root / 'nested' / 'visuals', workspace), workspace)

    def test_failed_conversion_does_not_publish_partial_glb(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / 'input.step'
            source.write_text('fixture', encoding='utf-8')
            output = root / 'models' / 'camera.glb'
            workspace = root / 'pipeline'
            argv = ['step_to_glb.py', str(source), str(output), '--freecad-python', sys.executable,
                    '--blender', sys.executable, '--work-dir', str(workspace)]

            def fail_worker(command, **kwargs):
                config = json.loads(Path(command[-1]).read_text(encoding='utf-8'))
                Path(config['output']).write_bytes(b'unverified geometry')
                raise subprocess.CalledProcessError(1, command)

            with patch.object(sys, 'argv', argv), patch.object(entry.subprocess, 'run', side_effect=fail_worker):
                with self.assertRaises(subprocess.CalledProcessError):
                    entry.main()
            self.assertEqual(list(output.parent.iterdir()), [])
            self.assertEqual(list((workspace / 'intermediate').iterdir()), [])
            self.assertEqual(source.read_text(encoding='utf-8'), 'fixture')


if __name__ == '__main__':
    unittest.main(verbosity=2)
