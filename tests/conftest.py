from __future__ import annotations

import math
import sys
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

import pytest
from pytest_mock.plugin import MockerFixture

if TYPE_CHECKING:
    from src.vio import VIOModule
    from src.vio_library import CameraCoordinateTransformation


def dont_run_forever(*args, **kwargs) -> Callable:
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            return f(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture
def config(mocker: MockerFixture) -> None:
    sys.path.append("src")

    # make these constant
    mocker.patch("config.CAM_UPDATE_FREQ", 10)
    mocker.patch("config.CAM_POS", [15, 10, 10])
    mocker.patch("config.CAM_ATTITUDE", [0, -math.pi / 2, math.pi / 2])
    mocker.patch("config.CAM_GROUND_HEIGHT", 10)


@pytest.fixture
def vio_module(config: None, mocker: MockerFixture) -> VIOModule:
    # patch the run_forever decorator
    mocker.patch("bell.avr.utils.decorators.run_forever", dont_run_forever)

    # patch the send message function
    mocker.patch("src.vio.VIOModule.send_message")

    # create module object
    from src.vio import VIOModule

    return VIOModule()


@pytest.fixture
def camera_coordinate_transformation(config: None) -> CameraCoordinateTransformation:
    # create module object
    from src.vio_library import CameraCoordinateTransformation

    return CameraCoordinateTransformation()
