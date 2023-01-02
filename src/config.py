import math

CAM_UPDATE_FREQ = 10
"""
Times per second to update data from the camera.
"""

CAM_POS = (17, 0, 8.5)
"""
Centimeters from FC forward, right, down
"""

CAM_ATTITUDE = (0, -math.pi / 2, math.pi / 2)
"""
Roll, pitch, yaw in radians
cam x = body -y; cam y = body x, cam z = body z
"""

CAM_GROUND_HEIGHT = 10
"""
Centimeters above the ground.
"""
