#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

"""
This script 
"""

import sys
import os
import requests
from time import sleep

from requests.api import get

URL = "raspberrypi.local"

def run():
    send_photo_url = f"{URL}/send-photo"
    send_morph_video_url = f"{URL}/send-morph-video"
    status_url = f"{URL}/status/1"
    get_video_frame_url = f"{URL}/get-morph-video-frame"

    user_photo_file = None
    video_frame_file = None

    try:
        if len(sys.argv) < 2:
            raise ValueError("please provide the picture path")

        photo_path = sys.argv[1]

        # Check if file exists and is a file
        if not os.path.isfile(photo_path):
            raise FileNotFoundError(f"'{photo_path}' is a wrong path")

        print(f"Photo path: {photo_path}")

        # Open the file and send it in the POST request
        user_photo_file = open(photo_path, 'rb')
        files = {'photo': user_photo_file}
        response = requests.post(send_photo_url, files=files)

        # Check response status
        if response.ok:
            print("Photo uploaded successfully!")
            print("Server response:", response.text)
        else:
            raise Exception(f"failed to upload photo : {response.status_code}")

        # Get the video frame for morphism
        print(f"waiting for the video frame at {get_video_frame_url}")
        while True:
            try:
                response = requests.post(get_video_frame_url, data={}, headers=None, timeout=5)

                if response.status_code == 200 and response.headers.get("Content-Type", "").startswith("image/"):
                    print("Image received.")
                    video_frame_file = open("temp/video_frame.jpg", "wb")
                    video_frame_file.write(response.content)
                    break
                else:
                    print("server not ready, retrying...")
                    sleep(2)

            except requests.RequestException as e:
                print(f"request failed: {e}, retrying...")
                sleep(2)

        # TODO: send the photos to the face morph API
        # then send it to the mirror

        user_photo_file.close()
        video_frame_file.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()

