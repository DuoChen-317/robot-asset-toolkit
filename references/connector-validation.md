# Connector insertion, retention and release validation

Use for cable/socket, transceiver/cage and similar insertion tasks. Read [compliant mechanisms](compliant-mechanisms.md) when contact, bending or latch mechanics must be authored. The toolkit supplies the workflow and evidence helpers, not a connector-independent controller or a calibrated force model.

## Define success before solving

Identify the mating frame, insertion axis and sign, outside/start pose, nominal seating datum, end clearance and dimensional tolerance. A fully inserted connector may retain an exposed handle; visible housing overlap alone is not seating evidence. Record tolerances in physical units and derive them from the actual geometry/specification or task requirement.

Choose relevant phases and explicit criteria:

| Phase | Evidence |
| --- | --- |
| Settle outside | Finite states, stable attachments and intended alignment; no initial interpenetration |
| Insert and seat | Solver-derived displacement relative to mating datum, sustained seat interval, relevant contact and force limits |
| Passive lock / lid close | Actual latch/pocket engagement or lid/cam mechanism; no hidden attach/detach switch |
| Pull without unlocking | Specified body load, duration and allowed drift; verify the insertion drive is not itself providing retention |
| Unlock | Handle/lid actuation produces measured relative travel or angle and mechanical release |
| Extract | Component passes the defined clearance plane without teleportation or disabled collision |
| Elastic return | Node/contact displacement from the unloaded reference after a stated observation interval, with an explicit tolerance |
| Misalignment | Defined lateral/height/angular error, bounded loads and measured blockage/contact at the expected region |

Use only phases relevant to the connector: an FFC lid and a QSFP pull-tab are different mechanisms. Do not carry over loads, joint gains or stroke thresholds solely because they worked in another example. A test adapter should expose those parameters and case IDs, save the actual values used and refuse overwriting previous results.

## Control a physical experiment

Use force/torque-limited fixture drives or external forces compatible with the intended setup. Configure constraints once; then let the solver determine moving-body and deformable-node states. Do not author per-step poses or node points, remove collider APIs, disable contact pairs or attach/detach the plug to obtain a claimed physical result. Initial placement and deliberately kinematic fixtures are allowed when explicitly part of the experiment; identify the contact/motion behaviors they do and do not validate.

For the retention phase, remove or account for the insertion actuator's holding force. State whether loads are applied to the body, handle, fixture or lid. Apply release actuation through the actual modeled linkage, then observe body motion and clearance. Save continuous state through the transition rather than stitching unrelated solves together as one test.

A misalignment fixture may hold offset DOFs fixed. Report that constraint: entrance blockage then says nothing about free-hand self-alignment, damage or robot recovery. Test offsets appropriate to the real opening and intended uncertainty instead of blindly using the case-study millimeter values.

## Record what the runtime can identify

Record input hashes, runtime/schema versions, timestep, solver/contact settings, device mapping, gravity, fixtures, phase/load histories and sample times. Capture solved body poses, native deformable-node states and any native render-skin output used. Capture contacts at a stated interval; declare whether identifiers are bodies, collision shapes or contacts. Body-pair reporting cannot prove which of several pads on one body was touched. Missing FEM contact dots do not mean there was no FEM contact.

If transforming instances, measure seating and errors in the mating frame; compare FEM return in a consistent local/rest frame. World-origin assumptions often make a translated fixture appear to fail. Keep internal body/joint/material/attachment targets valid after prim-root relocation. Validate a nonidentity placement and, when required, simultaneous interacting instances.

Useful result fields include independent `seating_pass`, `retention_pass`, `release_pass`, `extraction_pass`, `return_pass`, `misalignment_blocked` and an overall status scoped to the requested checks. Use `not_tested` or `unavailable` when evidence is absent; do not let a missing value become an implicit pass. Raw state integrity and a render are separate from these mechanical criteria.

## Reuse and communicate the evidence

Start with one complete cycle, then scale only as the task requires. Full-rack geometry, all-port collision checks, all-FEM initialization, single-module full-rack motion and simultaneous multi-module motion are distinct validation levels. Report each performed level and preserve failures. Do not announce universal asset readiness from a standalone port result.

Use `scripts/inspect_usd.py` for static dependencies/physics inventory and `scripts/check_sim_record.py` for recorded-state integrity. Neither computes seating, forces, retention or return acceptance for an unknown mechanism. Compute those with the model-specific geometry/load adapter and retain the equations, thresholds and raw-data identity. See [recorded physics and presentation](physics-recording-and-presentation.md) for playback and video provenance.
