# URDF physics with GLB appearance

Use this branch for URDF + GLB, or validated articulated USD + GLB/visual USD. The default source contract is verified robot descriptions for motion/physics and user-selected GLB for appearance.

## Preserve the sources of truth

| Content | Source and policy |
| --- | --- |
| Links/joints, anchors, axes, limits, mimic | Original URDF or verified motion asset; do not reconstruct from visual-node placement |
| Mass, COM, inertia and collision | Verified physical description; do not replace during appearance transfer |
| Drives and sensors | Existing validated USD/configuration; missing controls are separate work |
| Visual geometry/material regions | Selected GLB/visual USD, mapped to actual physical links |
| Lights/floor/cameras | Separate preview environment unless explicitly part of delivery |

Check source correctness and model identity first. A URDF can contain missing or erroneous dynamics; using it as a baseline does not certify it. Document any additional or estimated parameters.

Keep GLB geometry by default. Material-only transfer onto existing geometry needs established topology/UV/region correspondence. Nearest-neighbour colour projection is an explicitly chosen approximation, not a silent replacement for preserving GLB appearance.

## Import and record the physical baseline

Record input paths/hashes, reference pose, units, axes and target runtime. Inspect GLB nodes, materials, images, textures and UVs before interpreting the user's word “texture.”

For Isaac/PhysX, use the installed Isaac URDF importer and [Isaac validation guidance](isaac-and-delivery.md). Preserve source collision instead of generating replacement collision from visuals. If another conversion route is selected, follow its dependency/preflight contract and validate for its actual target runtime; another engine's USD conversion is not a PhysX pass.

An existing trusted physics USD can be referenced/copied as a baseline. Inspect actual composed prim paths, payloads and instances rather than assuming `/Robot/link1`. Record articulation/joint identities, body associations, local anchors, limits, drives, inertials and collision geometry/transforms/approximation/filtering.

## Convert visual resources

When installed, read `omniverse-cad-to-simready` and its applicable stage references. For preserving existing appearance, select conversion-only/property-assignment-skip intent, complete its required preflight and use its specialized GLB conversion route. If that optional skill/runtime is missing, report the missing dependency and the affected stage; do not claim it was run or silently replace its selected converter.

Do not deploy material-generation services or generate new appearance merely to transfer existing materials. Already converted visual USD can skip completed conversion. Record the converter and inspect actual stage units/upAxis and coordinate magnitudes. Editing metadata alone does not rotate or rescale the geometry.

## Map visual groups to physical links

Make a reviewable mapping with source nodes/prims, target physical links, reference pose, alignment transforms and coverage/exclusion reasons. Multiple GLB parts may belong to one rigid link. A mesh spanning two moving links needs a justified split or user clarification.

Use names/hierarchy as candidates, then verify against joints and geometry. Avoid fixed object indices, face counts or robot-specific naming assumptions. Match specialized names such as gripper fingers before broad link prefixes. Account for every relevant mesh.

For column-vector transforms, with alignment A from visual world into robot world at reference pose q0:

```text
T_link_visual = inverse(T_world_link(q0)) * A * T_visualWorld_source
```

This local transform stays constant as the physical link moves. Baking vertices into link-local coordinates is another option; do not apply the alignment twice.

USD Gf row-vector matrix multiplication uses the equivalent order `M_source * M_align * inverse(M_link)`. Confirm the library's convention. Nonuniform scale needs inverse-transpose normal handling; mirrored geometry also needs winding/culling checks.

## Compose visuals and materials

Create a candidate composition that preserves the physical baseline. Attach source visuals under actual target links and hide only replaced old visual children to avoid overlap/flicker. Do not hide or remove collision/physical parents just to conceal old appearance.

De-instance only the necessary links/visual subtrees when editing requires it, preserving unrelated physics/collision instances. Traverse instance proxies and check inherited parent transforms, resetXformStack and transform op order.

- **PBR parameter materials:** retain colour, metallic, roughness and actually used alpha/emissive/double-sided behaviour. Prefer a verified converted material network; reauthor UsdPreviewSurface only with checked parameter/render correspondence. Avoid applying sRGB conversion twice or replacing colours with a historical case's palette.
- **Image textures:** also preserve UV primvars, image files, sampler/colour-space settings, channel interpretation and shader connections. A diffuse-colour-only script cannot support this case.

Copy/reference required material scopes along with geometry. Validate and remap material bindings, GeomSubset regions, shader connections and collection/internal paths after relocation. Re-resolve relative asset paths against the new layer and make final dependencies portable.

Do not merge materials by RGB alone: identical colours may differ in roughness, metallic, opacity or textures. Optional per-link/material mesh batching follows correctness validation and must preserve geometry, normals and UVs.

Visual composition should not introduce new rigid bodies, drives or collision. Historical gravity/solver/drive tuning is not an appearance-transfer step.

## Validate and publish the candidate

1. **Static resources:** stage/defaultPrim, complete mapping, visual counts and geometry, resolvable bindings/subsets/UV/images/references.
2. **Alignment/rendering:** dimensions, axes, mounting interfaces and reference pose; whole-robot and necessary detail renders in the actual target renderer. Material counts alone are insufficient.
3. **Physical invariants:** compare joints, bodies, local anchors, limits, inertials, drives, collision and filtering against the pre-composition USD. Where paths are relocated, compare semantics through a mapping rather than file bytes.
4. **Motion following:** use nonzero configurations and relevant arm/finger/lift/base movements. A visual's relative transform to its physical link stays constant while its world transform follows the link.
5. **Bounded physics:** verify actual DOFs, response and visual/collision alignment, recording runtime/settings/steps. Joint counts do not directly equal actuated DOFs.

State unexecuted checks explicitly. Preserve failures and the existing production asset; replace only the authorized destination after validation and recoverable backup.

Use the existing asset-library layout or `final_usd/` with one clear entry and dependencies. Flattening does not embed external textures. Report sources/hashes, importers/converters, physical baseline, mapping, unit/frame transformations, appearance policy, checks and remaining gaps.
