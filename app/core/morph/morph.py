#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the GPLv3 license.

import logging, cv2, shutil
from pathlib import Path

import app.config as cfg
from app.utils import image_processing, video_processing
from .face_movie_wrapper import align_faces, run_morph


logger = logging.getLogger(__name__)

def generate_morph_specialized() -> bool:
    try:
        align_input1_dir = cfg.MORPH_TMP_DIR/"align_input1"
        align_input2_dir = cfg.MORPH_TMP_DIR/"align_input2"
        align_output1_dir = cfg.MORPH_TMP_DIR/"align_output1"
        morph_input_dir = cfg.MORPH_TMP_DIR/"morph_input"
        cfg.MORPH_TMP_DIR.mkdir(parents=True, exist_ok=True)
        align_input1_dir.mkdir(exist_ok=True)
        align_input2_dir.mkdir(exist_ok=True)
        align_output1_dir.mkdir(exist_ok=True)
        morph_input_dir.mkdir(exist_ok=True)

        # Crop inputs
        user_capture_cropped_path = cfg.MORPH_TMP_DIR/f"{cfg.USER_CAPTURE_PATH.stem}_cropped{cfg.USER_CAPTURE_PATH.suffix}"
        user_child_cropped_path = cfg.MORPH_TMP_DIR/f"{cfg.USER_CHILD_PATH.stem}_cropped{cfg.USER_CHILD_PATH.suffix}"
        image_processing.crop_face_contour(cfg.USER_CAPTURE_PATH, user_capture_cropped_path, offset=40)
        image_processing.crop_face_contour(cfg.USER_CHILD_PATH, user_child_cropped_path, offset=40)

        # Remove background
        user_capture_rembg_path = cfg.MORPH_TMP_DIR/f"{cfg.USER_CAPTURE_PATH.stem}_rembg{cfg.USER_CAPTURE_PATH.suffix}"
        user_child_rembg_path = cfg.MORPH_TMP_DIR/f"{cfg.USER_CHILD_PATH.stem}_rembg{cfg.USER_CHILD_PATH.suffix}"
        image_processing.remove_background(user_capture_cropped_path, user_capture_rembg_path)
        image_processing.remove_background(user_child_cropped_path, user_child_rembg_path)

        # Align user child img to user current capture
        shutil.copy2(user_child_rembg_path, align_input1_dir/user_child_rembg_path.name)
        success = align_faces(
            images_dir=align_input1_dir,
            target_path=user_capture_rembg_path,
            align_script_path=cfg.FACE_MOVIE_FACE_ALIGN_SCRIPT,
            aligned_dir=align_output1_dir
        )
        if not success:
            logger.error("Child-capture alignment failed.")
            return False

        # Resize
        logger.info("Resizing and cropping aligned capture image to match user image...")
        capture_img = cv2.imread(str(user_capture_rembg_path))
        child_img = cv2.imread(str(user_child_rembg_path))

        capture_img = image_processing.resize_and_crop_to_match(capture_img, child_img)
        cv2.imwrite(str(align_input2_dir/"0.jpg"), capture_img)

        # Call runway and extract frame
        extracted_frame_path = morph_input_dir/"1.jpg"
        video_processing.extract_frame(cfg.GENERATED_VIDEO_PATH, extracted_frame_path, frame_number=0)

        # Align capture to extracted frame
        # shutil.copy2(user_capture_rembg_path, align_input2_dir/"0.jpg")
        success = align_faces(
            images_dir=align_input2_dir,
            target_path=extracted_frame_path,
            align_script_path=cfg.FACE_MOVIE_FACE_ALIGN_SCRIPT,
            aligned_dir=morph_input_dir
        )
        if not success:
            logger.error("Capture-1st runway frame alignment failed")
            return False

        return run_morph(
            cfg.FACE_MOVIE_MORPH_SCRIPT,
            morph_input_dir,
            cfg.MORPH_VIDEO_PATH,
            1.0,
            0.5,
            25
        )

    except Exception as e:
        logger.exception(f"Unexpected error during morph generation: {e}")
        return False
