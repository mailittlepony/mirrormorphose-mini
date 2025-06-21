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

shared_data = {
    "user_photo": None,
    "last_camera_frame": None,
    "runway_task_status": 0
}

lock = Lock()
