#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the license.

import cv2
import numpy as np
import time
import mediapipe as mp
from tensorflow.lite.python.interpreter import Interpreter

class FaceDetector:
    def __init__(self, model_path, input_shape=(64, 64), camera_index=0, threshold_time=3.0):
        self.input_shape = input_shape
        self.threshold_time = threshold_time
        self.class_labels = ['forward_look', 'close_look', 'left_look', 'right_look']

        self.interpreter = self._load_model(model_path)
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(refine_landmarks=True)

        self.lookaway_start = None
        self.gaze_active = False
        self.threshold_time = 3.0              
        self.lookaway_grace_period = 0.5      
        self._gaze_start_callback = None
        self._gaze_end_callback = None


        self.LEFT_EYE = [33, 133]
        self.RIGHT_EYE = [362, 263]

    def _load_model(self, path):
        interpreter = Interpreter(model_path=path)
        interpreter.allocate_tensors()
        return interpreter

    def _get_eye_images(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)
        eye_imgs = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                for eye_indices in [self.LEFT_EYE, self.RIGHT_EYE]:
                    eye_coords = []
                    for idx in eye_indices:
                        x = int(face_landmarks.landmark[idx].x * frame.shape[1])
                        y = int(face_landmarks.landmark[idx].y * frame.shape[0])
                        eye_coords.append((x, y))

                    x_min = max(min(p[0] for p in eye_coords) - 5, 0)
                    x_max = min(max(p[0] for p in eye_coords) + 5, frame.shape[1])
                    y_min = max(min(p[1] for p in eye_coords) - 5, 0)
                    y_max = min(max(p[1] for p in eye_coords) + 5, frame.shape[0])

                    eye_img = frame[y_min:y_max, x_min:x_max]
                    if eye_img.size > 0:
                        eye_img_resized = cv2.resize(eye_img, self.input_shape)
                        eye_imgs.append(eye_img_resized)
        return eye_imgs

    def _predict(self, eye_img):
        input_data = np.expand_dims(eye_img.astype(np.float32) / 255.0, axis=0)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        return self.class_labels[np.argmax(output_data[0])]

    def process_frame(self, frame):
        eye_imgs = self._get_eye_images(frame)
        current_time = time.time()

        if eye_imgs:
            eye_input = np.hstack(eye_imgs) if len(eye_imgs) == 2 else eye_imgs[0]
            eye_input = cv2.resize(eye_input, self.input_shape)
            prediction = self._predict(eye_input)

            if prediction == "forward_look":
                self.lookaway_start = None
                if self.start_stare is None:
                    self.start_stare = current_time
                elif not self.gaze_active and (current_time - self.start_stare >= self.threshold_time):
                    self.gaze_active = True
                    if self._gaze_start_callback:
                        self._gaze_start_callback()
            else:
                if self.gaze_active:
                    if self.lookaway_start is None:
                        self.lookaway_start = current_time
                    elif current_time - self.lookaway_start >= self.lookaway_grace_period:
                        self.gaze_active = False
                        self.start_stare = None
                        self.lookaway_start = None
                        if self._gaze_end_callback:
                            self._gaze_end_callback()
                else:
                    self.start_stare = None
                    self.lookaway_start = None
        else:
            if self.gaze_active:
                if self.lookaway_start is None:
                    self.lookaway_start = current_time
                elif current_time - self.lookaway_start >= self.lookaway_grace_period:
                    self.gaze_active = False
                    self.start_stare = None
                    self.lookaway_start = None
                    if self._gaze_end_callback:
                        self._gaze_end_callback()
            else:
                self.start_stare = None
                self.lookaway_start = None

    def set_gaze_start_callback(self, callback):
        self._gaze_start_callback =  callback
    
    def set_gaze_end_callback(self, callback):
        self._gaze_end_callback = callback
