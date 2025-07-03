#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

try:
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
    picam2.preview_configuration.main.format = "BGR888"
    picam2.configure("preview")
    picam2.start()

    def get_frame():
        return picam2.capture_array()

    def release():
        pass

except:
    import cv2

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_frame():
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from webcam.")
        return frame
    def release():
        cap.release()

