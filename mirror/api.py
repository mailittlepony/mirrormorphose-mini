#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

import threading
from runwayml import RunwayML, TaskFailedError
from dotenv import load_dotenv
from os import getenv
from base64 import b64encode
import requests
from shared import RAM_DISK
import shared

load_dotenv()
api_key = getenv("RUNWAYML_API_SECRET")

test_video = True
runway_client = RunwayML(api_key=api_key)

def runway_generate_video(img):
    video_path = f"{RAM_DISK}/generated_video.mp4"

    if test_video:
        with shared.lock:
            shared.shared_data["runway_task_status"] = 0 
        return

    def start_task():
        try:
            base64_jpg = b64encode(img).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{base64_jpg}"

            with shared.lock:
                shared.shared_data["runway_task_status"] = 1

            task = runway_client.image_to_video.create(
                model='gen4_turbo',
                prompt_image=data_uri,
                prompt_text='Generate a video',
                ratio='1280:720',
                duration=5,
            ).wait_for_task_output()

            video_url = task.output[0]
            if not video_url.startswith("http"):
                raise RuntimeError("Invalid URL in task output")

            # Download video with timeout
            response = requests.get(video_url, stream=True, timeout=20)
            response.raise_for_status()

            with open(video_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    
            with shared.lock:
                shared.shared_data["runway_task_status"] = 0

        except TaskFailedError as e:
            print(f"Error : {e.task_details}")

        except Exception as e:
            print(f"Error : {e}")

    threading.Thread(target=start_task, daemon=True).start()
