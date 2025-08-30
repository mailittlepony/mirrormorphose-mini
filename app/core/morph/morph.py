#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the GPLv3 license.

import logging, cv2
from pathlib import Path

from app.config import TEMP_DIR, TEMP_REMBG_DIR, FACE_MOVIE_FACE_ALIGN_SCRIPT, FACE_MOVIE_MORPH_SCRIPT
from app.core.utils.image_processing import crop_face_contour, remove_background
from .face_movie_wrapper import align_faces, run_morph

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

        for directory in [processed_dir, TEMP_REMBG_DIR, aligned_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        result = crop_faces(TEMP_DIR, processed_dir)
        if result is None:
            logger.error("Face cropping failed.")
            return False
        cropped_capture_path, cropped_user_path = result

        success = remove_background([
            cropped_capture_path,
            cropped_user_path
        ], TEMP_REMBG_DIR)
        if not success:
            logger.error("Background removal failed.")
            return False

        success = align_faces(
            images_dir=capture_rembg_path.parent,
            target_path=capture_rembg_path,
            align_script_path=FACE_MOVIE_FACE_ALIGN_SCRIPT,
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
        capture_img = cv2.imread(str(aligned_capture_path))
        user_img = cv2.imread(str(aligned_user_path))

        resized_capture = resize_and_crop_to_match(capture_img, user_img)
        resized_capture.save(aligned_capture_path)

        success = align_faces(
            images_dir=aligned_dir,
            target_path=aligned_user_path,
            align_script_path=FACE_MOVIE_FACE_ALIGN_SCRIPT,
            aligned_dir=aligned_dir
        )

        if not success:
            logger.error("Second face alignment failed after resizing.")
            return False
        else:
            logger.info("Second face alignment succeeded.")

        return run_morph(
            FACE_MOVIE_MORPH_SCRIPT,
            aligned_dir,
            output_video_path,
            transition_dur,
            pause_dur,
            fps
        )

    except Exception as e:
        logger.exception(f"Unexpected error during morph generation: {e}")
        return False

def crop_faces(images_dir: Path, temp_dir: Path) -> tuple[Path, Path] | None:
    capture_path = images_dir / "capture.jpg"
    user_image_path = images_dir / "user_image.jpg"

    logger.info(f"Capture input: {capture_path} exists: {capture_path.exists()}")
    logger.info(f"User image input: {user_image_path} exists: {user_image_path.exists()}")

    capture_cropped = crop_face_contour(str(capture_path), None)
    user_cropped = crop_face_contour(str(user_image_path), None)

    if capture_cropped is None or user_cropped is None:
        logger.error("Face detection failed on one of the images.")
        return None

    cropped_capture_path = temp_dir / "capture_cropped.jpg"
    cropped_user_path = temp_dir / "user_image_cropped.jpg"

    cv2.imwrite(str(cropped_capture_path), capture_cropped)
    cv2.imwrite(str(cropped_user_path), user_cropped)
    logger.info("Faces cropped successfully.")

    return cropped_capture_path, cropped_user_path
