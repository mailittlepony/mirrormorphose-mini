#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the GPLv3 license.

import cv2

import app.config as cfg

import threading
import cv2

full_cap = None
preview_cap = None

_last_full_frame = None
_last_preview_frame = None

# Locks for thread safety
_full_lock = threading.Lock()
_preview_lock = threading.Lock()


def init() -> None:
    global full_cap, preview_cap

    # Full
    full_cap = cv2.VideoCapture(cfg.VIDEO_DEVICE_FULL, cv2.CAP_V4L2)
    full_cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.CAMERA_FULL_WIDTH)
    full_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.CAMERA_FULL_HEIGHT)
    full_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cfg.CAMERA_FULL_FORMAT))

    # Preview
    preview_cap = cv2.VideoCapture(cfg.VIDEO_DEVICE_PREVIEW, cv2.CAP_V4L2)
    preview_cap.set(cv2.CAP_PROP_FRAME_WIDTH, cfg.CAMERA_PREVIEW_WIDTH)
    preview_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cfg.CAMERA_PREVIEW_HEIGHT)
    preview_cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*cfg.CAMERA_PREVIEW_FORMAT))

    if not preview_cap.isOpened() or not full_cap.isOpened():
        raise Exception("could not open video devices")


def free() -> None:
    global full_cap, preview_cap

    with _full_lock:
        if full_cap:
            full_cap.release()
            full_cap = None

    with _preview_lock:
        if preview_cap:
            preview_cap.release()
            preview_cap = None


def read(preview=False):
    """Return the last captured frame (thread-safe)."""
    if preview:
        with _preview_lock:
            return _last_preview_frame.copy() if _last_preview_frame is not None else None
    else:
        with _full_lock:
            return _last_full_frame.copy() if _last_full_frame is not None else None


def capture(preview=False):
    """Grab a new frame from the camera and update the last frame."""
    global _last_full_frame, _last_preview_frame

    if preview:
        with _preview_lock:
            if preview_cap is None or not preview_cap.isOpened():
                return False, None
            ret, frame = preview_cap.read()
            if ret:
                _last_preview_frame = frame.copy()
            return ret, frame
    else:
        with _full_lock:
            if full_cap is None or not full_cap.isOpened():
                return False, None
            ret, frame = full_cap.read()
            if ret:
                _last_full_frame = frame.copy()
            return ret, frame

