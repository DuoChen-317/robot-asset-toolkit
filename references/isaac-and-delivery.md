# Isaac import, diagnosis and delivery

## Match the actual runtime

Read the installed version and its examples/importer source. Historical working patterns here refer to Isaac Sim 5.1; they are not universal API guarantees. A single asset conversion does not require deploying the entire SimReady service ecosystem.

In Isaac 5.1, inspect `standalone_examples/api/isaacsim.asset.importer.urdf/urdf_import.py` and the importer extension's `impl/commands.py`. After creating SimulationApp, enable `isaacsim.asset.importer.urdf`, create its import config and invoke `URDFParseAndImportFile` with explicit source/destination and articulation-root intent.

Record merge-fixed-joints, fixed-base, convex decomposition, self-collision, inertia import and distance-scale settings. Fixed-base suits a grounded arm, not a freely moving vehicle; see [mobile-manipulator.md](mobile-manipulator.md). Confirm merged tools retain geometry and appropriate mass/frame semantics.

## Bounded validation

Stage candidates under the shared workspace's `intermediate/`, with logs and reports in that workspace; see [project-layout.md](project-layout.md). Publish the complete USD and its dependencies after validation. Use a separate process and a reasonable timeout. Do not reuse streaming ports, overwrite verified assets or terminate other workloads.

1. Record input identity and remove conflicting Python/conda environment settings only for the new process. Check available GPU resources and the runtime's device numbering.
2. Check importer return state and actual USD output, not just the shell exit status.
3. Include `Usd.TraverseInstanceProxies()` when inspecting instance-contained meshes. Match full link path segments, not a substring that also occurs in the robot root's name.
4. Confirm visual geometry and expected mechanism/joints. Correct face count alone does not prove correct appearance.
5. If defaultPrim is missing, identify the intended model root before authoring it, or specify the intended referenced prim explicitly.
6. Avoid simultaneous edits through separate stages composed from the same file. For tests, create a new in-memory World/stage and reference the exported asset; release conflicting independent stage handles. Wait for loading using the installed version's synchronous/asynchronous contract.
7. Find the actual ArticulationRootAPI prim, verify the physical handle and expected DOFs, then run a small bounded physics check, such as 30 steps. Add control/contact tests only as required by the task.
8. Write a structured pass/fail report with inputs, settings, geometry paths, DOFs and executed steps. Some Kit wrappers return zero after app.close even when earlier work failed: missing reports, tracebacks or failure markers override a superficial zero exit code.

Short simulation does not establish accurate mass, controller readiness, complete collision freedom or training readiness. Missing inertials and zero effort/velocity values remain explicit data gaps.

## Multiple GPUs

Physical nvidia-smi indices, CUDA_VISIBLE_DEVICES remapping and Vulkan/Omniverse enumeration may differ. Do not blindly pair a single exposed physical GPU with `active_gpu=0`.

Read the platform's existing launch handling and Kit enumeration logs. Verify both rendering and physics devices. An isolated process may use explicit physical indices and disable automatic multi-GPU, but whether CUDA_VISIBLE_DEVICES stays set depends on the runtime. Rule out mapping problems before blaming a shared server's driver or restarting it.

## An import makes a task stop

Correlate the event time across task stdout/stderr, Kit logs and accessible system records. Distinguish simulation pause, process exit, streaming disconnection and UI job status. Logs may be under installation `kit/logs/Kit/` or user log locations; discover them.

- **Unsupported Format / failed asset load:** inspect the actual file header, size, mesh URI and ZIP member content, not only its extension.
- **NULL UsdStage / missing temporary USD:** inspect the preceding conversion failure, not only the final fatal error.
- **Resource exhaustion:** check the incident-time logs/exit state; free memory after a crash does not disprove an earlier OOM.
- **Joint/inertial/collision warnings:** separate import blockers from physical-model gaps. Do not solve every failure by reducing visual fidelity.

One observed non-STL payload starts with `%TSD-Header-###%`. Do not interpret it as binary STL or strip an arbitrary fixed header. Re-export/repackage from readable authorized source data or use the user's legitimate decoding environment, then verify the ZIP member itself.

## Authorized remote delivery

Use only current authorization and available connection configuration. Do not store credentials in scripts, reports or archives.

Check SSH reachability, target access, space and the transfer subsystem separately. An SFTP side-panel disconnection does not establish a model-format error or prove that no files arrived. SCP can be an alternative when supported; legacy `scp -O` worked in one Windows/OpenSSH setup but is not required universally.

Transfer to a temporary destination, compare hashes, inspect ZIP CRC and actual geometry, then replace only intended targets with recoverable backups. Compare extracted content with the tested input. Keep failed packages, backups and diagnostics out of final delivery. Flattened USD still needs its external image dependencies packaged.
