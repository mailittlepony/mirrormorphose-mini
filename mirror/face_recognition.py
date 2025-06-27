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

try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter

class LightweightFaceDetector:
    def __init__(self, model_path, face_cascade_path, eye_cascade_path, _input_shape=(64, 64)):
        self._input_shape = _input_shape
        self._class_labels = ['forward', 'not_forward']

        self._interpreter = self._load_model(model_path)
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

        self._face_cascade = cv2.CascadeClassifier(face_cascade_path)
        self._eye_cascade = cv2.CascadeClassifier(eye_cascade_path)
        if self._face_cascade.empty() or self._eye_cascade.empty():
            raise IOError(f"Could not load Haar cascade files from {face_cascade_path} or {eye_cascade_path}")

        self._lookaway_start = None
        self._gaze_active = False
        self.threshold_time = 1.5
        self.lookaway_grace_period = 0.5 
        self._start_stare = None
        self.last_known_prediction = "looking_away"

        self._gaze_start_callback = None
        self._gaze_end_callback = None

        self._tracker = None
        self.tracking_bbox = None
        self._frame_counter = 0
        self._detection_interval = 10
        self.prediction_history = deque(maxlen=5)

    def _load_model(self, path):
        interpreter = Interpreter(model_path=path)
        interpreter.allocate_tensors()
        return interpreter

    def _detect_faces(self, gray_frame):
        return self._face_cascade.detectMultiScale(gray_frame, 1.1, 5)

    def _select_closest_face(self, faces):
        if len(faces) == 0:
            return None
        return max(faces, key=lambda f: f[2] * f[3])

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
        else:
            self._tracker = None
            self.tracking_bbox = None
            return None

    def _get_gaze_direction_heuristic(self, eye_roi_gray):
        if eye_roi_gray is None or eye_roi_gray.size == 0:
            return "not_forward" 
            
        eye_roi_gray = cv2.equalizeHist(eye_roi_gray)
        _, thresholded_eye = cv2.threshold(eye_roi_gray, 45, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresholded_eye, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return "not_forward"

        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        
        if M['m00'] == 0:
            return "not_forward"

        cx = int(M['m10'] / M['m00'])
        eye_width = eye_roi_gray.shape[1]
        
        pos_ratio = cx / eye_width
        
        if pos_ratio < 0.40 or pos_ratio > 0.60:
            return "not_forward"
        else:
            return "forward"

    def _get_eye_data(self, frame, face_bbox):
        fx, fy, fw, fh = face_bbox
        face_roi_color = frame[fy:fy+fh, fx:fx+fw]
        face_roi_gray = cv2.cvtColor(face_roi_color, cv2.COLOR_BGR2GRAY)

        eyes = self._eye_cascade.detectMultiScale(face_roi_gray, 1.1, 3)

        if len(eyes) < 2:
            return None

        eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
        eyes = sorted(eyes, key=lambda e: e[0])

        eye_imgs_color = []
        eye_imgs_gray = []
        for (ex, ey, ew, eh) in eyes:
            eye_roi_color = face_roi_color[ey:ey+eh, ex:ex+ew]
            eye_roi_gray = face_roi_gray[ey:ey+eh, ex:ex+ew]
            if eye_roi_color.size > 0:
                eye_imgs_color.append(eye_roi_color)
                eye_imgs_gray.append(eye_roi_gray)
        
        if len(eye_imgs_color) != 2:
            return None

        left_eye_resized = cv2.resize(eye_imgs_color[0], self._input_shape)
        right_eye_resized = cv2.resize(eye_imgs_color[1], self._input_shape)
        combined_eyes = np.hstack((left_eye_resized, right_eye_resized))
        model_input = cv2.resize(combined_eyes, self._input_shape)
        
        return {
            "model_input": model_input,
            "left_eye_gray": eye_imgs_gray[0],
            "right_eye_gray": eye_imgs_gray[1]
        }

    def _predict_with_model(self, eye_img):
        input_data = np.expand_dims(eye_img.astype(np.float32) / 255.0, axis=0)
        self._interpreter.set_tensor(self._input_details[0]['index'], input_data)
        self._interpreter.invoke()
        output_data = self._interpreter.get_tensor(self._output_details[0]['index'])
        return self._class_labels[np.argmax(output_data[0])]

    def _reset_gaze_state(self, reason=""):
        self._start_stare = None
        self._lookaway_start = None
        if self._gaze_active:
            self._gaze_active = False
            if self._gaze_end_callback:
                self._gaze_end_callback()

    def process_frame(self, frame):
        current_time = time.time()
        
        self._frame_counter += 1
        if self._tracker is not None:
            self._update_tracker(frame)

        if self.tracking_bbox is None or self._frame_counter % self._detection_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._detect_faces(gray)
            closest_face = self._select_closest_face(faces) if len(faces) > 0 else None
            
            if closest_face is not None:
                self.tracking_bbox = tuple(closest_face.astype(int))
                self._init_tracker(frame, self.tracking_bbox)
            else:
                self.tracking_bbox = None
                self._tracker = None
                self._reset_gaze_state("Face Lost")
                self.last_known_prediction = "not_forward"
                # Clear history when face is lost
                self.prediction_history.clear()
                return

        current_prediction = "not_forward" 
        if self.tracking_bbox is not None:
            eye_data = self._get_eye_data(frame, self.tracking_bbox)
            
            if eye_data:
                heuristic_gaze = self._get_gaze_direction_heuristic(eye_data["left_eye_gray"])
                if heuristic_gaze == "not_forward":
                    current_prediction = "not_forward"
                else:
                    current_prediction = self._predict_with_model(eye_data["model_input"])

        self.prediction_history.append(current_prediction)
        
        stable_prediction = "not_forward"
        if len(self.prediction_history) == self.prediction_history.maxlen:
            try:
                stable_prediction = max(set(self.prediction_history), key=self.prediction_history.count)
            except ValueError:
                stable_prediction = "not_forward"
                
        self.last_known_prediction = stable_prediction

        is_looking_forward = (stable_prediction == "forward")

        if is_looking_forward:
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
                    self._reset_gaze_state("Looked Away")
            else:
                self._start_stare = None

    def set_gaze_start_callback(self, callback): self._gaze_start_callback = callback
    def set_gaze_end_callback(self, callback): self._gaze_end_callback = callback
    def release(self): self._tracker = None
