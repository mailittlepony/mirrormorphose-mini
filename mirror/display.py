#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

# def change_video_source(path):
#     pass

# def play_async():
#     pass

# def release():
#     pass

from lib.overlayx import overlayx

omxplayer_args = [
    "--aspect-mode stretch",
    "--no-osd",
    "--no-keys"
    "-o hdmi"
]

# "omxplayer --win "0 0 1080 1920" --aspect-mode stretch --no-osd -o hdmi stream.h264"
