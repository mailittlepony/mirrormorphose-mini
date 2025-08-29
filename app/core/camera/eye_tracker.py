#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the MIT license.

import threading

import app.config as cfg

from .gaze_tracker.gaze_tracker import GazeTracker
from .camera import camera_capture

MOUTH_LMK = [
    78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 191, 80, 81, 82, 13
]

eye_tracker_running = False
_eye_tracker_pid = None

def eye_tracker_init() -> None:
    global tracker
    tracker = GazeTracker(enable_tracking=True, model_dir=str(cfg.MODEL_DIR))

def eye_tracker_start() -> None:
    global _eye_tracker_pid, eye_tracker_running

    if not tracker:
        return

    if _eye_tracker_pid and _eye_tracker_pid.is_alive():
        print("[INFO] Eye tracker already running.")
        return

    eye_tracker_running = True

    def worker():
        try:
            while True:
                ret, frame = camera_capture()
                if not ret:
                    break

                state = tracker.get_eye_state(frame)
                print("Eye state:", state)

                frame = tracker.draw_bbox(frame, state)
        except Exception as e:
            print(f"[ERROR] {e}")

    _eye_tracker_pid = threading.Thread(target=worker, daemon=True)
    _eye_tracker_pid.start()

def eye_tracker_stop() -> None:
    """Signal the worker thread to stop gracefully."""
    global eye_tracker_running
    if eye_tracker_running:
        eye_tracker_running = False
        print("[INFO] Eye tracker stopping...")
    else:
        print("[INFO] Eye tracker is not running.")

def eye_tracker_free() -> None:
    global _eye_tracker_pid, eye_tracker_running, tracker
    eye_tracker_running = False
    _eye_tracker_pid = None
    del tracker
    print("[INFO] Eye tracker resources freed.")
