#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import logging
import time
import cv2
import requests

from config import AUTH_TOKEN, URL, MODEL_PATH, FACE_CASCADE_PATH, EYE_CASCADE_PATH
from face_recognition import LightweightFaceDetector

logger = logging.getLogger(__name__)


def monitor_gaze_stream() -> None:
    try:
        detector = LightweightFaceDetector(
            str(MODEL_PATH),
            str(FACE_CASCADE_PATH),
            str(EYE_CASCADE_PATH)
        )
    except IOError as e:
        logger.error(f"Failed to initialize gaze detector: {e}")
        return

    def send_gaze_start():
        try:
            requests.post(
                f"{URL}/start_eye_contact",
                headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
                timeout=5
            )
        except requests.RequestException:
            pass

    def send_gaze_end():
        try:
            requests.post(
                f"{URL}/stop_eye_contact",
                headers={'Authorization': f'Bearer {AUTH_TOKEN}'},
                timeout=5
            )
        except requests.RequestException:
            pass

    detector.set_gaze_start_callback(send_gaze_start)
    detector.set_gaze_end_callback(send_gaze_end)

    while True:
        cap = None
        try:
            cap = cv2.VideoCapture(f"{URL}/get_camera_stream")
            if not cap.isOpened():
                raise ConnectionError("Stream failed to open")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                detector.process_frame(frame)

                if detector.tracking_bbox:
                    x, y, w, h = detector.tracking_bbox
                    color = (0, 0, 255) if detector._gaze_active else (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                cv2.imshow('Gaze Stream Monitor', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return

        except (ConnectionError, cv2.error):
            logger.warning("Connection lost or error reading from stream; retrying in 5 seconds.")

        finally:
            if cap:
                cap.release()
            cv2.destroyAllWindows()

        time.sleep(5)

