#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import logging
from os import remove
from PIL import Image
from config import (
    TEMP_DIR,
    TEMP_REMBG_DIR,
    FACE_ALIGN_SCRIPT,
    MORPH_SCRIPT,
)
from morph import align_faces, run_morph
from pipeline.preprocess import call_runway, remove_background_for_images, crop_faces, resize_and_crop_to_match
from pipeline.postprocess import extract_first_frame

logger = logging.getLogger(__name__)

def generate_morph_specialized(
    runway: bool = True,
    transition_dur: float = 1.5,
    pause_dur: float = 1.0,
    fps: int = 25
) -> bool:
    try:
        processed_dir = TEMP_DIR / "morph_temp_processed"
        aligned_dir = TEMP_DIR / "aligned_faces"
        output_video_path = TEMP_DIR / "morph_video.mp4"

        capture_rembg_path = TEMP_REMBG_DIR / "capture_cropped_rembg.jpg"
        user_rembg_path = TEMP_REMBG_DIR / "user_image_cropped_rembg.jpg"

        for directory in [processed_dir, TEMP_REMBG_DIR, aligned_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        result = crop_faces(TEMP_DIR, processed_dir)
        if result is None:
            logger.error("Face cropping failed.")
            return False
        cropped_capture_path, cropped_user_path = result

        success = remove_background_for_images([
            str(cropped_capture_path),
            str(cropped_user_path)
        ])
        if not success:
            logger.error("Background removal failed.")
            return False

        success = align_faces(
            images_dir=capture_rembg_path.parent,
            target_path=capture_rembg_path,
            align_script_path=FACE_ALIGN_SCRIPT,
            aligned_dir=aligned_dir
        )
        if not success:
            logger.error("Face alignment failed.")
            return False

        aligned_capture_path = aligned_dir / "capture_cropped_rembg.jpg"
        aligned_user_path = aligned_dir / "user_image_cropped_rembg.jpg"

        if runway:
            logger.info("Calling Runway API...")
            if not call_runway(str(aligned_user_path)):
                logger.error("Runway API call failed.")
                return False
            video_input_path = TEMP_DIR / "video_generated.mp4"
        else:
            logger.info("Skipping Runway. Using local video: video_generated.mp4")
            video_input_path = TEMP_DIR / "video_generated.mp4"

        if not extract_first_frame(video_input_path, str(aligned_user_path)):
            logger.error("Failed to extract first frame.")
            return False

        logger.info("Resizing and cropping aligned capture image to match user image...")
        capture_img = Image.open(aligned_capture_path)
        user_img = Image.open(aligned_user_path)

        resized_capture = resize_and_crop_to_match(capture_img, user_img)
        resized_capture.save(aligned_capture_path)

        success = align_faces(
            images_dir=aligned_dir,
            target_path=aligned_user_path,
            align_script_path=FACE_ALIGN_SCRIPT,
            aligned_dir=aligned_dir
        )

        if not success:
            logger.error("Second face alignment failed after resizing.")
            return False
        else:
            logger.info("Second face alignment succeeded.")

        return run_morph(
            MORPH_SCRIPT,
            aligned_dir,
            output_video_path,
            transition_dur,
            pause_dur,
            fps
        )

    except Exception as e:
        logger.exception(f"Unexpected error during morph generation: {e}")
        return False

