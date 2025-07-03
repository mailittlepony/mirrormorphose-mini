#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from overlayx import overlayx
from omxplayer.player import OMXPlayer
import threading, time, shared

fade_delay_ms = 800

def init():
    overlayx.init()

def load_videos():
    global morph_video, ai_video

    args = [
        "--loop",
        "--no-keys",
        "--no-osd",
        "-o hdmi",
        "--aspect-mode stretch",
        "--win 0,0,1080,1920"
    ]

    morph_video = OMXPlayer(shared.MORPH_VIDEO_PATH, args=args, dbus_name='org.mpris.MediaPlayer2.morphvid')
    ai_video = OMXPlayer(shared.AI_VIDEO_PATH, args=args, dbus_name='org.mpris.MediaPlayer2.aivid')

    time.sleep(2.5)

    morph_video.pause()
    ai_video.pause()

    def monitor_morph():
        while True:
            try:
                if morph_video.playback_status() == "Playing" and \
                   morph_video.duration() - morph_video.position() < 0.2:
                    ai_video.set_position(0)
                    ai_video.set_layer(1)
                    morph_video.set_layer(0)
                    ai_video.play()
                    morph_video.pause()
            except Exception as e:
                print(f"[monitor_morph] Error: {e}")
            time.sleep(0.1)

    threading.Thread(target=monitor_morph, daemon=True).start()

def play():
    morph_video.set_position(0)
    morph_video.set_layer(1)
    morph_video.play()
    threading.Thread(target=overlayx.start_fade_in, args=(fade_delay_ms, 5), daemon=True).start()

def stop():
    def aux():
        overlayx.start_fade_out(fade_delay_ms, 5)
        morph_video.pause()
        ai_video.pause()

    threading.Thread(target=aux, daemon=True).start()

def free():
    overlayx.free()

