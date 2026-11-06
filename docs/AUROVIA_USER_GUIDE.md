# AUROVIA
## Autonomous Vehicle Simulation — User Guide

**Project:** AUROVIA<br>
**Platform:** ROS 2 Lyrical, Gazebo Sim and RViz2<br>
**Vehicle type:** Ackermann-steered autonomous vehicle<br>
**Document:** User Guide<br>
**Status:** Initial documentation draft

---

# 1. Introduction

AUROVIA is an autonomous vehicle simulation project developed using ROS 2 and Gazebo Sim. It provides a simulated automotive environment for exploring vehicle control, sensor integration, odometry, road navigation, traffic infrastructure and autonomous driving behaviour.

The project combines an Ackermann-steered vehicle with a custom urban environment containing multiple road layouts, traffic lights, streetlights, flyover infrastructure, roadworks and other urban features.

The simulation is designed to support the development and demonstration of automotive robotics concepts in a controlled virtual environment.

## 1.1 Project objectives

The main objectives are to:

- Simulate an Ackermann-steered road vehicle.
- Demonstrate manual and autonomous vehicle control.
- Integrate automotive and environmental sensors.
- Estimate vehicle movement using odometry.
- Develop road-following and obstacle-avoidance behaviour.
- Simulate traffic lights and urban road infrastructure.
- Provide day and night lighting conditions.
- Visualise vehicle and sensor information through RViz2 and the vehicle dashboard.

# 2. System Requirements

The project uses the following software environment:


| Component | Technology |
|---|---|
| Operating system | Ubuntu 26.04 LTS |
| Robotics middleware | ROS 2 Lyrical |
| Simulation | Gazebo Sim |
| Visualisation | RViz2 |
| Build system | colcon and CMake |
| C++ build standard | C++17 for the custom GUI plugins |
| Python | ROS 2 Python packages |
| Vehicle model | Ackermann-steered Audibot |

A computer with sufficient memory and processing capability is recommended because the simulation contains a detailed urban environment, vehicle sensors, lighting systems and multiple simulation plugins.

Performance will depend on the host computer, graphics hardware, virtualisation configuration and the complexity of the active simulation.

# 3. Project Environment

## 3.1 Urban environment

AUROVIA contains eight main city zones.

| Zone | Description |
|---|---|
| Zone 1 | Main urban road |
| Zone 2 | Three-stage curved road and landscaped garden |
| Zone 3 | Signalised intersection with traffic lights and pedestrian crossings |
| Zone 4 | Roadworks area with cones and warning signage |
| Zone 5 | Open test area |
| Zone 6 | Urban streetscape with roads, sidewalks, buildings, trees and lighting |
| Zone 7 | East–west flyover with elevated road infrastructure and underdeck lighting |
| Zone 8 | Two curved access roads connecting the open test area to the east and west flyover ramps |

The environment supports different road layouts and driving scenarios rather than a single straight test track.

## 3.2 Vehicle model

The simulation uses an Ackermann-steered Audibot vehicle.

The model includes vehicle dynamics and control interfaces for:

- Steering.
- Throttle.
- Braking.
- Forward and reverse gear selection.
- Vehicle speed commands.
- Headlamp control.

The vehicle model is designed to represent a road vehicle rather than a differential-drive mobile robot.

# 4. System Architecture

AUROVIA is organised into ROS 2 packages, Gazebo plugins, vehicle models, launch files, configuration files and supporting scripts.

The main components include:

| Component | Responsibility |
|---|---|
| `audibot_description` | Vehicle model and its sensor description |
| `audibot_gazebo` | Gazebo world, launch files, configuration and Audibot integration |
| `vehicle_system` | Vehicle control, sensor processing, dashboard and navigation nodes |
| `project3_odometry` | Vehicle odometry estimation |
| `vehicle_interfaces` | Custom ROS 2 messages and services |
| `project3_traffic_lights` | Custom traffic-light simulation plugin |
| `vehicle_gazebo_lighting` | Headlamp, city-lighting and camera-lighting plugins |

The main simulation launch file is:

`project3_audibot.launch.xml`

It brings together the vehicle, Gazebo environment, ROS-Gazebo bridge, odometry, vehicle-control components, navigation component and visualisation tools.

The main launch configuration starts the road navigator with its `enabled` parameter set to `false`. Autonomous navigation therefore requires the appropriate activation and configuration; launching the simulation alone should not be interpreted as automatically starting autonomous driving.

# 5. Sensors and Perception

The vehicle model incorporates several sensors to support environmental awareness and vehicle-state estimation.

## 5.1 LiDAR

The LiDAR provides laser-scan measurements through the ROS topic:

`/scan`

The vehicle system includes a LiDAR processing node that evaluates the surrounding environment and calculates obstacle distances in selected directions.

Its processing includes:

- Front-sector obstacle detection.
- Left- and right-side clearance assessment.
- Filtering of known vehicle self-detections.
- Nearest valid obstacle-distance calculation.

The processed information can be used by the autonomous navigation system when determining whether a route is safe.

## 5.2 Inertial Measurement Unit

The IMU provides information about the vehicle's motion and orientation.

Its ROS topic is:

`/audibot/imu`

The data is represented using the standard ROS 2 `sensor_msgs/Imu` message.

## 5.3 Camera

The simulated camera provides image data through:

`/audibot/camera/image_raw`

Camera calibration information is published through:

`/audibot/camera/camera_info`

These topics provide the foundation for camera visualisation and future computer-vision development.

## 5.4 GNSS

The GNSS sensor provides simulated positioning information through:

- `/audibot/fix`
- `/audibot/gnss_heading`

These provide position and heading-related information for vehicle localisation and navigation development.

# 6. Vehicle Control

The `vehicle_system` package provides the software components used to control the simulated vehicle.

## 6.1 Vehicle control authority

The central vehicle-control component coordinates manual and autonomous control commands.

It supports:

- Starting the vehicle control system.
- Selecting manual control.
- Selecting autonomous control.
- Stopping the vehicle.
- Managing forward and reverse gear states.
- Applying braking and coordinating vehicle state.

The system is designed to prevent manual and autonomous command sources from controlling the vehicle simultaneously.

The vehicle-control service is:

`/vehicle/control`

Its interface is defined by the custom `VehicleControl.srv` service.

## 6.2 Manual control

Manual control allows the vehicle to be driven using the available control interfaces.

The simulation supports forward and reverse movement, steering and braking.

The vehicle control system acts as the authority that determines which command source is allowed to control the vehicle.

## 6.3 Autonomous control

The autonomous navigation component is implemented in:

`vehicle_system/road_navigator.py`

It uses odometry, LiDAR information and traffic-light states to make navigation decisions.

The navigation system includes:

- Route-following behaviour.
- Steering calculation for an Ackermann vehicle.
- Obstacle detection and avoidance.
- Safe stopping when the route is blocked.
- Traffic-light response.
- Destination and sensor-timeout handling.

The navigator uses the vehicle's estimated position and heading to calculate steering commands.

Its principal autonomous command topics are:

- `/vehicle/autonomous/drive_command`
- `/vehicle/autonomous/steering_command`

Autonomous navigation must be configured and enabled before it can control the vehicle.

# 7. Road Navigation and Obstacle Avoidance

The navigation system is designed to follow a route while considering the vehicle's surroundings.

## 7.1 Route following

The road navigator uses vehicle odometry to estimate the vehicle's position and orientation.

A lookahead point is used to calculate the required steering direction. The steering calculation accounts for the vehicle's wheelbase and maximum steering angle.

## 7.2 Obstacle avoidance

The navigation component evaluates the front, left and right LiDAR sectors.

When an obstacle is detected within the configured threshold, the navigator evaluates the available side clearance.

Depending on the available space, the system can:

1. Continue following the route.
2. Select a suitable side for avoidance.
3. Temporarily follow an offset target.
4. Return towards the original route after the obstacle is cleared.
5. Stop if neither side provides sufficient clearance.

## 7.3 Safety conditions

The navigation component includes conditions for stopping when:

- The destination has been reached.
- Odometry data becomes stale.
- LiDAR data becomes stale or insufficient.
- An obstacle blocks the route and no safe avoidance direction is available.
- The traffic-light state requires the vehicle to stop.

These behaviours are implemented in the navigation logic and should be evaluated under different simulation conditions.

# 8. Traffic-Light System

The signalised intersection in Zone 3 contains two traffic lights and pedestrian crossings.

A custom Gazebo GUI plugin controls the traffic-light sequence.

The traffic-light states are:

- Red.
- Amber.
- Green.

The controller operates a timed sequence with the following configured durations:

| Phase | Duration |
|---|---:|
| All-red clearance | 1 second |
| Green | 15 seconds |
| Amber | 3 seconds |

The south and north traffic directions operate in alternating phases.

The signal states are published through:

- `/project3/traffic_light/south_state`
- `/project3/traffic_light/north_state`

The autonomous navigation component subscribes to these states and uses them when approaching the configured intersection.

The traffic-light controller uses a timed sequence; it is not an adaptive traffic-management system.

# 9. Lighting System

AUROVIA includes custom lighting components to support day and night simulation.

## 9.1 City lighting

The city-lighting system manages streetlights distributed throughout selected city zones.

The configured city-lighting arrangement contains 63 lights across Zones 1, 2, 5, 6, 7 and 8.

The system changes the environment's lighting conditions according to the selected day or night state.

## 9.2 Camera lighting

A separate Gazebo system plugin applies corresponding lighting conditions to the camera rendering environment.

This helps maintain consistency between the world lighting and the simulated camera view.

## 9.3 Vehicle headlamps

The custom headlamp plugin responds to the vehicle headlamp state published through:

`/vehicle/headlamp_state`

This allows the simulated headlamp appearance to change in response to the vehicle lighting command.

# 10. ROS 2 Interfaces

AUROVIA uses standard ROS 2 messages as well as custom interfaces.

The custom interfaces are provided by `vehicle_interfaces`.

## 10.1 Custom messages

`DriveCommand.msg` contains:

- Vehicle speed.
- Gear selection.
- Brake state.

`VehicleState.msg` contains:

- Running state.
- Vehicle speed.
- Gear selection.
- Brake state.
- Operating phase.

## 10.2 Custom service

`VehicleControl.srv` provides a service interface for requesting vehicle-control operations and receiving the resulting status.

These interfaces separate vehicle-control requests from the underlying Gazebo vehicle actuation.

# 11. Installation and Build

## 11.1 Prepare ROS 2

Source ROS 2 Lyrical:

```bash
source /opt/ros/lyrical/setup.bash
```

Navigate to the repository:

```bash
cd ~/Project3-Ackermann-Vehicle-Simulation
```

## 11.2 Install dependencies

Install the dependencies declared by the project packages:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

Ensure the required ROS 2 and Gazebo repositories are configured before running this command.

## 11.3 Build the workspace

The repository contains archived package backups. Build from the `src` directory explicitly to avoid duplicate package discovery:

```bash
colcon build --base-paths src --symlink-install
```

After a successful build, source the workspace:

```bash
source install/setup.bash
```

## 11.4 Configure Gazebo plugins

Configure the GUI plugin search path:

```bash
export GZ_GUI_PLUGIN_PATH="$PWD/install/vehicle_gazebo_lighting/lib:$PWD/install/project3_traffic_lights/lib${GZ_GUI_PLUGIN_PATH:+:$GZ_GUI_PLUGIN_PATH}"
```

Configure the simulation system plugin search path:

```bash
export GZ_SIM_SYSTEM_PLUGIN_PATH="$PWD/install/audibot_gazebo/lib:$PWD/install/vehicle_gazebo_lighting/lib${GZ_SIM_SYSTEM_PLUGIN_PATH:+:$GZ_SIM_SYSTEM_PLUGIN_PATH}"
```

The GUI plugin directories contain the custom headlamp, city-lighting and traffic-light plugins.

The system plugin directories contain the Audibot interface and camera-lighting system plugins.

The sourced workspace also provides the Gazebo resource path. Preserve its existing entries rather than replacing it blindly.

These environment settings must be available in the terminal used to launch Gazebo.

# 12. Launching the Simulation

After sourcing ROS 2 and the workspace and configuring the Gazebo plugin paths, launch AUROVIA:

```bash
ros2 launch audibot_gazebo project3_audibot.launch.xml
```

The main launch file starts:

- Gazebo and the AUROVIA city world.
- The blue Audibot vehicle.
- ROS-Gazebo bridge.
- Vehicle odometry.
- RViz2 and RQT Publisher.
- Vehicle control.
- Drive controller.
- LiDAR processor.
- Road navigator.

**Important:** The road navigator is launched with `enabled=false`. Autonomous navigation is not automatically activated by starting the simulation.

The plugin libraries and their installation paths have been inspected in the development workspace. The custom plugin libraries, installation paths and environment configuration have been verified. The main AUROVIA simulation has also been successfully launched from the existing development workspace without reported launch errors. A separate clean installation on a fresh system remains to be tested. before treating this procedure as fully validated for public release.

# 13. Visualisation and Monitoring

The project uses Gazebo and RViz2 for visualisation.

Gazebo provides the simulated vehicle and city environment.

RViz2 can be used to inspect:

- Vehicle coordinate frames.
- Odometry.
- LiDAR scans.
- Camera data.
- Robot transforms.
- Other ROS visualisation data.

The project also contains a vehicle dashboard component for displaying vehicle and sensor information.

# 14. Road Map Generation

The project includes scripts for extracting road geometry from the Gazebo world and generating a road graph.

The principal scripts are:

- `scripts/generate_city_road_map.py`
- `scripts/build_city_road_graph.py`

The first script extracts road-surface geometry from selected zones in the world file and generates Python road-map data.

The second script processes the extracted road segments to construct a graph containing road nodes and edges.

These scripts provide a structured representation of the city road layout for navigation development.

The generated graph should not be assumed to represent a fully connected drivable network without further validation.

# 15. Project Limitations and Development Considerations

AUROVIA is an evolving simulation project. Its current functionality should be distinguished from proposed future extensions.

Areas requiring further validation or development may include:

- Comprehensive testing across every road zone and route.
- Broader validation of obstacle avoidance under different traffic and environmental conditions.
- Further camera-based perception and computer-vision development.
- Validation of road-network connectivity and route coverage.
- Testing of vehicle behaviour under different day and night conditions.
- Finalisation of package metadata and repository-wide licensing.
- Verification of installation instructions on a clean ROS 2 environment.

# 16. Troubleshooting

## 16.1 ROS 2 cannot find a package

Confirm that the ROS 2 underlay and project overlay have been sourced:

```bash
source /opt/ros/lyrical/setup.bash
source ~/Project3-Ackermann-Vehicle-Simulation/install/setup.bash
```

## 16.2 Gazebo cannot find a custom plugin

Check that the plugin library has been built and installed.

Also verify the appropriate Gazebo plugin search path:

- `GZ_GUI_PLUGIN_PATH` for GUI plugins.
- `GZ_SIM_SYSTEM_PLUGIN_PATH` for Gazebo system plugins.

## 16.3 Gazebo cannot find a model or world resource

Check the resource paths and confirm that the relevant package has been installed and its resources are available to Gazebo.

## 16.4 Autonomous navigation does not start

Check the road navigator's `enabled` parameter, vehicle-control operating mode, odometry availability, LiDAR data and traffic-light state topics.

The main launch file starts the road navigator disabled by default.

# 17. Project Structure

The main repository structure is organised as follows:

```text
Project3-Ackermann-Vehicle-Simulation/
│
├── src/
│   ├── audibot_description/
│   ├── audibot_gazebo/
│   ├── project3_odometry/
│   ├── project3_traffic_lights/
│   ├── vehicle_description/
│   ├── vehicle_gazebo_lighting/
│   ├── vehicle_interfaces/
│   └── vehicle_system/
│
├── scripts/
│   ├── generate_city_road_map.py
│   └── build_city_road_graph.py
│
├── docs/
│   └── images/
│
├── backups/
│
├── README.md
└── ...
```

# 18. Acknowledgements and Licensing

The project incorporates the Audibot vehicle model, originally attributed in the repository to Micho Radovnikovich.

The original model's BSD licence and attribution requirements must be preserved.

Custom project components and third-party dependencies may have separate licensing terms. Users should consult the relevant package and dependency licences before redistribution.

---

**End of User Guide**
