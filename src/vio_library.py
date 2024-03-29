import math
from typing import Dict, Tuple

import config
import numpy as np
import transforms3d as t3d
from bell.avr.mqtt.payloads import AVRVIOResync
from bell.avr.utils.decorators import try_except
from loguru import logger
from models import CameraFrameData
from nptyping import Float, NDArray, Shape


class CameraCoordinateTransformation:
    """
    This class handles all the coordinate transformations we need to use to get
    relevant data from the tracking camera
    """

    def __init__(self):
        # dict to hold transformation matrixes
        self.tm: Dict[str, NDArray[Shape["4, 4, 4, 4"], Float]] = {}
        # setup transformation matrixes
        self.setup_transforms()

    def setup_transforms(self) -> None:
        cam_rpy = config.CAM_ATTITUDE

        H_aeroBody_TRACKCAMBody = t3d.affines.compose(
            np.asarray(config.CAM_POS),
            t3d.euler.euler2mat(
                cam_rpy[0],
                cam_rpy[1],
                cam_rpy[2],
                axes="rxyz",
            ),
            np.asarray((1, 1, 1)),
        )
        self.tm["H_aeroBody_TRACKCAMBody"] = H_aeroBody_TRACKCAMBody
        self.tm["H_TRACKCAMBody_aeroBody"] = np.linalg.inv(H_aeroBody_TRACKCAMBody)

        pos = list(config.CAM_POS)
        pos[2] = -1 * config.CAM_GROUND_HEIGHT

        H_aeroRef_TRACKCAMRef = t3d.affines.compose(
            np.asarray(pos),
            t3d.euler.euler2mat(
                cam_rpy[0],
                cam_rpy[1],
                cam_rpy[2],
                axes="rxyz",
            ),
            np.asarray((1, 1, 1)),
        )
        self.tm["H_aeroRef_TRACKCAMRef"] = H_aeroRef_TRACKCAMRef

        H_aeroRefSync_aeroRef = np.eye(4)
        self.tm["H_aeroRefSync_aeroRef"] = H_aeroRefSync_aeroRef

        H_nwu_aeroRef = t3d.affines.compose(
            np.asarray((0, 0, 0)),
            t3d.euler.euler2mat(math.pi, 0, 0),
            np.asarray((1, 1, 1)),
        )
        self.tm["H_nwu_aeroRef"] = H_nwu_aeroRef

    @try_except(reraise=False)
    def transform_trackcamera_to_global_ned(
        self, data: CameraFrameData
    ) -> Tuple[
        NDArray[Shape["3"], Float],
        NDArray[Shape["3"], Float],
        Tuple[float, float, float],
    ]:
        """
        Takes in raw sensor data from the camera frame, does the necessary
        transformations between the sensor, vehicle, and reference frames to
        present the sensor data in the "global" NED reference frame.

        Arguments:
        --------------------------
        data : Camera Frame data

        Returns:
        --------------------------
        pos: list
            The NED position of the vehice. A 3 unit list [north, east, down]
        vel: list
            The NED velocities of the vehicle. A 3 unit list [Vn, Ve, Vd]
        rpy: list
            The euler representation of the vehicle attitude.
            A 3 unit list [roll,math.pitch, yaw]

        """
        quaternion = np.array(data["rotation"])

        position = (
            data["translation"][0] * 100,
            data["translation"][1] * 100,
            data["translation"][2] * 100,
        )  # cm

        velocity = np.transpose(
            [
                data["velocity"][0] * 100,
                data["velocity"][1] * 100,
                data["velocity"][2] * 100,
                0,
            ]
        )  # cm/s

        H_TRACKCAMRef_TRACKCAMBody = t3d.affines.compose(
            np.asarray(position),
            t3d.quaternions.quat2mat(quaternion),
            np.asarray((1, 1, 1)),
        )

        self.tm["H_TRACKCAMRef_TRACKCAMBody"] = H_TRACKCAMRef_TRACKCAMBody

        H_aeroRef_aeroBody = self.tm["H_aeroRef_TRACKCAMRef"].dot(
            self.tm["H_TRACKCAMRef_TRACKCAMBody"].dot(
                self.tm["H_TRACKCAMBody_aeroBody"]
            )
        )

        self.tm["H_aeroRef_aeroBody"] = H_aeroRef_aeroBody

        H_aeroRefSync_aeroBody = self.tm["H_aeroRefSync_aeroRef"].dot(
            H_aeroRef_aeroBody
        )
        self.tm["H_aeroRefSync_aeroBody"] = H_aeroRefSync_aeroBody

        T, R, Z, S = t3d.affines.decompose44(H_aeroRefSync_aeroBody)
        eul = t3d.euler.mat2euler(R, axes="rxyz")

        H_vel = self.tm["H_aeroRefSync_aeroRef"].dot(self.tm["H_aeroRef_TRACKCAMRef"])

        vel = np.transpose(H_vel.dot(velocity))

        return T, vel, eul

    @try_except()
    def sync(self, resync_data: AVRVIOResync) -> None:
        """
        Computes offsets between TRACKCAMera ref and "global" frames, to align coord. systems
        """
        # get current readings on where the aeroBody is, according to the sensor
        if "H_aeroRef_aeroBody" not in self.tm:
            raise ValueError("H_aeroRef_aeroBody transformation matrix not found")

        H = self.tm["H_aeroRef_aeroBody"]
        T, R, Z, S = t3d.affines.decompose44(H)
        eul = t3d.euler.mat2euler(R, axes="rxyz")

        # Find the heading offset...
        heading = eul[2]

        # wrap heading in (0, 2*pi)
        if heading < 0:
            heading += 2 * math.pi

        # compute the difference between our global reference, and what our sensor is reading for heading
        heading_offset = resync_data.hdg - (math.degrees(heading))
        logger.debug(f"TRACKCAM: Resync: Heading Offset:{heading_offset}")

        # build a rotation matrix about the global Z axis to apply the heading offset we computed
        H_rot_correction = t3d.affines.compose(
            np.asarray((0, 0, 0)),
            t3d.axangles.axangle2mat(np.array((0, 0, 1)), math.radians(heading_offset)),
            np.asarray((1, 1, 1)),
        )

        # apply the heading correction to the position data the TRACKCAM is providing
        H = H_rot_correction.dot(H)
        T, R, Z, S = t3d.affines.decompose44(H)
        eul = t3d.euler.mat2euler(R, axes="rxyz")

        # Find the position offset
        pos_offset = [
            resync_data.n - T[0],
            resync_data.e - T[1],
            resync_data.d - T[2],
        ]
        logger.debug(f"TRACKCAM: Resync: Pos offset:{pos_offset}")

        # build a translation matrix that corrects the difference between where the sensor thinks we are and were our reference thinks we are
        H_aeroRefSync_aeroRef = t3d.affines.compose(
            np.asarray(pos_offset), H_rot_correction[:3, :3], np.asarray((1, 1, 1))
        )
        self.tm["H_aeroRefSync_aeroRef"] = H_aeroRefSync_aeroRef
