#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

"""
Video processing utilities including reversing, concatenation, vignette,
frame extraction, download.
"""

import os
import logging
import cv2
import numpy as np
from pathlib import Path
import subprocess
from typing import List

logger = logging.getLogger(__name__)

def reverse_video_from_path(input_video_path: str, output_video_path: str) -> bool:
    try:
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video {input_video_path}")
            return False
        
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        
        frames.reverse()
        height, width, layers = frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, 25, (width, height))

        for frame in frames:
            out.write(frame)
        out.release()

        logger.info(f"Video reversed and saved to {output_video_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to reverse video: {e}")
        return False

def concatenate_videos_ffmpeg(video_paths: List[str], output_path: str) -> bool:
    try:
        list_file = Path("concat_list.txt")
        with list_file.open("w") as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")
        
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac",
            output_path
        ]

        logger.info("Concatenating videos with ffmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        list_file.unlink(missing_ok=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg concat failed: {result.stderr}")
            return False

        logger.info(f"Videos concatenated successfully to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error concatenating videos: {e}")
        return False

def add_vignette(video_path: str, output_path: str, vignette_image_path: str) -> bool:
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video {video_path}")
            return False

        vignette = cv2.imread(vignette_image_path, cv2.IMREAD_UNCHANGED)
        if vignette is None:
            logger.error(f"Failed to load vignette image {vignette_image_path}")
            return False

        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps = cap.get(cv2.CAP_PROP_FPS)

        vignette_resized = cv2.resize(vignette, (width, height))

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            b, g, r, a = cv2.split(vignette_resized)
            alpha = a.astype(float) / 255.0
            overlay_color = cv2.merge((b, g, r))

            frame_float = frame.astype(float)
            overlay_float = overlay_color.astype(float)

            for c in range(3):
                frame_float[:, :, c] = (alpha * overlay_float[:, :, c] +
                                        (1 - alpha) * frame_float[:, :, c])

            frame = frame_float.astype(np.uint8)
            out.write(frame)

        cap.release()
        out.release()
        logger.info(f"Vignette added and saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to add vignette: {e}")
        return False

def get_first_frame(video_path: str, output_image_path: str) -> bool:
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video {video_path}")
            return False
        
        ret, frame = cap.read()
        cap.release()
        if not ret:
            logger.error("Failed to read first frame")
            return False
        
        cv2.imwrite(output_image_path, frame)
        logger.info(f"First frame extracted and saved to {output_image_path}")
        return True
    except Exception as e:
        logger.error(f"Error extracting first frame: {e}")
        return False

def download_video(url: str, output_path: str) -> bool:
    import requests
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Video downloaded from {url} to {output_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download video: {e}")
        return False

