#!/usr/bin/env python3
"""Check local URDF resources, then optionally build an independent portable bundle.

Standard library only. Does not change kinematics or estimate physical parameters.
"""
import argparse
import copy
import hashlib
import json
import math
import re
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numbers(text, count, label):
    values = [float(value) for value in text.split()]
    require(len(values) == count and all(math.isfinite(x) for x in values),
            f'{label}: expected {count} finite numbers, got {text!r}')
    return values


def package_map(items):
    result = {}
    for item in items:
        name, sep, directory = item.partition('=')
        require(sep and name and directory, '--package requires name=directory')
        require(name not in result, f'Duplicate package mapping: {name}')
        result[name] = Path(directory).expanduser().resolve()
        require(result[name].is_dir(), f'Package directory missing: {directory}')
    return result


def resolve_mesh(uri, urdf, packages):
    require(uri, 'Mesh filename is empty')
    if uri.startswith('package://'):
        package, sep, relative = uri[10:].partition('/')
        require(sep and package in packages, f'Unmapped {uri}; supply --package {package}=directory')
        root = packages[package]
        path = (root / unquote(relative)).resolve()
        require(path.is_relative_to(root), f'Package URI escapes its package: {uri}')
    elif uri.startswith('file://'):
        parts = urlsplit(uri)
        require(parts.netloc in ('', 'localhost'), f'Remote file URI not supported: {uri}')
        raw = unquote(parts.path)
        if sys.platform == 'win32' and re.match(r'^/[A-Za-z]:/', raw):
            raw = raw[1:]
        path = Path(raw).resolve()
    else:
        require('://' not in uri, f'Remote mesh unsupported by local checker: {uri}')
        # Accept both common slash styles on the current host.
        path = Path(unquote(uri).replace('\\', '/')).expanduser()
        if not path.is_absolute():
            path = urdf.parent / path
        path = path.resolve()
    require(path.is_file(), f'Missing mesh: {uri} -> {path}')
    return path


def inspect_mesh(path, data):
    require(not data.startswith(b'%TSD-Header-###%'),
            f'{path.name}: TSD-wrapped content, not readable standard mesh data; re-export/repackage from a readable source')
    info = {'file': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if path.suffix.lower() != '.stl':
        info['geometry_check'] = 'not checked; use the target format loader and include dependencies'
        return info
    require(len(data) >= 84, f'{path.name}: too short for binary STL')
    triangles = struct.unpack_from('<I', data, 80)[0]
    expected = 84 + triangles * 50
    if len(data) != expected:
        if data.lstrip().lower().startswith(b'solid'):
            raise ValueError(f'{path.name}: ASCII or malformed STL; this checker requires binary STL. Convert using a mesh/CAD loader and retry.')
        raise ValueError(f'{path.name}: invalid binary STL length {len(data)}; header declares {triangles} triangles, expected {expected}')
    require(triangles > 0, f'{path.name}: empty STL')
    low, high = [math.inf] * 3, [-math.inf] * 3
    for index, record in enumerate(struct.iter_unpack('<12fH', memoryview(data)[84:])):
        require(all(math.isfinite(v) for v in record[:12]), f'{path.name}: NaN/Inf at triangle {index}')
        for offset in (3, 6, 9):
            for axis in range(3):
                value = record[offset + axis]
                low[axis] = min(low[axis], value)
                high[axis] = max(high[axis], value)
    info.update(binary_stl_valid=True, triangles=triangles, raw_bounds=low + high)
    return info


def load_check(urdf, packages):
    require(urdf.is_file(), f'URDF missing: {urdf}')
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.fromstring(urdf.read_bytes(), parser=parser)
    require(root.tag == 'robot', 'Expected a concrete robot URDF, not Xacro or another XML format')
    links, joints = root.findall('link'), root.findall('joint')
    names = [link.get('name') for link in links]
    require(names and all(names) and len(names) == len(set(names)), 'Missing or duplicate link names')
    joint_names = [joint.get('name') for joint in joints]
    require(all(joint_names) and len(joint_names) == len(set(joint_names)), 'Missing or duplicate joint names')
    parents, children = {}, {name: [] for name in names}
    warnings = []
    supported = {'fixed', 'revolute', 'continuous', 'prismatic', 'floating', 'planar'}
    for joint in joints:
        name, kind = joint.get('name'), joint.get('type')
        require(kind in supported, f'{name}: unsupported joint type {kind}')
        p, c = joint.find('parent'), joint.find('child')
        require(p is not None and c is not None, f'{name}: parent/child missing')
        parent, child = p.get('link'), c.get('link')
        require(parent in children and child in children and parent != child, f'{name}: invalid parent/child')
        require(child not in parents, f'{child}: multiple parents')
        parents[child] = parent
        children[parent].append(child)
        if kind in ('revolute', 'continuous', 'prismatic'):
            axis = joint.find('axis')
            xyz = numbers(axis.get('xyz', '1 0 0') if axis is not None else '1 0 0', 3, f'{name} axis')
            require(sum(v * v for v in xyz) > 1e-20, f'{name}: zero joint axis')
            limit = joint.find('limit')
            if kind in ('revolute', 'prismatic'):
                require(limit is not None, f'{name}: limit missing')
                lower, upper = numbers(f"{limit.get('lower', 'nan')} {limit.get('upper', 'nan')}", 2, f'{name} limits')
                require(lower <= upper, f'{name}: lower limit exceeds upper')
            if limit is None:
                warnings.append(f'{name}: effort/velocity limits not supplied')
            else:
                for attr in ('effort', 'velocity'):
                    raw = limit.get(attr)
                    if raw is None:
                        warnings.append(f'{name}: {attr} missing')
                    else:
                        value = numbers(raw, 1, f'{name} {attr}')[0]
                        require(value >= 0, f'{name}: negative {attr}')
                        if value == 0:
                            warnings.append(f'{name}: {attr}=0; control capability not validated')
        mimic = joint.find('mimic')
        if mimic is not None:
            require(mimic.get('joint') in joint_names and mimic.get('joint') != name, f'{name}: invalid mimic joint')
    roots = set(names) - set(parents)
    require(len(roots) == 1, f'Expected one root link, got {sorted(roots)}')
    seen, pending = set(), [next(iter(roots))]
    while pending:
        current = pending.pop()
        require(current not in seen, f'Cycle at {current}')
        seen.add(current)
        pending.extend(children[current])
    require(seen == set(names), 'Disconnected link graph or cycle')
    for origin in root.findall('.//origin'):
        for attr in ('xyz', 'rpy'):
            numbers(origin.get(attr, '0 0 0'), 3, f'origin {attr}')
    for link in links:
        if link.find('inertial') is None:
            warnings.append(f"{link.get('name')}: inertial absent; physical parameters not validated")
    blobs, mesh_reports = {}, []
    for mesh in root.findall('.//mesh'):
        scale = numbers(mesh.get('scale', '1 1 1'), 3, 'mesh scale')
        require(all(v > 0 for v in scale), 'Mesh scale must be positive; bake mirrored geometry before export')
        path = resolve_mesh(mesh.get('filename'), urdf, packages)
        if path not in blobs:
            blobs[path] = path.read_bytes()
            mesh_reports.append(inspect_mesh(path, blobs[path]))
    if not blobs:
        warnings.append('Primitive-only URDF: mesh checks not applicable; verify primitive dimensions in the target loader')
    if root.findall('.//texture'):
        warnings.append('Texture dependencies require explicit collection; automatic pack is disabled for this URDF')
    for info in mesh_reports:
        if not info.get('binary_stl_valid'):
            warnings.append(f"{Path(info['file']).name}: non-STL geometry and dependent files need loader validation")
    report = {'static_checks_passed': True, 'urdf': str(urdf), 'root_link': next(iter(roots)),
              'links': len(links), 'joints': len(joints),
              'joint_types': {kind: sum(j.get('type') == kind for j in joints) for kind in sorted(supported) if any(j.get('type') == kind for j in joints)},
              'meshes': mesh_reports, 'warnings': warnings,
              'not_validated': ['surface error', 'assembly alignment', 'collision', 'inertia correctness', 'mimic coupling semantics', 'simulator import', 'controller behavior']}
    return root, blobs, report


def pack(urdf, packages, out, archive_path):
    root, blobs, report = load_check(urdf, packages)
    require(not root.findall('.//texture'), 'Automatic pack does not collect textures; explicitly package materials/textures instead')
    require(all(path.suffix.lower() == '.stl' for path in blobs), 'Automatic pack currently supports binary STL only; preserve other mesh dependency trees manually')
    require(not out.exists() or (out.is_dir() and not any(out.iterdir())), f'Refusing nonempty output: {out}')
    require(archive_path is None or not archive_path.exists(), f'Refusing existing archive: {archive_path}')
    mapping, used, payload = {}, set(), {}
    for path, data in blobs.items():
        # Stable, portable names, including collision handling across source directories.
        stem = re.sub(r'[^A-Za-z0-9_-]', '_', path.stem) or 'mesh'
        name, suffix = stem + '.stl', 1
        while name.lower() in used:
            name = f'{stem}_{suffix}.stl'
            suffix += 1
        used.add(name.lower())
        mapping[path] = 'meshes/' + name
        payload[mapping[path]] = data
    portable = copy.deepcopy(root)
    for mesh in portable.findall('.//mesh'):
        mesh.set('filename', mapping[resolve_mesh(mesh.get('filename'), urdf, packages)])
    payload['robot.urdf'] = ET.tostring(portable, encoding='utf-8', xml_declaration=True)
    payload['README.txt'] = (
        'Import robot.urdf; keep meshes/ beside it. Units must be verified as metres/radians.\n'
        'This bundle passed static tree/path/binary-STL checks. These checks do not prove simulation readiness.\n'
        'Kinematics, inertial values, scale and mesh geometry are preserved from the input.\n'
        'Source warnings:\n' + '\n'.join(report['warnings']) + '\n'
    ).encode('utf-8')
    if archive_path is not None:
        if archive_path.is_relative_to(out):
            require(archive_path.relative_to(out).as_posix() not in payload, 'Archive path collides with a bundle member')
        archive_path.parent.mkdir(parents=True, exist_ok=True)
    # Validate the newly serialized XML and actual staged files before publishing.
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='urdf-stage-', dir=out.parent) as temporary:
        stage = Path(temporary)
        for name, data in payload.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        load_check(stage / 'robot.urdf', {})
        for name, data in payload.items():
            path = out / name
            path.parent.mkdir(parents=True, exist_ok=True)
            require(not path.exists(), f'Output changed during packing: {path}')
            with path.open('xb') as stream:
                stream.write(data)
    if archive_path is not None:
        with zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in sorted(payload.items()):
                archive.writestr(out.name + '/' + name, data)
        with zipfile.ZipFile(archive_path) as archive:
            require(archive.testzip() is None, 'ZIP CRC failed')
            for name, expected in payload.items():
                actual = archive.read(out.name + '/' + name)
                require(actual == expected, f'ZIP payload differs: {name}')
                if name.endswith('.stl'):
                    inspect_mesh(Path(name), actual)
        report['archive'] = {'path': str(archive_path), 'sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(), 'internal_meshes_checked': True}
    report['portable_urdf'] = str(out / 'robot.urdf')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['validate', 'pack'])
    parser.add_argument('urdf', type=Path)
    parser.add_argument('--package', action='append', default=[], metavar='NAME=DIRECTORY')
    parser.add_argument('--out', type=Path, help='Empty/new destination directory for pack')
    parser.add_argument('--zip', type=Path, dest='archive', help='Optional new ZIP path for pack')
    parser.add_argument('--report', type=Path, help='Optional new JSON report path')
    args = parser.parse_args()
    try:
        require(args.report is None or not args.report.exists(), 'Refusing existing report')
        urdf, packages = args.urdf.expanduser().resolve(), package_map(args.package)
        if args.mode == 'pack':
            require(args.out is not None, '--out is required for pack')
            report = pack(urdf, packages, args.out.expanduser().resolve(),
                          args.archive.expanduser().resolve() if args.archive else None)
        else:
            require(args.out is None and args.archive is None, '--out/--zip only apply to pack')
            _, _, report = load_check(urdf, packages)
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            with args.report.open('x', encoding='utf-8') as stream:
                stream.write(text + '\n')
        print(text)
        return 0
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile) as exc:
        print(json.dumps({'static_checks_passed': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
