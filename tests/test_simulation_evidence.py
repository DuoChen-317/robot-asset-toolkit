"""Generated fixtures test optional evidence helpers without vendor assets or Isaac."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_sim_record import inspect_record
from inspect_usd import inspect_usd
from make_preview_gif import make_gif

HAS_NUMPY = importlib.util.find_spec('numpy') is not None
HAS_USD = importlib.util.find_spec('pxr') is not None
FFMPEG = os.environ.get('TOOLKIT_FFMPEG') or shutil.which('ffmpeg')
FFPROBE = os.environ.get('TOOLKIT_FFPROBE') or shutil.which('ffprobe')


@unittest.skipUnless(HAS_NUMPY, 'Optional NumPy is not installed')
class RecordChecks(unittest.TestCase):
    def fixture(self, root, **changes):
        import numpy as np
        poses = np.zeros((4, 2, 7)); poses[..., 6] = 1.
        poses[:, 0, 0] = [0, .02, .02, .07]
        data = dict(telemetry=np.column_stack([np.arange(4) * .01, np.zeros(4)]),
                    poses=poses, nodes=np.zeros((4, 8, 3)))
        data.update(changes)
        p = root / 'record.npz'; np.savez_compressed(p, **data)
        return p

    def test_valid_record_and_retiming_holds(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); p = self.fixture(root)
            mapping = root / 'frames.json'; mapping.write_text('[0, 0, 1, 2, 3, 3]')
            r = inspect_record(p, 'telemetry', 'poses', ['nodes'], 0, frame_map=mapping)
            self.assertEqual(r['status'], 'PASS')
            self.assertEqual(r['samples'], 4)
            self.assertEqual(r['frame_map']['frames'], 6)
            self.assertAlmostEqual(r['duration_s'], .03)

    def test_reject_nonfinite_states_and_nonunit_quaternions(self):
        import numpy as np
        for failure in ['nan_node', 'zero_quaternion', 'wrong_sample_count']:
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as d:
                root = Path(d); p = self.fixture(root)
                with np.load(p) as src: data = {k: src[k] for k in src.files}
                if failure == 'nan_node': data['nodes'][1, 1, 0] = np.nan
                elif failure == 'zero_quaternion': data['poses'][2, 0, 3:] = 0
                else: data['nodes'] = data['nodes'][:-1]
                np.savez_compressed(p, **data)
                self.assertEqual(inspect_record(p, 'telemetry', 'poses', ['nodes'], 0)['status'], 'FAIL')

    def test_reject_repeated_times_and_invalid_frame_identity(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = self.fixture(root, telemetry=np.array([[0., 0], [.01, 0], [.01, 0], [.03, 0]]))
            with self.assertRaises(ValueError): inspect_record(p, 'telemetry', 'poses', time_column=0)
            p = self.fixture(root)
            mapping = root / 'map.json'
            for values in ['[0,4]', '[0,true]', '[0,1.0]', '[]']:
                mapping.write_text(values)
                self.assertEqual(inspect_record(p, 'telemetry', 'poses', time_column=0,
                                                 frame_map=mapping)['status'], 'FAIL')


@unittest.skipUnless(HAS_USD, 'Optional pxr is not installed')
class UsdChecks(unittest.TestCase):
    def fixture(self, path):
        from pxr import Usd, UsdGeom, UsdPhysics, Sdf
        s = Usd.Stage.CreateNew(str(path))
        root = UsdGeom.Xform.Define(s, '/Asset').GetPrim(); s.SetDefaultPrim(root)
        UsdGeom.SetStageMetersPerUnit(s, 1.); UsdGeom.SetStageUpAxis(s, 'Z')
        body = UsdGeom.Xform.Define(s, '/Asset/Body').GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(body)
        cube = UsdGeom.Cube.Define(s, '/Asset/Body/Collision').GetPrim()
        UsdPhysics.CollisionAPI.Apply(cube)
        leaf = UsdGeom.Mesh.Define(s, '/Asset/Leaf').GetPrim()
        leaf.SetMetadata('apiSchemas', Sdf.TokenListOp.CreateExplicit(['OmniPhysicsSurfaceDeformableSimAPI']))
        s.GetRootLayer().Save()
        return s

    def test_inventory_is_read_only_and_sees_unregistered_FEM(self):
        from _evidence import sha256
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'asset.usda'; s = self.fixture(p)
            before = sha256(p); r = inspect_usd(p, Path(d))
            self.assertEqual(r['status'], 'PASS')
            self.assertEqual(r['counts_including_instance_proxies']['rigid_bodies'], 1)
            self.assertEqual(r['counts_including_instance_proxies']['surface_FEM'], 1)
            self.assertEqual(sha256(p), before)

    def test_reject_dangling_targets_and_missing_dependencies(self):
        from pxr import Usd, UsdGeom
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.usda'; s = self.fixture(p)
            s.GetPrimAtPath('/Asset').CreateRelationship('missing').SetTargets(['/Absent'])
            s.GetRootLayer().Save()
            self.assertEqual(inspect_usd(p)['status'], 'FAIL')
            self.assertEqual(inspect_usd(p)['dangling_targets'][0]['target'], '/Absent')
            s.GetPrimAtPath('/Asset').RemoveProperty('missing')
            s.GetRootLayer().subLayerPaths = ['missing-layer.usda']; s.GetRootLayer().Save()
            self.assertEqual(inspect_usd(p)['status'], 'FAIL')
            self.assertTrue(inspect_usd(p)['unresolved_dependencies'])

    def test_dependency_containment_and_instance_meshes(self):
        from pxr import Usd, UsdGeom
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); part = root / 'part.usda'; s = self.fixture(part)
            package = root / 'package'; package.mkdir()
            p = package / 'entry.usda'; composed = Usd.Stage.CreateNew(str(p))
            top = UsdGeom.Xform.Define(composed, '/Asset').GetPrim(); composed.SetDefaultPrim(top)
            for name in ['First', 'Second']:
                child = UsdGeom.Xform.Define(composed, '/Asset/' + name).GetPrim()
                child.GetReferences().AddReference('../part.usda'); child.SetInstanceable(True)
            composed.GetRootLayer().Save()
            report = inspect_usd(p, package)
            self.assertEqual(report['status'], 'FAIL')
            self.assertIn(str(part.resolve()), report['outside_package'])
            self.assertEqual(report['counts_including_instance_proxies']['meshes'], 2)
            self.assertEqual(inspect_usd(p, root)['status'], 'PASS')


@unittest.skipUnless(FFMPEG and FFPROBE, 'Optional FFmpeg/FFprobe are not installed')
class GifChecks(unittest.TestCase):
    def fixture(self, root):
        video = root / 'source.mp4'
        subprocess.run([FFMPEG, '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=80x48:rate=12',
                        '-t', '1', '-c:v', 'mpeg4', str(video)], check=True, capture_output=True)
        return video

    def test_looping_GIF_contains_real_decoded_frames(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = self.fixture(root); out = root / 'out.gif'
            r = make_gif(source, out, FFMPEG, FFPROBE, width=64, fps=8, colors=64, crop=[0, 0, 64, 48])
            self.assertEqual(r['frames'], 8)
            self.assertEqual(r['resolution'], [64, 48])
            self.assertTrue(r['all_frames_decoded'])
            self.assertAlmostEqual(r['duration_s'], 1., delta=.03)
            self.assertIn(b'NETSCAPE2.0\x03\x01\x00\x00', out.read_bytes())
            before = out.read_bytes()
            with self.assertRaises(ValueError): make_gif(source, out, FFMPEG, FFPROBE)
            self.assertEqual(out.read_bytes(), before)

    def test_bad_encoder_does_not_leave_partial_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = self.fixture(root); out = root / 'out.gif'
            with self.assertRaises(OSError): make_gif(source, out, root / 'no-ffmpeg', FFPROBE)
            self.assertFalse(out.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
