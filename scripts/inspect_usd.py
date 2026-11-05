"""Read-only USD composition and authored-physics inspection (requires pxr)."""
import argparse
from pathlib import Path

from _evidence import check_new_report, emit, sha256


def inspect_usd(path, package_root=None):
    from pxr import Usd, UsdGeom, UsdPhysics, UsdUtils

    path = Path(path).resolve()
    stage = Usd.Stage.Open(str(path))
    if not stage:
        raise ValueError('Could not open USD')
    layers, assets, missing = UsdUtils.ComputeAllDependencies(str(path))
    errors = []
    root = stage.GetDefaultPrim()
    if not root:
        errors.append('No valid defaultPrim')
    if missing:
        errors.append('Unresolved asset dependencies')
    dependencies = sorted(set([layer.realPath for layer in layers if not layer.anonymous] + list(assets)))
    outside = []
    if package_root is not None:
        package_root = Path(package_root).resolve()
        for name in dependencies:
            if '://' in name or not Path(name).resolve().is_relative_to(package_root):
                outside.append(name)
        if outside:
            errors.append('Dependencies outside package root or not filesystem resources')
    counts = dict(meshes=0, rigid_bodies=0, colliders=0, joints=0, physics_scenes=0, surface_FEM=0)
    # Include instance proxies to count geometry/physics visible through instances.
    for p in stage.Traverse(Usd.TraverseInstanceProxies()):
        raw = p.GetMetadata('apiSchemas')
        counts['meshes'] += int(p.IsA(UsdGeom.Mesh))
        counts['rigid_bodies'] += int(p.HasAPI(UsdPhysics.RigidBodyAPI))
        counts['colliders'] += int(p.HasAPI(UsdPhysics.CollisionAPI))
        counts['joints'] += int(p.IsA(UsdPhysics.Joint))
        counts['physics_scenes'] += int(p.IsA(UsdPhysics.Scene))
        # Native standalone USD may not register the target runtime's beta schema.
        counts['surface_FEM'] += int('OmniPhysicsSurfaceDeformableSimAPI' in str(raw))
    dangling = []
    # Inspect classes too: flattened prototypes/materials can be root class specs.
    for p in stage.TraverseAll():
        for prop in p.GetRelationships():
            for target in prop.GetTargets():
                if not stage.GetObjectAtPath(target):
                    dangling.append({'property': str(prop.GetPath()), 'target': str(target), 'kind': 'relationship'})
        for prop in p.GetAttributes():
            for target in prop.GetConnections():
                if not stage.GetObjectAtPath(target):
                    dangling.append({'property': str(prop.GetPath()), 'target': str(target), 'kind': 'connection'})
    if dangling:
        errors.append('Dangling relationship or attribute-connection targets')
    units = {'meters_per_unit': UsdGeom.GetStageMetersPerUnit(stage), 'up_axis': str(UsdGeom.GetStageUpAxis(stage)),
             'meters_per_unit_authored': stage.HasAuthoredMetadata('metersPerUnit'),
             'up_axis_authored': stage.HasAuthoredMetadata('upAxis')}
    return {'status': 'FAIL' if errors else 'PASS', 'entry_sha256': sha256(path),
            'validation_scope': 'Static composed stage, active variants, loaded payloads; not PhysX execution or cooked collision',
            'default_prim': str(root.GetPath()) if root else None, 'units': units,
            'counts_including_instance_proxies': counts, 'dependencies': dependencies,
            'unresolved_dependencies': sorted(missing), 'outside_package': outside,
            'dangling_targets': dangling, 'errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('usd', type=Path)
    parser.add_argument('--package-root', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        check_new_report(args.report)
        report = inspect_usd(args.usd, args.package_root)
        emit(report, args.report)
        return int(report['status'] != 'PASS')
    except (ValueError, OSError, ImportError, RuntimeError) as exc:
        parser.exit(2, 'USD inspection failed: %s\n' % exc)


if __name__ == '__main__':
    raise SystemExit(main())
