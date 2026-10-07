# daniela-embodiment

ROS2 embodiment for Daniela OS — the physical (or simulated)
body the neural core controls.

- **motor_node** — subscribes to `/cmd_vel`, drives actuators
- **perception_node** — publishes `/camera/image` + `/scan`
- **bringup.launch.py** — starts both nodes
- **urdf/daniela.urdf** — minimal robot description (base + camera)

## Run (ROS2 Humble+)

```bash
# Install ROS2 deps
sudo apt install ros-humble-rclpy ros-humble-std-msgs \
  ros-humble-sensor-msgs ros-humble-geometry-msgs

# Source ROS2
source /opt/ros/humble/setup.bash

# Install this package
pip install -e .

# Bring up
ros2 launch daniela_embodiment bringup.launch.py

# Drive it
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}}"
```

## Topics

| Topic | Type | Direction |
|-------|------|-----------|
| `/cmd_vel` | `geometry_msgs/Twist` | in (motor) |
| `/camera/image` | `sensor_msgs/Image` | out (perception) |
| `/scan` | `sensor_msgs/LaserScan` | out (perception) |

## Simulation

Pair with `daniela-simulation` to run the same nodes
against a MuJoCo / Isaac world instead of real hardware.
