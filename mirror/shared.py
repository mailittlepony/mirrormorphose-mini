#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

from threading import Lock

shared_data = {
    "user_photo": None,
    "last_camera_frame": None,
    "runway_task_output": None
}

lock = Lock()
