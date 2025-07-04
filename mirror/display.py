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
    _dbus_obj_path = "/org/mpris/MediaPlayer2"
    _dbus_base_interface = "org.mpris.MediaPlayer2"
    _user = getuser()
    _dbus_address_path = f"/tmp/omxplayerdbus.{_user}"
    _dbus_pid_path = f"{_dbus_address_path}.pid"
    _bus = None

    def __init__(self, path):
        self._dbus_service_name = f"{self._dbus_base_interface}.omxplayer{Video.instance_count}"
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
            if Video.instance_count == 0:
                self._wait_for_dbus(2)
            time.sleep(2)
            self.pause()

            self._duration = self.dbus_get_property("Duration", return_signature="x")[0]

            Video.instance_count += 1
        except Exception as e:
            raise RuntimeError(f"Failed to launch omxplayer or set environment: {e}")

    def play(self):
        self.dbus_call_method("Play")

    def pause(self):
        self.dbus_call_method("Pause")

    def stop(self):
        self.dbus_call_method("Stop")

    def set_position(self, ms):
        position = self.get_position()
        if position > 0:
            self.dbus_call_method("Seek", (-position,), "x")

    def seek(self, ms):
        return self.dbus_call_method("Seek", ( ms,), "x")

    def set_layer(self, layer):
        self.dbus_call_method("SetLayer", (layer,), "x")

    def get_playback_status(self):
        return self.dbus_call_method("PlaybackStatus")

    def get_position(self):
        return self.dbus_get_property("Position", return_signature="x")[0]

    def get_duration(self):
        return self._duration

    def quit(self):
        self.dbus_call_method("Quit", root=True)

    def dbus_call_method(self, method, args=None, arg_signature=None, return_signature=None, root=False):
        interface = "" if root else ".Player"

        reply = self._bus.con.call_sync(
            self._dbus_service_name,
            Video._dbus_obj_path,
            f"{Video._dbus_base_interface}{interface}",
            method,
            GLib.Variant(f"({arg_signature})", args) if args and arg_signature else None,
            GLib.VariantType.new(f"({return_signature})") if return_signature else None,
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )

        if reply and return_signature:
            return reply.unpack()
        
        return None

    def dbus_get_property(self, property, return_signature, root=False):
        interface = "" if root else ".Player"

        reply = self._bus.con.call_sync(
            self._dbus_service_name,
            Video._dbus_obj_path,
            "org.freedesktop.DBus.Properties",
            "Get",
            GLib.Variant("(ss)", (f"{Video._dbus_base_interface}{interface}", property)),
            GLib.VariantType.new(f"({return_signature})"),
            Gio.DBusCallFlags.NONE,
            -1,
            None
        )

        if reply and return_signature:
            return reply.unpack()

        return None

    def close(self):
        if self._omx_proc.poll() is None:
            try:
                self.quit()
            except Exception as e:
                print(f"Failed to quit omxplayer: {e}")

        if os.path.exists(Video._dbus_address_path):
            os.remove(Video._dbus_address_path)
        if os.path.exists(Video._dbus_pid_path):
            os.remove(Video._dbus_pid_path)

        Video.instance_count -= 1

    def _wait_for_dbus(self, timeout=1.0):
        start_time = time.monotonic()

        while time.monotonic() - start_time < timeout:
            if self._omx_proc.poll() is not None:
                stderr = self._omx_proc.stderr.read().decode()
                raise RuntimeError(f"omxplayer failed to start: '{stderr}'")
            try:
                with open(Video._dbus_address_path, "r") as f:
                    os.environ["DBUS_SESSION_BUS_ADDRESS"] = f.read().strip()

                Video._bus = SessionBus()
                return
            except Exception:
                time.sleep(0.1)

        raise RuntimeError("Timed out waiting for omxplayer D-Bus session.")

    def __del__(self):
        self.close()

fade_delay_ms = 2000

def init():
    overlayx.init("")

def load_videos():
    global morph_video, ai_video
    morph_video = Video(os.path.abspath(shared.MORPH_VIDEO_PATH))
    ai_video = Video(os.path.abspath(shared.AI_VIDEO_PATH))

    def monitor_morph():
        while True:
            if morph_video.get_duration() - morph_video.get_position() <= 200000:
                morph_video.set_position(0)
                morph_video.pause()
                ai_video.play()
                ai_video.set_position(0)
                ai_video.set_layer(1)
                morph_video.set_layer(0)
            time.sleep(0.1)

    threading.Thread(target=monitor_morph, daemon=True).start()

def play():
    ai_video.pause()
    ai_video.set_layer(0)
    morph_video.set_position(0)
    morph_video.set_layer(1)
    morph_video.play()
    threading.Thread(target=overlayx.start_fade_in, args=(fade_delay_ms, 5), daemon=True).start()

def stop():
    morph_video.pause()

    def fade_out():
        overlayx.start_fade_out(fade_delay_ms, 5)
        ai_video.pause()

    threading.Thread(target=fade_out, daemon=True).start()

def free():
    overlayx.free()
    ai_video.close()
    morph_video.close()

