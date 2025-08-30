#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from typing import Optional
import cv2, os

import app.config as cfg
from .camera import camera
from .display import display
from .morph import morph
from app.utils import video_processing
from .camera.gaze_tracker.gaze_tracker import GazeTracker

_tracker = None

def start() -> GazeTracker:
    # Check if user uploaded its child image
    if not cfg.USER_CHILD_PATH.exists():
        raise RuntimeError("User child picture was not uploaded.")

    # Take picture of the user
    frame = camera.read(preview=False)
    if frame is not None:
        cv2.imwrite(str(cfg.USER_CAPTURE_PATH), frame)
    else:
        raise RuntimeError("Could not take a picture of the user.")

    # Start gaze detection (new instance of GazeTracker)
    global _tracker
    _tracker = GazeTracker(enable_tracking=True, model_dir=str(cfg.MODEL_DIR))

    # Prepare the three video to display (morph, ai_video, reversed_ai_video)
    morph.generate_morph_specialized()

    # Reverse generated video
    reversed_video_path = cfg.TEMP_DIR/f"{cfg.GENERATED_VIDEO_PATH.stem}_reversed{cfg.GENERATED_VIDEO_PATH.suffix}"
    video_processing.reverse_video(cfg.GENERATED_VIDEO_PATH, reversed_video_path)

    # Concatenate generated video + reversed generated video
    video_processing.concatenate_videos([cfg.GENERATED_VIDEO_PATH, reversed_video_path], cfg.FINAL_GENERATED_VIDEO_PATH)

    # Load video for the display
    display.load_videos()

    return _tracker

def get_tracker() -> Optional[GazeTracker]:
    global _tracker
    return _tracker;

def stop() -> None:
    # Stop gaze detection (del GazeTracker)
    global _tracker
    del _tracker
    _tracker = None

    display.stop()

    # Delete temp
    # os.rmdir(cfg.TEMP_DIR)

