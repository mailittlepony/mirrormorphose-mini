#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong
#
# Distributed under terms of the MIT license.

"""
This script can:
1. Fetch images from server (camera + video frame).
2. Generate morphing video using two images.
3. Send morphing video to the server.
"""

import sys
import os
import requests
from time import sleep
import subprocess
import image_processing

# ==== VARIABLES ====
URL = "http://192.168.11.41:8000"
TEMP_DIR = "temp"
CAPTURE_IMG = os.path.join(TEMP_DIR, "capture.jpg")
VIDEO_FRAME_IMG = os.path.join(TEMP_DIR, "video_frame.jpg")
CAPTURE_REMBG = os.path.join(TEMP_DIR, "capture_rembg.jpg")
VIDEO_FRAME_REMBG = os.path.join(TEMP_DIR, "video_frame_rembg.jpg")
ALIGNED_DIR = os.path.join(TEMP_DIR, "aligned_faces")
OUTPUT_VIDEO = os.path.join(TEMP_DIR, "output.mp4")
FACE_ALIGN_SCRIPT = "face-movie/face-movie/align.py"
MORPH_SCRIPT = "face-movie/face-movie/main.py"
TRANSITION_DUR = 2.0
PAUSE_DUR = 0.5
FPS = 25

# ==== FUNCTIONS ====

def fetch_images():
    get_video_frame_url = f"{URL}/get_video_frame_for_morph"
    get_camera_frame_url = f"{URL}/get_camera_capture"

    print("[INFO] Requesting camera image...")
    response = requests.post(get_camera_frame_url)
    if response.ok and response.headers.get("Content-Type", "").startswith("image/"):
        with open(CAPTURE_IMG, 'wb') as f:
            f.write(response.content)
        print(f"[SUCCESS] Image saved to {CAPTURE_IMG}")
    else:
        print(f"[ERROR] Failed to download camera image: {response.status_code}\n{response.text}")
        return

    print(f"[INFO] Waiting for video frame from {get_video_frame_url}...")
    while True:
        try:
            response = requests.post(get_video_frame_url, timeout=5)
            if response.ok and response.headers.get("Content-Type", "").startswith("image/"):
                with open(VIDEO_FRAME_IMG, 'wb') as f:
                    f.write(response.content)
                print(f"[SUCCESS] Video frame saved to {VIDEO_FRAME_IMG}")
                break
            else:
                print("[INFO] Server not ready, retrying...")
                sleep(2)
        except requests.RequestException as e:
            print(f"[ERROR] Request failed: {e}, retrying...")
            sleep(2)


def generate_morph(a_path, b_path):
    print("[INFO] Generating morphing video with", a_path, "and", b_path)

    if not os.path.isfile(a_path) or not os.path.isfile(b_path):
        print("[ERROR] One or both image paths are invalid.")
        return

    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(ALIGNED_DIR, exist_ok=True)

    try:
        print("[INFO] Aligning face images...")
        subprocess.run([
            "python", FACE_ALIGN_SCRIPT,
            "-images", TEMP_DIR,
            "-target", a_path,
            "-overlay",
            "-outdir", ALIGNED_DIR
        ], check=True)
        print("[SUCCESS] Face alignment completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Face alignment failed: {e}")
        return

    try:
        print("[INFO] Generating morphing video...")
        subprocess.run([
            "python", MORPH_SCRIPT,
            "-morph",
            "-images", ALIGNED_DIR,
            "-td", str(TRANSITION_DUR),
            "-pd", str(PAUSE_DUR),
            "-fps", str(FPS),
            "-out", OUTPUT_VIDEO
        ], check=True)
        print(f"[SUCCESS] Morphing video created: {OUTPUT_VIDEO}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Morphing process failed: {e}")
        return


def send_video(video_path):
    send_morph_url = f"{URL}/upload_morph_video"

    if not os.path.isfile(video_path):
        print(f"[ERROR] File '{video_path}' does not exist.")
        return

    with open(video_path, 'rb') as f:
        file = f.read()
        headers = {
            'Content-Type': 'video/mp4',
            'Accept': 'application/json'
        }
        print("[INFO] Sending morph video to server...")
        response = requests.post(send_morph_url, headers=headers, data=file)

    if response.ok:
        print("[SUCCESS] Morphing video sent successfully!")
    else:
        print(f"[ERROR] Failed to send video: {response.status_code}\n{response.text}")


def remove_background_for_images(image_paths):
    for image_path in image_paths:
        filename, ext = os.path.splitext(os.path.basename(image_path))
        output_path = os.path.join(TEMP_DIR, f"{filename}_rembg{ext}")
        print(f"[INFO] Removing background: {image_path} → {output_path}")
        image_processing.remove_background(image_path, output_path)


# ==== MAIN ====

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    if len(sys.argv) == 1:
        fetch_images()

    elif sys.argv[1] == "generate_morph":
        if len(sys.argv) == 4:
            generate_morph(sys.argv[2], sys.argv[3])
        else:
            generate_morph(CAPTURE_REMBG, VIDEO_FRAME_REMBG)

    elif sys.argv[1] == "send_video":
        if len(sys.argv) == 3:
            send_video(sys.argv[2])
        else:
            send_video(OUTPUT_VIDEO)

    elif sys.argv[1] == "remove_background":
        if len(sys.argv) >= 3:
            remove_background_for_images(sys.argv[2:])
        else:
            remove_background_for_images([CAPTURE_IMG, VIDEO_FRAME_IMG])

    else:
        print("Usage:")
        print("  python main.py")
        print("  python main.py generate_morph <PATH_IMG_A> <PATH_IMAGE_B>")
        print("  python main.py send_video <PATH_VIDEO>")
        print("  python main.py remove_background <PATH_IMG_1> <PATH_IMG_2> ...")


if __name__ == "__main__":
    main()

