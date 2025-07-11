#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

"""
This script processes the video.
"""

import os
import logging
import cv2
import numpy as np
from pathlib import Path
import subprocess

logging.basicConfig(level=logging.INFO)
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

def concatenate_videos_ffmpeg(video_paths: list, output_path: str) -> bool:
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


def generate_morph_specialized(
    images_path,
    capture_rembg_path, 
    video_frame_rembg_path, 
    output_video_path,
    align_script_path, 
    morph_script_path, 
    aligned_dir, 
    temp_dir, 
    transition_dur, 
    pause_dur, 
    fps
):
    """
    Generates a morph video with custom cropping, resizing, and alignment.
    This version is corrected to handle the external script's behavior.
    """
    if not all(os.path.exists(p) for p in [capture_rembg_path, video_frame_rembg_path]):
        logging.error("One or more input files for morphing not found.")
        return False
    
    os.makedirs(aligned_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        logging.info("Aligning background-removed faces...")
        align_command = [
            "python", align_script_path,
            "-images", images_path,
            "-target", video_frame_rembg_path,
            "-overlay",
            "-outdir", aligned_dir
        ]
        subprocess.run(align_command, check=True, capture_output=True, text=True)
        logging.info("Face alignment completed.")
    except FileNotFoundError:
        logging.error(f"Alignment script not found at '{align_script_path}'. Please check the path.")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Face alignment failed: {e.stderr}")
        return False
        
    base_capture_name = os.path.basename(capture_rembg_path)
    base_frame_name = os.path.basename(video_frame_rembg_path)

    aligned_capture_name = base_capture_name
    aligned_frame_name = base_frame_name

    aligned_capture_path = os.path.join(aligned_dir, aligned_capture_name)
    aligned_frame_path = os.path.join(aligned_dir, aligned_frame_name)
    
    logging.debug(f"Checking for aligned files: {aligned_capture_path}, {aligned_frame_path}")
    
    if not all(os.path.exists(p) for p in [aligned_capture_path, aligned_frame_path]):
        logging.error("Aligned images were not created by the script with the expected names.")
        if os.path.exists(aligned_dir):
            logging.debug(f"Contents of '{aligned_dir}': {os.listdir(aligned_dir)}")
        return False

    target_frame = cv2.imread(video_frame_rembg_path)
    target_h, target_w = target_frame.shape[:2]
    logging.info(f"Target resolution for morph is {target_w}x{target_h}.")

    aligned_capture_img = cv2.imread(aligned_capture_path)
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    ac_h, ac_w = aligned_capture_img.shape[:2]
    paste_x = (target_w - ac_w) // 2
    paste_y = (target_h - ac_h) // 2
    src_x_start = max(0, -paste_x)
    src_y_start = max(0, -paste_y)
    dst_x_start = max(0, paste_x)
    dst_y_start = max(0, paste_y)
    paste_w = min(ac_w - src_x_start, target_w - dst_x_start)
    paste_h = min(ac_h - src_y_start, target_h - dst_y_start)
    canvas[dst_y_start:dst_y_start+paste_h, dst_x_start:dst_x_start+paste_w] = \
        aligned_capture_img[src_y_start:src_y_start+paste_h, src_x_start:src_x_start+paste_w]
    final_capture_path = os.path.join(temp_dir, "morph_input_1.jpg")
    cv2.imwrite(final_capture_path, canvas)

    aligned_frame_img = cv2.imread(aligned_frame_path)
    resized_frame_img = cv2.resize(aligned_frame_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    final_frame_path = os.path.join(temp_dir, "morph_input_2.jpg")
    cv2.imwrite(final_frame_path, resized_frame_img)
    
    final_morph_input_dir = os.path.join(temp_dir, "final_morph_inputs")
    os.makedirs(final_morph_input_dir, exist_ok=True)
    for f in os.listdir(final_morph_input_dir):
        os.remove(os.path.join(final_morph_input_dir, f))
    os.rename(final_capture_path, os.path.join(final_morph_input_dir, "01_capture.jpg"))
    os.rename(final_frame_path, os.path.join(final_morph_input_dir, "02_frame.jpg"))
    
    try:
        logging.info("Generating final morphing video...")
        morph_command = [
            "python", morph_script_path,
            "-morph",
            "-images", final_morph_input_dir, 
            "-td", str(transition_dur),
            "-pd", str(pause_dur),
            "-fps", str(fps),
            "-out", output_video_path
        ]
        subprocess.run(morph_command, check=True, capture_output=True, text=True)
        logging.info(f"Morphing video created: {output_video_path}")
    except FileNotFoundError:
        logging.error(f"Morphing script not found at '{morph_script_path}'. Please check the path.")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"Final morphing process failed: {e.stderr}")
        return False

    return True
