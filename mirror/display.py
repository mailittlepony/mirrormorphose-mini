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

from overlayx import overlayx
import threading, subprocess, dbus, time, shared

fade_delay_ms = 800

def _get_dbus_interface(proc):
    bus = dbus.SessionBus()
    for service in bus.list_names():
        if service.startswith('org.mpris.MediaPlayer2.omxplayer'):
            try:
                obj = bus.get_object(service, '/org/mpris/MediaPlayer2')
                interface = dbus.Interface(obj, 'org.mpris.MediaPlayer2.Player')
                # Confirm it's the right process by checking PID
                pid_obj = dbus.Interface(obj, dbus_interface='org.freedesktop.DBus.Properties')
                pid = pid_obj.Get('org.mpris.MediaPlayer2.omxplayer', 'Pid')
                if pid == proc.pid:
                    return interface, pid_obj
            except:
                continue
    return None, None

def _goto_position_ms(video, timestamp):
    pass

def _set_layer(video, layer):
    props = video[1]
    props.Set('org.mpris.MediaPlayer2.omxplayer', 'Layer', dbus.Int32(layer))

def _start_omxplayer(video_path, layer):
    cmd = [
        "omxplayer"
        "--aspect-mode stretch",
        "--no-osd",
        "--no-keys"
        "--loop"
        f"--layer={layer}",
        "-o hdmi",
        video_path
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    interface, props = _get_dbus_interface(proc)

    interface.Pause()

    return (interface, props)

def init():
    global morph_video, ai_video, morph_video_duration, ai_video_duration
    overlayx.init()
    morph_video = _start_omxplayer(shared.MORPH_VIDEO_PATH, layer=1)
    morph_video_duration = morph_video[1].Get('org.mpris.MediaPlayer2.Player', 'Duration')
    ai_video = _start_omxplayer(shared.AI_VIDEO_PATH, layer=0)
    ai_video_duration = ai_video[1].Get('org.mpris.MediaPlayer2.Player', 'Duration')

def play():
    threading.Thread(overlayx.start_fade_in(fade_delay_ms, 5), daemon=True).start()
    _goto_position_ms(morph_video, 0)
    _set_layer(morph_video, 1)
    morph_video[0].Play()

def check_switch():
    if (morph_video[1].Get('org.mpris.MediaPlayer2.Player', 'Position') >= morph_video_duration - 10):
        _goto_position_ms(ai_video, 0)
        ai_video[0].Play()
        _set_layer(morph_video, 0)
        _set_layer(ai_video, 1)
        morph_video[0].Pause()

def stop():
    threading.Thread(overlayx.start_fade_out(fade_delay_ms, 5), daemon=True).start()
    ai_video[0].Pause()
    morph_video[0].Pause()

def free():
    overlayx.free()

# "omxplayer --win "0 0 1080 1920" --aspect-mode stretch --no-osd -o hdmi stream.h264"
