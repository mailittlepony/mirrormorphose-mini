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
import logging
import requests
import time
import cv2
from dotenv import load_dotenv
from face_recognition import LightweightFaceDetector
import image_processing
import video_processing
import api

from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()
AUTH_TOKEN = os.getenv("AUTH_TOKEN")


# ==== Constants ====


TEMP_DIR = Path("temp")
TEMP_REMBG_DIR = TEMP_DIR / "temp_rembg"
FACE_ALIGN_SCRIPT = Path("face-movie/face-movie/align.py")
MORPH_SCRIPT = Path("face-movie/face-movie/main.py")
MODEL_PATH = Path("models/eye_direction_model.tflite")
FACE_CASCADE_PATH = Path('models/haarcascade_frontalface_default.xml')
EYE_CASCADE_PATH = Path('models/haarcascade_eye_tree_eyeglasses.xml')
CAMERA_INDEX = 0
URL = "http://mirrormini.local:8000"


# ==== FUNCTIONS ====


def fetch_assets() -> bool:
    headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
    try:
        resp = requests.post(f"{URL}/get_camera_capture", headers=headers)
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("image/"):
            (TEMP_DIR / "capture.jpg").write_bytes(resp.content)
            logger.info("Camera capture saved.")
        else:
            logger.error("Camera capture response not an image.")
            return False

        resp = requests.post(f"{URL}/get_user_image", headers=headers)
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("image/"):
            (TEMP_DIR / "user_image.jpg").write_bytes(resp.content)
            logger.info("User image saved.")
        else:
            logger.error("User image response not an image.")
            return False

    except requests.RequestException as e:
        logger.error(f"Failed fetching assets: {e}")
        return False
    return True


def generate_morph_wrapper() -> bool:
    success = video_processing.generate_morph_specialized(
        images_path=str(TEMP_REMBG_DIR),
        capture_rembg_path=str(TEMP_REMBG_DIR / "capture_rembg.jpg"),
        video_frame_rembg_path=str(TEMP_REMBG_DIR / "video_frame_rembg.jpg"),
        output_video_path=str(TEMP_DIR / "morph_video.mp4"),
        align_script_path=str(FACE_ALIGN_SCRIPT),
        morph_script_path=str(MORPH_SCRIPT),
        aligned_dir=str(TEMP_DIR / "aligned_faces"),
        temp_dir=str(TEMP_DIR / "morph_temp_processed"),
        transition_dur=2.0,
        pause_dur=0.5,
        fps=25
    )
    if not success:
        logger.error("Morph generation failed.")
    return success


def send_video(video_path: str) -> bool:
    path = Path(video_path)
    if not path.is_file():
        logger.error(f"Video file {video_path} does not exist.")
        return False

    with path.open('rb') as f:
        files = {'file': (path.name, f, 'video/mp4')}
        headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
        try:
            response = requests.post(f"{URL}/upload_media", files=files, headers=headers)
            response.raise_for_status()
            logger.info(f"Uploaded video {video_path} successfully.")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to send video: {e}")
            return False


def remove_background_for_images(image_paths) -> bool:
    os.makedirs(TEMP_REMBG_DIR, exist_ok=True)
    all_success = True
    for image_path in image_paths:
        filename, ext = os.path.splitext(os.path.basename(image_path))
        output_path = os.path.join(TEMP_REMBG_DIR, f"{filename}_rembg{ext}")
        success = image_processing.remove_background(image_path, output_path)
        if not success:
            print(f"[ERROR] Failed to remove background from {image_path}")
            all_success = False
    return all_success


def reverse_video(video_path) -> bool:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TEMP_DIR / "reversed_video.mp4"
    try:
        video_processing.reverse_video_from_path(str(video_path), str(output_path))
        return True
    except Exception as e:
        logger.error(f"Failed to reverse video: {e}")
        return False


def concatenate_videos(videos_list) -> bool:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    if not all(Path(v).exists() for v in videos_list):
        logger.error("One or more videos for concatenation do not exist.")
        return False
    output_path = TEMP_DIR / "concatenated_video.mp4"
    try:
        video_processing.concatenate_videos_ffmpeg(videos_list, str(output_path))
        return True
    except Exception as e:
        logger.error(f"Failed to concatenate videos: {e}")
        return False


def add_vignette_video(video_path, output_path) -> bool:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        video_processing.add_vignette(video_path, output_path, "res/vignette.png")
        Path(video_path).unlink(missing_ok=True)
        Path(output_path).rename(video_path)
        logger.info(f"Vignette added and original video replaced: {video_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to add vignette or replace video: {e}")
        return False


def monitor_gaze_stream():
    try:
        detector = LightweightFaceDetector(str(MODEL_PATH), str(FACE_CASCADE_PATH), str(EYE_CASCADE_PATH))
    except IOError as e:
        logger.error(f"Failed to initialize gaze detector: {e}")
        return

    def send_gaze_start():
        try:
            requests.post(f"{URL}/start_eye_contact", headers={'Authorization': f'Bearer {AUTH_TOKEN}'}, timeout=5)
        except requests.RequestException:
            pass

    def send_gaze_end():
        try:
            requests.post(f"{URL}/stop_eye_contact", headers={'Authorization': f'Bearer {AUTH_TOKEN}'}, timeout=5)
        except requests.RequestException:
            pass

    detector.set_gaze_start_callback(send_gaze_start)
    detector.set_gaze_end_callback(send_gaze_end)

    while True:
        cap = None
        try:
            cap = cv2.VideoCapture(f"{URL}/get_camera_stream")
            if not cap.isOpened():
                raise ConnectionError("Stream failed to open")
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                detector.process_frame(frame)
                if detector.tracking_bbox:
                    x, y, w, h = detector.tracking_bbox
                    color = (0, 0, 255) if detector._gaze_active else (0, 255, 0)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.imshow('Gaze Stream Monitor', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return
        except (ConnectionError, cv2.error):
            logger.warning("Connection lost or error reading from stream; retrying in 5 seconds.")
        finally:
            if cap:
                cap.release()
            cv2.destroyAllWindows()
        time.sleep(5)


def preload_videos():
    try:
        requests.post(f"{URL}/load_videos", headers={'Authorization': f'Bearer {AUTH_TOKEN}'})
        logger.info("Preloaded videos on server.")
    except requests.RequestException as e:
        logger.error(f"Failed to preload videos: {e}")


def call_runway(img_path) -> bool:
    with open(img_path, 'rb') as img_file:
        video_url = api.runway_generate_video(img_file.read())
    if not video_processing.download_video(video_url, str(TEMP_DIR / "video_generated.mp4")):
        logger.error("Failed to download video from runway.")
        return False
    if not video_processing.get_first_frame(str(TEMP_DIR / "video_generated.mp4"), str(TEMP_REMBG_DIR / "video_frame_rembg.jpg")):
        logger.error("Failed to extract first frame from generated video.")
        return False
    return True


def run_full_pipeline():
    if not fetch_assets():
        logging.error("Failed to fetch assets.")
        return

    if not remove_background_for_images([f"{TEMP_DIR}/capture.jpg", f"{TEMP_DIR}/user_image.jpg"]):
        logging.error("Background removal failed.")
        return

    if not call_runway(f"{TEMP_REMBG_DIR}/user_image_rembg.jpg"):
        logging.error("Runway generation failed.")
        return

    if not generate_morph_wrapper():
        logging.error("Morph generation failed.")
        return

    if not add_vignette_video(f"{TEMP_DIR}/morph_video.mp4", f"{TEMP_DIR}/final_morph_video.mp4"):
        logging.error("Vignette addition failed for morph video.")
        return

    if not send_video(f"{TEMP_DIR}/morph_video.mp4"):
        logging.warning("Morph video not sent.")
        return
    
    if not reverse_video(f"{TEMP_DIR}/video_generated.mp4"):
        logging.error("Video could not be reversed.")
        return

    if not concatenate_videos([f"{TEMP_DIR}/video_generated.mp4", f"{TEMP_DIR}/reversed_video.mp4"]):
        logging.error("Videos could not be concatenated.")
        return

    if not add_vignette_video(f"{TEMP_DIR}/concatenated_video.mp4", f"{TEMP_DIR}/final_concatenated_video.mp4"):
        logging.error("Vignette addition failed for concatenated video.")
        return

    if not send_video(f"{TEMP_DIR}/concatenated_video.mp4"):
        logging.warning("Concatenated video not sent.")
        return

    preload_videos()
    monitor_gaze_stream()


# ==== MAIN ====


COMMANDS = {
    "fetch": fetch_assets,
    "generate_morph": generate_morph_wrapper,
    "send_video": lambda: send_video(sys.argv[2] if len(sys.argv) > 2 else f"{TEMP_DIR}/morph_video.mp4"),
    "remove_background": lambda: remove_background_for_images(sys.argv[2:] if len(sys.argv) >= 3 else [f"{TEMP_DIR}/capture.jpg", f"{TEMP_DIR}/user_image.jpg"]),
    "reverse_video": lambda: reverse_video(sys.argv[2] if len(sys.argv) > 2 else f"{TEMP_DIR}/video_generated.mp4"),
    "concatenate_videos": lambda: concatenate_videos(sys.argv[2:] if len(sys.argv) >= 4 else [f"{TEMP_DIR}/video_generated.mp4", f"{TEMP_DIR}/reversed_video.mp4"]),
    "add_vignette": lambda: (
        add_vignette_video(sys.argv[2], sys.argv[3])
        if len(sys.argv) == 4 else (
            add_vignette_video(f"{TEMP_DIR}/concatenated_video.mp4", f"{TEMP_DIR}/final_concatenated_video.mp4"),
            add_vignette_video(f"{TEMP_DIR}/morph_video.mp4", f"{TEMP_DIR}/final_morph_video.mp4")
        )
    ),
    "monitor": monitor_gaze_stream,
    "load_videos": preload_videos,
}

def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    if len(sys.argv) == 1:
        run_full_pipeline()
    else:
        command = sys.argv[1]
        if command in COMMANDS:
            COMMANDS[command]()
        else:
            print(f"Unknown command: {command}")
            print("Available commands:", ", ".join(COMMANDS.keys()))

if __name__ == "__main__":
    main()

