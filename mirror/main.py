#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GLPv3 license.

import cv2, time
# import camera
import http_server
import shared
# from face_recognition import LightweightFaceDetector

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

    # face_detector = LightweightFaceDetector(f"{MODEL_DIR}/eye_direction_model.tflite", f"{MODEL_DIR}/haarcascade_frontalface_default.xml", f"{MODEL_DIR}/haarcascade_eye_tree_eyeglasses.xml")
    # face_detector.set_gaze_start_callback(gaze_start_callback)
    # face_detector.set_gaze_end_callback(gaze_end_callback)

    try:
        frame_count = 0
        start_time = time.time()

        while True:
            frame_count += 1

            if time.time() - start_time >= 1.0:
                fps = frame_count / (time.time() - start_time)
                # print(f"FPS: {fps:.2f}")
                frame_count = 0
                start_time = time.time()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("Shutting down...")

    finally:
        # camera.release()
        cv2.destroyAllWindows()
        http_server.stop()

if __name__ == "__main__":
    run()
