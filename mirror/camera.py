#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

import cv2

# ========== MACOS: Simulate picam2.capture_array() ==========
def init_webcam():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_frame():
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from webcam.")
        return frame

    return cap, get_frame

# ========== RASPBERRY PI: Real picamera2 (for later) ==========
def init_picam2():
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
    picam2.preview_configuration.main.format = "BGR888"
    picam2.configure("preview")
    picam2.start()

    def get_frame():
        return picam2.capture_array()

    return picam2, get_frame
