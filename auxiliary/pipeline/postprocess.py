#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import logging
from pathlib import Path
from typing import List

from config import TEMP_DIR, VIGNETTE_PATH
import utils.video_processing as video_processing

logger = logging.getLogger(__name__)

def reverse_video(video_path: str) -> bool:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TEMP_DIR / "reversed_video.mp4"
    try:
        video_processing.reverse_video_from_path(str(video_path), str(output_path))
        return True
    except Exception as e:
        logger.error(f"Failed to reverse video: {e}")
        return False

def concatenate_videos(videos_list: List[str]) -> bool:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if not all(Path(v).exists() for v in videos_list):
        logger.error("One or more videos for concatenation do not exist.")
        return False
    output_path = TEMP_DIR / "concatenated_video.mp4"
    try:
        video_processing.concatenate_videos_ffmpeg(videos_list, str(output_path))
        return True
    except Exception as e:
        logger.error(f"Failed to concatenate videos: {e}")
        return False

def add_vignette_video(video_path: str, output_path: str) -> bool:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        video_processing.add_vignette(video_path, output_path, str(VIGNETTE_PATH))
        Path(video_path).unlink(missing_ok=True)
        Path(output_path).rename(video_path)
        logger.info(f"Vignette added and original video replaced: {video_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to add vignette or replace video: {e}")
        return False

def extract_first_frame(video_path: str, output_image_path: str) -> bool:
    import cv2
    video_path = Path(video_path)
    output_image_path = Path(output_image_path)

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        return False

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"Failed to open video: {video_path}")
        return False

    success, frame = cap.read()
    cap.release()

    if not success:
        logger.error(f"Failed to read first frame from: {video_path}")
        return False

    output_image_path.parent.mkdir(parents=True, exist_ok=True)

    if not cv2.imwrite(str(output_image_path), frame):
        logger.error(f"Failed to save frame to: {output_image_path}")
        return False

    logger.info(f"First frame saved to: {output_image_path}")
    return True
