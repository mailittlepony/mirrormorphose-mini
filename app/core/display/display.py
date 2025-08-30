#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the GPLv3 license.

import mpv, time, threading

import app.config as cfg

player = None
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
        idle=True,
        force_window=True,
        background="#000000"
    )

    # Loop the second video of the playlist
    @player.property_observer('time-remaining')
    def time_observer(_name, value):
        if player.playlist_pos_1 == len(player.playlist):
            if value and value <= 0.1:
                player.time_pos = 0

def load_videos() -> None:
    global player
    if player is None:
        raise RuntimeError("Display was not initialized.")

    player.playlist_append(str(cfg.MORPH_VIDEO_PATH))
    player.playlist_append(str(cfg.FINAL_GENERATED_VIDEO_PATH))
    print("Videos loaded succesfully")

def play() -> None:
    global player, is_playing
    if player is None:
        raise RuntimeError("Display was not initialized.")

    # if is_playing:
    #     return

    def worker(player):
        player.playlist_pos = 0
        player.wait_until_playing()
        _fade_transition(player, duration=1.0, direction=1, step=0.01)
    threading.Thread(target=worker, args=(player,), daemon=True).start()
    is_playing = True
    print("Video is playing...")

def stop() -> None:
    global player, is_playing
    if player is None:
        raise RuntimeError("Display was not initialized.")

    # if not is_playing:
    #     return

    def worker(player):
        global is_playing
        _fade_transition(player, duration=1.0, direction=-1, step=0.01, blocking=True)
        player.stop(keep_playlist=True)
        is_playing = False
        print("Video stopped.")

    threading.Thread(target=worker, args=(player,), daemon=True).start()

def close() -> None:
    global player
    if player is None:
        raise RuntimeError("Display was not initialized.")
    player.quit()
    print("Videos unloaded.")

def _fade_transition(player, duration: float, direction: int = 1, step: float = 0.05, blocking=False):
    fade = 0.0 if direction == 1 else 1.0
    dt = duration * step

    def aux():
        nonlocal fade
        while 0.0 <= fade <= 1.0:
            fade = max(0.0, min(1.0, fade))
            player.glsl_shader_opts=f"fade/fade={fade}"
            fade += direction * step
            time.sleep(dt)

    if blocking:
        aux()
    else:
        threading.Thread(target=aux, daemon=True).start()
