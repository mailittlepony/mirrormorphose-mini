#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import logging
from pathlib import Path
import requests

from config import AUTH_TOKEN, URL

logger = logging.getLogger(__name__)


def fetch_assets() -> bool:
    headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}
    try:
        resp = requests.post(f"{URL}/get_camera_capture", headers=headers)
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("image/"):
            Path("temp/capture.jpg").write_bytes(resp.content)
            logger.info("Camera capture saved.")
        else:
            logger.error("Camera capture response not an image.")
            return False

        resp = requests.post(f"{URL}/get_user_image", headers=headers)
        resp.raise_for_status()
        if resp.headers.get("Content-Type", "").startswith("image/"):
            Path("temp/user_image.jpg").write_bytes(resp.content)
            logger.info("User image saved.")
        else:
            logger.error("User image response not an image.")
            return False

    except requests.RequestException as e:
        logger.error(f"Failed fetching assets: {e}")
        return False
    return True


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


def preload_videos() -> None:
    try:
        requests.post(f"{URL}/load_videos", headers={'Authorization': f'Bearer {AUTH_TOKEN}'})
        logger.info("Preloaded videos on server.")
    except requests.RequestException as e:
        logger.error(f"Failed to preload videos: {e}")

