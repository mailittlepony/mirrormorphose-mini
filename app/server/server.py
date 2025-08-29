#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from http.server import ThreadingHTTPServer
import threading

from .http_handler import MirrorHTTPRequestHandler
from ..config import HTTP_PORT

httpd = None

def run_async():
    global httpd
    httpd = ThreadingHTTPServer(('', HTTP_PORT), MirrorHTTPRequestHandler)
    print(f"[INFO] HTTP server running on port {HTTP_PORT}")
    def worker(_httpd):
        try:
            _httpd.serve_forever()
        except Exception as e:
            print(f"[ERROR] HTTP server stopped: {e}")
        finally:
            _httpd.server_close()
            print("[INFO] HTTP server closed.")

    t = threading.Thread(target=worker, args=(httpd,), daemon=True)
    t.start()
    return t

def close():
    global httpd
    if httpd:
        httpd.shutdown()
