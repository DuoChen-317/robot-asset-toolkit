# Project and artifact layout

Apply this policy across CAD conversion, assembly, URDF and USD workflows. Standardize directory responsibilities, not directory names. Reuse the user's existing layout and keep original inputs in place, including inputs outside the project. No `source/`, `stp/` or other fixed input hierarchy is required.

The following is an example for a project without an established layout. Create only directories needed for the current request:

```text
project/
├── <existing inputs>/      Original CAD/vendor assets; may live elsewhere
├── glb/                    Verified final GLB files only
├── assembly/               Requested editable assemblies
├── final_urdf/             URDF entry, meshes, required textures/config, short instructions
├── final_usd/              USD entry, required layers, materials and textures
├── packages/               Requested final ZIP archives
└── _conversion_work/       One shared process workspace
    ├── reports/            Conversion/check reports, mappings and detailed notes
    ├── scripts/            Project-specific or modified scripts
    ├── logs/               Diagnostic logs
    ├── intermediate/       Temporary meshes, expanded files and staged candidates
    ├── previews/           Inspection renders and preview scenes
    └── archive/            Retained previous versions and failed candidates
```

## Asset boundaries

- A GLB output directory contains only verified final `.glb` files, whatever that directory is called. Reports and notes belong in the workspace.
- A URDF/USD delivery is a dependency-complete asset, not necessarily one file. Include required meshes, images, material definitions, USD layers, Xacro modules and runtime configuration. Detailed diagnostics and test scenes stay in the workspace.
- An editable assembly is a delivery when the user needs to continue authoring. Failed assemblies, automatic backups and screenshot-only scenes stay in the workspace. Deliver previews/scenes separately when they are themselves requested outputs.
- Reuse one process workspace across stages. An existing `pipeline/` or other equivalent directory is valid: pass it with `--work-dir` instead of creating another work tree. Run unchanged common tools from the skill; do not copy them into every project.
- Put requested ZIPs in `packages/` or alongside the asset directory, outside the directory being packed. Do not include the process workspace in delivery archives.

## Naming and repeated runs

Use clear asset/configuration names for final entries. Multiple cameras or actual configurations can have separate entries; “one clear entry” applies to each asset/configuration, not the whole project.

Keep dates, run numbers and repair suffixes in the workspace rather than accumulating `final_final` variants in delivery. Preserve existing verified outputs unless an update is authorized. For an authorized update, retain recoverable previous versions as needed and publish the validated replacement. Resolve report-name conflicts with an explicit work subdirectory such as `_conversion_work/runs/camera_002/`.

Failed candidates belong in the workspace; successful temporary staging may be cleaned automatically. Do not retain every large intermediate by default, clear user directories, rename unknown files or reorganize vendor packages merely to match this example.

## Tool defaults and final checks

Both entry points default to `_conversion_work/` alongside the final output directory. They do not infer a project root from names such as `source` or `glb`. For nested outputs or an existing shared workspace, pass its actual path with `--work-dir`.

STEP conversion writes `.conversion.json` and `.validation.json` to the workspace's `reports/`. URDF commands can write there with `--report`; without that option, their reports go to stdout. Checking an existing URDF does not add a report to its asset directory.

Validate candidates in the workspace before publishing. Re-read final entries, hashes and dependencies after relocation. Portable assets must not depend on temporary files in the inputs/workspace; explicitly agreed external asset-library references are separate. Relocating USD/DAE/OBJ requires checking all layer, material and texture paths, not just moving the entry file. Keep final usage notes short and state the actual validation scope; detailed evidence belongs in reports.
