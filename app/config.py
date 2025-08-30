#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.


from os import getenv
from pathlib import Path
from dotenv import load_dotenv

# Server
HTTP_PORT = 8000
STATIC_DIR = Path("web/static")
INDEX_PATH = Path("web/index.html")

# App paths
RAMDISK_DIR = Path("app/ramdisk")
TEMP_DIR = RAMDISK_DIR/"tmp"

# APIs
load_dotenv()
RUNWAY_AUTH_TOKEN = getenv("RUNWAYML_API_SECRET")

# Camera
VIDEO_DEVICE_PREVIEW = "/dev/video12"
CAMERA_PREVIEW_WIDTH = 640
CAMERA_PREVIEW_HEIGHT = 480
CAMERA_PREVIEW_FORMAT = 'GREY'
VIDEO_DEVICE_FULL = "/dev/video11"
CAMERA_FULL_WIDTH = 640
CAMERA_FULL_HEIGHT = 480
CAMERA_FULL_FORMAT = 'UYVY'

# Face detection/recognition
MODEL_DIR = Path("app/res/models")
FACE_CASCADE_PATH = MODEL_DIR/"haarcascade_frontalface_default.xml"
EYE_CASCADE_PATH = MODEL_DIR/"haarcascade_eye_tree_eyeglasses.xml"

# Display
SHADER_DIR = Path("app/core/display/shaders")

# Morph
TEMP_REMBG_DIR = TEMP_DIR/"tmp_rembg"
FACE_MOVIE_FACE_ALIGN_SCRIPT = Path("app/core/morph/face-movie/face-movie/align.py")
FACE_MOVIE_MORPH_SCRIPT = Path("app/core/morph/face-movie/face-movie/main.py")
