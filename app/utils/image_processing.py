#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path
from rembg import remove, new_session
from typing import Optional, Union

def crop_face_contour(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    offset: int = 0
) -> None:
    """
    Detect the face in an image using MediaPipe and crop to the face contour.

    Args:
        input_path (Union[str, Path]): Path to the input image.
        output_path (Union[str, Path]): Path to save cropped image.
        offset (int): Number of pixels to expand the crop around the face.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If face cannot be detected.
    """
    input_path = Path(input_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load image
    image = cv2.imread(str(input_path))
    if image is None:
        raise RuntimeError(f"Failed to read image: {input_path}")

    # Convert to RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Initialize MediaPipe Face Mesh
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)

    results = face_mesh.process(image_rgb)
    face_mesh.close()

    if not results.multi_face_landmarks:
        raise RuntimeError("No face detected in the image.")

    landmarks = results.multi_face_landmarks[0].landmark

    h, w, _ = image.shape

    # Get bounding box of face contour
    xs = [int(landmark.x * w) for landmark in landmarks]
    ys = [int(landmark.y * h) for landmark in landmarks]

    x_min = max(min(xs) - offset, 0)
    x_max = min(max(xs) + offset, w)
    y_min = max(min(ys) - offset, 0)
    y_max = min(max(ys) + offset, h)

    # Crop and save
    cropped = image[y_min:y_max, x_min:x_max]
    cv2.imwrite(str(output_path), cropped)

def resize_and_crop_to_match(source_img: np.ndarray, target_img: np.ndarray) -> np.ndarray:
    """
    Resize the source image to fully cover the target image dimensions,
    then crop it around the center to match the target size.

    Args:
        source_img (np.ndarray): Source image as a NumPy array (H x W x C, BGR).
        target_img (np.ndarray): Target image as a NumPy array (H x W x C, BGR).

    Returns:
        np.ndarray: Resized and center-cropped source image matching target dimensions.

    Raises:
        ValueError: If input images are None or not 2D/3D arrays.
    """
    # Validate input
    if source_img is None or target_img is None:
        raise ValueError("Source or target image is None.")
    if len(source_img.shape) not in (2, 3) or len(target_img.shape) not in (2, 3):
        raise ValueError("Input images must be 2D (grayscale) or 3D (color) arrays.")

    src_h, src_w = source_img.shape[:2]
    tgt_h, tgt_w = target_img.shape[:2]

    # Compute scaling factor to cover target fully
    scale = max(tgt_w / src_w, tgt_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)

    # Resize the source image
    resized = cv2.resize(source_img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Compute center coordinates for cropping
    center_x = new_w // 2
    center_y = new_h // 2

    # Compute top-left corner of the crop
    crop_x = max(0, center_x - tgt_w // 2)
    crop_y = max(0, center_y - tgt_h // 2)

    # Ensure crop does not go out of bounds
    crop_x = min(crop_x, new_w - tgt_w)
    crop_y = min(crop_y, new_h - tgt_h)

    # Crop the resized image to match target size
    cropped = resized[crop_y:crop_y + tgt_h, crop_x:crop_x + tgt_w]

    return cropped

def refine_edges(image_rgba: np.ndarray, blur_radius: int = 4) -> np.ndarray:
    """
    Smooth the alpha channel of an RGBA image using Gaussian blur.

    Args:
        image_rgba (np.ndarray): Input image (H x W x 4, RGBA)
        blur_radius (int): Gaussian blur radius

    Returns:
        np.ndarray: RGBA image with smoothed alpha channel

    Raises:
        ValueError: If input image is None or not RGBA
    """
    if image_rgba is None or image_rgba.shape[2] != 4:
        raise ValueError("Input image must be RGBA with 4 channels.")

    # Extract alpha channel
    alpha = image_rgba[:, :, 3]

    # Apply Gaussian blur to smooth edges
    alpha_blurred = cv2.GaussianBlur(alpha, (0, 0), sigmaX=blur_radius, sigmaY=blur_radius)

    # Replace alpha channel
    result = image_rgba.copy()
    result[:, :, 3] = alpha_blurred
    return result


def add_black_background(image_rgba: np.ndarray) -> np.ndarray:
    """
    Place an RGBA image over a solid black background.

    Args:
        image_rgba (np.ndarray): Input image (H x W x 4)

    Returns:
        np.ndarray: Image with black background (H x W x 3, BGR)

    Raises:
        ValueError: If input image is not RGBA
    """
    if image_rgba is None or image_rgba.shape[2] != 4:
        raise ValueError("Input image must be RGBA with 4 channels.")

    # Split channels
    b, g, r, a = cv2.split(image_rgba)

    # Prepare black background
    black_bg = np.zeros_like(image_rgba[:, :, :3], dtype=np.uint8)

    # Alpha blending: out = fg*alpha + bg*(1-alpha)
    alpha_normalized = a.astype(np.float32) / 255.0
    for c in range(3):
        black_bg[:, :, c] = (r if c == 2 else g if c == 1 else b) * alpha_normalized + black_bg[:, :, c] * (1 - alpha_normalized)

    return black_bg

def remove_background(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    session: Optional[object] = None
) -> None:
    """
    Remove background from an image using rembg, refine edges, and apply black background.

    Args:
        input_path (Union[str, Path]): Path to input image.
        output_path (Union[str, Path]): Path to save processed image.
        session (Optional[object]): Optional rembg session.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If rembg fails or image cannot be decoded.
        ValueError: If image format is invalid.
    """
    input_path = Path(input_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {input_path}")

    # Read input image as bytes
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    # Create rembg session if not provided
    if session is None:
        session = new_session("u2net_human_seg")

    # Remove background
    output_bytes = remove(input_bytes, session=session)

    # Convert bytes to RGBA NumPy array
    arr = np.frombuffer(output_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)  # Keep alpha if exists
    if image is None:
        raise RuntimeError("Failed to decode image from rembg output.")

    # Ensure RGBA
    if image.ndim == 2:
        # Grayscale -> BGRA
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    elif image.shape[2] == 3:
        # BGR -> BGRA
        image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Refine edges
    refined = refine_edges(image)

    # Apply black background
    final_image = add_black_background(refined)

    # Save result as PNG
    cv2.imwrite(str(output_path), final_image)
