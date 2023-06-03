# pip install opencv-python

import cv2  # pyright: ignore
from bell.avr.mqtt.module import MQTTModule
from bell.avr.mqtt.payloads import AVRVIOImageCapture
from bell.avr.utils.images import deserialize_image


class ViewerModule(MQTTModule):
    def __init__(self):
        super().__init__()

        self.topic_callbacks = {"avr/vio/image/capture": self.show_image}
        self.first = True

    def show_image(self, payload: AVRVIOImageCapture) -> None:
        raw_image_data = deserialize_image(payload)
        cv2.imshow(payload.side, raw_image_data)
        cv2.waitKey(1)


if __name__ == "__main__":
    module = ViewerModule()
    module.run(host="drone.nathanv.home")
