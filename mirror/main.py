#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GLPv3 license.

import cv2
import camera
import http_server
import shared
from face_recognition import LightweightFaceDetector

try:
    import display

    display.init()

    def gaze_start_callback():
        print("Gaze started")
        display.play()

    def gaze_end_callback():
        print("Gaze ended")
        display.stop()
except:
    def gaze_start_callback():
        print("Gaze started")

    def gaze_end_callback():
        print("Gaze ended")

MODEL_DIR = "models"

def run():
    http_server.start_non_blocking()

    face_detector = LightweightFaceDetector(f"{MODEL_DIR}/eye_direction_model.tflite", f"{MODEL_DIR}/haarcascade_frontalface_default.xml", f"{MODEL_DIR}/haarcascade_eye_tree_eyeglasses.xml")
    face_detector.set_gaze_start_callback(gaze_start_callback)
    face_detector.set_gaze_end_callback(gaze_end_callback)

    try:
        while True:
            frame = camera.get_frame()

            face_detector.process_frame(frame)

            with shared.lock:
                shared.shared_data["last_camera_frame"] = frame

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Shutting down...")

    finally:
        camera.release()
        cv2.destroyAllWindows()
        http_server.stop()

if __name__ == "__main__":
    run()
