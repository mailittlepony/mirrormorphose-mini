#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

from urllib.parse import unquote
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
import cv2
from mimetypes import guess_type
import os
import api
import shared

STATIC_DIR = "static"

class MirrorHTTPRequestHandler(BaseHTTPRequestHandler):
# Override
    def do_GET(self):
        routes = { 
            "/": self._handle_serve_index 
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        elif self.path.startswith("/static/"):
            self._handle_serve_static_file()
        else:
            self._send_response_str(404, "Route not found")
            
    def do_POST(self):
        routes = {
            "/upload_user_photo": self._handle_upload_user_photo,
            "/upload_morph_video": self._handle_upload_morph_video,
            "/get_video_frame_for_morph": self._handle_get_video_frame_for_morph,
            "/get_camera_capture": self._handle_get_camera_capture,
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self._send_response_str(404, "Route not found")

# Handlers

    """
    GET Handlers
    """
    def _handle_serve_index(self):
        file_path = "index.html"
        if not os.path.exists(file_path):
            self._send_response_str(404, "index.html not found.")
            return

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self._send_response(200, content, content_type="text/html")
        except Exception as e:
            self._send_response_str(500, f"Server error: {e}")

    def _handle_serve_static_file(self):
        # Strip "/static/" and resolve file path
        rel_path = unquote(self.path[len("/static/"):])
        safe_path = os.path.normpath(rel_path).lstrip(os.sep)  # prevent path traversal
        file_path = os.path.join(STATIC_DIR, safe_path)

        if not os.path.isfile(file_path):
            self._send_response_str(404, "File not found")
            return

        # Guess MIME type
        mime_type, _ = guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            self._send_response(200, content, mime_type)
        except Exception as e:
            self._send_response_str(500, f"Error reading file: {e}")

    """
    POST Handlers
    """
    def _handle_upload_user_photo(self):
        def runway_task_end(output, ret):
            shared.shared_data["runway_task_output"] = output
            print(ret)

        # Parse the multipart form data
        form = FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': self.headers.get('Content-Type'),
            }
        )

        if 'photo' not in form:
            self._send_response_str(400, "Missing 'photo' field.")
            return

        fileitem = form['photo']
        if not fileitem.file or not fileitem.filename:
            self._send_response_str(400, "No file uploaded.")
            return

        if fileitem.type not in [ "image/jpeg", "image/png" ]:
            self._send_response_str(415, f"Unsupported media type: {fileitem.type}")
            return

        try:
            with open("user_photo.jpg", 'wb') as out_file:
                while True:
                    chunk = fileitem.file.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    api.runway_generate_video(fileitem, runway_task_end)
            self._send_response_str(200, f"Uploaded successfully. Sent to Runway API.")
        except Exception as e:
            self._send_response_str(500, f"Error saving file: {e}")

    def _handle_upload_morph_video(self):
        content_type = self.headers.get('Content-Type', '')
        # Validate content type
        if not content_type.startswith("video/"):
            self._send_response_str(415, "Unsupported Media Type. Expected type starting with 'video/'.")
            return

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_response_str(400, "Empty request body.")
            return

        try:
            file_data = self.rfile.read(content_length)

            os.makedirs("temp", exist_ok=True)
            with open("temp/morph_video.mp4", "wb") as f:
                f.write(file_data)

            self._send_response_str(200, "Face morph video uploaded successfully.")

        except Exception as e:
            self._send_response_str(500, f"Server error: {e}")

    def _handle_get_video_frame_for_morph(self):
        try:
            with shared.lock:
                video_ready = shared.shared_data.get("runway_task_output") is not None

            if not video_ready:
                self._send_response_str(404, "Runway video not downloaded yet.")
                return

            video_path = "temp/generated_video.mp4"
            if not os.path.isfile(video_path):
                self._send_response_str(404, "Video file not found.")
                return

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self._send_response_str(500, "Failed to open video file.")
                return

            target_frame_index = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_index)

            success, frame = cap.read()
            cap.release()

            if not success or frame is None:
                self._send_response_str(500, "Failed to read the video frame.")
                return

            success, jpeg = cv2.imencode(".jpg", frame)
            if not success:
                self._send_response_str(500, "Failed to encode frame as JPEG.")
                return

            self._send_response(200, jpeg.tobytes(), content_type="image/jpeg")

        except Exception as e:
            self._send_response_str(500, f"Error: {str(e)}")


    def _handle_get_camera_capture(self):
        try:
            with shared.lock:
                frame = shared.shared_data.get("last_camera_frame")

            if frame is None:
                raise RuntimeError("last frame is None")

            ret, jpeg = cv2.imencode('.jpg', frame)
            if not ret:
                raise RuntimeError("JPEG encoding failed.")

            self._send_response(200, jpeg.tobytes(), "image/jpeg")

        except Exception as e:
            self._send_response_str(500, f'Error: {str(e)}')

# Helpers
    def _send_response_str(self, code, content=""):
        self._send_response(code, content.encode(), "text/plain")

    def _send_response(self, code, content=b"", content_type="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
