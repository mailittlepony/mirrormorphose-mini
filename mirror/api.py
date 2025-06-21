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

load_dotenv()
api_key = getenv("RUNWAYML_API_SECRET")

runway_api_call = False
runway_client = RunwayML(api_key=api_key)

def runway_generate_video(img, task_end_callback):
    if not runway_api_call:
        return

    def start_task():
        try:
            base64_jpg = b64encode(img).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{base64_jpg}"

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

            video_path = "temp/generated_video.mp4"
            with open(video_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            try:
                task_end_callback(task.output[0], "")
            except Exception as cb_err:
                print(f"Callback error: {cb_err}")

        except TaskFailedError as e:
            task_end_callback(None, e.task_details)

        except Exception as e:
            task_end_callback(None, str(e))

    threading.Thread(target=start_task, daemon=True).start()
