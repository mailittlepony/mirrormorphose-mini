#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
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
import shutil

URL = "http://192.168.11.41:8000"

def fetch_images():
    get_video_frame_url = f"{URL}/get_video_frame_for_morph"
    get_camera_frame_url = f"{URL}/get_camera_capture"

    #Get camera image
    print("[INFO] Requesting camera image...")
    response = requests.post(get_camera_frame_url)

    if response.ok and response.headers.get("Content-Type", "").startswith("image/"):
        with open("temp/capture.jpg", 'wb') as f:
            f.write(response.content)
        print("[SUCCESS] Image saved to temp/capture.jpg")
    else:
        print(f"[ERROR] Failed to download camera image: {response.status_code}\n{response.text}")
        return

    # Get video frame
    print(f"[INFO] Waiting for video frame from {get_video_frame_url}...")
    while True:
        try:
            response = requests.post(get_video_frame_url, timeout=5)

            if response.ok and response.headers.get("Content-Type", "").startswith("image/"):
                with open("temp/video_frame.jpg", 'wb') as f:
                    f.write(response.content)
                print("[SUCCESS] Video frame saved to temp/video_frame.jpg")
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

    IMAGES_DIR = "temp"
    ALIGN_OUTPUT = "temp/aligned_faces"
    BASE_IMAGE = a_path 
    OUTPUT_VIDEO = "temp/output.mp4"
    TRANSITION_DUR = 2.0
    PAUSE_DUR = 0.5
    FPS = 25

    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(ALIGN_OUTPUT, exist_ok=True)

    # 2. Align faces
    try:
        print("[INFO] Aligning face images...")
        subprocess.run([
            "python", "face-movie/face-movie/align.py",
            "-images", IMAGES_DIR,
            "-target", BASE_IMAGE,
            "-overlay",
            "-outdir", ALIGN_OUTPUT
        ], check=True)
        print("[SUCCESS] Face alignment completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Face alignment failed: {e}")
        return

    # 3. Morph images
    try:
        print("[INFO] Generating morphing video...")
        subprocess.run([
            "python", "face-movie/face-movie/main.py",
            "-morph",
            "-images", ALIGN_OUTPUT,
            "-td", str(TRANSITION_DUR),
            "-pd", str(PAUSE_DUR),
            "-fps", str(FPS),
            "-out", OUTPUT_VIDEO
        ], check=True)
        print(f"[SUCCESS] Morphing video created: {OUTPUT_VIDEO}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Morphing process failed: {e}")
        return
    print("[SUCCESS] Morphing video generated.")  


def send_video(video_path):
    send_morph_url = f"{URL}/upload_morph_video"

    if not os.path.isfile(video_path):
        print(f"[ERROR] File '{video_path}' does not exist.")
        return

    with open(video_path, 'rb') as f:
        # files = {'file': (os.path.basename(video_path), f, 'video/mp4')}
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


def main():
    os.makedirs("temp", exist_ok=True)
    if len(sys.argv) == 1:
        fetch_images()
    elif sys.argv[1] == "generate_morph":
        if len(sys.argv) == 4:
            generate_morph(sys.argv[2], sys.argv[3])
        else:
            generate_morph("temp/capture.jpg", "temp/video_frame.jpg")
    elif sys.argv[1] == "send_video":
        if len(sys.argv) == 3:
            send_video(sys.argv[2])
        else:
            send_video("temp/output.mp4")
    else:
        print("Usage:")
        print("  python main.py                     # fetch camera & video frame")
        print("  python main.py generate_morph <PATH_IMG_A> <PATH_IMAGE_B>")
        print("  python main.py send_video <PATH_VIDEO>")


if __name__ == "__main__":
    main()

