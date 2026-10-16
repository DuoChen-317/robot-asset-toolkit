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
