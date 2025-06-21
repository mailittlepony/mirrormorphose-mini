#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

"""
This script processes the image and removes the background
"""
import cv2
from rembg import remove, new_session
from PIL import Image, ImageFilter
import numpy as np
import io

def refine_edges(image_with_alpha):
    alpha_channel = np.array(image_with_alpha.convert("RGBA"))[:, :, 3]
    blurred_alpha = Image.fromarray(alpha_channel).filter(ImageFilter.GaussianBlur(4))
    image_with_alpha.putalpha(blurred_alpha)
    return image_with_alpha

def add_black_background(image_with_alpha):
    black_bg = Image.new("RGBA", image_with_alpha.size, (0, 0, 0, 255))
    black_bg.paste(image_with_alpha, (0, 0), image_with_alpha)
    return black_bg

def remove_background(input_path, output_path):
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    session = new_session("u2net_human_seg")
    output_bytes = remove(input_bytes, session=session)
    image = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

    refined = refine_edges(image)
    final_image = add_black_background(refined)

    final_image.save(output_path, format="PNG")

