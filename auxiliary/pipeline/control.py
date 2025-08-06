#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import logging
from pathlib import Path

from config import TEMP_DIR, TEMP_REMBG_DIR
from pipeline.fetch import fetch_assets, send_video, preload_videos
from pipeline.morph_wrapper import generate_morph_specialized
from pipeline.postprocess import (
    add_vignette_video,
    reverse_video,
    concatenate_videos
)
from pipeline.monitor import monitor_gaze_stream

logger = logging.getLogger(__name__)


def run_full_pipeline(runway: bool = True) -> None:
    if not fetch_assets():
        logger.error("Failed to fetch assets.")
        return

    if not generate_morph_specialized():
        logger.error("Morph generation failed.")
        return

    if not add_vignette_video(
        str(TEMP_DIR / "morph_video.mp4"),
        str(TEMP_DIR / "final_morph_video.mp4")
    ):
        logger.error("Vignette addition failed for morph video.")
        return

    if not send_video(str(TEMP_DIR / "morph_video.mp4")):
        logger.warning("Morph video not sent.")
        return

    if not reverse_video(str(TEMP_DIR / "video_generated.mp4")):
        logger.error("Video could not be reversed.")
        return

    if not concatenate_videos([
        str(TEMP_DIR / "video_generated.mp4"),
        str(TEMP_DIR / "reversed_video.mp4")
    ]):
        logger.error("Videos could not be concatenated.")
        return

    if not add_vignette_video(
        str(TEMP_DIR / "concatenated_video.mp4"),
        str(TEMP_DIR / "final_concatenated_video.mp4")
    ):
        logger.error("Vignette addition failed for concatenated video.")
        return

    if not send_video(str(TEMP_DIR / "concatenated_video.mp4")):
        logger.warning("Concatenated video not sent.")
        return
    
    if not preload_videos():
        logger.error("Preloading failed.")
        return

    if not monitor_gaze_stream():
        logger.error("Streaming failed.")
        return

    logger.info("Pipeline completed successfully.")
