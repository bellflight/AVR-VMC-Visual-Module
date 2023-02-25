from __future__ import annotations

import math
import sys
from typing import TYPE_CHECKING

import pytest
from bell.avr.utils.testing import dont_run_forever
from pytest_mock.plugin import MockerFixture

if TYPE_CHECKING:
    from src.vio import VIOModule
    from src.vio_library import CameraCoordinateTransformation
    from src.zed_library import ZEDCamera


@pytest.fixture
def config(mocker: MockerFixture) -> None:
    sys.path.append("src")

    # make these constant
    mocker.patch("config.CAM_UPDATE_FREQ", 10)
    mocker.patch("config.CAM_POS", [15, 10, 10])
    mocker.patch("config.CAM_ATTITUDE", [0, -math.pi / 2, math.pi / 2])
    mocker.patch("config.CAM_GROUND_HEIGHT", 10)


@pytest.fixture
def config_continuous_sync_off(config: None, mocker: MockerFixture) -> None:
    mocker.patch("config.CONTINUOUS_SYNC", False)


@pytest.fixture
def camera_coordinate_transformation(config: None) -> CameraCoordinateTransformation:
    # create module object
    from src.vio_library import CameraCoordinateTransformation

    return CameraCoordinateTransformation()


@pytest.fixture
def zed_camera(mocker: MockerFixture) -> ZEDCamera:
    # mock the pyzed package
    sys.modules["pyzed"] = mocker.MagicMock()
    sys.modules["pyzed.sl"] = mocker.MagicMock()

    # create object
    from src.zed_library import ZEDCamera

    zed_camera = ZEDCamera()

    # patch the constants
    mocker.patch("src.zed_library.sl.ERROR_CODE.SUCCESS", True)

    # patch the zed object
    mocker.patch.object(zed_camera, "zed")
    mocker.patch.object(zed_camera.zed, "open", return_value=True)
    mocker.patch.object(zed_camera.zed, "grab", return_value=True)
    mocker.patch.object(zed_camera.zed, "enable_positional_tracking", return_value=True)

    zed_camera.setup()

    return zed_camera


@pytest.fixture
def vio_module(config: None, zed_camera: None, mocker: MockerFixture) -> VIOModule:
    # patch the run_forever decorator
    mocker.patch("bell.avr.utils.decorators.run_forever", dont_run_forever)

    # patch the send message function
    mocker.patch("src.vio.VIOModule.send_message")

    # create module object
    from src.vio import VIOModule

    return VIOModule()
