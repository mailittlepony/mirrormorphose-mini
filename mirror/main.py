#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GLPv3 license.

import cv2
import camera as cam
import http_server
import shared
from face_recognition import FaceDetector

USE_WEBCAM = True  # Set False when running on Raspberry Pi
camera, get_frame = cam.init_webcam() if USE_WEBCAM else cam.init_picam2()

def gaze_start_callback():
    print("Gaze started")

def gaze_end_callback():
    print("Gaze ended")

def run():
    http_server.start_non_blocking()

    face_detector = FaceDetector("models/eye_direction_model.tflite")
    face_detector.set_gaze_start_callback(gaze_start_callback)
    face_detector.set_gaze_end_callback(gaze_end_callback)

    try:
        while True:
            frame = get_frame()

            face_detector.process_frame(frame)

            with shared.lock:
                shared.shared_data["last_camera_frame"] = frame

            # cv2.imshow(WINDOW_NAME, displayed_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Shutting down...")

    finally:
        if USE_WEBCAM:
            camera.release()
        cv2.destroyAllWindows()
        http_server.stop()

if __name__ == "__main__":
    run()
