#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def extract_eye_data(frame, face_bbox, eye_cascade, input_shape):
    fx, fy, fw, fh = face_bbox
    face_color = frame[fy:fy+fh, fx:fx+fw]
    face_gray = cv2.cvtColor(face_color, cv2.COLOR_BGR2GRAY)
    eyes = eye_cascade.detectMultiScale(face_gray, 1.1, 3)

    if len(eyes) < 2:
        return None

    eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
    eyes = sorted(eyes, key=lambda e: e[0])

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

    left_eye = cv2.resize(eye_imgs_color[0], input_shape)
    right_eye = cv2.resize(eye_imgs_color[1], input_shape)
    combined = np.hstack((left_eye, right_eye))
    model_input = cv2.resize(combined, input_shape)

    return {
        "model_input": model_input,
        "left_eye_gray": eye_imgs_gray[0],
        "right_eye_gray": eye_imgs_gray[1],
    }


def estimate_gaze_direction(eye_gray):
    if eye_gray is None or eye_gray.size == 0:
        return False

    eye_gray = cv2.equalizeHist(eye_gray)
    _, threshold = cv2.threshold(eye_gray, 45, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return False

    largest = max(contours, key=cv2.contourArea)
    M = cv2.moments(largest)

    if M['m00'] == 0:
        return False

    cx = int(M['m10'] / M['m00'])
    eye_width = eye_gray.shape[1]
    ratio = cx / eye_width

    return 0.4 <= ratio <= 0.6

