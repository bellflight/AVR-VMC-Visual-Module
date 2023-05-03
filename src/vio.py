import math
import threading
from typing import Literal, Tuple

import config
import numpy as np
from bell.avr.mqtt.module import MQTTModule
from bell.avr.mqtt.payloads import (
    AVRVIOAttitudeEulerRadians,
    AVRVIOConfidence,
    AVRVIOHeading,
    AVRVIOImageCapture,
    AVRVIOImageRequest,
    AVRVIOImageStreamEnable,
    AVRVIOPositionLocal,
    AVRVIOResync,
    AVRVIOVelocity,
)
from bell.avr.utils.decorators import run_forever, try_except
from bell.avr.utils.images import serialize_image
from bell.avr.utils.timing import rate_limit
from loguru import logger
from vio_library import CameraCoordinateTransformation
from zed_library import ZEDCamera


class VIOModule(MQTTModule):
    def __init__(self):
        super().__init__()

        # record if sync has happend once
        self.init_sync = False

        # record image streaming state
        self.image_stream_enabled: bool = False
        self.image_stream_side: Literal["left", "right"] = "left"
        self.image_stream_compressed: bool = False
        self.image_stream_frequency: int = 1

        # connected libraries
        self.camera = ZEDCamera()
        self.coord_trans = CameraCoordinateTransformation()

        # mqtt
        self.topic_callbacks = {
            "avr/vio/resync": self.handle_resync,
            "avr/vio/image/request": self.handle_image_request,
            "avr/vio/image/stream/enable": self.handle_image_stream_enable,
            "avr/vio/image/stream/disable": self.handle_image_stream_disable,
        }

    def handle_image_request(self, payload: AVRVIOImageRequest) -> None:
        """
        Handle a single image request
        """
        self.send_rgb_image(side=payload.side, compressed=payload.compressed)

    def handle_image_stream_enable(self, payload: AVRVIOImageStreamEnable) -> None:
        """
        Handle an image streaming request
        """
        self.image_stream_enabled = True
        self.image_stream_side = payload.side
        self.image_stream_compressed = payload.compressed
        self.image_stream_frequency = payload.frequency

    def handle_image_stream_disable(self) -> None:
        """
        Disable image streaming
        """
        self.image_stream_enabled = False

    def send_rgb_image(self, side: Literal["left", "right"], compressed: bool) -> None:
        """
        Send an RGB image from the tracking camera.
        """

        image_data = self.camera.get_rgb_image(side)
        serialized_image_data = serialize_image(image_data, compress=compressed)

        payload = AVRVIOImageCapture(**serialized_image_data, side=side)
        self.send_message("avr/vio/image/capture", payload)

    def handle_resync(self, payload: AVRVIOResync) -> None:
        # whenever new data is published to the ZEDCamera resync topic, we need to compute a new correction
        # to compensate for sensor drift over time.
        if not self.init_sync or config.CONTINUOUS_SYNC:
            self.coord_trans.sync(payload)
            self.init_sync = True

    @try_except(reraise=False)
    def publish_updates(
        self,
        ned_pos: Tuple[float, float, float],
        ned_vel: Tuple[float, float, float],
        rpy: Tuple[float, float, float],
        tracker_confidence: float,
    ) -> None:
        if np.isnan(ned_pos).any():
            raise ValueError("Camera has NaNs for position")

        # send position update
        self.send_message(
            "avr/vio/position/local",
            AVRVIOPositionLocal(n=ned_pos[0], e=ned_pos[1], d=ned_pos[2]),
        )

        if np.isnan(rpy).any():
            raise ValueError("Camera has NaNs for orientation")

        # send orientation update
        self.send_message(
            "avr/vio/attitude/euler/radians",
            AVRVIOAttitudeEulerRadians(psi=rpy[0], theta=rpy[1], phi=rpy[2]),
        )

        # send heading update
        heading = rpy[2]
        # correct for negative heading
        if heading < 0:
            heading += 2 * math.pi
        heading = np.rad2deg(heading)
        self.send_message("avr/vio/heading", AVRVIOHeading(hdg=heading))
        # coord_trans.heading = rpy[2]

        if np.isnan(ned_vel).any():
            raise ValueError("Camera has NaNs for velocity")

        # send velocity update
        self.send_message(
            "avr/vio/velocity",
            AVRVIOVelocity(Vn=ned_vel[0], Ve=ned_vel[1], Vd=ned_vel[2]),
        )

        self.send_message(
            "avr/vio/confidence",
            AVRVIOConfidence(
                tracking=tracker_confidence,
            ),
        )

    @run_forever(frequency=config.CAM_UPDATE_FREQ)
    @try_except(reraise=False)
    def process_camera_data(self) -> None:
        data = self.camera.get_pipe_data()

        if data is None:
            logger.debug("Waiting on camera data")
            return

        # collect data from the sensor and transform it into "global" NED frame
        (
            ned_pos,
            ned_vel,
            rpy,
        ) = self.coord_trans.transform_trackcamera_to_global_ned(data)

        self.publish_updates(
            tuple(ned_pos),
            tuple(ned_vel),
            rpy,
            data["tracker_confidence"],
        )

    @run_forever(frequency=100)
    def stream_rgb_images(self) -> None:
        if self.image_stream_enabled:
            rate_limit(
                lambda: self.send_rgb_image(
                    self.image_stream_side, self.image_stream_compressed
                ),
                frequency=self.image_stream_frequency,
            )

    def run(self) -> None:
        self.run_non_blocking()

        # setup the tracking camera
        logger.debug("Setting up camera connection")
        self.camera.setup()

        # start the image stream handler loop
        stream_thread = threading.Thread(target=self.stream_rgb_images)
        stream_thread.start()

        # begin processing data
        self.process_camera_data()


if __name__ == "__main__":
    vio = VIOModule()
    vio.run()
