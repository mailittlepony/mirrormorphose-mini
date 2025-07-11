#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

import cv2
from face_recognition import LightweightFaceDetector

MODEL_PATH = "models/eye_direction_model.tflite"
FACE_CASCADE_PATH = 'models/haarcascade_frontalface_default.xml'
EYE_CASCADE_PATH = 'models/haarcascade_eye_tree_eyeglasses.xml'
CAMERA_INDEX = 0

def on_gaze_start(): print("CALLBACK: Gaze has started!")
def on_gaze_end(): print("CALLBACK: Gaze has ended!")

try:
    detector = LightweightFaceDetector(MODEL_PATH, FACE_CASCADE_PATH, EYE_CASCADE_PATH)
    detector.set_gaze_start_callback(on_gaze_start)
    detector.set_gaze_end_callback(on_gaze_end)
except IOError as e:
    print(e)
    print("Please ensure haarcascade files are in the same directory.")
    exit()

cap = cv2.VideoCapture(CAMERA_INDEX)
if not cap.isOpened():
    print(f"Error: Could not open camera {CAMERA_INDEX}")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 15) # Request a lower FPS for stability

while True:
    ret, frame = cap.read()
    if not ret:
        break

    detector.process_frame(frame)

    # --- Visualization ---
    if detector.tracking_bbox is not None:
        x, y, w, h = detector.tracking_bbox
        color = (0, 255, 0) if not detector._gaze_active else (255, 0, 0)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        
        gaze_status = "ACTIVE" if detector._gaze_active else "INACTIVE"
        pred_text = f"Prediction: {detector.last_known_prediction}"
        status_text = f"Gaze: {gaze_status}"
        cv2.putText(frame, pred_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(frame, status_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cv2.imshow('Lightweight Gaze Detector', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

detector.release()
cap.release()
cv2.destroyAllWindows()
