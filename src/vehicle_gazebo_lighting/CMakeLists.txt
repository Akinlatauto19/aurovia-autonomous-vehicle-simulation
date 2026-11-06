cmake_minimum_required(VERSION 3.22)
project(vehicle_gazebo_lighting)

find_package(ament_cmake REQUIRED)
find_package(gz-gui REQUIRED)
find_package(gz-rendering REQUIRED)
find_package(gz-transport REQUIRED)
find_package(gz-msgs REQUIRED)
find_package(gz-plugin REQUIRED COMPONENTS register)
find_package(Qt6 REQUIRED COMPONENTS Core Quick)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


qt_add_resources(PROJECT3_HEADLAMP_RESOURCES
  Project3HeadlampPlugin.qrc
)

add_library(Project3HeadlampPlugin SHARED
  src/Project3HeadlampPlugin.cc
   ${PROJECT3_HEADLAMP_RESOURCES}
)

target_include_directories(Project3HeadlampPlugin PRIVATE
  include
)

target_link_libraries(Project3HeadlampPlugin
  PRIVATE
    gz-gui::gz-gui
    gz-rendering::gz-rendering
    gz-transport::gz-transport
    gz-plugin::gz-plugin
    Qt6::Core
    Qt6::Quick
)


install(
  TARGETS Project3HeadlampPlugin
  LIBRARY DESTINATION lib
)

qt_add_resources(PROJECT3_CITY_LIGHTING_RESOURCES
  Project3CityLightingPlugin.qrc
)

add_library(Project3CityLightingPlugin SHARED
  src/Project3CityLightingPlugin.cc
  ${PROJECT3_CITY_LIGHTING_RESOURCES}
)

target_link_libraries(Project3CityLightingPlugin
  PRIVATE
    gz-gui::gz-gui
    gz-rendering::gz-rendering
    gz-transport::gz-transport
    gz-plugin::gz-plugin
    Qt6::Core
    Qt6::Quick
)

install(
  TARGETS Project3CityLightingPlugin
  LIBRARY DESTINATION lib
)


find_package(gz-sim REQUIRED)

add_library(Project3CameraLightingSystem SHARED
  src/Project3CameraLightingSystem.cc
)

target_include_directories(Project3CameraLightingSystem PRIVATE include)

target_link_libraries(Project3CameraLightingSystem PRIVATE
  gz-sim::gz-sim
  gz-rendering::gz-rendering
  gz-transport::gz-transport
  gz-msgs::gz-msgs
  gz-plugin::gz-plugin
)

install(TARGETS Project3CameraLightingSystem
  LIBRARY DESTINATION lib
)

ament_package()
