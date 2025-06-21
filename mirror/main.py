#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

import cv2
import camera as cam
import http_server
import shared

USE_WEBCAM = True  # Set False when running on Raspberry Pi

camera, get_frame = cam.init_webcam() if USE_WEBCAM else cam.init_picam2()

def run():
    http_server.start_non_blocking()

    try:
        while True:
            frame = get_frame()

            with shared.lock:
                shared.shared_data["last_camera_frame"] = frame

            cv2.imshow("Frame", frame)
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
