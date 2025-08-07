#! /usr/bin/env python3
# vim:fenc=utf-8
#
# copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# distributed under terms of the mit license.

import cv2
import logging
from config import FACE_CASCADE_PATH

logger = logging.getLogger(__name__)


class TrackerManager:
    def __init__(self, detection_interval=10):
        self._tracker = None
        self._bbox = None
        self._frame_counter = 0
        self._detection_interval = detection_interval
    
    @property
    def bbox(self):
        return self._bbox

    def has_valid_bbox(self):
        return self._bbox is not None

    def should_detect(self):
        return self._frame_counter % self._detection_interval == 0

    def start_tracking(self, frame, bbox):
        self._tracker = cv2.legacy.TrackerKCF_create()
        self._tracker.init(frame, bbox)
        self._bbox = bbox

    def update(self, frame):
        if self._tracker is None:
            return None

        success, bbox = self._tracker.update(frame)
        if success:
            self._bbox = tuple(map(int, bbox))
            return self._bbox

        self._tracker = None
        self._bbox = None
        return None

    def increment_frame(self):
        self._frame_counter += 1

    def reset(self):
        self._tracker = None
        self._bbox = None
        self._frame_counter = 0


def crop_face(image_path: str, margin_ratio: float = 0.4, raise_top_ratio: float = 0.3):
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to read image: {image_path}")
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(str(FACE_CASCADE_PATH))

    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    if len(faces) == 0:
        logger.warning(f"No faces detected in image: {image_path}")
        return None

    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])

    margin_w = int(w * margin_ratio)
    margin_h = int(h * margin_ratio)
    extra_top = int(h * raise_top_ratio)

    x1 = x - margin_w
    y1 = y - extra_top
    x2 = x + w + margin_w
    y2 = y + h + margin_h

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(image.shape[1], x2)
    y2 = min(image.shape[0], y2)

    box_w = x2 - x1
    box_h = y2 - y1

    if box_w > box_h:
        diff = box_w - box_h
        y1 = max(0, y1 - diff // 2)
        y2 = min(image.shape[0], y2 + diff - diff // 2)
    else:
        diff = box_h - box_w
        x1 = max(0, x1 - diff // 2)
        x2 = min(image.shape[1], x2 + diff - diff // 2)

    cropped = image[y1:y2, x1:x2]
    return cropped
