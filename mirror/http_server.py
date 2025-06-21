#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

from http_handler import MirrorHTTPRequestHandler
from http.server import ThreadingHTTPServer
import threading

PORT = 8000

thread = None
httpd = None

def run():
    global httpd
    httpd = ThreadingHTTPServer(('', PORT), MirrorHTTPRequestHandler)
    print(f"HTTP server running on port {PORT}")
    httpd.serve_forever()

def start_non_blocking():
    global thread
    thread = threading.Thread(target=run)
    thread.start()


def stop():
    if httpd:
        httpd.shutdown()
        httpd.server_close()
    if thread:
        thread.join()


