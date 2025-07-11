#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

try:
    from picamera2 import Picamera2

    picam2 = Picamera2()
    config = picam2.create_preview_configuration(
        main={"size": (410, 308), "format": "RGB888"},
        #main={"size": (1640, 1232), "format": "RGB888"},
        #lores={"size": (410, 308), "format": "YUV420"}
    )
    picam2.configure(config)
    picam2.start()

    def get_frame(preview="main"):
        return picam2.capture_array(preview)

    def release():
        pass

except ImportError:
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

except Exception as e:
    print(f"Camera error : {e}")
