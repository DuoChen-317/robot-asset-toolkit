"""Internal FreeCAD stage; invoke via step_to_glb.py."""
import os
import sys
import traceback

def run():
    import os
    import sys, hashlib
    cli_args = sys.argv[1:]
    sys.argv = ["FreeCAD"]
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    import json
    import math
    import array
    import time
    from pathlib import Path
    import FreeCAD as App
    import FreeCADGui as Gui
    Gui.showMainWindow()
    Gui.getMainWindow().hide()
    import ImportGui
    import MeshPart

    config = json.loads(Path(cli_args[0]).read_text(encoding='utf-8'))
    source = Path(config['source'])
    ROOT = source.parent
    OUT = Path(config['work'])
    INTERMEDIATE = OUT
    if sys.byteorder != 'little':
        raise RuntimeError('This binary intermediate currently requires little-endian runtimes')
    LINEAR_MM = config['linear_mm']
    ANGLE_RAD = math.radians(config['angle_deg'])

    def matrix(placement):
        m = placement.toMatrix()
        return [[getattr(m, 'A%d%d' % (r, c)) * (0.001 if c == 4 and r < 4 else 1)
                 for c in range(1, 5)] for r in range(1, 5)]

    def bbox(bb):
        return [bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax]

    files = [source]
    reports = []
    for file_index, src in enumerate(files):
        started = time.time()
        print('IMPORT', src.name, flush=True)
        doc = App.newDocument('Convert%d' % file_index)
        ImportGui.insert(str(src), doc.Name, merge=False, useLinkGroup=False)
        doc.recompute()
        if any(o.isDerivedFrom('App::Link') for o in doc.Objects):
            raise RuntimeError('Importer retained App::Link instances; expand with verified global placements or use a native assembly exporter, then validate separately')
        nodes = [o for o in doc.Objects if o.TypeId == 'App::Part' or o.isDerivedFrom('Part::Feature')]
        node_names = {o.Name for o in nodes}
        shapes = [o for o in nodes if o.isDerivedFrom('Part::Feature') and not o.Shape.isNull()]
        if not shapes:
            raise RuntimeError('No importable solid/surface parts found')
        scene = {'source': str(src.relative_to(ROOT)), 'name': src.stem,
                 'linear_deflection_mm': LINEAR_MM, 'angular_deflection_degrees': config['angle_deg'],
                 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                 'nodes': [], 'parts': [], 'source_bbox_mm': None}
        total_bounds = App.BoundBox()
        total_mesh_bounds = App.BoundBox()
        count = 0
        bin_path = INTERMEDIATE / 'scene.bin'
        with bin_path.open('wb') as stream:
            for obj in nodes:
                parents = [p for p in obj.InList if p.Name in node_names and p.TypeId == 'App::Part']
                parent = parents[0] if parents else None
                global_place = obj.getGlobalPlacement()
                local_place = parent.getGlobalPlacement().inverse().multiply(global_place) if parent else global_place
                scene['nodes'].append({'id': obj.Name, 'label': obj.Label,
                                       'parent': parent.Name if parent else None,
                                       'matrix_m': matrix(local_place), 'type': obj.TypeId})
                if obj not in shapes:
                    continue
                count += 1
                print('MESH %d/%d %s' % (count, len(shapes), obj.Label), flush=True)
                # Remove the placement already applied inside TopoShape. Scene nodes
                # subsequently restore the exact original assembly placement.
                shape = obj.Shape.copy()
                shape.Placement = App.Placement()
                mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=LINEAR_MM,
                                             AngularDeflection=ANGLE_RAD, Relative=False,
                                             Segments=True)
                points, triangles = mesh.Topology
                if not points or not triangles:
                    raise RuntimeError('Empty mesh: ' + obj.Label)
                if mesh.countSegments() != len(shape.Faces):
                    raise RuntimeError('Face segment count mismatch: ' + obj.Label)
                materials = []
                mat_map = {}
                facet_mats = array.array('I', [0]) * len(triangles)
                appearances = list(obj.ViewObject.ShapeAppearance)
                if not appearances:
                    raise RuntimeError('No readable CAD material appearance for ' + obj.Label)
                assigned = 0
                for face_index in range(len(shape.Faces)):
                    appearance = appearances[face_index] if len(appearances) == len(shape.Faces) else appearances[0]
                    rgba = tuple(float(x) for x in appearance.DiffuseColor)
                    if len(rgba) == 3:
                        rgba = rgba + (1.0,)
                    key = rgba
                    if key not in mat_map:
                        mat_map[key] = len(materials)
                        materials.append(list(rgba))
                    for facet in mesh.getSegment(face_index):
                        facet_mats[facet] = mat_map[key]
                        assigned += 1
                if assigned != len(triangles):
                    raise RuntimeError('Unassigned triangles: ' + obj.Label)
                positions = array.array('f', (v * 0.001 for p in points for v in (p.x, p.y, p.z)))
                indices = array.array('I', (v for t in triangles for v in t))
                record = {'id': obj.Name, 'label': obj.Label, 'offset': stream.tell(),
                          'vertices': len(points), 'triangles': len(triangles),
                          'materials_srgb': materials, 'cad_faces': len(shape.Faces),
                          'cad_solids': len(shape.Solids), 'shape_valid': shape.isValid(),
                          'cad_volume_mm3': shape.Volume, 'mesh_volume_mm3': mesh.Volume}
                positions.tofile(stream)
                indices.tofile(stream)
                facet_mats.tofile(stream)
                scene['parts'].append(record)
                world_shape = shape.copy()
                world_shape.Placement = global_place
                total_bounds.add(world_shape.BoundBox)
                mesh.transform(global_place.toMatrix())
                total_mesh_bounds.add(mesh.BoundBox)
        scene['source_bbox_mm'] = bbox(total_bounds)
        scene['mesh_bbox_mm'] = bbox(total_mesh_bounds)
        scene['triangles'] = sum(p['triangles'] for p in scene['parts'])
        scene['vertices'] = sum(p['vertices'] for p in scene['parts'])
        scene['seconds'] = round(time.time() - started, 2)
        scene['binary'] = bin_path.name
        (INTERMEDIATE / 'scene.json').write_text(json.dumps(scene, ensure_ascii=False, indent=2), encoding='utf-8')
        reports.append(scene)
        print('DONE', src.name, len(scene['parts']), 'parts', scene['triangles'], 'triangles', scene['seconds'], 'seconds', flush=True)
        App.closeDocument(doc.Name)

if __name__ == '__main__':
    code = 0
    try:
        run()
    except BaseException:
        traceback.print_exc()
        code = 1
    sys.stdout.flush()
    sys.stderr.flush()
    # Avoid Qt teardown faults after this isolated, hidden FreeCAD worker exits.
    os._exit(code)
