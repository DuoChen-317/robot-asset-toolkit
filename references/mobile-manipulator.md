# Mobile bases with arms

Use this branch for AGV/AMR or other wheeled platforms carrying manipulators, lifts, cameras and tools. It describes whole-robot assets and their validation, not a complete navigation or task-execution system.

## Establish the requested readiness

- **Assembly/display:** correct geometry and mounting transforms; no implied drive capability.
- **Mobile physics:** real bodies/joints, justified mass/inertia, wheel contact and bounded drive tests.
- **Control-integration asset:** the selected framework's naming/interfaces and required configuration, explicitly requested and tested.

Determine the base type, steering/drive mechanism, mount, arm pose, lift and target runtime from existing data. Missing drive/physical specifications block those validation layers, not independent geometry work.

## Compose modules

Prefer wrapping trustworthy vendor base/arm URDF/Xacro modules in one assembly description. Deliver necessary referenced modules and a reproducible Xacro expansion when applicable. The static checker expects expanded URDF.

The chassis can branch to wheels, sensors and an arm mount. Add lift/turntable joints where the actual mechanism needs them. Resolve duplicated link/joint names with stable prefixes and update parent/child, mimic, transmission, plugin, ros2_control, SRDF and frame references in the configurations actually being delivered.

Inspect a fixed-base arm's `world` link and anchoring joint before attaching it to the chassis. Replace only the obsolete world anchoring in the assembly copy, preserving genuine arm-internal fixed joints and its chassis mount. Maintain a connected single-root tree. Do not double-count fixed-body mass/inertia or duplicate collisions when merging.

## Frames

A common chassis convention is +X forward, +Y left, +Z up. If source assets differ, define the frame transformation explicitly so visual and wheel-control directions remain consistent. Measure the chassis/mount-to-arm transform using [geometry-and-frames.md](geometry-and-frames.md).

Navigation may use `map → odom → base_link`, optionally with `base_footprint`:

- Localization/SLAM typically publishes map-to-odom.
- Odometry/state estimation typically publishes odom-to-base.
- Robot description and joint states provide internal chassis/arm/sensor relationships.

These are different responsibilities. Do not add a fixed odom-to-base transform to make a TF tree appear connected, or publish the same dynamic transform from multiple systems. Whether base_footprint exists and how it relates to the chassis follows the platform contract.

## Wheels, free roots and planning coordinates

| Mechanism | Check |
| --- | --- |
| Differential drive | Left/right order, radius, separation, joint axes and signs; usually continuous wheel joints; no direct sideways velocity |
| Omnidirectional | Wheel order/orientation and kinematic model; a plain cylindrical collider does not reproduce roller-wheel lateral contact |
| Steering drive | Distinct steering and rolling joints, with the actual steering limits |
| Casters, suspension, lifts | Passive/moving joints or explicitly documented simplifications |

The vehicle's physical root must be mobile while the mounting joint fixes the arm relative to the chassis. In Isaac, inspect the imported USD for residual world anchors as well as the fixed-base import setting. Follow the engine's free-root implementation; do not insert a floating/planar URDF joint unconditionally, since support varies.

Planning planar joints or X/Y/yaw virtual rails are not physical wheel joints. Use the planner/SRDF or a separate planning description where supported, and validate odometry/execution mapping. Do not count a free body, virtual planning axes and wheel actuators as interchangeable DOFs.

## Dynamics and collision

Account for the base, arm, mount, tool and payload. Record data/estimation sources. Check combined centre of mass, support/contact, ground clearance and stability for arm extension and relevant accelerations; payload capacity alone does not prove stability.

Keep detailed visual meshes independent from practical collision shapes. Chassis collision should not unintentionally contact the floor instead of wheels, block steering or seal moving clearances. Validate wheel-ground friction/contact and slipping rather than assuming spinning wheel meshes establish locomotion.

Check arm clearance against chassis, mounts, sensors and payload zones. Record deliberate collision exclusions rather than disabling useful contact to hide a modelling error. For navigation integration, a chassis-only footprint may not cover an extended arm.

## Validation and delivery

1. Expand Xacro; inspect naming, tree structure, paths, mount transforms and legacy anchors.
2. If drive interfaces exist, test forward/turning and the mechanism's other supported motions. Check wheel contact, direction and slip.
3. With the base controlled stationary, test nonzero arm configurations and tool following.
4. Move the base and verify the mounted arm/tool follow it, including lift/turntable motion. Test the requested folded/extended/payload conditions.
5. Record driven/passive wheel, steering, lift and arm joints separately from free-root state and planning coordinates. Do not prescribe six or nine total DOFs universally.

Deliver one whole-robot entry point, resources and necessary configuration with frame conventions, base settings, drive interface and actual test scope. Limited smoke tests do not prove all-condition stability.

Stop-and-operate tasks may coordinate arrival, stabilization/docking, workpiece localization, arm work, retraction and departure. Base localization error contributes to operation error; consider task-appropriate vision/fixtures/docking instead of treating arm repeatability as whole-system accuracy. Simultaneous base/arm motion requires separately validated whole-body planning and execution.

## Official references

- [Clearpath platform extension](https://docs.clearpathrobotics.com/docs_robots/legacy/ros1_robots/indoor_robots/ridgeback/tutorials_ridgeback/) — historical ROS 1 wrapping example; adapt APIs to the actual environment.
- [Nav2 transforms](https://github.com/ros-navigation/docs.nav2.org/blob/rolling/docs/configuration_and_development/first_time_robot_setup_guide/transformation/setup_transforms.md).
- [MoveIt base-and-arm planning](https://moveit.picknik.ai/main/doc/examples/mobile_base_arm/mobile_base_arm_tutorial.html).
- [Clearpath whole-body example](https://clearpathrobotics.github.io/clearpath_community_demos/demos_docs/mobile_manipulation.html) — one specific platform, not universal DOF/settings.
