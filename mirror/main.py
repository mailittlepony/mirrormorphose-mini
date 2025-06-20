#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

"""

"""

import cv2
import os
import threading
import base64
from dotenv import load_dotenv
from runwayml import RunwayML, TaskFailedError
from http.server import BaseHTTPRequestHandler, HTTPServer

load_dotenv()
api_key = os.getenv("RUNWAYML_API_SECRET")
client = RunwayML(api_key=api_key)
api_call = False

PORT = 8000
httpd = None
server_thread = None

lock = threading.Lock()

class MirrorHTTPRequestHandler(BaseHTTPRequestHandler):
    shared_data = { "last_frame":None, "user_photo":None, "runway_task":None }

    def read_uploaded_file(self, expected_type_prefix):
        try:
            content_type = self.headers.get('Content-Type', '')

            # Validate content type
            if not content_type.startswith(expected_type_prefix):
                self.send_response(415)
                self.end_headers()
                msg = f"Unsupported Media Type. Expected type starting with '{expected_type_prefix}'."
                self.wfile.write(msg.encode())
                return None

            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Empty request body.")
                return None

            file_data = self.rfile.read(content_length)
            return file_data

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Server error: {e}".encode())
            return None

    def do_POST(self):
        if self.path == '/upload_user_photo':
            user_photo_data = self.read_uploaded_file("image/");
            if user_photo_data:
                os.makedirs("temp", exist_ok=True)
                with open("temp/user_photo.jpg", "wb") as f:
                    f.write(user_photo_data)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"User photo uploaded successfully.")
                base64_jpg = base64.b64encode(user_photo_data).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{base64_jpg}"
                if api_call:
                    with lock:
                        self.shared_data["runway_task"] = generate_video(data_uri);

        elif self.path == '/upload_morph_video':
            morph_video_data = self.read_uploaded_file("video/");
            if morph_video_data:
                os.makedirs("temp", exist_ok=True)
                with open("temp/morph_video.mp4", "wb") as f:
                    f.write(morph_video_data)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Face morph video uploaded successfully.")

        elif self.path == '/get_video_frame_for_morph':
            with lock:
                try:
                    if self.shared_data.get("runway_task") is None:
                        raise Exception()
                    task = client.tasks.retrieve(id=self.shared_data.get("runway_task"))
                    if task == True:
                        print('Image URL:', task.output[0]);
                        self.send_response(200)
                        self.end_headers()
                        self.wfile.write(b"Runway video generated.")
                    else:
                        raise Exception()
                except Exception:
                    self.send_response(400)
                    self.end_headers()

        elif self.path == '/get_camera_capture':
            try:
                with lock:
                    frame = self.shared_data.get("last_frame")

                if frame is None:
                    raise RuntimeError("last frame is None")
                ret, jpeg = cv2.imencode('.jpg', frame)
                if not ret:
                    raise RuntimeError("JPEG encoding failed.")

                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.end_headers()
                self.wfile.write(jpeg.tobytes())

            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f'Error: {str(e)}'.encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

# ========== MACOS: Simulate picam2.capture_array() ==========
def init_webcam():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def get_frame():
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame from webcam.")
        return frame

    return cap, get_frame

# ========== RASPBERRY PI: Real picamera2 (for later) ==========
def init_picam2():
    from picamera2 import Picamera2

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (640, 480)
    picam2.preview_configuration.main.format = "BGR888"
    picam2.configure("preview")
    picam2.start()

    def get_frame():
        return picam2.capture_array()

    return picam2, get_frame

# ========== Select the source here ==========
USE_WEBCAM = True  # Set False when running on Raspberry Pi

camera, get_frame = init_webcam() if USE_WEBCAM else init_picam2()

def generate_video(data_uri):
    try:
        return client.image_to_video.create(
            model='gen4_turbo',
            prompt_image=data_uri,
            prompt_text='Generate a video',
            ratio='1280:720',
            duration=5,
        )

    except TaskFailedError as e:
        print('Runway video failed to generate.')
        print(e.task_details)
        return None

def http_server_run():
    global httpd
    httpd = HTTPServer(('', PORT), MirrorHTTPRequestHandler)
    print(f"HTTP server running on port {PORT}")
    httpd.serve_forever()

def run():
    global server_thread

    # Start HTTP server in background
    server_thread = threading.Thread(target=http_server_run)
    server_thread.daemon = True
    server_thread.start()

    try:
        while True:
            # Capture camera frame
            frame = get_frame()
            with lock:
                MirrorHTTPRequestHandler.shared_data["last_frame"] = frame

            # Process it with face_detection script
            cv2.imshow("Frame", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        print("shutting down...")
    finally:
        if USE_WEBCAM:
            camera.release()
        cv2.destroyAllWindows()

        if httpd:
            httpd.shutdown()
            httpd.server_close()
        if server_thread:
            server_thread.join()

if __name__ == "__main__":
    run()
