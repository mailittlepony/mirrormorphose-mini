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
    def __init__(self, model_path, _input_shape=(64, 64), camera_index=0, threshold_time):
        self._input_shape = _input_shape
        self._class_labels = ['forward_look', 'close_look', 'left_look', 'right_look']

        self._interpreter = self._load_model(model_path)
        self._input_details = self._interpreter.get_input_details()
        self._output_details = self._interpreter.get_output_details()

        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(refine_landmarks=True)

        self._lookaway_start = None
        self._gaze_active = False
        self.threshold_time = 1.5            
        self.lookaway_grace_period = 0.5
        self._start_stare = None

        self._gaze_start_callback = None
        self._gaze_end_callback = None

        self._LEFT_EYE = [33, 133]
        self._RIGHT_EYE = [362, 263]

        self._tracker = None
        self._tracking_bbox = None

        self._closest_face_id = None
        self._closest_face_history = []  
        self._history_length = 5  

    def _load_model(self, path):
        _interpreter = Interpreter(model_path=path)
        _interpreter.allocate_tensors()
        return _interpreter

    def _get_face_bboxes_and_depths(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return []

        faces = []
        h, w, _ = frame.shape

        for face_landmarks in results.multi_face_landmarks:
            x_coords = [lm.x * w for lm in face_landmarks.landmark]
            y_coords = [lm.y * h for lm in face_landmarks.landmark]
            z_coords = [lm.z for lm in face_landmarks.landmark]

            x_min, x_max = int(min(x_coords)), int(max(x_coords))
            y_min, y_max = int(min(y_coords)), int(max(y_coords))
            bbox = (x_min, y_min, x_max - x_min, y_max - y_min)

            avg_z = sum(z_coords) / len(z_coords)

            faces.append({
                "landmarks": face_landmarks,
                "bbox": bbox,
                "avg_z": avg_z
            })
        return faces

    def _select_closest_face(self, faces):
        if not faces:
            return None
        closest_idx = 0
        min_z = faces[0]["avg_z"]
        for i, face in enumerate(faces[1:], start=1):
            if face["avg_z"] < min_z:
                min_z = face["avg_z"]
                closest_idx = i
        return closest_idx

    def _update_closest_face_history(self, face_id):
        self._closest_face_history.append(face_id)
        if len(self._closest_face_history) > self._history_length:
            self._closest_face_history.pop(0)

        if len(set(self._closest_face_history)) == 1:
            return self._closest_face_history[-1] 
        return None  

    def _init_tracker(self, frame, bbox):
        self._tracker = cv2.TrackerCSRT_create()
        self._tracker.init(frame, bbox)
        self._tracking_bbox = bbox

    def _update_tracker(self, frame):
        if self._tracker is None:
            return None
        success, bbox = self._tracker.update(frame)
        if success:
            self._tracking_bbox = tuple(map(int, bbox))
            return self._tracking_bbox
        else:
            self._tracker = None
            self._tracking_bbox = None
            return None

    def _get_eye_images_from_landmarks(self, frame, landmarks):
        eye_imgs = []
        h, w, _ = frame.shape

        for eye_indices in [self._LEFT_EYE, self._RIGHT_EYE]:
            eye_coords = []
            for idx in eye_indices:
                x = int(landmarks.landmark[idx].x * w)
                y = int(landmarks.landmark[idx].y * h)
                eye_coords.append((x, y))

            x_min = max(min(p[0] for p in eye_coords) - 5, 0)
            x_max = min(max(p[0] for p in eye_coords) + 5, w)
            y_min = max(min(p[1] for p in eye_coords) - 5, 0)
            y_max = min(max(p[1] for p in eye_coords) + 5, h)

            eye_img = frame[y_min:y_max, x_min:x_max]
            if eye_img.size > 0:
                eye_img_resized = cv2.resize(eye_img, self._input_shape)
                eye_imgs.append(eye_img_resized)
        return eye_imgs

    def _predict(self, eye_img):
        input_data = np.expand_dims(eye_img.astype(np.float32) / 255.0, axis=0)
        self._interpreter.set_tensor(self._input_details[0]['index'], input_data)
        self._interpreter.invoke()
        output_data = self._interpreter.get_tensor(self._output_details[0]['index'])
        return self._class_labels[np.argmax(output_data[0])]

    def process_frame(self, frame):
        current_time = time.time()

        if self._tracker is None:
            faces = self._get_face_bboxes_and_depths(frame)
            if not faces:
                self._closest_face_history.clear()
                self._start_stare = None
                self._lookaway_start = None
                if self._gaze_active:
                    self._gaze_active = False
                    if self._gaze_end_callback:
                        self._gaze_end_callback()
                return

            closest_idx = self._select_closest_face(faces)
            stable_face_id = self._update_closest_face_history(closest_idx)

            if stable_face_id is not None:
                face = faces[stable_face_id]
                self._init_tracker(frame, face["bbox"])
                self._closest_face_id = stable_face_id
                landmarks = face["landmarks"]
            else:
                self._start_stare = None
                self._lookaway_start = None
                return
        else:
            bbox = self._update_tracker(frame)
            if bbox is None:
                self._tracker = None
                self._tracking_bbox = None
                self._closest_face_history.clear()
                self._start_stare = None
                self._lookaway_start = None
                if self._gaze_active:
                    self._gaze_active = False
                    if self._gaze_end_callback:
                        self._gaze_end_callback()
                return
            faces = self._get_face_bboxes_and_depths(frame)
            landmarks = None
            min_dist = float('inf')
            x, y, w_box, h_box = bbox
            center = (x + w_box / 2, y + h_box / 2)
            for face in faces:
                fx, fy, fw, fh = face["bbox"]
                fcenter = (fx + fw / 2, fy + fh / 2)
                dist = (center[0] - fcenter[0])**2 + (center[1] - fcenter[1])**2
                if dist < min_dist:
                    min_dist = dist
                    landmarks = face["landmarks"]

            if landmarks is None:
                self._start_stare = None
                self._lookaway_start = None
                return

        eye_imgs = self._get_eye_images_from_landmarks(frame, landmarks)

        if eye_imgs:
            eye_input = np.hstack(eye_imgs) if len(eye_imgs) == 2 else eye_imgs[0]
            eye_input = cv2.resize(eye_input, self._input_shape)
            prediction = self._predict(eye_input)

            if prediction == "forward_look":
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
                        self._gaze_active = False
                        self._start_stare = None
                        self._lookaway_start = None
                        if self._gaze_end_callback:
                            self._gaze_end_callback()
                else:
                    self._start_stare = None
                    self._lookaway_start = None
        else:
            if self._gaze_active:
                if self._lookaway_start is None:
                    self._lookaway_start = current_time
                elif current_time - self._lookaway_start >= self.lookaway_grace_period:
                    self._gaze_active = False
                    self._start_stare = None
                    self._lookaway_start = None
                    if self._gaze_end_callback:
                        self._gaze_end_callback()
            else:
                self._start_stare = None
                self._lookaway_start = None

    def set_gaze_start_callback(self, callback):
        self._gaze_start_callback = callback
    
    def set_gaze_end_callback(self, callback):
        self._gaze_end_callback = callback

    def release(self):
            if self._face_mesh:
                self._face_mesh.close()
                self._face_mesh = None
            self._tracker = None
            self._tracking_bbox = None
            self._closest_face_history.clear()
            self._closest_face_id = None
            self._gaze_start_callback = None
            self._gaze_end_callback = None
            self._input_details = None
            self._output_details = None
            self._interpreter = None
            self._input_shape = None
            self._class_labels = None
            self._start_stare = None
            self._lookaway_start = None
            self._gaze_active = False
