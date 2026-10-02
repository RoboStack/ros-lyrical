import sys
import unittest

import launch
from launch import LaunchDescription
import launch_ros.actions
import launch_testing.actions
import launch_testing.asserts
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rcl_interfaces.srv import GetParameters

# Minimal URDF as a Python string
minimal_robot_urdf = """<?xml version="1.0"?>
<robot name="minimal_robot">
    <link name="base_link" />
    <link name="child_link" />
    <joint name="base_to_child" type="fixed">
        <parent link="base_link" />
        <child link="child_link" />
        <origin xyz="0 0 1" rpy="0 0 0" />
    </joint>
</robot>
"""


def generate_test_description():
    # Launch robot_state_publisher with our URDF
    rsp_node = launch_ros.actions.Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': minimal_robot_urdf}]
    )

    ld = LaunchDescription([
        rsp_node,
        launch_testing.actions.ReadyToTest()
    ])
    # We return a dictionary so we can refer to our node later if needed.
    return ld, {'rsp_node': rsp_node}


class TestRobotStatePublisher(unittest.TestCase):

    def test_node_output(self, proc_output):
        # Lyrical reports successful URDF parsing with this message.
        proc_output.assertWaitFor(
            expected_output="Robot initialized", timeout=10, stream='stderr'
        )

    def test_parameter_service(self):
        context = rclpy.Context()
        rclpy.init(context=context)
        executor = None
        node = None
        try:
            executor = SingleThreadedExecutor(context=context)
            node = rclpy.create_node('robot_state_publisher_smoke_test', context=context)
            client = node.create_client(
                GetParameters, '/robot_state_publisher/get_parameters'
            )
            self.assertTrue(
                client.wait_for_service(timeout_sec=10.0),
                'robot_state_publisher parameter service was not ready'
            )

            request = GetParameters.Request()
            request.names = ['robot_description']
            future = client.call_async(request)
            rclpy.spin_until_future_complete(
                node, future, executor=executor, timeout_sec=10.0
            )

            self.assertTrue(future.done(), 'parameter request timed out')
            self.assertIsNone(future.exception())
            self.assertIsNotNone(future.result())
        finally:
            if executor is not None:
                executor.shutdown()
            if node is not None:
                node.destroy_node()
            rclpy.shutdown(context=context)


# See https://github.com/RoboStack/ros-humble/pull/320#issuecomment-3078288316
@launch_testing.post_shutdown_test()
@unittest.skipIf(sys.platform == "win32", "Skip exit code check on Windows")
class TestRobotStatePublisherPostShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        allowable_exit_codes = [launch_testing.asserts.EXIT_OK]
        if sys.platform == "darwin":
            allowable_exit_codes.extend([-6, -9])

        launch_testing.asserts.assertExitCodes(
            proc_info, allowable_exit_codes=allowable_exit_codes
        )
