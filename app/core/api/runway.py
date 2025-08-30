#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the GPLv3 license.

from typing import Optional

import numpy as np
from runwayml import RunwayML, TaskFailedError
from base64 import b64encode

from app.config import RUNWAY_AUTH_TOKEN

test_video = True
runway_client = RunwayML(api_key=RUNWAY_AUTH_TOKEN)

def generate_video(img: np.ndarray) -> Optional[str]:
    try:
        base64_jpg = b64encode(img).decode("utf-8")
        data_uri = f"data:image/jpeg;base64,{base64_jpg}"

        task = runway_client.image_to_video.create(
            model='gen4_turbo',
            prompt_image=data_uri,
            prompt_text='The camera is still, with natural lighting. Subject sits still and maintains a serious expression holding direct eye contact with the camera while blinking occasionally. Subject nods slowly at the 3-second marks and occasionally tilts his head slightly.',
            ratio='720:1280',
            duration=5,
        ).wait_for_task_output()

        video_url = task.output[0]
        if not video_url.startswith("http"):
            raise RuntimeError("Invalid URL in task output")

        return video_url

    except TaskFailedError as e:
        print(f"Error : {e.task_details}")

    except Exception as e:
        print(f"Error : {e}")
