# Robot Asset & Assembly Simulation Toolkit

[English](README.md) | [简体中文](README.zh-CN.md)

An agent skill and focused tools for preparing reusable robot assets, building compliant assembly tests, and presenting recorded physics. Covers CAD, visual assemblies, URDF, articulated USD, connector insertion, flexible cables, spring fingers and latch release.

**Keep geometry sources, physics definitions, solved-state evidence and rendered playback traceable.** The repository name and skill invocation stay `robot-asset-toolkit`.

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
| Compliant assembly modeling | Rigid/FEM/equivalent-spring selection, cable attachments, latch/cam linkage and documented approximations |
| Connector insertion tests | Seating, retention without unlocking, mechanical release, extraction, elastic return and misalignment evidence |
| Recorded physics presentation | Synchronized opaque material/collision views, mechanism close-ups, portable replay guidance and looping GIFs |

Assembly interpretation, link mapping, dynamics, FEM construction and test-controller adapters require model-specific work. Bundled helpers check files and records and convert video; they do not supply a universal physical model, insertion controller, navigation stack or robot policy.

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
Use $robot-asset-toolkit to validate insertion, retention and pull-tab release for my connector and socket.
Use $robot-asset-toolkit to model a flexible cable or spring finger with explicit FEM and attachment assumptions.
Use $robot-asset-toolkit to show the same recorded physics in material and collision views, then make a README GIF.
```

The skill instructions are English; the agent should respond in the user's language.

## Run the tools directly

The original conversion/URDF tools use Python 3.10+ and the standard library. Runtime-specific conversion workers use modules bundled with FreeCAD and Blender. The optional USD inspector requires `pxr`, the NPZ checker requires NumPy, and the GIF helper calls separately installed FFmpeg/FFprobe. Missing optional dependencies do not affect the URDF tools.

### STEP to GLB

Install FreeCAD and Blender separately and supply their actual executable paths:

```sh
python scripts/step_to_glb.py input.step output.glb \
  --freecad-python /path/to/freecad/python \
  --blender /path/to/blender \
  --work-dir /project/_conversion_work \
  --linear-mm 0.01 --angle-deg 5
```

PowerShell example:

```powershell
python scripts/step_to_glb.py 'D:/models/input.step' 'D:/exports/output.glb' `
  --freecad-python 'C:/Apps/FreeCAD/bin/python.exe' `
  --blender 'C:/Apps/Blender/blender.exe' `
  --work-dir 'D:/models/_conversion_work' `
  --linear-mm 0.01 --angle-deg 5
```

The final output directory contains only verified GLBs. Conversion and validation JSON reports go to `<work-dir>/reports/`; temporary GLBs are validated in the workspace before publication. `--work-dir` defaults to `_conversion_work/` beside the output directory; specify it to reuse an existing workspace. Existing outputs/reports are refused. Source CAD is unchanged; there is no general decimation or automatic recentering/uprighting. Repeated-index degenerate triangles are removed and counted.

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
  --out /project/final_urdf \
  --work-dir /project/_conversion_work \
  --report /project/_conversion_work/reports/urdf-pack.json \
  --zip /project/packages/robot.zip
```

The bundle contains `robot.urdf`, required meshes and a short usage note. Mesh paths become relative; numerical mechanism and inertial definitions remain unchanged. An optional `--report /path/to/new-report.json` writes the validation report. `--package` may be repeated in either mode.

ZIP archives and detailed reports stay outside the final asset directory. Reuse the project's existing input/output names; no `source/` folder or fixed project hierarchy is required. Only create directories needed for the current task. See the shared [project layout policy](references/project-layout.md) for GLB, assembly, URDF and USD deliveries.

Automatic packing supports **binary STL and primitive-only URDF**. ASCII STL must first be converted with a mesh loader. Textured/non-STL dependency trees require explicit packaging. Expand Xacro before running the checker. Primitive dimensions, mass/inertia correctness, mimic semantics, collisions, controller behaviour and simulator compatibility are outside its static checks.

### Inspect simulation assets, records and previews

```sh
# Static USD inspection using a Python environment with pxr.
python scripts/inspect_usd.py /project/final_usd/module.usd \
  --package-root /project/final_usd --report /project/_conversion_work/reports/usd.json

# NumPy record check: array keys/order come from your solver adapter.
python scripts/check_sim_record.py trajectory.npz \
  --time-key telemetry --time-column 0 --pose-key body_q --deform-key shell_q

# Sample actual rendered frames; keep the original MP4 for higher quality.
python scripts/make_preview_gif.py insertion.mp4 preview.gif \
  --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe --width 960 --fps 8 --colors 128
```

All three helpers refuse existing report destinations; the GIF tool also refuses an existing output. USD inspection inventories authored physics and active composition, not cooked collisions or runtime behavior. Record checking verifies arrays/timing, not seating or retention. GIF conversion does not authenticate its input as physics.

The skill's model-specific workflows cover [compliant mechanisms](references/compliant-mechanisms.md), [connector validation](references/connector-validation.md), and [native records and presentation](references/physics-recording-and-presentation.md). They separate live solving from baked replay, report independent acceptance criteria and keep case-specific forces, materials and GPU choices out of universal defaults.

## Dependencies and tested scope

| Component | Purpose / status |
| --- | --- |
| Python 3.10+ | Static URDF tools and orchestration; CI checks Python 3.10 and 3.12 |
| FreeCAD 1.1.1 + Blender 5.1.2 | STEP→GLB integration tested on Windows with a generated two-part coloured, nested assembly |
| Isaac Sim 5.1 | Articulated robot checks and native connector/cable/FEM case evidence; requires the installed runtime's matching APIs and beta settings |
| `pxr` / NumPy (optional) | USD dependency/physics inventory and NPZ state-integrity checks; generated fixtures exercise the helpers without Isaac |
| FFmpeg + FFprobe (optional) | GIF palette conversion and full-frame decode checks; required only for previews |
| `omniverse-cad-to-simready` | Optional external skill for USD conversion workflows; install its own converters/dependencies separately |

The FreeCAD worker currently expects its `ShapeAppearance` and segmented `MeshPart` APIs. It refuses retained `App::Link` instances instead of silently dropping them. Other runtime versions/platforms need verification. Proprietary CAD, vendor robot assets and large simulation caches are not bundled.

USD appearance composition covers per-link geometry and PBR material workflows. Image textures additionally require UVs, files and shader-network validation; the historical colour-only cases do not establish universal image-texture support. Missing dependencies must be reported, not silently substituted.

Historical [FFC and QSFP case notes](references/case-studies.md) document full standalone cycles and their approximations. A single-module full-rack QSFP cycle passed, while return of all rack FEM regions and simultaneous multi-module operation retained failures. These are scoped engineering demonstrations, not calibrated force predictions or universal benchmarks. The separate [simulation portfolio](https://github.com/DuoChen-317/simulation-portfolio) contains case assets/media where access is granted; it is not a dependency of this skill.

## Repository layout

```text
SKILL.md                 Agent entry point
agents/openai.yaml       Optional Codex UI metadata
references/              Task-specific technical guidance
scripts/                 Conversion, URDF, USD, record and GIF helpers
tests/                   Generated-fixture tests, with optional USD/NumPy/media checks
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

CI exercises the standard-library tools and an optional-evidence job with USD, NumPy and FFmpeg. It does not install FreeCAD, Blender or Isaac Sim. Tests cover malformed/wrapped STL, invalid joint trees, path resolution, output protection, packed geometry/transform preservation, broken USD dependencies, invalid state records and decoded GIF generation. Optional tests skip locally when their dependencies are unavailable.

When contributing, keep changes reproducible and include relevant checks. Use generated fixtures or assets you may redistribute; keep credentials, private paths, large CAD/mesh files and generated simulation output out of commits. Report the actual software version and validation scope.

## License and external software

This repository is released under [MIT](LICENSE). FreeCAD, Blender, Isaac Sim, USD converters and other referenced tools are separate projects with their own licenses and installation requirements. Vendor CAD and robot models are not included or relicensed by this repository. External conversion helpers are referenced rather than copied into this toolkit.
