from __future__ import annotations

from typing import TYPE_CHECKING

from src.models import ResyncData, CameraFrameData

import numpy as np
import pytest

if TYPE_CHECKING:
    from src.vio_library import CameraCoordinateTransformation


def test_setup_transforms(
    camera_coordinate_transformation: CameraCoordinateTransformation,
) -> None:
    camera_coordinate_transformation.setup_transforms()

    expected = {
        "H_aeroBody_TRACKCAMBody": np.array(
            [
                [3.74939946e-33, -6.12323400e-17, -1, 15],
                [1, 6.12323400e-17, 0, 10],
                [6.12323400e-17, -1, 6.12323400e-17, 10],
                [0, 0, 0, 1],
            ]
        ),
        "H_TRACKCAMBody_aeroBody": np.array(
            [
                [3.74939946e-33, 1, 6.12323400e-17, -10],
                [-6.12323400e-17, 6.12323400e-17, -1, 10],
                [-1, -0, 6.12323400e-17, 1.50000000e01],
                [0, 0, 0, 1],
            ]
        ),
        "H_aeroRef_TRACKCAMRef": np.array(
            [
                [3.74939946e-33, -6.12323400e-17, -1, 15],
                [1, 6.12323400e-17, 0, 10],
                [6.12323400e-17, -1, 6.12323400e-17, -10],
                [0, 0, 0, 1],
            ]
        ),
        "H_aeroRefSync_aeroRef": np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ]
        ),
        "H_nwu_aeroRef": np.array(
            [
                [1, 0, 0, 0],
                [0, -1, -1.2246468e-16, 0],
                [0, 1.2246468e-16, -1, 0],
                [0, 0, 0, 1],
            ]
        ),
    }

    for key, value in expected.items():
        assert np.allclose(camera_coordinate_transformation.tm[key], value)


@pytest.mark.parametrize(
    "data, expected, expected_H_TRACKCAMRef_TRACKCAMBody, expected_H_aeroRef_aeroBody, expected_H_aeroRefSync_aeroBody",
    [
        (
            {
                "rotation": (0, 0, 0, 0),
                "translation": (0, 0, 0),
                "velocity": (0, 0, 0),
                "tracker_confidence": 1.0,
            },
            (
                np.array([0, 0, -20]),
                (0, 0, 0, 0),
                (-0, 0, -1.5040389444259048e-49),
            ),
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ]
            ),
            np.array(
                [
                    [1, -1.50403894e-49, 0, 0],
                    [-1.50403894e-49, 1, 0, 0],
                    [0, 0, 1, -20],
                    [0, 0, 0, 1],
                ]
            ),
            np.array(
                [
                    [1, -1.50403894e-49, 0, 0],
                    [-1.50403894e-49, 1, 0, 0],
                    [0, 0, 1, -20],
                    [0, 0, 0, 1],
                ]
            ),
        )
    ],
)
def test_transform_trackcamera_to_global_ned(
    camera_coordinate_transformation: CameraCoordinateTransformation,
    data: CameraFrameData,
    expected: tuple,
    expected_H_TRACKCAMRef_TRACKCAMBody: np.ndarray,
    expected_H_aeroRef_aeroBody: np.ndarray,
    expected_H_aeroRefSync_aeroBody: np.ndarray,
) -> None:
    values = camera_coordinate_transformation.transform_trackcamera_to_global_ned(data)
    for v, e in zip(values, expected):
        assert np.allclose(v, e)

    assert np.allclose(
        expected_H_TRACKCAMRef_TRACKCAMBody,
        camera_coordinate_transformation.tm["H_TRACKCAMRef_TRACKCAMBody"],
    )
    assert np.allclose(
        expected_H_aeroRef_aeroBody,
        camera_coordinate_transformation.tm["H_aeroRef_aeroBody"],
    )
    assert np.allclose(
        expected_H_aeroRefSync_aeroBody,
        camera_coordinate_transformation.tm["H_aeroRefSync_aeroBody"],
    )


@pytest.mark.parametrize(
    "camera_frame_data, resync_data, expected_H_aeroRefSync_aeroRef",
    [
        (
            {
                "rotation": (0, 0, 0, 0),
                "translation": (0, 0, 0),
                "velocity": (0, 0, 0),
                "tracker_confidence": 1.0,
            },
            {"n": 0, "e": 0, "d": 0, "heading": 0},
            np.array(
                [
                    [1, -2.4492936e-16, 0, 0],
                    [2.4492936e-16, 1, 0, 0],
                    [0, 0, 1, 20],
                    [0, 0, 0, 1],
                ]
            ),
        ),
        (
            {
                "rotation": (0.5, 1, 1.5, 2),
                "translation": (1, 2, 3),
                "velocity": (4, 5, 6),
                "tracker_confidence": 1.0,
            },
            {"n": 7, "e": 8, "d": 9, "heading": -10},
            np.array(
                [
                    [2.04520132e-01, 9.78862358e-01, 0, -5.93488455e01],
                    [-9.78862358e-01, 2.04520132e-01, 0, -3.05189768e02],
                    [0, 0, 1, 2.19000000e02],
                    [0, 0, 0, 1],
                ]
            ),
        ),
    ],
)
def test_sync(
    camera_coordinate_transformation: CameraCoordinateTransformation,
    camera_frame_data: CameraFrameData,
    resync_data: ResyncData,
    expected_H_aeroRefSync_aeroRef: np.ndarray,
) -> None:
    camera_coordinate_transformation.setup_transforms()
    camera_coordinate_transformation.transform_trackcamera_to_global_ned(
        camera_frame_data
    )
    camera_coordinate_transformation.sync(resync_data)
    assert np.allclose(
        expected_H_aeroRefSync_aeroRef,
        camera_coordinate_transformation.tm["H_aeroRefSync_aeroRef"],
    )
