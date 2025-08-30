#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 ubuntu <ubuntu@mirrormini>
#
# Distributed under terms of the MIT license.

import logging, io
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session
from pathlib import Path
from typing import Union, Sequence, Optional

from ..camera.gaze_tracker.gaze_tracker import GazeTracker


logger = logging.getLogger(__name__)

def crop_face_contour(
    frame: np.ndarray, 
    tracker: GazeTracker, 
    x_offset: int = 0, 
    y_offset: int = 0
) -> Optional[np.ndarray]:
    """
    Crop the face from an image using Mediapipe face contour landmarks.

    Args:
        frame: The image as a numpy array.
        tracker: Mediapipe tracker object with select_landmarks method.
        x_offset: Horizontal padding; positive to grow, negative to shrink.
        y_offset: Vertical padding; positive to grow, negative to shrink.

    Returns:
        Cropped face as a numpy array, or None if no landmarks detected.
    """

# Face contour landmarks
    FACE_CONTOUR_LMK = [
        10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 
        361, 288, 397, 365, 379, 378, 400, 377, 152, 148,
        176, 149, 150, 136, 172, 58, 132, 93, 234, 127,
        162, 21, 54, 103, 67, 109
    ]

    landmarks = tracker.select_landmarks(FACE_CONTOUR_LMK)
    if not landmarks or len(landmarks) == 0:
        return None

    points = np.array([[int(p[0]), int(p[1])] for p in landmarks])

    # Bounding box of face contour
    x_min = np.min(points[:, 0]) - x_offset
    y_min = np.min(points[:, 1]) - y_offset
    x_max = np.max(points[:, 0]) + x_offset
    y_max = np.max(points[:, 1]) + y_offset

    # Clamp values to image size
    x_min = max(x_min, 0)
    y_min = max(y_min, 0)
    x_max = min(x_max, frame.shape[1])
    y_max = min(y_max, frame.shape[0])

    cropped_face = frame[y_min:y_max, x_min:x_max]
    return cropped_face

def refine_edges(image_with_alpha: Image.Image) -> Image.Image:
    """
    Applies Gaussian blur to the alpha channel for smoother edges.
    """
    alpha_channel = np.array(image_with_alpha.convert("RGBA"))[:, :, 3]
    blurred_alpha = Image.fromarray(alpha_channel).filter(ImageFilter.GaussianBlur(4))
    image_with_alpha.putalpha(blurred_alpha)
    return image_with_alpha

def add_black_background(image_with_alpha: Image.Image) -> Image.Image:
    black_bg = Image.new("RGBA", image_with_alpha.size, (0, 0, 0, 255))
    black_bg.paste(image_with_alpha, (0, 0), image_with_alpha)
    return black_bg


def remove_background(
    inputs: Union[Path, Sequence[Path]],
    output: Path
) -> bool:
    inputs = [inputs] if isinstance(inputs, Path) else list(inputs)
    if len(inputs) > 1:
        output.mkdir(parents=True, exist_ok=True)

    ok = True
    for inp in inputs:
        try:
            img_bytes = Path(inp).read_bytes()
            session = new_session("u2net_human_seg")
            out_bytes = remove(img_bytes, session=session)
            image = Image.open(io.BytesIO(out_bytes)).convert("RGBA")
            final = add_black_background(refine_edges(image))

            save_path = output if len(inputs) == 1 else output / f"{inp.stem}_processed.png"
            final.save(save_path, "PNG")
        except Exception as e:
            logger.error(f"Failed on {inp}: {e}")
            ok = False
    return ok
