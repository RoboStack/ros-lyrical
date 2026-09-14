import sys
import unittest

import launch
from launch import LaunchDescription
import launch_ros.actions
import launch_testing.actions
import launch_testing.asserts


def generate_test_description():
    static_transform_publisher = launch_ros.actions.Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="screen",
        arguments=[
            "--x", "0",
            "--y", "0",
            "--z", "0",
            "--roll", "0",
            "--pitch", "0",
            "--yaw", "0",
            "--frame-id", "world",
            "--child-frame-id", "child",
        ],
        additional_env={
            "RMW_IMPLEMENTATION": "rmw_zenoh_cpp",
            # This smoke test only needs to verify that the node initializes.
            "ZENOH_ROUTER_CHECK_ATTEMPTS": "-1",
        },
    )

    return LaunchDescription([
        static_transform_publisher,
        launch_testing.actions.ReadyToTest(),
    ])


class TestStaticTransformPublisher(unittest.TestCase):

    def test_node_initializes(self, proc_output):
        proc_output.assertWaitFor(
            expected_output="Spinning until stopped - publishing transform",
            timeout=10,
            stream="stderr",
        )


@unittest.skipIf(
    sys.platform == "darwin",
    "Post-shutdown exit codes are unreliable on macOS.",
)
@launch_testing.post_shutdown_test()
class TestStaticTransformPublisherPostShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        launch_testing.asserts.assertExitCodes(proc_info)
