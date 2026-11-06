from setuptools import find_packages, setup

package_name = 'vehicle_system'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    package_data={'': ['py.typed']},
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Akinkunmi Abdullateef Akindolapo',
    maintainer_email='akinkunmiakindolapo@gmail.com',
    description='ROS 2 Python nodes for vehicle control, sensor processing, dashboard monitoring and autonomous navigation in AUROVIA.',
    license='BSD-3-Clause',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'vehicle_control = vehicle_system.vehicle_control:main',
        'steering_controller = vehicle_system.steering_controller:main',
        'drive_controller = vehicle_system.drive_controller:main',
        'light_sensor = vehicle_system.light_sensor:main',
        'headlamp_controller = vehicle_system.headlamp_controller:main',
        'dashboard = vehicle_system.dashboard:main',
        'imu_processor = vehicle_system.imu_processor:main',
        'camera_processor = vehicle_system.camera_processor:main',
        'gnss_processor = vehicle_system.gnss_processor:main',
        'lidar_processor = vehicle_system.lidar_processor:main',
        'road_navigator = vehicle_system.road_navigator:main',
    ],
 },

)
