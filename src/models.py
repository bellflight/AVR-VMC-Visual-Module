from typing import Tuple, TypedDict


class CameraFrameData(TypedDict):
    rotation: Tuple[float, float, float, float]  # quaternion
    translation: Tuple[float, float, float]
    velocity: Tuple[float, float, float]
    tracker_confidence: float


class ResyncData(TypedDict):
    n: float
    e: float
    d: float
    heading: float  # radians
