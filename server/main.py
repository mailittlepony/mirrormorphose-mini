#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from http.server import ThreadingHTTPServer

from .http_handler import MirrorHTTPRequestHandler
from .config import HTTP_PORT

def run_server():
    global httpd
    httpd = ThreadingHTTPServer(('', HTTP_PORT), MirrorHTTPRequestHandler)
    print(f"HTTP server running on port {HTTP_PORT}")
    httpd.serve_forever()
