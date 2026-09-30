import sys

from launch import LaunchDescription
from launch.actions import TimerAction
import launch_ros.actions
import launch_pytest
import pytest


@pytest.fixture
def zenoh_router():
    return launch_ros.actions.Node(
        package="rmw_zenoh_cpp",
        executable="rmw_zenohd",
        output="screen",
    )


@pytest.fixture
def static_transform_publisher():
    return launch_ros.actions.Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        output="screen",
        cached_output=True,
        arguments=[
            "--frame-id", "world",
            "--child-frame-id", "child",
        ],
        additional_env={
            "RMW_IMPLEMENTATION": "rmw_zenoh_cpp",
            "RCUTILS_LOGGING_USE_STDOUT": "1",
            "ZENOH_ROUTER_CHECK_ATTEMPTS": "10",
        },
    )

@launch_pytest.fixture
def launch_description(zenoh_router, static_transform_publisher):
    return LaunchDescription([
        zenoh_router,
        TimerAction(period=1.0, actions=[static_transform_publisher]),
    ])

@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Zenoh router initialization hangs on Windows.",
)
@pytest.mark.launch(fixture=launch_description)
def test_node_initializes(static_transform_publisher, launch_context):
    def validate_output(output):
        assert "Spinning until stopped - publishing transform" in output

    launch_pytest.tools.process.assert_output_sync(
        launch_context,
        static_transform_publisher,
        validate_output,
        timeout=10,
    )
