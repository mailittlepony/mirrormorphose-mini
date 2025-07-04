#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the GPLv3 license.

from overlayx import overlayx
from pydbus import SessionBus
from gi.repository import GLib, Gio
from getpass import getuser
import os, subprocess, time, threading, shared

class Video:
    instance_count = 0

    def __init__(self, path):
        self._dbus_obj_path = "/org/mpris/MediaPlayer2"
        self._dbus_base_interface = "org.mpris.MediaPlayer2"
        self._dbus_service_name = f"{self._dbus_base_interface}.omxplayer{Video.instance_count}"
        self._user = getuser()
        self._dbus_address_path = f"/tmp/omxplayerdbus.{self._user}"
        self._dbus_pid_path = f"{self._dbus_address_path}.pid"
        self._video_path = path

        cmd = [
            "omxplayer",
            "--loop",
            "--no-keys",
            "--no-osd",
            "-o", "hdmi",
            "--aspect-mode", "stretch",
            "--win", "0,0,1080,1920",
            f"--dbus_name={self._dbus_service_name}",
            path
        ]

        try:
            self._omx_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._wait_for_dbus(2)
            self.pause()

            # self._duration = self.send_command("Player", "Duration")

            Video.instance_count += 1
        except Exception as e:
            raise RuntimeError(f"Failed to launch omxplayer or set environment: {e}")

    def play(self):
        self.send_command("Play")

    def pause(self):
        self.send_command("Pause")

    def stop(self):
        self.send_command("Stop")

    def set_position(self, ms):
        return self.send_command("SetPosition", ("/not/used", ms,), "sx")

    def set_layer(self, layer):
        self.send_command("SetLayer", (layer,), "x")

    def get_playback_status(self):
        return self.send_command("PlaybackStatus")

    def get_position(self):
        return self.send_command("Posititon")

    def get_duration(self):
        return self._duration

    def quit(self):
        self.send_command("Quit", root=True)

    def send_command(self, method, args=None, signature="()", root=False):

        interface = "" if root else ".Player"

        return self._bus.con.call_sync(
            self._dbus_service_name,
            self._dbus_obj_path,
            f"{self._dbus_base_interface}{interface}",
            method,
            None,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )

    def close(self):
        if os.path.exists(self._dbus_address_path):
            os.remove(self._dbus_address_path)
        if os.path.exists(self._dbus_pid_path):
            os.remove(self._dbus_pid_path)

        try:
            self.quit()
        except Exception as e:
            print(f"Failed to quit omxplayer: {e}")

        Video.instance_count -= 1

    def _wait_for_dbus(self, timeout=1.0):
        start_time = time.monotonic()

        while time.monotonic() - start_time < timeout:
            if self._omx_proc.poll() is not None:
                stderr = self._omx_proc.stderr.read().decode()
                raise RuntimeError(f"omxplayer failed to start: '{stderr}'")
            try:
                with open(self._dbus_pid_path, "r") as f:
                    os.environ["DBUS_SESSION_BUS_PID"] = f.read().strip()

                with open(self._dbus_address_path, "r") as f:
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = f.read().strip()

                self._bus = SessionBus()
                return
            except Exception:
                time.sleep(0.1)

        raise RuntimeError("Timed out waiting for omxplayer D-Bus session.")

    def __del__(self):
        self.close()

fade_delay_ms = 800

def init():
    overlayx.init()

def load_videos():
    global morph_video
    path = os.path.abspath(os.path.expanduser("~/generated_video.mp4"))
    morph_video = Video(path)

    morph_video.pause()

def play():
    morph_video.set_position(0)
    morph_video.set_layer(1)
    morph_video.play()
    threading.Thread(target=overlayx.start_fade_in, args=(fade_delay_ms, 5), daemon=True).start()

def free():
    overlayx.free()

