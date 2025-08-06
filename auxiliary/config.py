#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the MIT license.

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "")
URL = os.getenv("SERVER_URL", "http://mirrormini.local:8000")

TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_REMBG_DIR = TEMP_DIR / "temp_rembg"
FACE_ALIGN_SCRIPT = PROJECT_ROOT / "face-movie/face-movie/align.py"
MORPH_SCRIPT = PROJECT_ROOT / "face-movie/face-movie/main.py"
MODEL_PATH = PROJECT_ROOT / "models/eye_direction_model.tflite"
FACE_CASCADE_PATH = PROJECT_ROOT / "models/haarcascade_frontalface_default.xml"
EYE_CASCADE_PATH = PROJECT_ROOT / "models/haarcascade_eye_tree_eyeglasses.xml"
CAMERA_INDEX = 0
VIGNETTE_PATH = PROJECT_ROOT / "res/vignette.png"

