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

import logging
import subprocess

logger = logging.getLogger(__name__)

def concatenate(video_paths: list, output_path: str) -> bool:
    try:
        if not video_paths:
            logger.error("No videos to concatenate.")
            return False

        input_args = []
        for vp in video_paths:
            input_args += ['-i', vp]

        n = len(video_paths)
        filter_complex = "".join(f"[{i}:v:0]" for i in range(n))
        filter_complex += f"concat=n={n}:v=1:a=0[outv]"

        cmd = [
            "ffmpeg", "-y",
            *input_args,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            output_path
        ]

        logger.info(f"Concatenating {n} videos with ffmpeg concat filter...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"FFmpeg concat filter failed: {result.stderr}")
            return False

        logger.info(f"Videos concatenated successfully to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Error concatenating videos: {e}")
        return False

def download(url: str, output_path: str) -> bool:
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

