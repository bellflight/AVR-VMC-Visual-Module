from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import pytest
from pytest_mock.plugin import MockerFixture

from src.models import CameraFrameData

if TYPE_CHECKING:
    from src.zed_library import ZEDCamera


@pytest.mark.parametrize(
    "last_pos, translation, rotation, expected",
    [
        (
            (1, 2, 3),
            (4, 5, 6),
            (0.5, 1, 1.5, 2.0),
            {
                "rotation": (0.5, 1, 1.5, 2.0),
                "tracker_confidence": 1.0,
                "translation": (4, 5, 6),
                "velocity": (3.0, 3.0, 3.0),
            },
        ),
    ],
)
def test_get_pipe_data(
    zed_camera: ZEDCamera,
    mocker: MockerFixture,
    last_pos: Tuple[float, float, float],
    translation: Tuple[float, float, float],
    rotation: Tuple[float, float, float, float],
    expected: CameraFrameData,
) -> None:
    # mock incoming values
    mocker.patch.object(zed_camera, "last_pos", last_pos)
    zed_camera.zed_pose.get_translation.return_value.get.return_value = translation
    zed_camera.zed_pose.pose_confidence = 1.0
    from src.zed_library import sl

    sl.Orientation.return_value.get.return_value = rotation

    # force 1 seond since last reading
    zed_camera.last_time = 0
    zed_camera.zed.get_timestamp.return_value.get_milliseconds.return_value = 1000

    assert zed_camera.get_pipe_data() == expected
