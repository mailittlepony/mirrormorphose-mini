#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from http.server import BaseHTTPRequestHandler
from mimetypes import guess_type
from urllib.parse import unquote
import os

class MirrorHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        routes = { 
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self._serve_direct_file("web")

    def do_POST(self):
        routes = {
        }
        handler = routes.get(self.path)
        if handler:
            handler()
        else:
            self._send_response_str(404)

    """
    GET Handlers
    """
    def _serve_direct_file(self, base_dir):
        request_path = unquote(self.path)
        if request_path == "/":
            request_path = "/index.html"

        # Normalize and strip leading slashes to avoid path traversal
        safe_path = os.path.normpath(request_path).lstrip("/\\")
        file_path = os.path.join(base_dir, safe_path)

        # Prevent escaping base_dir
        if not os.path.abspath(file_path).startswith(os.path.abspath(base_dir)):
            self._send_response_str(403, "Forbidden")
            return

        if not os.path.isfile(file_path):
            self._send_response_str(404)
            return

        mime_type, _ = guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self._send_response(200, content, mime_type)
        except Exception as e:
            self._send_response_str(500, f"Server error: {e}")
    """
    POST Handlers 
    """

    """
    Helpers
    """
    def _send_response_str(self, code, content=""):
        self._send_response(code, content.encode(), "text/plain")

    def _send_response(self, code, content=b"", content_type="text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
