#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

from urllib.parse import unquote
from http.server import BaseHTTPRequestHandler
from cgi import FieldStorage
from mimetypes import guess_type
from shared import STATIC_DIR, RAM_DISK
from dotenv import load_dotenv
import cv2, os, api, shared, display

load_dotenv()
auth_token = os.getenv("AUTH_TOKEN")

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
            "/upload_media": self._handle_upload_media,
            "/get_camera_capture": self._handle_get_camera_capture,
            "/get_video_url": self._handle_get_video_url,
            "/load_videos": self._handle_load_videos,
            "/start_eye_contact": self._handle_start_eye_contact,
            "/stop_eye_contact": self._handle_stop_eye_contact,
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

    def _handle_upload_media(self):
        content_type = self.headers.get('Content-Type')
        if not content_type or 'multipart/form-data' not in content_type:
            self._send_response_str(400, "Content-Type must be multipart/form-data")
            return

        auth_header = self.headers.get("Authorization")

        # Parse form-data
        form = FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
            }
        )

        file_item = form['file']
        if not file_item.filename:
            self._send_response_str(400, "No file uploaded")
            return

        filename = os.path.basename(file_item.filename)
        file_ext = os.path.splitext(filename)[1].lower()

        try:
            isadmin =  auth_header == f"Bearer {auth_token}"

            if file_ext.lower() in [".jpg", ".jpeg", ".png"]:
                response = f"Child picture uploaded: {filename}"
                filename = f"user_photo{file_ext}"
                api.runway_generate_video(file_item)
            elif filename == os.path.basename(shared.MORPH_VIDEO_PATH):
                if not isadmin:
                    raise Exception("Access forbidden.")
                response = f"Morph video uploaded: {filename}"
            elif filename == os.path.basename(shared.AI_VIDEO_PATH):
                if not isadmin:
                    raise Exception(f"Forbidden access {auth_token}")
                response = f"Loopable Runway video uploaded: {filename}"
            else:
                raise Exception("Unknown uploaded item.")

            with open(f"{RAM_DISK}/{filename}", "wb") as f:
                while True:
                    chunk = file_item.file.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

            self._send_response_str(200, response)
        except Exception as e:
            self._send_response_str(403, f'{e}')

    def _handle_get_video_url(self):
        video_url = shared.shared_data.get("generated_video_url")

        if video_url:
            self._send_response_str(200, video_url) 
        else:
            self._send_response_str(400, "Not ready yet.")

    def _handle_get_camera_capture(self):
        auth_header = self.headers.get("Authorization")
        if auth_header != f"Bearer {auth_token}":
            self._send_response_str(403, f"Forbidden access {auth_token}")
            return

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

    def _handle_load_video(self):
        auth_header = self.headers.get("Authorization")
        if auth_header != f"Bearer {auth_token}":
            self._send_response_str(403, f"Forbidden access {auth_token}")
            return
        try:
            display.load_videos()
            self._send_response_str(200)
        except Exception as e:
            self._send_response_str(500, f"Error: {e}")

    def _handle_start_eye_contact(self):
        auth_header = self.headers.get("Authorization")
        if auth_header != f"Bearer {auth_token}":
            self._send_response_str(403, f"Forbidden access {auth_token}")
            return

        try:
            display.play()
            self._send_response_str(200)
        except Exception as e:
            self._send_response_str(500, f"Error: {e}")

    def _handle_stop_eye_contact(self):
        auth_header = self.headers.get("Authorization")
        if auth_header != f"Bearer {auth_token}":
            self._send_response_str(403, f"Forbidden access {auth_token}")
            return

        try:
            display.stop()
            self._send_response_str(200)
        except Exception as e:
            self._send_response_str(500, f"Error: {e}")

# Helpers
    def _send_response_str(self, code, content=""):
        self._send_response(code, content.encode(), "text/plain")

    def _send_response(self, code, content=b"", content_type="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
