#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitg <mailitg@maili-mba.local>
#
# Distributed under terms of the GPLv3 license.

import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def align_faces(
    images_dir: Path,
    target_path: Path,
    align_script_path: Path,
    aligned_dir: Path,
) -> bool:
    try:
        subprocess.run(
            [
                "python", str(align_script_path),
                "-images", str(images_dir),
                "-target", str(target_path),
                "-overlay",
                "-outdir", str(aligned_dir)
            ],
            check=True, capture_output=True, text=True
        )
        logger.info("Face alignment completed.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Face alignment failed: {e.stderr}")
        return False


def run_morph(morph_script_path: Path, morph_input_dir: Path, output_video_path: Path, transition_dur: float, pause_dur: float, fps: int) -> bool:
    try:
        subprocess.run(
            [
                "python", str(morph_script_path),
                "-morph",
                "-images", str(morph_input_dir),
                "-td", str(transition_dur),
                "-pd", str(pause_dur),
                "-fps", str(fps),
                "-out", str(output_video_path)
            ],
            check=True, capture_output=True, text=True
        )
        logger.info(f"Morphing video created at {output_video_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Morphing process failed: {e.stderr}")
        return False


