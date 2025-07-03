#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

import ctypes
from os import path

lib = ctypes.CDLL(path.join(path.dirname(__file__), "liboverlayx.so"))

lib.overlay_init.restype = ctypes.c_int
lib.overlay_free.restype = ctypes.c_int

lib.overlay_start_fade_in.argtypes = [ctypes.c_int, ctypes.c_int]
lib.overlay_start_fade_in.restype = ctypes.c_int

lib.overlay_start_fade_out.argtypes = [ctypes.c_int, ctypes.c_int]
lib.overlay_start_fade_out.restype = ctypes.c_int


class OverlayError(Exception):
    pass


def init() -> None:
    """Initialize the overlay system."""
    if lib.overlay_init() != 0:
        raise OverlayError("Failed to initialize overlay.")


def start_fade_in(duration_ms: int, step: int) -> None:
    """Start a fade-in effect."""
    if lib.overlay_start_fade_in(duration_ms, step) != 0:
        raise OverlayError("Fade-in failed.")


def start_fade_out(duration_ms: int, step: int) -> None:
    """Start a fade-out effect."""
    if lib.overlay_start_fade_out(duration_ms, step) != 0:
        raise OverlayError("Fade-out failed.")

def free() -> None:
    """Free overlay resources."""
    if lib.overlay_free() != 0:
        raise OverlayError("Failed to free overlay resources.")

