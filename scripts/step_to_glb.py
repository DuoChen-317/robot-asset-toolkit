#!/usr/bin/env python3
"""Convert STEP/STP with explicit tessellation using FreeCAD and Blender runtimes."""
import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Bundled Python runtimes may omit the script directory from sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from artifact_layout import resolve_work_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--freecad-python', required=True, type=Path)
    parser.add_argument('--blender', required=True, type=Path)
    parser.add_argument('--work-dir', type=Path,
                        help='Separate process workspace; defaults to a sibling _conversion_work directory')
    parser.add_argument('--linear-mm', type=float, default=0.01)
    parser.add_argument('--angle-deg', type=float, default=5.0)
    parser.add_argument('--roundtrip-mm', type=float, default=0.001)
    parser.add_argument('--timeout', type=float, default=1800,
                        help='Timeout seconds for each conversion stage')
    args = parser.parse_args()
    source, output = args.source.expanduser().resolve(), args.output.expanduser().resolve()
    if source.suffix.lower() not in ('.step', '.stp') or not source.is_file():
        parser.error('Source must be an existing STEP/STP file')
    if output.suffix.lower() != '.glb':
        parser.error('Output must have a .glb suffix')
    for key in ('linear_mm', 'angle_deg', 'roundtrip_mm', 'timeout'):
        if not math.isfinite(getattr(args, key)) or getattr(args, key) <= 0:
            parser.error(key + ' must be positive and finite')
    if args.angle_deg > 180:
        parser.error('angle-deg must not exceed 180')
    for executable in (args.freecad_python, args.blender):
        if not executable.is_file():
            parser.error('Executable missing: ' + str(executable))
    try:
        work_dir = resolve_work_dir(output.parent, args.work_dir)
    except ValueError as exc:
        parser.error(str(exc))
    reports = work_dir / 'reports'
    conversion = reports / (output.stem + '.conversion.json')
    validation = reports / (output.stem + '.validation.json')
    for target in (output, conversion, validation):
        if target.exists():
            parser.error('Refusing existing output: ' + str(target))
    output.parent.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    intermediates = work_dir / 'intermediate'
    intermediates.mkdir(parents=True, exist_ok=True)
    scripts = Path(__file__).resolve().parent
    # Intermediates are kept out of the user's final asset folder.
    with tempfile.TemporaryDirectory(prefix='step-glb-', dir=intermediates) as temporary:
        work = Path(temporary)
        staged_output = work / output.name
        config = work / 'config.json'
        config.write_text(json.dumps({
            'source': str(source), 'output': str(staged_output), 'work': str(work),
            'validation_path': str(validation),
            'linear_mm': args.linear_mm, 'angle_deg': args.angle_deg,
            'roundtrip_mm': args.roundtrip_mm,
        }), encoding='utf-8')
        subprocess.run([str(args.freecad_python), '-u', str(scripts / '_step_mesh.py'),
                        str(config)], check=True, timeout=args.timeout)
        subprocess.run([str(args.blender), '--background', '--factory-startup',
                        '--python-exit-code', '1', '--python', str(scripts / '_mesh_glb.py'),
                        '--', str(config)], check=True, timeout=args.timeout)
        info = json.loads((work / 'scene.json').read_text(encoding='utf-8'))
        result = json.loads(validation.read_text(encoding='utf-8'))
        if result.get('result') != 'PASS' or not staged_output.is_file():
            raise RuntimeError('Conversion did not produce verified GLB')
        info.pop('binary', None)
        info['output'] = str(output)
        conversion.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
        if output.exists():
            raise FileExistsError('Refusing existing output: ' + str(output))
        shutil.move(str(staged_output), str(output))
    print('Verified GLB:', output, flush=True)
    print('Validation:', validation, flush=True)


if __name__ == '__main__':
    main()
