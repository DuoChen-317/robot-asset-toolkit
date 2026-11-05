# Anonymized workflow lessons

These are observed outcomes and failure patterns, not robot-identification rules or universal settings. Original robot CAD, user conversations, machine paths and remote configuration are not distributed.

## Fixed tool on an existing six-axis arm

A STEP-derived tool assembly was aligned in Blender to the arm's actual terminal flange. The original faces had about 1.60 degrees of tilt, 2.88 mm axial gap and 2.01 mm lateral offset. A rigid transform of the complete tool corrected the interface while preserving the robot pose and internal tool arrangement.

The robot and tool had different bolt-circle diameters. The task explicitly required mating-face alignment only, so fastener/hole incompatibility was recorded rather than represented as repaired. This decision does not generalize to other tasks.

The arm's existing URDF was retained and a fixed tool link added. The high-resolution tool mesh retained 367,167 triangles. Link-local coordinates and FK justified an identity mounting joint in this specific case; other tools need their computed transform.

An initial archive passed ZIP CRC and transport SHA-256 checks but contained a wrapped tool file instead of standard STL. The target importer reported Unsupported Format, then a fatal missing/NULL USD stage. Repacking readable source bytes and checking the actual ZIP member's binary STL length fixed the issue. Transport integrity was never a substitute for payload-format validation.

The repaired asset passed six-DOF articulation and 30-step physics checks in Isaac Sim 5.1. Existing zero effort/velocity fields and missing measured tool inertials remained documented gaps, so this was not a claim of calibrated dynamics or controller readiness.

## Articulated robot with coloured GLB visuals

A coloured GLB was converted into visual USD while a trusted robot asset supplied joints, collision and physical data. Each visual group was attached to the matching link using a reference-pose relative transform. Motion probes checked that appearance followed the articulation.

The inspected GLB contained 11 materials and no image/texture resources. This validated PBR appearance transfer, not universal image-texture support.

In a later robot variant, an early candidate inferred joint anchors and collision from the GLB. That candidate was rejected: the corrected process imported the actual URDF first, inspected its real USD link paths and then attached GLB appearance. Source-specific node names and tuning parameters were not reusable defaults.

Related composition work exposed additional pitfalls: omitted instance-contained meshes, copied bindings still targeting the old material scope, unit scaling applied twice and fixed-joint anchors pulling mounted geometry into the parent body. Static previews alone did not establish runtime correctness.

## Flexible FFC and a locking socket

A 40-pin, 100 mm FFC and a detailed FH12 socket were tested in Isaac Sim 5.1 / PhysX GPU surface FEM. A native shell had 517 nodes and 920 triangles, with 22 front nodes attached to a reinforced-end rigid body. A much denser CAD skin followed the native deformable output. The open/insert/seat/close/retention/reopen/extract cycle ran for 1.22 physical seconds and was presented as a 24-second video.

The 0.08 N retention pull was a fixture-specific test, not a connector rating. The 5 g front-end mass represented reinforced end plus fixture, with front-end gravity disabled; it was not bare-cable measured mass. Equivalent PET/Cu/PET properties, collision proxies, lid/cam mechanics and reconstructed terminal details were documented. The visual curved terminals had no individual elastic solve. No conductivity, fatigue or damage was modeled.

Lessons: native node/skin motion must be recorded and checked independently of appearance. Keep FEM attachments inside the reusable cable, but keep the insertion fixture outside it. Preserve component bytes and verify relocated references, nonzero joint poses and multiple placements. Material/fixture estimates and mismatches between a download listing and actual CAD dimensions remain explicit, even when the full cycle passes.

## Detailed QSFP transceiver, latch and spring contacts

A transceiver was split into body and release slider, with 55 authored colliders including 38 individual gold pads and a beveled paddle card. The matching standalone socket used 38 passive spring contact crowns and 8 native FEM EMI regions. Socket-contact arms translated as rigid spring-loaded crowns; only the modeled FEM regions reproduced continuum bending. External appearance was based on third-party CAD, while functional slots, pockets, contact details and release mechanics included reference reconstruction.

An aligned single-port cycle passed insertion, passive locking, a 5 N body retention pull, 12 N handle release and extraction. The detailed run reached approximately 20.400 mm seating, 0.102 mm retention drift and 0.054 mm final FEM return error. Fixed-offset entrance tests at 2 mm lateral and 1.5 mm vertical offset were blocked before the rear contacts. Those offsets, loads, material values and tolerances belong to this fixture, not the general workflow.

All 8 full-rack ports passed separately scoped rigid contact tests. A single-module full-rack test with all 64 FEM regions enabled completed the cycle, but its approximately 2.202 mm return residual exceeded the 1 mm criterion in the observation window. Simultaneous multi-module operation also retained failures. Reporting cycle completion separately from elastic return prevented a standalone pass from being presented as full-rack acceptance.

A whole-board/individual-pad comparison showed no demonstrated large performance penalty for the detailed version in that shared-server experiment. One run per variant and a seated VRAM sample could not establish speed superiority or peak memory. Native rigid contact reporting identified body pairs rather than individual collision shapes; red dots could not label which pad on a multi-pad body was touched.

The same 0.45-second detailed trajectory later drove both opaque full-cabinet rendering and diagnostic collision views, with latch/contact/EMI close-ups. State hashes and a common frame map established synchronization. The 20-second video and looping GIF were recorded-state presentations, not new full-rack physics solves. Full-cabinet appearance alone did not change the original single-port validation scope.

Case assets and media are maintained separately in the [simulation portfolio](https://github.com/DuoChen-317/simulation-portfolio); access may be restricted. This skill is self-contained and does not require that repository. It redistributes neither the case CAD nor vendor specifications, and does not extend their licenses.
