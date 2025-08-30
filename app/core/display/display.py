#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the GPLv3 license.

import mpv, time, threading

import app.config as cfg

player = None
is_fade_out = False
is_playing = False

def init() -> None:
    global player
    player = mpv.MPV(
        vo="gpu-next",
        gpu_context="drm",
        hwdec="rkmpp-copy",
        glsl_shaders=':'.join([str(p) for p in cfg.SHADER_DIR.rglob("*.glsl")]),
        log_handler=print,
        loglevel='fatal',
        keep_open=True,
        idle=True
    )

    @player.property_observer('time-remaining')
    def time_observer(_name, value):
        global is_fade_out
        if player.playlist_pos_1 == len(player.playlist):
            if value and value <= 1 and is_fade_out == False:
                is_fade_out = True
                _fade_transition(player, duration=1.0, direction=-1, step=0.01)
        else:
            is_fade_out = False

def load_videos() -> None:
    global player
    if player is None:
        raise RuntimeError("Display was not initialized.")

    player.playlist_append(cfg.MORPH_VIDEO_PATH)
    player.playlist_append(cfg.FINAL_GENERATED_VIDEO_PATH)

def play() -> None:
    global player, is_playing
    if player is None:
        raise RuntimeError("Display was not initialized.")

    def worker(player):
        player.playlist_pos = 0
        player.wait_until_playing()
        _fade_transition(player, duration=1.0, direction=1, step=0.01)
    threading.Thread(target=worker, args=(player,), daemon=True)
    is_playing = True

def stop() -> None:
    global player, is_playing
    if player is None:
        raise RuntimeError("Display was not initialized.")
    player.stop(keep_playlist=True)
    is_playing = False

def close() -> None:
    global player
    if player is None:
        raise RuntimeError("Display was not initialized.")
    player.quit()

def _fade_transition(player, duration: float, direction: int = 1, step: float = 0.05):
    fade = 0.0 if direction == 1 else 1.0
    dt = duration * step

    def aux():
        nonlocal fade
        while 0.0 <= fade <= 1.0:
            fade = max(0.0, min(1.0, fade))
            player.glsl_shader_opts=f"fade/fade={fade}"
            fade += direction * step
            time.sleep(dt)

    threading.Thread(target=aux, daemon=True).start()
