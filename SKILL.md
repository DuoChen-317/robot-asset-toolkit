---
name: robot-asset-toolkit
description: Build reusable robot and assembly simulation assets from CAD, GLB, URDF and USD. Use for precision conversion, robot/tool assembly, articulated USD, connector insertion and latch release, flexible cables and FEM spring fingers, contact validation, and rendering recorded physics with synchronized material and collision views. Navigation, general robot policy training and arbitrary controller synthesis are separate work.
---

# Robot Asset & Assembly Simulation Toolkit

Turn source geometry and assembly intent into editable models, reusable physics assets and evidenced assembly tests. Keep the repository and invocation name `robot-asset-toolkit`. Continue from the user's current stage. Respond in the user's language; these English instructions do not require English conversation.

## Project and artifact layout

Before generating files, read [project-layout.md](references/project-layout.md) and reuse the user's directories. No fixed input folder such as `source/` is required. Keep original inputs, final assets and process artifacts separate. GLB output folders hold only final GLBs; URDF/USD deliveries include their necessary dependencies. Use one shared workspace for reports, scripts, logs, previews and failed/previous versions. Create only directories needed for the task.

## Choose the entry point

| Request | Workflow |
| --- | --- |
| STEP/STP for Blender | [STEP to GLB](references/step-to-glb.md); stop after conversion and checks |
| Mount a component or align an assembly | [Geometry and frames](references/geometry-and-frames.md) |
| Add a tool to an existing URDF | Preserve the existing robot; add the required links/joints |
| Build URDF from an assembly | Identify rigid bodies, actual mechanisms, joint frames and limits |
| AGV/AMR with an arm | [Mobile manipulators](references/mobile-manipulator.md) |
| URDF physics with GLB appearance in USD | [USD visual composition](references/urdf-usd-glb-visuals.md) |
| Isaac import failure or runtime checks | [Isaac and delivery](references/isaac-and-delivery.md) |
| Flexible cable, spring contact, latch or deformable assembly | [Compliant mechanisms](references/compliant-mechanisms.md) |
| Insertion, retention, unlock/extraction or misalignment test | [Connector validation](references/connector-validation.md) |
| Render actual solver records, collision views, close-ups, MP4 or GIF | [Recorded physics and presentation](references/physics-recording-and-presentation.md) |

Read only the references needed for the current task. Bundled helpers cover conversion, static packaging, USD inspection, trajectory integrity and GIF generation. Mechanism interpretation, FEM construction, controller adapters and USD composition remain model-specific work.

## Establish the sources and mechanism

- Inventory current CAD, GLB, Blend, URDF/Xacro and USD files. Respect recently overwritten user versions; record hashes to identify the inputs actually used.
- Reuse a trustworthy existing URDF and its meshes. Check its dimensions, reference pose and frame convention against the assembly instead of assuming they match.
- Separate alternative tools from parts that belong in one assembly. Do not install every available candidate by default.
- Group by rigid bodies and real motion: rigid tools may use one link or fixed joints; grippers, steering, lifts and turntables need their actual joints. CAD hierarchy alone does not establish kinematics.
- When joint axes, zero positions, limits, couplings or inertial data cannot be established, request the missing information while continuing independent geometry work. Closed loops require an explicit target-engine representation or documented approximation.
- Confirm units, intended precision, target runtime and output location from available evidence. Discover software paths on each machine. Use only the current task's authorization for remote access and publication.

## Geometry and assembly

Keep exact source CAD. For high-precision requests, use explicit tessellation settings without silently decimating or deforming geometry. Record tessellation settings, export numerical error and mating-face error separately: matching bounding boxes do not prove a surface-error bound.

Use actual mating faces, axes and orientation datums to align the complete component with a rigid transform. Preserve its internal part arrangement and the existing robot pose unless the task calls for changes. Distinguish coplanar contact, body penetration, fastener interference, hole-pattern compatibility and motion-range collision. A rigid transform cannot correct incompatible bolt-circle diameters.

Round-trip the exported assembly and check parts, valid triangles, hierarchy, units and placement. STEP-to-GLB does not automatically create robot joints. STL does not preserve materials or units.

## URDF construction

Use metres, radians and a consistent right-handed frame convention. Follow the FK and relative-transform equations in [geometry-and-frames.md](references/geometry-and-frames.md).

- **Existing URDF:** preserve the original mechanism and physical data. Select the actual mounting parent and compute the new component's relative frame. Do not force every tool's fixed-joint origin to zero.
- **New URDF:** define rigid-body link frames, joint origins at the reference pose, joint types, local axes and limits from mechanism evidence. Include mimic/transmission/TCP definitions only when established and needed.
- **Dynamics:** distinguish visual fidelity from physical readiness. Do not invent measured mass, inertia or actuator capability. Explicitly permitted estimates need their method and source recorded.
- **Collision:** preserve detailed visuals while selecting suitable collision primitives, convex components or validated decomposition. Do not replace trusted URDF collision with a GLB convex hull as a side effect of visual conversion.
- **Resources:** use ROS package URIs for ROS packages or relative paths for portable bundles. Include the required resources; avoid another machine's absolute paths in final assets.

For a mobile manipulator, compose the base, mounting structure, lift, arm and tool at the whole-robot level. Resolve naming collisions and all affected references/configuration. Fix the arm to the chassis while keeping the vehicle root mobile; check legacy world anchors before composing. Model wheel joints, free-root physics, navigation TF and planning virtual joints as distinct concerns.

## USD and visual transfer

Use URDF or an already validated physics USD for joints, mass/inertia and collision. Use GLB for mapped visual parts and existing materials. Attach each visual group in its target link's local frame so it follows the actual mechanism.

When available, use `omniverse-cad-to-simready` for its specialized conversion stage, with conversion-only/property-assignment-skip intent and its required preflight. This toolkit does not bundle that optional skill or replace its converters. Select URDF conversion for the actual target runtime; Isaac/PhysX and other runtimes require their own validation.

Identify whether “texture” means PBR colour/metallic/roughness or image-based textures. Preserve existing appearance; image textures additionally need UVs, assets and shader connections. Do not generate replacement materials or modify drives, gravity or collision during appearance-only work.

## Evidence and validation

1. **Static:** unique names, a connected single-root joint tree, valid references, units, mesh headers/counts and portable resource paths.
2. **Geometry and kinematics:** reference and nonzero joint poses, expected axes, fixed-component following, interface tolerances and export round-trip consistency.
3. **Target runtime:** actual importer/version, valid articulation and expected DOFs, relevant collision/inertial warnings, bounded physics execution and rendering where requested.

Mobile assets also need base and arm motion checked separately and together. Count actuated, passive and free-root coordinates appropriately; do not assume six or nine total DOFs for every robot. Visual composition additionally requires mapping coverage, material resolution, nonzero-pose following and physical-baseline comparisons.

If a runtime is unavailable, state the completed validation layer. An XML parser, successful render, process exit code or ZIP CRC alone does not establish simulation readiness.

For connector work, define seating, retention, release, clearance and elastic-return criteria before running; report them separately. Drive the test with the intended fixture forces/constraints, not per-step body or deformable-node pose assignment. A fixture's imposed alignment is part of the result's scope. Read [connector-validation.md](references/connector-validation.md) for the test matrix and [compliant-mechanisms.md](references/compliant-mechanisms.md) for native FEM and equivalent-spring boundaries.

For video work, record solver states first and render those records separately. Keep opaque materials and diagnostic cutaways on the same time/frame mapping. A baked replay is playback, not another physics test. Contact points identify only the entities the runtime actually reports; do not infer per-pad identities from body-pair sensors. Follow [physics-recording-and-presentation.md](references/physics-recording-and-presentation.md).

### Bundled static checker and packer

Run from this skill's root, or use absolute script paths:

```sh
python scripts/check_pack_urdf.py validate /path/to/robot.urdf --report /project/_conversion_work/reports/urdf-check.json
python scripts/check_pack_urdf.py validate /path/to/robot.urdf --package robot_description=/path/to/robot_description
python scripts/check_pack_urdf.py pack /path/to/robot.urdf --out /project/final_urdf --work-dir /project/_conversion_work --report /project/_conversion_work/reports/urdf-pack.json --zip /project/packages/robot.zip
```

`--package` is repeatable. Packing preserves geometry, scales, joints and inertial values while rewriting mesh paths. Automatic packing supports binary STL and primitive-only URDF, not textured/non-STL dependency trees. Expand Xacro first. The checker does not compute assembly transforms, validate physical parameters or test collisions/controllers. ZIPs and detailed reports must stay outside the final asset directory. Existing nonempty outputs, reports and archives are refused; select a clear new destination or resolve the explicitly intended update rather than blindly retrying.

### Simulation evidence helpers

- `scripts/inspect_usd.py`: read-only default-prim, unit, dependency, relationship and authored-physics inventory. Use a Python with `pxr`; it does not run PhysX or certify cooked collision shapes.
- `scripts/check_sim_record.py`: configurable NumPy NPZ time, pose, quaternion, deformable-node and frame-map checks. It checks record integrity, not mechanical success.
- `scripts/make_preview_gif.py`: sample an existing rendered video with FFmpeg, create a looping GIF and verify its decoding. It creates no new motion or physics. See the presentation reference for usage and provenance.

## Final delivery

Follow [project-layout.md](references/project-layout.md). Otherwise suggest `final_urdf/` or `final_usd/` with a clear entry per asset/configuration, required dependencies and brief instructions. Requested ZIPs default to `packages/`. Keep detailed reports, scripts, logs, failed candidates and backups in the shared workspace. Final assets must not reference temporary workspace files. Do not remove unrelated user work.

Read the ZIP contents and validate their actual mesh data after packing. Transfer hashes prove transport integrity, not format correctness. Authorized remote delivery requires hash checks, extraction and resource validation, with recoverable replacement of existing assets. Flattening USD does not embed external textures.

Report the import entry point, package location, checks actually performed and remaining limitations. Do not extend asset authoring into unrequested service deployment, platform registration, navigation or training.

For anonymized lessons from real workflows, see [case studies](references/case-studies.md).
