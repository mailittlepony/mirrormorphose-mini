#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

from threading import Lock

RAM_DISK = "ramdisk"
TEMP_DIR = "temp"
STATIC_DIR = "static"

# Files path
MORPH_VIDEO_PATH = f"{RAM_DISK}/morph_video.mp4"
AI_VIDEO_PATH = f"{RAM_DISK}/concatenated_video.mp4"

shared_data = {
    "user_photo": None,
    "last_camera_frame": None,
    "generated_video_url": None
}

lock = Lock()
