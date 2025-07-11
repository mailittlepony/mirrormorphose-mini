#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the license.

import cv2
import numpy as np
import time
from collections import deque
import logging

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class LightweightFaceDetector:
    def __init__(self, model_path, face_cascade_path, eye_cascade_path, input_shape=(64, 64)):
        logger.info("Initializing LightweightFaceDetector")

        self._input_shape = input_shape
        self._class_labels = ['forward', 'not_forward']
        self._interpreter = Interpreter(model_path=model_path)
        self._interpreter.allocate_tensors()

        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

        self._face_cascade = cv2.CascadeClassifier(face_cascade_path)
        self._eye_cascade = cv2.CascadeClassifier(eye_cascade_path)

        if self._face_cascade.empty() or self._eye_cascade.empty():
            raise IOError("Failed to load Haar cascade XML files")

        self._gaze_active = False
        self._gaze_start_callback = None
        self._gaze_end_callback = None
        self._start_stare = None
        self._lookaway_start = None

        self.threshold_time = 1.5
        self.lookaway_grace_period = 0.5

        self.last_known_prediction = "not_forward"
        self.prediction_history = deque(maxlen=5)

        self._tracker = None
        self.tracking_bbox = None
        self._frame_counter = 0
        self._detection_interval = 10

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
        if len(faces) == 0:
            return None
        return max(faces, key=lambda f: f[2] * f[3])  # Largest area

    def _init_tracker(self, frame, bbox):
        self._tracker = cv2.TrackerKCF_create()
        self._tracker.init(frame, bbox)
        self.tracking_bbox = bbox

    def _update_tracker(self, frame):
        if self._tracker is None:
            return None

        success, bbox = self._tracker.update(frame)
        if success:
            self.tracking_bbox = tuple(map(int, bbox))
            return self.tracking_bbox

        self._tracker = None
        self.tracking_bbox = None
        return None

    def _get_eye_data(self, frame, face_bbox):
        fx, fy, fw, fh = face_bbox
        face_color = frame[fy:fy+fh, fx:fx+fw]
        face_gray = cv2.cvtColor(face_color, cv2.COLOR_BGR2GRAY)
        eyes = self._eye_cascade.detectMultiScale(face_gray, 1.1, 3)

        if len(eyes) < 2:
            return None

        # Pick the two largest eyes
        eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
        eyes = sorted(eyes, key=lambda e: e[0])  # Left-to-right

        eye_imgs_color = []
        eye_imgs_gray = []

        for (ex, ey, ew, eh) in eyes:
            eye_color = face_color[ey:ey+eh, ex:ex+ew]
            eye_gray = face_gray[ey:ey+eh, ex:ex+ew]
            if eye_color.size > 0:
                eye_imgs_color.append(eye_color)
                eye_imgs_gray.append(eye_gray)

        if len(eye_imgs_color) != 2:
            return None

        # Stack two color eye images side-by-side and resize
        left_eye = cv2.resize(eye_imgs_color[0], self._input_shape)
        right_eye = cv2.resize(eye_imgs_color[1], self._input_shape)
        combined = np.hstack((left_eye, right_eye))  # Shape: (64, 128, 3)
        model_input = cv2.resize(combined, self._input_shape)  # Back to (64, 64, 3)

        return {
            "model_input": model_input,
            "left_eye_gray": eye_imgs_gray[0],
            "right_eye_gray": eye_imgs_gray[1],
        }

    def _get_gaze_direction_heuristic(self, eye_gray):
        if eye_gray is None or eye_gray.size == 0:
            return "not_forward"

        eye_gray = cv2.equalizeHist(eye_gray)
        _, threshold = cv2.threshold(eye_gray, 45, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return "not_forward"

        largest = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest)

        if M['m00'] == 0:
            return "not_forward"

        cx = int(M['m10'] / M['m00'])
        eye_width = eye_gray.shape[1]
        ratio = cx / eye_width

        return "forward" if 0.4 <= ratio <= 0.6 else "not_forward"

    def _predict_with_model(self, eye_img):
        input_tensor = np.expand_dims(eye_img.astype(np.float32) / 255.0, axis=0)  # (1, 64, 64, 3)
        self._interpreter.set_tensor(self._input_details[0]['index'], input_tensor)
        self._interpreter.invoke()
        output = self._interpreter.get_tensor(self._output_details[0]['index'])
        prediction = self._class_labels[np.argmax(output[0])]
        return prediction

    def process_frame(self, frame):
        self._frame_counter += 1
        current_time = time.time()

        if self._tracker:
            self._update_tracker(frame)

        if self.tracking_bbox is None or self._frame_counter % self._detection_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._detect_faces(gray)
            face = self._select_closest_face(faces)
            if face is not None:
                self.tracking_bbox = tuple(face.astype(int))
                self._init_tracker(frame, self.tracking_bbox)
            else:
                self._reset_gaze_state("Face lost")
                self.prediction_history.clear()
                self.last_known_prediction = "not_forward"
                return

        current_prediction = "not_forward"
        if self.tracking_bbox is not None:
            eye_data = self._get_eye_data(frame, self.tracking_bbox)
            if eye_data:
                if self._get_gaze_direction_heuristic(eye_data["left_eye_gray"]) == "forward":
                    current_prediction = self._predict_with_model(eye_data["model_input"])

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
        self._tracker = None

