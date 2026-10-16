# Robot Asset Toolkit

[English](README.md) | [简体中文](README.zh-CN.md)

An agent skill and a small set of tools for moving robot assets from CAD and visual assemblies to URDF and articulated USD.

**Keep the source of truth clear: CAD/GLB for appearance; verified robot descriptions for motion and physics.**

## What it does

| Workflow | Delivery |
| --- | --- |
| STEP/STP → GLB | Explicit tessellation, readable CAD colours and assembly hierarchy, automatic Blender round-trip checks |
| Robot + tool assembly | Mating-face alignment, coordinate transforms and interference assessment |
| Existing URDF extension | New fixed or moving components while preserving the original mechanism |
| URDF from an assembly | A structured process for rigid bodies, joints, frames and missing mechanism data |
| AGV/AMR + arm | Whole-robot composition, wheel/lift joints, mobile-root handling and validation |
| URDF + GLB → articulated USD | Preserve robot physics and attach GLB visuals/materials to their actual links |
| Final URDF packaging | Static checks, portable mesh paths and ZIP-internal STL validation |

This is **a skill plus focused CLI tools**, not a universal automatic robot reconstructor. Assembly interpretation, link mapping, dynamics and USD composition require model-specific work. It does not implement navigation, controllers or task scheduling.

## Install as a skill

Clone the repository, then place or link its whole directory in a skill discovery location supported by your agent. The directory contains `SKILL.md`, `agents/`, `references/` and `scripts/`; keep them together. Follow your agent's current installation documentation for the exact discovery path.

```sh
git clone https://github.com/DuoChen-317/robot-asset-toolkit.git
```

In Codex, you can also ask the skill installer:

```text
Use $skill-installer to install the skill from https://github.com/DuoChen-317/robot-asset-toolkit.
```

Example requests:

```text
Use $robot-asset-toolkit to convert this STEP assembly to a high-fidelity GLB.
Use $robot-asset-toolkit to mount this gripper on my existing robot URDF.
Use $robot-asset-toolkit to combine this mobile base and arm into one robot description.
Use $robot-asset-toolkit to create an Isaac USD using my URDF for physics and GLB for appearance.
```

The skill instructions are English; the agent should respond in the user's language.

## Run the tools directly

The entry-point tools use Python 3.10+ and the standard library. Runtime-specific conversion workers use the Python modules bundled with FreeCAD and Blender; installing `bpy` or FreeCAD into the system Python is not required.

### STEP to GLB

Install FreeCAD and Blender separately and supply their actual executable paths:

```sh
python scripts/step_to_glb.py input.step output.glb \
  --freecad-python /path/to/freecad/python \
  --blender /path/to/blender \
  --linear-mm 0.01 --angle-deg 5
```

PowerShell example:

```powershell
python scripts/step_to_glb.py 'D:/models/input.step' 'D:/exports/output.glb' `
  --freecad-python 'C:/Apps/FreeCAD/bin/python.exe' `
  --blender 'C:/Apps/Blender/blender.exe' `
  --linear-mm 0.01 --angle-deg 5
```

Outputs: the GLB plus `.conversion.json` and `.validation.json` sidecars. Existing outputs are refused. Source CAD is unchanged; there is no general decimation or automatic recentering/uprighting. Repeated-index degenerate triangles are removed and counted.

`0.01 mm` and `5°` are configurable starting settings, **not a measured global surface-error guarantee**. Round-trip checks cover parts, triangles, actual vertex bounds, hierarchy, node transforms and readable material colours. See [conversion details and limitations](references/step-to-glb.md).

### Check a URDF

```sh
python scripts/check_pack_urdf.py validate /path/to/robot.urdf
python scripts/check_pack_urdf.py validate /path/to/robot.urdf \
  --package robot_description=/path/to/robot_description
```

### Build a portable URDF bundle

```sh
python scripts/check_pack_urdf.py pack /path/to/robot.urdf \
  --out /path/to/final_urdf --zip /path/to/final_urdf.zip
```

The bundle contains `robot.urdf`, required meshes and a short usage note. Mesh paths become relative; numerical mechanism and inertial definitions remain unchanged. An optional `--report /path/to/new-report.json` writes the validation report. `--package` may be repeated in either mode.

Automatic packing supports **binary STL and primitive-only URDF**. ASCII STL must first be converted with a mesh loader. Textured/non-STL dependency trees require explicit packaging. Expand Xacro before running the checker. Primitive dimensions, mass/inertia correctness, mimic semantics, collisions, controller behaviour and simulator compatibility are outside its static checks.

## Dependencies and tested scope

| Component | Purpose / status |
| --- | --- |
| Python 3.10+ | Static URDF tools and orchestration; CI checks Python 3.10 and 3.12 |
| FreeCAD 1.1.1 + Blender 5.1.2 | STEP→GLB integration tested on Windows with a generated two-part coloured, nested assembly |
| Isaac Sim 5.1 | Workflow guidance informed by real articulated robot import and bounded physics tests; no universal USD composer is bundled |
| `omniverse-cad-to-simready` | Optional external skill for USD conversion workflows; install its own converters/dependencies separately |

The FreeCAD worker currently expects its `ShapeAppearance` and segmented `MeshPart` APIs. It refuses retained `App::Link` instances instead of silently dropping them. Other runtime versions/platforms need verification. Images, proprietary CAD and vendor robot assets are not bundled.

USD appearance composition covers per-link geometry and PBR material workflows. Image textures additionally require UVs, files and shader-network validation; the historical colour-only cases do not establish universal image-texture support. Missing dependencies must be reported, not silently substituted.

## Repository layout

```text
SKILL.md                 Agent entry point
agents/openai.yaml       Optional Codex UI metadata
references/              Task-specific technical guidance
scripts/                 STEP conversion workers and URDF tools
tests/                   Portable static-tool tests and a CAD fixture generator
README.md                English documentation
README.zh-CN.md           Chinese documentation
LICENSE                  MIT license for this repository
```

## Validation and development

```sh
python -m unittest discover -s tests -v
python -m compileall -q scripts
```

For the optional CAD integration test, use FreeCAD's Python to generate a fixture, then run the converter against that fixture in a new output directory:

```sh
/path/to/freecad/python tests/make_step_fixture.py /path/to/test-work/assembly.step
python scripts/step_to_glb.py /path/to/test-work/assembly.step /path/to/test-work/assembly.glb \
  --freecad-python /path/to/freecad/python --blender /path/to/blender
```

CI exercises the standard-library tools; it does not install FreeCAD, Blender or Isaac Sim. The static tests check malformed/wrapped STL, invalid joint trees, path resolution, output protection and packed geometry/transform preservation.

When contributing, keep changes reproducible and include relevant checks. Use generated fixtures or assets you may redistribute; keep credentials, private paths, large CAD/mesh files and generated simulation output out of commits. Report the actual software version and validation scope.

## License and external software

This repository is released under [MIT](LICENSE). FreeCAD, Blender, Isaac Sim, USD converters and other referenced tools are separate projects with their own licenses and installation requirements. Vendor CAD and robot models are not included or relicensed by this repository. External conversion helpers are referenced rather than copied into this toolkit.
