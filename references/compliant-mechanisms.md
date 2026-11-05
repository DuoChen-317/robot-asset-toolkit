# Compliant cables, contacts and latch mechanisms

Use this reference when parts must bend, spring back, retain an inserted component or release through a real linkage. For the loading sequence and acceptance evidence, continue with [connector validation](connector-validation.md).

## Establish what the geometry actually contains

Separate vendor CAD, public third-party CAD, standard-derived geometry, reference reconstruction and numerical collision proxies. A detailed exterior does not establish an accurate interior. Pin source revisions and hashes; identify which dimensions came from nominal standards, direct measurements or estimates. A user photo supports appearance and mechanism interpretation, not unmeasured internal material parameters.

Identify rigid housings, free flexible sections, reinforced ends, attached nodes, contact crowns, latch teeth/pockets, return springs, cams and pull handles. Make a motion/contact map before assigning APIs: which part deforms, which part moves rigidly, which surfaces carry retention, and what mechanically releases them? Do not infer this from CAD parent names alone.

## Choose the physical representation by the question

| Required behavior | Useful representation | Boundary to report |
| --- | --- | --- |
| Housing guidance, receiving slots and board interference | Rigid bodies with simple/convex or runtime-supported concave collision | Visual triangles and authored collider counts do not prove the cooked collision surface |
| Contact crown preload and travel | Passive joint with equivalent spring/damper and stops | A translating contact crown does not reproduce continuum bending of its arm |
| Cable tail sag, bending or EMI finger deformation | Native surface/shell FEM, appropriate attachment and collision | Verify actual solver nodes and visual skinning; shape animation is not FEM |
| Pull-tab release or socket lid | Separate moving rigid bodies and actual joint/cam/contact linkage | A scripted attachment toggle is not passive locking or mechanical release |

Use only the complexity needed for the test. Keep high-quality visuals separate from collision and simulation meshes. Do not replace a hollow socket or a module's paddle card with one solid box that fills the mating clearance. If individual pads matter, give their contact faces resolvable collision geometry and verify corresponding receiver contact. Electrical conduction still requires a separate model.

For shell FEM, establish thickness, node topology, density, Young's modulus, Poisson's ratio, damping, attachment and friction. Laminated FFC can require equivalent material properties; record the layer calculation and whether it is isotropic or directional. Reinforced ends and fixtures may have equivalent masses distinct from the bare cable. Do not call those measured masses. Attach only the intended boundary nodes so the free section remains solver-driven. Verify attached endpoints and deformed visual skin in a nonzero pose.

For passive joints, record rest position/preload, stiffness, damping, allowed travel, mass and stops. Source actual force/travel data when available; otherwise distinguish engineering estimates from numerical stabilization choices. A kinematic base can mount a socket, but a kinematic moving test piece cannot establish force-driven insertion response. Preserve physically relevant collision between latch, cam, pocket and housing throughout the cycle.

## Solve and inspect in the native runtime

Use the installed Isaac/PhysX API and beta-feature requirements, not a copied historical API assumed universal. Initialize one fixture first. Inspect finite node/pose states, attachments, contact penetration, measured seating and spring return before expanding the scene. State gravity and which DOFs the fixture constrains. Free-grasp behavior cannot be inferred from a test with locked lateral/rotational DOFs.

Thin contacts make timestep, contact/rest offsets, solver iterations and scale consequential. Check them against the smallest meaningful physical gap/thickness; do not enlarge geometry or disable collisions just to force seating. Vary suspect solver settings in a controlled comparison when failures justify it. Retain the failed record and distinguish physical interference from solver instability.

A single-part or single-port success is not a full-rack result. Run multi-instance translation/rotation and relevant simultaneous-load cases separately. Report cycle completion and final return independently: all plugs may extract while some FEM regions remain displaced. Record the observation window, reference/rest frame, return metric and threshold; extending the window is a new observation, not grounds to rewrite an earlier failure.

## Compare fidelity without overclaiming performance

For whole-board versus individual-pad collision, keep source dimensions, loads, contacts, timestep and output sampling consistent. Compare acceptance outcomes, native stepping wall time, device allocation and memory measurement method. Separate startup, cooking, solving and rendering time. A single run on a shared GPU does not establish speed superiority; a seated memory sample is not peak memory. Repeat under comparable conditions only when a performance decision actually needs that evidence.

Reusable assets should contain their internal mechanisms, materials, collision and attachments, with all internal targets remapped to the component root. Keep the environment, external robot/fixture and its controller outside the component unless they are part of the intended deliverable. Preserve both an editable/composed version when needed and an independently checked portable version; use [USD visual composition](urdf-usd-glb-visuals.md) and [Isaac delivery](isaac-and-delivery.md) for composition pitfalls.

The FFC and QSFP [case notes](case-studies.md) record observed settings and limitations. Their forces, dimensions, material constants and GPU choices are case data, not defaults for a new connector.
