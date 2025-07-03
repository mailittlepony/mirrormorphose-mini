#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from overlayx import overlayx
from pydbus import SessionBus
import threading, time, shared, subprocess

fade_delay_ms = 800

class Player:
    instance_count = 0

    def __init__(self, video_path):
        service_name = f"org.mpris.MediaPlayer2.omxplayer{Player.instance_count}"
        object_path = "/org/mpris/MediaPlayer2"

        cmd = [
            "omxplayer",
            "--loop",
            "--no-keys",
            "--no-osd",
            "-o", "hdmi",
            "--aspect-mode", "stretch",
            "--win", "0,0,1080,1920",
            f"--dbus_name={service_name}",
            video_path
        ]
        try:
            self.omxmplayer_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self._bus = SessionBus()
            self._omxplayer_dbus = self._bus.get(service_name, object_path)

            self.duration = self._omxplayer_dbus.Duration()

            Player.instance_count += 1
        except FileNotFoundError:
            print("omxplayer not found. Make sure it's installed.")
            self.omxmplayer_proc = None
        except Exception as e:
            print(f"Failed to start omxplayer: {e}")
            self.omxmplayer_proc = None

    def SetPosition(self, timestamp_ms):
        return self._omxplayer_dbus.SetPosition("/not/used", timestamp_ms)

    def __getattr__(self, name):
        return getattr(self._omxplayer_dbus, name)

    def __del__(self):
        Player.instance_count -= 1
        self._omxmplayer_proc.terminate()

def init():
    overlayx.init()

def load_videos():
    global morph_video, ai_video
    morph_video = Player(shared.MORPH_VIDEO_PATH)
    ai_video = Player(shared.AI_VIDEO_PATH)

    morph_video.Pause()
    ai_video.Pause()

    def monitor_morph():
        while True:
            try:
                if morph_video.PlaybackStatus() == "Playing" and \
                   morph_video.duration - morph_video.Position() < 20:
                    ai_video.SetPosition(0)
                    ai_video.SetLayer(1)
                    morph_video.SetLayer(0)
                    ai_video.Play()
                    morph_video.Pause()
            except Exception as e:
                print(f"[monitor_morph] Error: {e}")
            time.sleep(0.1)

    threading.Thread(target=monitor_morph, daemon=True).start()

def play():
    morph_video.SetPosition(0)
    morph_video.SetLayer(1)
    morph_video.Play()
    threading.Thread(target=overlayx.start_fade_in, args=(fade_delay_ms, 5), daemon=True).start()

def stop():
    def aux():
        overlayx.start_fade_out(fade_delay_ms, 5)
        morph_video.Pause()
        ai_video.Pause()

    threading.Thread(target=aux, daemon=True).start()

def free():
    overlayx.free()

