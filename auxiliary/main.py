#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

"""
This script can:
1. Fetch assets from server (camera + AI generated video url).
2. Generate morphing video using two images.
3. Send morphing video to the server.
4. Reverse video.
5. Concatenate videos
"""

import sys
import os
import requests
from time import sleep
import subprocess
import image_processing
import video_processing

# ==== VARIABLES ====
URL = "http://192.168.11.40:8000"
TEMP_DIR = "temp"
TEMP_REMBG_DIR = "temp/temp_rembg"
CAPTURE_IMG = os.path.join(TEMP_DIR, "capture.jpg")
CAPTURE_REMBG = os.path.join(TEMP_REMBG_DIR, "capture_rembg.jpg")
VIDEO_FRAME_REMBG = os.path.join(TEMP_REMBG_DIR, "video_frame_rembg.jpg")
ALIGNED_DIR = os.path.join(TEMP_DIR, "aligned_faces")
OUTPUT_VIDEO = os.path.join(TEMP_DIR, "output.mp4")
FACE_ALIGN_SCRIPT = "face-movie/face-movie/align.py"
MORPH_SCRIPT = "face-movie/face-movie/main.py"
TRANSITION_DUR = 2.0
PAUSE_DUR = 0.5
FPS = 25
VIDEO_REVERSED = os.path.join(TEMP_DIR, "reversed_video.mp4")
VIDEO_CONCATENATED = os.path.join(TEMP_DIR, "concatenated_video.mp4")
VIDEO_AI = os.path.join(TEMP_DIR, "video_generated.mp4")
MORPH_TEMP_DIR = os.path.join(TEMP_DIR, "morph_temp_processed")


# ==== FUNCTIONS ====


def fetch_assets():
    get_camera_frame_url = f"{URL}/get_camera_capture"
    get_video_url = f"{URL}/get_video_url"

    print("[INFO] Requesting camera image...")
    try:
        response = requests.post(get_camera_frame_url)
        response.raise_for_status() 
        if response.headers.get("Content-Type", "").startswith("image/"):
            with open(CAPTURE_IMG, 'wb') as f:
                f.write(response.content)
            print(f"[SUCCESS] Image saved to {CAPTURE_IMG}")
        else:
            print("[ERROR] Server did not return an image for camera capture.")
            return False
    except requests.RequestException as e:
        print(f"[ERROR] Failed to download camera image: {e}")
        return False

    print("[INFO] Requesting video url...")
    try:
        response = requests.post(get_video_url, timeout=10)
        response.raise_for_status()
        video_url = response.text.strip()
        print(f"[SUCCESS] Video URL retrieved: {video_url}")
    except requests.RequestException as e:
        print(f"[ERROR] Request to get video URL failed: {e}")
        return False

    if not video_processing.download_video(video_url, VIDEO_AI):
        print("[ERROR] Video download failed. Aborting.")
        return False

    if not video_processing.get_first_frame(VIDEO_AI, VIDEO_FRAME_REMBG):
        print("[ERROR] Frame extraction failed. Aborting.")
        return False

    print("\n[COMPLETE] All assets fetched and prepared successfully.")
    return True


def generate_morph_wrapper():
    """
    A wrapper to call the specialized morph generation process.
    """
    print("[INFO] Preparing to generate specialized morph.")
    
    success = video_processing.generate_morph_specialized(
        images_path=TEMP_REMBG_DIR,
        capture_rembg_path=CAPTURE_REMBG,
        video_frame_rembg_path=VIDEO_FRAME_REMBG,
        output_video_path=OUTPUT_VIDEO,
        align_script_path=FACE_ALIGN_SCRIPT,
        morph_script_path=MORPH_SCRIPT,
        aligned_dir=ALIGNED_DIR,
        temp_dir=MORPH_TEMP_DIR,
        transition_dur=TRANSITION_DUR,
        pause_dur=PAUSE_DUR,
        fps=FPS
    )
    
    if success:
        print("[INFO] Morph generation process finished successfully in main.")
    else:
        print("[ERROR] Morph generation process failed in main.")


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
    os.makedirs(TEMP_REMBG_DIR, exist_ok=True)
    for image_path in image_paths:
        filename, ext = os.path.splitext(os.path.basename(image_path))
        output_path = os.path.join(TEMP_REMBG_DIR, f"{filename}_rembg{ext}")
        image_processing.remove_background(image_path, output_path)
        print("[SUCCESS] Background removed successfully!")


def reverse_video(video_path):
    os.makedirs(TEMP_DIR, exist_ok=True)
    print(f"[INFO] Starting video reversal for: {video_path}")
    video_processing.reverse_video_from_path(video_path, VIDEO_REVERSED)


def concatenate_videos(videos_list):
    os.makedirs(TEMP_DIR, exist_ok=True)
    if all(os.path.exists(v) for v in videos_list):
        print(f"[INFO] Starting video concatenation for: {', '.join(videos_list)}")
        video_processing.concatenate_videos_ffmpeg(videos_list, VIDEO_CONCATENATED)
    else:
        print("[ERROR] One or more input video files not found.")


def run_full_pipeline():
    print("[INFO] Running full pipeline")
    
    if not fetch_assets():
        print("[ERROR] Could not fetch assets.")
        return
    print("[SUCCESS] Step 1/7: Fetching assets complete.")

    remove_background_for_images([CAPTURE_IMG]) 
    print("[SUCCESS] Step 2/7: Background removal complete.")

    generate_morph_wrapper()    
    print("[SUCCESS] Step 3/7: Morphing video generation complete.")
    
    send_video(OUTPUT_VIDEO)
    print("[SUCCESS] Step 4/7: Morphing video generation sent.")

    reverse_video(VIDEO_AI)
    print("[SUCCESS] Step 5/7: Video reversal complete.")

    concatenate_videos([VIDEO_AI, VIDEO_REVERSED])
    print("[SUCCESS] Step 6/7: Video concatenation complete.")

    send_video(VIDEO_CONCATENATED)
    print("[SUCCESS] Step 7/7: Final video sent.")
    print("[SUCCESS] PIPELINE FINISHED SUCCESSFULLY")


# ==== MAIN ====


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)

    if len(sys.argv) == 1:
        run_full_pipeline()

    elif sys.argv[1] == "fetch":
        fetch_assets()
    
    elif sys.argv[1] == "generate_morph":
        required_files = [CAPTURE_REMBG, VIDEO_FRAME_REMBG]

        if not all(os.path.exists(p) for p in required_files):
            print("[ERROR] Required files for morphing not found. (pictures or shape_predictor required for face-movie)")
            print("Please run 'fetch_assets' and 'remove_background' first.")
        else:
            generate_morph_wrapper()

    elif sys.argv[1] == "send_video":
        if len(sys.argv) == 3:
            send_video(sys.argv[2])
        else:
            send_video(OUTPUT_VIDEO)

    elif sys.argv[1] == "remove_background":
        if len(sys.argv) >= 3:
            remove_background_for_images(sys.argv[2:])
        else:
            remove_background_for_images([CAPTURE_IMG])

    elif sys.argv[1] == "reverse_video":
        if len(sys.argv) == 3:
            reverse_video(sys.argv[2])
        else:
            reverse_video(VIDEO_AI)

    elif sys.argv[1] == "concatenate_videos":
        if len(sys.argv) >= 4:
            concatenate_videos(sys.argv[2:])
        else:
            concatenate_videos([VIDEO_AI, VIDEO_REVERSED])

    else:
        print("Usage:")
        print("  python main.py (runs full pipeline)")
        print("  python main.py fetch (fetches assets from server)")
        print("  python main.py remove_background <PATH_IMG_1> <PATH_IMG_2> ...")
        print("  python main.py generate_morph")
        print("  python main.py reverse_video <PATH_VIDEO>")
        print("  python main.py concatenate_videos <PATH_VIDEO_1> <PATH_VIDEO_2> ...")
        print("  python main.py send_video <PATH_VIDEO>")


if __name__ == "__main__":
    main()

