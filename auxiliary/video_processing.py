#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

"""
This script processes the video.
"""

import subprocess
import os
import requests
import cv2
import numpy as np
import json
import shutil

def get_first_frame(video_path, output_image_path):
    if not os.path.exists(video_path):
        print(f"[ERROR] Input video not found at: {video_path}")
        return False

    print(f"[INFO] Extracting first frame from '{video_path}'...")
    
    command = [
        'ffmpeg',
        '-i', video_path,       
        '-vframes', '1',       
        '-q:v', '2',          
        '-y',                
        output_image_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] Frame saved successfully to: {output_image_path}")
        return True
    except FileNotFoundError:
        print("[ERROR] ffmpeg is not installed or not in your PATH.")
        return False
    except subprocess.CalledProcessError as e:
        print("[ERROR] Error during frame extraction:")
        print("Return Code:", e.returncode)
        print("Output:", e.stderr)
        return False


def download_video(url, output_path):
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        print("[SUCCESS] Video downloaded successfully.")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to download video: {e}")
        return False


def reverse_video_from_path(video_path, output_dir):
    command = [
        'ffmpeg',
        '-i', video_path,
        '-vf', 'reverse',
        '-an',
        '-y',
        output_dir
    ]
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] FFmpeg command successful! Reversed video saved as: {output_dir}")
        
    except FileNotFoundError:
        print("[ERROR] ffmpeg is not installed or not in your PATH.")
        
    except subprocess.CalledProcessError as e:
        print("[ERROR] Error during FFmpeg execution:")
        print("Return Code:", e.returncode)
        print("Output:", e.stderr)


def concatenate_videos_ffmpeg(video_list, output_path, temp_list_file="mylist.txt"):
    with open(temp_list_file, 'w') as f:
        for video in video_list:
            f.write(f"file '{os.path.abspath(video)}'\n")

    print(f"[INFO] Created temporary list file: {temp_list_file}")

    command = [
        'ffmpeg',
        '-f', 'concat',     
        '-safe', '0',        
        '-i', temp_list_file,
        '-c', 'copy',       
        '-y',              
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] Concatenation successful! Video saved as: {output_path}")
        
    except FileNotFoundError:
        print("[ERROR] ffmpeg is not installed or not in your PATH.")
        
    except subprocess.CalledProcessError as e:
        print("[ERROR] Error during FFmpeg execution:")
        print(e.stderr)
        
    finally:
        if os.path.exists(temp_list_file):
            os.remove(temp_list_file)
            print(f"[INFO] Removed temporary list file: {temp_list_file}")


def add_vignette(input_video: str, output_video: str, vignette_png: str):
    for f in [input_video, vignette_png]:
        if not os.path.exists(f):
            raise FileNotFoundError(f"Input file not found: {f}")

    print(f"Probing video dimensions for: {input_video}")
    ffprobe_cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        input_video
    ]
    
    try:
        result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
        video_info = json.loads(result.stdout)
        
        if "streams" not in video_info or not video_info["streams"]:
             raise ValueError("Could not parse video stream information.")
             
        dims = video_info["streams"][0]
        width = dims['width']
        height = dims['height']
        print(f"Detected video dimensions: {width}x{height}")

    except subprocess.CalledProcessError as e:
        raise FFmpegError(f"ffprobe failed to get video dimensions:\n{e.stderr}")
    except (json.JSONDecodeError, KeyError, IndexError):
        raise ValueError(f"Could not parse ffprobe output for video dimensions.")

    print(f"Applying vignette '{vignette_png}' to '{input_video}'...")
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", input_video,     
        "-i", vignette_png,     
        "-filter_complex", f"[1:v]scale={width}:{height}[vignette_scaled];[0:v][vignette_scaled]overlay",
        "-c:a", "copy",         
        "-y",                    
        output_video
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Successfully created vignetted video at: {output_video}")
    except subprocess.CalledProcessError as e:
        raise FFmpegError(f"ffmpeg command failed.\n"
                          f"Command: {' '.join(e.cmd)}\n"
                          f"ffmpeg stderr:\n{e.stderr}")


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
        print("[ERROR] One or more input files for morphing not found.")
        return False
    
    os.makedirs(aligned_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        print("[INFO] Aligning background-removed faces...")
        align_command = [
            "python", align_script_path,
            "-images", images_path,
            "-target", video_frame_rembg_path,
            "-overlay",
            "-outdir", aligned_dir
        ]
        subprocess.run(align_command, check=True, capture_output=True, text=True)
        print("[SUCCESS] Face alignment completed.")
    except FileNotFoundError:
        print(f"[ERROR] Alignment script not found at '{align_script_path}'. Please check the path.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Face alignment failed: {e.stderr}")
        return False
        
    base_capture_name = os.path.basename(capture_rembg_path)
    base_frame_name = os.path.basename(video_frame_rembg_path)

    aligned_capture_name = base_capture_name
    aligned_frame_name = base_frame_name

    aligned_capture_path = os.path.join(aligned_dir, aligned_capture_name)
    aligned_frame_path = os.path.join(aligned_dir, aligned_frame_name)
    
    print(f"[DEBUG] Checking for aligned files: {aligned_capture_path}, {aligned_frame_path}")
    
    if not all(os.path.exists(p) for p in [aligned_capture_path, aligned_frame_path]):
        print("[ERROR] Aligned images were not created by the script with the expected names.")
        # Add a helpful debug print
        if os.path.exists(aligned_dir):
            print(f"[DEBUG] Contents of '{aligned_dir}': {os.listdir(aligned_dir)}")
        return False

    target_frame = cv2.imread(video_frame_rembg_path)
    target_h, target_w = target_frame.shape[:2]
    print(f"[INFO] Target resolution for morph is {target_w}x{target_h}.")

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
        print("[INFO] Generating final morphing video...")
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
        print(f"[SUCCESS] Morphing video created: {output_video_path}")
    except FileNotFoundError:
        print(f"[ERROR] Morphing script not found at '{morph_script_path}'. Please check the path.")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Final morphing process failed: {e.stderr}")
        return False

    return True
