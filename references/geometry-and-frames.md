# Geometry, interfaces and frames

## CAD import and fidelity

Discover the actual installed runtimes. FreeCAD `ImportGui` with an offscreen hidden GUI can expose shape appearances when a pure headless import lacks ViewObjects. Keep the user's existing application session untouched.

For explicit tessellation use `MeshPart.meshFromShape` with `Relative=False`, a linear deflection in document units and an angular deflection in radians. Verify the API for the installed version. Do not confuse display deviation with an absolute surface tolerance.

Record BRep validity, skipped/cleaned geometry and the reasons. Avoid exporting both an assembly compound and its already included child geometry. Preserve source CAD. Compare part counts, valid triangles, hierarchy and actual world-space vertex bounds before/after export; sample surface distances when the requested accuracy needs stronger evidence.

Convert units exactly once. Scene unit labels do not prove vertex dimensions. GLB uses float32 positions, whose precision degrades at large coordinate magnitudes. STL stores neither units nor materials; coloured appearance needs a target-supported visual format and its resource dependencies.

## Identify and align actual interfaces

Use CAD planes/cylinders/circles and the assembly datums; fit mesh planes/axes only when necessary. A bounding-box centre, an asymmetric face centroid or a visually prominent bracket face is not necessarily the actual mounting datum.

Record each interface's owning rigid body, coordinate system, centre, normal, locating axis, orientation datum and relevant hole dimensions. Determine centre from cylindrical datums or hole patterns when appropriate.

Normal direction depends on the convention: a common robot-to-tool mounting axis points the same way, while both solid-outward mating normals point opposite ways. Minimum-rotation alignment determines tilt but not the required in-plane rotation. Use a locating key/hole datum or the user's intended azimuth; handle antiparallel axes explicitly.

For source/target centres `c_s`, `c_t` in one world frame and chosen rotation `R`, using column vectors:

```text
Delta = Translate(c_t) * R * Translate(-c_s)
T_tool_world_new = Delta * T_tool_world_old
```

Transform the whole component once. If the scene root also contains the robot, create/select a component-only group while preserving its members' world matrices. Nonuniform scale requires inverse-transpose normal transformation; ordinary direction transformation is insufficient.

Check axis angle, axial gap, lateral offset and in-plane azimuth after alignment. Preserve intended mounting offsets. Distinguish body contact/penetration from screw/hole incompatibility and future motion-range collision. A rigid transform cannot change a bolt-circle diameter.

## URDF frame transforms

Let `^A T_B` transform B-frame coordinates into A. Use metres, radians and a consistent right-handed convention. URDF origin rotation is:

```text
R = Rz(yaw) * Ry(pitch) * Rx(roll)
```

Obtain the parent-link pose at the actual reference joint configuration `q` through FK. Calibrate the robot root R to assembly world W rather than assuming the two coordinate systems match:

```text
^W T_P = ^W T_R * ^R T_P(q)
^P T_F = inverse(^W T_P) * ^W T_F
```

`^P T_F` becomes the fixed-joint origin for desired component frame F. If geometry was already baked into the parent frame, an identity joint transform may be appropriate. If F is at a real interface or TCP, its origin is usually nonzero. Do not force identity by ignoring frame differences.

Convert each source part's geometry into F:

```text
v_F = inverse(^W T_F) * ^W T_part * v_part
```

Apply each alignment exactly once across baked geometry, visual/collision origins and joint origins. Revolute/prismatic axes are local to the joint; prismatic limits are metres and angular limits are radians.

For a new description, establish axes, joint centres, reference pose, limits and couplings from mechanism data. Adjacent meshes do not prove a fixed connection or an allowed motion. Closed-loop cuts, mimic semantics and transmission/control support need an explicit target-runtime representation.

## Validation beyond appearance

- Compare reused URDF mechanisms and physical fields, recording URI changes separately.
- Reopen the actual exported URDF/meshes and evaluate both zero and nonzero configurations; cached assembly transforms alone are not independent evidence.
- Fixed components remain constant relative to their physical parent. Moving components follow the expected axis and mechanism.
- Surface intersection can be coplanar contact. Classify it using normals, depth, distance and intended clearance; finite sampling is not a proof of collision freedom.
- Select collision geometry by contact needs. A single convex hull can close a gripper gap or insertion cavity; fully detailed visuals can be unnecessarily costly collision input. Preserve visual fidelity independently.
