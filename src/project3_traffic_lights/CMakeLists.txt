cmake_minimum_required(VERSION 3.22)
project(project3_traffic_lights)

find_package(ament_cmake REQUIRED)
find_package(gz-gui REQUIRED)
find_package(gz-rendering REQUIRED)
find_package(gz-transport REQUIRED)
find_package(gz-plugin REQUIRED COMPONENTS register)
find_package(Qt6 REQUIRED COMPONENTS Core Quick)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

qt_add_resources(PROJECT3_TRAFFIC_LIGHTS_RESOURCES
  Project3TrafficLightsPlugin.qrc
)

add_library(Project3TrafficLightsPlugin SHARED
  src/Project3TrafficLightsPlugin.cc
  ${PROJECT3_TRAFFIC_LIGHTS_RESOURCES}
)

target_link_libraries(Project3TrafficLightsPlugin
  PRIVATE
    gz-gui::gz-gui
    gz-rendering::gz-rendering
    gz-transport::gz-transport
    gz-plugin::gz-plugin
    Qt6::Core
    Qt6::Quick
)

install(
  TARGETS Project3TrafficLightsPlugin
  LIBRARY DESTINATION lib
)

ament_package()
