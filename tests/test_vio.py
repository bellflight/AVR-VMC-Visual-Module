from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

import pytest
from bell.avr.mqtt.payloads import (
    AVRVIOAttitudeEulerRadians,
    AVRVIOConfidence,
    AVRVIOHeading,
    AVRVIOPositionLocal,
    AVRVIOResync,
    AVRVIOVelocity,
)
from pytest_mock.plugin import MockerFixture

if TYPE_CHECKING:
    from src.vio import VIOModule


def test_handle_resync_continuous_off(
    mocker: MockerFixture, config_continuous_sync_off: None, vio_module: VIOModule
) -> None:
    mocker.patch.object(vio_module.coord_trans, "sync")

    vio_module.handle_resync(AVRVIOResync(n=0, e=0, d=0, hdg=0))
    vio_module.handle_resync(AVRVIOResync(n=0, e=0, d=0, hdg=0))
    vio_module.coord_trans.sync.assert_called_once()


def test_handle_resync_continuous_on(
    mocker: MockerFixture, vio_module: VIOModule
) -> None:
    mocker.patch.object(vio_module.coord_trans, "sync")

    vio_module.handle_resync(AVRVIOResync(n=0, e=0, d=0, hdg=0))
    vio_module.handle_resync(AVRVIOResync(n=0, e=0, d=0, hdg=0))
    assert vio_module.coord_trans.sync.call_count == 2


@pytest.mark.parametrize(
    "ned_pos, ned_vel, rpy, tracker_confidence, expected_ned_update,"
    + " expected_eul_update, expected_heading_update, expected_vel_update,"
    + " expected_confidence_update",
    [
        (
            (1, 2, 3),
            (4, 5, 6),
            (1, 2, 3),
            1.0,
            AVRVIOPositionLocal(n=1.0, e=2.0, d=3.0),
            AVRVIOAttitudeEulerRadians(psi=1.0, theta=2.0, phi=3.0),
            AVRVIOHeading(hdg=171.88733853924697),
            AVRVIOVelocity(Vn=4, Ve=5, Vd=6),
            AVRVIOConfidence(tracking=1.0),
        ),
        (
            (float("nan"), 2, 3),
            (4, 5, 6),
            (1, 2, 3),
            1.0,
            None,
            None,
            None,
            None,
            None,
        ),
        (
            (1, 2, 3),
            (4, float("nan"), 6),
            (1, 2, 3),
            1.0,
            AVRVIOPositionLocal(n=1.0, e=2.0, d=3.0),
            AVRVIOAttitudeEulerRadians(psi=1.0, theta=2.0, phi=3.0),
            AVRVIOHeading(hdg=171.88733853924697),
            None,
            None,
        ),
        (
            (1, 2, 3),
            (4, 5, 6),
            (1, 2, float("nan")),
            1.0,
            AVRVIOPositionLocal(n=1.0, e=2.0, d=3.0),
            None,
            None,
            None,
            None,
        ),
    ],
)
def test_publish_update(
    vio_module: VIOModule,
    ned_pos: Tuple[float, float, float],
    ned_vel: Tuple[float, float, float],
    rpy: Tuple[float, float, float],
    tracker_confidence: float,
    expected_ned_update: AVRVIOPositionLocal,
    expected_eul_update: AVRVIOAttitudeEulerRadians,
    expected_heading_update: AVRVIOHeading,
    expected_vel_update: AVRVIOVelocity,
    expected_confidence_update: AVRVIOConfidence,
) -> None:
    vio_module.publish_updates(ned_pos, ned_vel, rpy, tracker_confidence)

    if expected_ned_update is not None:
        vio_module.send_message.assert_any_call(
            "avr/vio/position/local", expected_ned_update
        )

    if expected_eul_update is not None:
        vio_module.send_message.assert_any_call(
            "avr/vio/attitude/euler/radians", expected_eul_update
        )

    if expected_heading_update is not None:
        vio_module.send_message.assert_any_call(
            "avr/vio/heading", expected_heading_update
        )

    if expected_vel_update is not None:
        vio_module.send_message.assert_any_call("avr/vio/velocity", expected_vel_update)

    if expected_confidence_update is not None:
        vio_module.send_message.assert_any_call(
            "avr/vio/confidence", expected_confidence_update
        )


def test_process_camera_data_empty_response(
    mocker: MockerFixture, vio_module: VIOModule
) -> None:
    mocker.patch.object(vio_module.camera, "get_pipe_data", None)
    mocker.patch.object(vio_module.coord_trans, "transform_trackcamera_to_global_ned")

    vio_module.process_camera_data()
    vio_module.coord_trans.transform_trackcamera_to_global_ned.assert_not_called()


def test_process_camera_data(mocker: MockerFixture, vio_module: VIOModule) -> None:
    mocker.patch.object(vio_module.camera, "get_pipe_data")
    mocker.patch.object(
        vio_module.coord_trans,
        "transform_trackcamera_to_global_ned",
        return_value=((1, 2, 3), (4, 5, 6), (7, 8, 9)),
    )
    mocker.patch.object(vio_module, "publish_updates")

    vio_module.process_camera_data()
    vio_module.coord_trans.transform_trackcamera_to_global_ned.assert_called_once()
    vio_module.publish_updates.assert_called_once()
