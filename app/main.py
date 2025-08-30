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

    # command_queue = queue.Queue()
    try:
        # Module initialization
        server.run_async()
        camera.init()
        display.init()
        tracker = experience.get_tracker()

        while running:
            start = time.time()

            # try:
            #     command = command_queue.get_nowait()
            # except queue.Empty:
            #     command = None

            # if command == "START_EXPERIENCE":
            #     tracker = experience.start()
            # elif command == "STOP_EXPERIENCE":
            #     experience.stop()

            # Start of Main Loop

            camera.capture(preview=False)
            camera.capture(preview=True)

            if tracker:
                state = tracker.get_eye_state(camera.read(preview=True))
                print(state)
                if (state == "straight"):
                    if not display.is_playing:
                        display.play()
                else:
                    if display.is_playing:
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

