# STEP/STP to GLB

Use this workflow for CAD parts or ordinary assemblies, independently of URDF creation. The entry point orchestrates explicit FreeCAD tessellation and Blender GLB export. Neither runtime is installed by the script.

## Run

Discover an installed FreeCAD Python runtime that can import FreeCAD/FreeCADGui/MeshPart and a Blender executable. A generic FreeCAD command-line executable is not necessarily interchangeable with its Python runtime.

```sh
python scripts/step_to_glb.py input.step output.glb \
  --freecad-python /path/to/freecad/python \
  --blender /path/to/blender \
  --linear-mm 0.01 --angle-deg 5
```

Quote paths containing spaces and pass each argument independently. On Windows, use the PowerShell example in the root README. Do not hard-code another machine's software location.

| Option | Meaning |
| --- | --- |
| `--linear-mm` | Absolute linear tessellation deflection in millimetres; starts at 0.01 |
| `--angle-deg` | Angular tessellation deflection in degrees; starts at 5 |
| `--roundtrip-mm` | Maximum export/re-import vertex-bounds and node-translation discrepancy; starts at 0.001 |
| `--timeout` | Maximum seconds for each stage; starts at 1800 |

Select settings for the asset size and use. A timeout is not permission to reduce fidelity silently. Mesh deflection settings and round-trip bounds are not measured global CAD surface error.

## Workers and outputs

- `step_to_glb.py` validates paths/settings, refuses existing outputs, runs two isolated processes and manages temporary intermediate files.
- `_step_mesh.py` runs inside FreeCAD with an offscreen hidden GUI. It reads the STEP, records the source hash and BRep validity, and generates segmented triangle meshes and readable face colours.
- `_mesh_glb.py` runs in background Blender, reconstructs the part hierarchy/placements and exports GLB. It re-imports the GLB to check mesh counts, triangle counts, vertex bounds, CAD identities, parents, transforms and material colours.

Invoke the entry point, not the workers directly. Output consists of the GLB, `.conversion.json` and `.validation.json`. A successful result needs the validation report's `PASS`, input identity and actual output hash, not simply an existing GLB.

FreeCAD document coordinates are tessellated in millimetres and converted to metres once. Keep Blender import scale at 1. Retain assembly coordinates; upright/centred/grounded presentation changes are separate, explicitly recorded transforms when requested.

There is no general decimation. Repeated-index degenerate triangles are removed and counted. Readable CAD colour groups are preserved as generated PBR materials; this is not a promise to preserve every original CAD shader or transparency property. The GLB does not preserve exact analytic CAD surfaces.

## Compatibility and failures

The integration was exercised with FreeCAD 1.1.1 and Blender 5.1.2 on Windows. Other versions/platforms need their APIs and results checked. The intermediate format currently expects little-endian runtimes.

The worker supports ordinary `App::Part` / `Part::Feature` hierarchy. Retained `App::Link` instances cause an explicit error rather than missing geometry. Expand them with verified global placements or use an appropriate native assembly exporter and validate separately. Do not simply ignore instance nodes.

Missing appearances, empty meshes, inconsistent CAD-face segments or unassigned triangles stop conversion. Investigate the specific part; any material fallback should be explicit. Invalid source BReps are recorded and are not repaired merely by exporting a successful mesh.

After failure, a partial/unverified GLB may exist. Keep the failure evidence and choose a new output or handle only the known failed files. Do not remove unrelated versions.

FreeCAD native GLB export is another possible route for complex assemblies, but display `ViewObject.Deviation` should not be described as an absolute millimetre error setting. For explicit absolute tessellation, this toolkit uses MeshPart. A preview image is optional and does not replace geometry checks.
