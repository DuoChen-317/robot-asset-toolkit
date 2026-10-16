import importlib.util
import math
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

skill = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('urdf_helper', skill / 'scripts/check_pack_urdf.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class BundleChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='urdf-skill-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.mesh = b'fixture'.ljust(80, b'\0') + struct.pack('<I', 1) + struct.pack('<12fH', 0,0,1,0,0,0,1,0,0,0,1,0,0)
        (self.root / 'part.stl').write_bytes(self.mesh)
        self.xml = '''<robot name="sample"><link name="base"/><link name="tool"><visual><geometry><mesh filename="part.stl"/></geometry></visual></link><joint name="attach" type="fixed"><parent link="base"/><child link="tool"/><origin xyz="0.1 0 0.2" rpy="0 0 0.3"/></joint></robot>'''
        self.urdf = self.root / 'input.urdf'
        self.urdf.write_text(self.xml, encoding='utf-8')

    def test_portable_pack_preserves_geometry_transform_and_zip_payload(self):
        destination = self.root / 'final'
        archive = self.root / 'final.zip'
        report = helper.pack(self.urdf, {}, destination, archive)
        tree, data, checked = helper.load_check(destination / 'robot.urdf', {})
        self.assertEqual(tree.find('joint/origin').attrib, {'xyz':'0.1 0 0.2','rpy':'0 0 0.3'})
        self.assertEqual(list(data.values()), [self.mesh])
        self.assertTrue(checked['static_checks_passed'])
        with zipfile.ZipFile(archive) as bundle:
            self.assertEqual(bundle.read('final/meshes/part.stl'), self.mesh)
        self.assertTrue(report['archive']['internal_meshes_checked'])

    def test_tsd_and_truncation_rejected(self):
        for content in (b'%TSD-Header-###%' + bytes(200), self.mesh[:-1]):
            with self.assertRaises(ValueError):
                helper.inspect_mesh(Path('bad.stl'), content)

    def test_nan_rejected(self):
        bad = bytearray(self.mesh)
        struct.pack_into('<f', bad, 96, math.nan)
        with self.assertRaisesRegex(ValueError, 'NaN/Inf'):
            helper.inspect_mesh(Path('nan.stl'), bad)

    def test_disconnected_and_multiple_parent_rejected(self):
        bad = self.xml.replace('</robot>', '<link name="extra"/></robot>')
        self.urdf.write_text(bad, encoding='utf-8')
        with self.assertRaises(ValueError):
            helper.load_check(self.urdf, {})
        bad = self.xml.replace('</robot>', '<joint name="again" type="fixed"><parent link="base"/><child link="tool"/></joint></robot>')
        self.urdf.write_text(bad, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'multiple parents'):
            helper.load_check(self.urdf, {})

    def test_package_uri_and_escape(self):
        self.urdf.write_text(self.xml.replace('part.stl','package://robot_description/part.stl'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Unmapped'):
            helper.load_check(self.urdf, {})
        _, _, report = helper.load_check(self.urdf, {'robot_description': self.root})
        self.assertEqual(report['meshes'][0]['triangles'], 1)
        self.urdf.write_text(self.xml.replace('part.stl','package://robot_description/../part.stl'),encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'escapes'):
            helper.load_check(self.urdf, {'robot_description': self.root})

    def test_no_overwrite(self):
        destination = self.root / 'output'
        destination.mkdir()
        marker = destination / 'keep.txt'
        marker.write_text('keep',encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            helper.pack(self.urdf, {}, destination, None)
        self.assertEqual(marker.read_text(), 'keep')

    def test_primitive_only(self):
        self.urdf.write_text('<robot name="primitive"><link name="base"><visual><geometry><box size="1 1 1"/></geometry></visual></link></robot>',encoding='utf-8')
        report = helper.pack(self.urdf, {}, self.root / 'primitive', None)
        self.assertTrue(report['static_checks_passed'])

    def test_basename_collisions(self):
        (self.root/'second').mkdir()
        second = self.mesh[:-2] + b'\x01\x00'
        (self.root/'second/part.stl').write_bytes(second)
        xml = self.xml.replace('</visual>', '</visual><collision><geometry><mesh filename="second/part.stl"/></geometry></collision>')
        self.urdf.write_text(xml,encoding='utf-8')
        destination = self.root / 'output'
        helper.pack(self.urdf, {}, destination, None)
        self.assertEqual({p.read_bytes() for p in (destination/'meshes').iterdir()}, {self.mesh, second})


if __name__ == '__main__':
    unittest.main(verbosity=2)
