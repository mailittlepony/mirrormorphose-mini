#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import logging
from PIL import Image
import os
from pathlib import Path
from typing import List
import cv2

from utils import image_processing, video_processing
from utils.tracking import crop_face
from config import TEMP_REMBG_DIR

logger = logging.getLogger(__name__)

def remove_background_for_images(image_paths: List[str]) -> bool:
    os.makedirs(TEMP_REMBG_DIR, exist_ok=True)
    all_success = True
    for image_path in image_paths:
        filename, ext = os.path.splitext(os.path.basename(image_path))
        output_path = TEMP_REMBG_DIR / f"{filename}_rembg{ext}"
        success = image_processing.remove_background(image_path, str(output_path))
        if not success:
            logger.error(f"Failed to remove background from {image_path}")
            all_success = False
    return all_success


def call_runway(img_path: str) -> bool:
    from api.runway import runway_generate_video
    from config import TEMP_DIR, TEMP_REMBG_DIR

    with open(img_path, 'rb') as img_file:
        video_url = runway_generate_video(img_file.read())

    video_path = TEMP_DIR / "video_generated.mp4"
    frame_output = TEMP_REMBG_DIR / "video_frame_rembg.jpg"

    if not video_processing.download_video(video_url, str(video_path)):
        logger.error("Failed to download video from runway.")
        return False

    if not video_processing.get_first_frame(str(video_path), str(frame_output)):
        logger.error("Failed to extract first frame from generated video.")
        return False

    return True


def crop_faces(images_dir: Path, temp_dir: Path) -> tuple[Path, Path] | None:
    capture_path = images_dir / "capture.jpg"
    user_image_path = images_dir / "user_image.jpg"

    logger.info(f"Capture input: {capture_path} exists: {capture_path.exists()}")
    logger.info(f"User image input: {user_image_path} exists: {user_image_path.exists()}")

    capture_cropped = crop_face(str(capture_path))
    user_cropped = crop_face(str(user_image_path))

    if capture_cropped is None or user_cropped is None:
        logger.error("Face detection failed on one of the images.")
        return None

    cropped_capture_path = temp_dir / "capture_cropped.jpg"
    cropped_user_path = temp_dir / "user_image_cropped.jpg"

    cv2.imwrite(str(cropped_capture_path), capture_cropped)
    cv2.imwrite(str(cropped_user_path), user_cropped)
    logger.info("Faces cropped successfully.")

    return cropped_capture_path, cropped_user_path




def resize_and_crop_to_match(source_img: Image.Image, target_img: Image.Image) -> Image.Image:
    """
    Resize and crop source_img to match target_img's size,
    assuming the face is centered and must stay centered after scaling.

    Parameters:
        source_img (PIL.Image.Image): Image to scale and crop.
        target_img (PIL.Image.Image): Reference image with desired size and alignment.

    Returns:
        PIL.Image.Image: Resized and cropped source image.
    """
    src_w, src_h = source_img.size
    tgt_w, tgt_h = target_img.size

    # Scale up to fill the target completely (no padding)
    scale = max(tgt_w / src_w, tgt_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    resized = source_img.resize((new_w, new_h), Image.LANCZOS)

    # Use center point of the original image as anchor
    face_x = src_w / 2
    face_y = src_h / 2

    # Map to new scaled image
    face_x_scaled = face_x * scale
    face_y_scaled = face_y * scale

    # Crop to keep face at same location
    crop_x = int(face_x_scaled - tgt_w / 2)
    crop_y = int(face_y_scaled - tgt_h / 2)

    # Ensure crop stays within bounds
    crop_x = max(0, min(crop_x, new_w - tgt_w))
    crop_y = max(0, min(crop_y, new_h - tgt_h))

    cropped = resized.crop((crop_x, crop_y, crop_x + tgt_w, crop_y + tgt_h))
    return cropped

