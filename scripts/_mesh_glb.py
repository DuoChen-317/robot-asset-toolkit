"""Internal Blender stage; invoke via step_to_glb.py."""
import bpy
import sys, hashlib
from mathutils import Matrix, Vector
import array
import json
import math
import numpy as np
from pathlib import Path

config_path = Path(sys.argv[sys.argv.index('--') + 1])
config = json.loads(config_path.read_text(encoding='utf-8'))
OUT = Path(config['output']).parent
INTERMEDIATE = Path(config['work'])
if sys.byteorder != 'little':
    raise RuntimeError('This binary intermediate currently requires little-endian runtimes')

def linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def label(text):
    return text

def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)

def world_bbox():
    lows, highs = [], []
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        coords = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
        obj.data.vertices.foreach_get('co', coords)
        world = np.asarray(obj.matrix_world, dtype=np.float64)
        coords = coords.reshape((-1, 3)).astype(np.float64) @ world[:3, :3].T + world[:3, 3]
        lows.append(coords.min(axis=0)); highs.append(coords.max(axis=0))
    return np.min(lows, axis=0).tolist() + np.max(highs, axis=0).tolist()

def node_snapshot():
    result = {}
    for obj in bpy.context.scene.objects:
        identifier = obj.get('cad_name')
        if not identifier:
            continue
        if identifier in result:
            raise RuntimeError('Duplicate CAD node after import: ' + identifier)
        parent = obj.parent
        while parent and not parent.get('cad_name'):
            parent = parent.parent
        result[identifier] = {
            'parent': parent.get('cad_name') if parent else None,
            'matrix': np.asarray(obj.matrix_world, dtype=np.float64),
            'triangles': len(obj.data.polygons) if obj.type == 'MESH' else None,
            'colors': sorted(tuple(round(float(c), 5) for c in material.diffuse_color)
                             for material in obj.data.materials) if obj.type == 'MESH' else [],
        }
    return result

report_path = Path(config['validation_path'])
validation = []
for metadata in [INTERMEDIATE / 'scene.json']:
    info = json.loads(metadata.read_text(encoding='utf-8'))
    for node in info['nodes']:
        node['label'] = label(node['label'])
    clear()
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0
    objects = {}
    removed_degenerate = 0
    parts = {p['id']: p for p in info['parts']}
    materials = {}
    with (INTERMEDIATE / info['binary']).open('rb') as stream:
        for node in info['nodes']:
            part = parts.get(node['id'])
            if part:
                stream.seek(part['offset'])
                verts = array.array('f'); verts.fromfile(stream, part['vertices'] * 3)
                indices = array.array('I'); indices.fromfile(stream, part['triangles'] * 3)
                face_mats = array.array('I'); face_mats.fromfile(stream, part['triangles'])
                tri_np = np.frombuffer(indices, dtype=np.uint32).reshape(-1, 3)
                valid = (tri_np[:, 0] != tri_np[:, 1]) & (tri_np[:, 1] != tri_np[:, 2]) & (tri_np[:, 2] != tri_np[:, 0])
                removed_degenerate += int(np.count_nonzero(~valid))
                if not valid.all():
                    indices = array.array('I', tri_np[valid].flatten())
                    face_mats = array.array('I', np.frombuffer(face_mats, dtype=np.uint32)[valid])
                triangle_count = len(indices) // 3
                mesh = bpy.data.meshes.new(node['label'])
                mesh.vertices.add(part['vertices'])
                mesh.vertices.foreach_set('co', verts)
                mesh.loops.add(len(indices))
                mesh.loops.foreach_set('vertex_index', indices)
                mesh.polygons.add(triangle_count)
                mesh.polygons.foreach_set('loop_start', list(range(0, len(indices), 3)))
                mesh.polygons.foreach_set('loop_total', [3] * triangle_count)
                mesh.polygons.foreach_set('material_index', face_mats)
                mesh.polygons.foreach_set('use_smooth', [True] * triangle_count)
                mesh.update(calc_edges=True)
                mesh.set_sharp_from_angle(angle=math.radians(30))
                for rgba in part['materials_srgb']:
                    key = tuple(rgba)
                    if key not in materials:
                        mat = bpy.data.materials.new('CAD_Color_%03d' % len(materials))
                        color = tuple(linear(c) for c in rgba[:3]) + (rgba[3],)
                        mat.diffuse_color = color
                        mat.use_nodes = True
                        bsdf = mat.node_tree.nodes.get('Principled BSDF')
                        bsdf.inputs['Base Color'].default_value = color
                        bsdf.inputs['Roughness'].default_value = 0.4
                        materials[key] = mat
                    mesh.materials.append(materials[key])
                obj = bpy.data.objects.new(node['label'], mesh)
                obj['cad_faces'] = part['cad_faces']
            else:
                obj = bpy.data.objects.new(node['label'], None)
                obj.empty_display_type = 'PLAIN_AXES'
                obj.empty_display_size = 0.01
            obj['cad_name'] = node['id']
            obj['cad_label'] = node['label']
            bpy.context.scene.collection.objects.link(obj)
            objects[node['id']] = obj
        for node in info['nodes']:
            obj = objects[node['id']]
            if node['parent']:
                obj.parent = objects[node['parent']]
            obj.matrix_local = Matrix(node['matrix_m'])
    bpy.context.view_layer.update()
    before = world_bbox()
    before_nodes = node_snapshot()
    expected = [v * 0.001 for v in info['mesh_bbox_mm']]
    print('BOUNDS', before, 'EXPECTED', expected, flush=True)
    if max(abs(a-b) for a,b in zip(before, expected)) > 0.000001:
        raise RuntimeError('Assembly placement mismatch: ' + info['name'])
    target = Path(config['output'])
    print('EXPORT', target.name, info['triangles'], 'triangles', flush=True)
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB',
                              export_yup=True, export_normals=True,
                              export_materials='EXPORT', export_extras=True,
                              export_animations=False, export_cameras=False,
                              export_lights=False)
    clear()
    bpy.ops.import_scene.gltf(filepath=str(target))
    bpy.context.view_layer.update()
    after = world_bbox()
    after_nodes = node_snapshot()
    if set(before_nodes) != set(after_nodes):
        raise RuntimeError('CAD node identities changed after GLB roundtrip')
    for identifier, prior in before_nodes.items():
        current = after_nodes[identifier]
        if any(prior[key] != current[key] for key in ('parent', 'triangles')):
            raise RuntimeError('CAD hierarchy/part mesh count changed: ' + identifier)
        if len(prior['colors']) != len(current['colors']) or any(
                max(abs(a-b) for a,b in zip(left,right)) > 0.0001
                for left,right in zip(prior['colors'], current['colors'])):
            raise RuntimeError('Material colors changed after GLB roundtrip: ' + identifier)
        if np.max(np.abs(prior['matrix'][:3,:3] - current['matrix'][:3,:3])) > 0.000001:
            raise RuntimeError('CAD node orientation/scale changed: ' + identifier)
        if np.max(np.abs(prior['matrix'][:3,3] - current['matrix'][:3,3])) * 1000 > config['roundtrip_mm']:
            raise RuntimeError('CAD node translation changed: ' + identifier)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    triangles = sum(len(o.data.polygons) for o in mesh_objs)
    print('COUNTS', len(mesh_objs), len(info['parts']), triangles, info['triangles'], flush=True)
    if triangles != info['triangles'] - removed_degenerate or len(mesh_objs) != len(info['parts']):
        raise RuntimeError('Geometry count mismatch after GLB reimport: ' + info['name'])
    error_mm = max(abs(a-b) for a,b in zip(before, after)) * 1000
    if error_mm > config['roundtrip_mm']:
        raise RuntimeError('GLB size mismatch: ' + info['name'])
    validation.append({'file': target.name,
                       'source_sha256': info['source_sha256'],
                       'glb_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'bytes': target.stat().st_size,
                       'mesh_objects': len(mesh_objs), 'triangles': triangles,
                       'source_tessellation_triangles': info['triangles'],
                       'removed_zero_area_repeated_index_triangles': removed_degenerate,
                       'materials': len(bpy.data.materials),
                       'hierarchy_roundtrip_verified': True,
                       'node_transform_roundtrip_verified': True,
                       'material_color_roundtrip_verified': True,
                       'bbox_m': after, 'roundtrip_bbox_error_mm': error_mm,
                       'result': 'PASS'})
    report_path.write_text(json.dumps(validation[-1], ensure_ascii=False, indent=2), encoding='utf-8')
    print('VERIFIED', target.name, len(mesh_objs), 'parts', triangles, 'triangles', flush=True)
print('ALL GLB FILES VERIFIED', flush=True)
