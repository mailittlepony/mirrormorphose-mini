#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the license.

import logging
import time
import numpy as np
import cv2
from collections import deque

from utils.eye_processing import extract_eye_data, estimate_gaze_direction
from utils.gaze_model import GazeModel
from utils.tracking import TrackerManager

logger = logging.getLogger(__name__)


class LightweightFaceDetector:
    CLASS_LABELS = ['forward', 'not_forward']
    DEFAULT_INPUT_SHAPE = (64, 64)
    DEFAULT_THRESHOLD_TIME = 1.5
    DEFAULT_LOOKAWAY_GRACE = 0.5

    def __init__(
        self,
        model_path: str,
        face_cascade_path: str,
        eye_cascade_path: str,
        input_shape: tuple = DEFAULT_INPUT_SHAPE
    ):
        logger.info("Initializing LightweightFaceDetector")

        self._input_shape = input_shape
        self._face_cascade = cv2.CascadeClassifier(face_cascade_path)
        self._eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        if self._face_cascade.empty() or self._eye_cascade.empty():
            raise IOError("Failed to load Haar cascade XML files")

        self._model = GazeModel(model_path, input_shape, self.CLASS_LABELS)
        self._tracker = TrackerManager()

        self._gaze_active = False
        self._gaze_start_callback = None
        self._gaze_end_callback = None

        self._start_stare = None
        self._lookaway_start = None
        self.threshold_time = self.DEFAULT_THRESHOLD_TIME
        self.lookaway_grace_period = self.DEFAULT_LOOKAWAY_GRACE

        self.last_known_prediction = "not_forward"
        self.prediction_history = deque(maxlen=5)

        logger.info("Face detector initialized.")

    def set_gaze_start_callback(self, callback):
        self._gaze_start_callback = callback

    def set_gaze_end_callback(self, callback):
        self._gaze_end_callback = callback

    def _reset_gaze_state(self, reason=""):
        if self._gaze_active:
            logger.info(f"Resetting gaze state. Reason: {reason}")
            self._gaze_active = False
            if self._gaze_end_callback:
                self._gaze_end_callback()

        self._start_stare = None
        self._lookaway_start = None

    def _detect_faces(self, gray):
        return self._face_cascade.detectMultiScale(gray, 1.1, 5)

    def _select_closest_face(self, faces):
        return max(faces, key=lambda f: f[2] * f[3]) if faces else None

    def process_frame(self, frame):
        current_time = time.time()
        self._tracker.increment_frame()

        if not self._tracker.has_valid_bbox() or self._tracker.should_detect():
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._detect_faces(gray)
            face = self._select_closest_face(faces)
            if face is not None:
                self._tracker.start_tracking(frame, tuple(face.astype(int)))
            else:
                self._reset_gaze_state("Face lost")
                self.prediction_history.clear()
                self.last_known_prediction = "not_forward"
                return

        bbox = self._tracker.update(frame)
        current_prediction = "not_forward"

        if bbox:
            eye_data = extract_eye_data(frame, bbox, self._eye_cascade, self._input_shape)
            if eye_data and estimate_gaze_direction(eye_data["left_eye_gray"]):
                current_prediction = self._model.predict(eye_data["model_input"])

        self.prediction_history.append(current_prediction)
        stable_prediction = (
            max(set(self.prediction_history), key=self.prediction_history.count)
            if len(self.prediction_history) == self.prediction_history.maxlen
            else "not_forward"
        )

        self.last_known_prediction = stable_prediction
        is_forward = (stable_prediction == "forward")

        if is_forward:
            self._lookaway_start = None
            if self._start_stare is None:
                self._start_stare = current_time
            elif not self._gaze_active and (current_time - self._start_stare >= self.threshold_time):
                self._gaze_active = True
                if self._gaze_start_callback:
                    self._gaze_start_callback()
        else:
            if self._gaze_active:
                if self._lookaway_start is None:
                    self._lookaway_start = current_time
                elif current_time - self._lookaway_start >= self.lookaway_grace_period:
                    self._reset_gaze_state("Looked away")
            else:
                self._start_stare = None

    def release(self):
        logger.info("Releasing resources.")
        self._tracker.reset()

