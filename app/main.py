#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the MIT license.

import signal, sys, time, queue

from app.core import experience

from .server import server
from .core.camera import camera
from .core.display import display

running = True

FPS = 30

def handle_sigint(sig, frame):
    global running
    print("\n[INFO] Caught Ctrl+C, shutting down...")
    running = False

signal.signal(signal.SIGINT, handle_sigint)  # catch Ctrl+C (SIGINT)
signal.signal(signal.SIGTERM, handle_sigint) # catch kill (SIGTERM)

def run():
    print("Mirrormorphose-mini program v1.0")
    print("[INFO] Starting...")

    try:
        # Module initialization
        server.run_async()
        camera.init()
        display.init()

        # Gaze detection
        is_gaze = False
        last_change_time = 0
        debounce_seconds = 0.5
        gaze_stable_start = 0.0
        min_stable_duration = 2.0

        while running:
            start = time.time()

            # Start of Main Loop

            camera.capture(preview=False)
            camera.capture(preview=True)

            tracker = experience.get_tracker()
            if tracker:
                frame = camera.read(preview=True)
                state = tracker.get_eye_state(frame)
                # print(state)
                if state in ("straight", "down"):
                    if gaze_stable_start == 0.0:
                        # first frame of potential gaze
                        gaze_stable_start = start

                    # only start gaze if stable duration reached
                    if not is_gaze and (start - gaze_stable_start) >= min_stable_duration:
                        is_gaze = True
                        print("Gaze started")
                        display.play()
                else:
                    # reset stable timer if gaze lost or other state
                    gaze_stable_start = 0.0
                    if is_gaze and state != "blinking":
                        # normal debounce for ending gaze
                        if (start - last_change_time) >= debounce_seconds:
                            is_gaze = False
                            last_change_time = start
                            print("Gaze ended")
                            display.stop()

            # End of Main Loop

            elapsed = time.time() - start
            sleep_time = max(0, 1.0 / FPS - elapsed)
            time.sleep(sleep_time)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        server.close()
        camera.free()
        display.close()

        print("[INFO] Program exited cleanly.")
        sys.exit(0)

