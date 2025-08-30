#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright (C) 2025 Stanley Arnaud <stantonik@stantonik-mba.local>
#
# Distributed under terms of the MIT license.

from pathlib import Path
from typing import List, Optional, Union
import ffmpeg
import shutil
import requests

def resize_video(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    width: int,
    height: int,
    keep_aspect_ratio: bool = True
) -> None:
    """
    Resize a video to a target width and height using ffmpeg-python.
    If input and output paths are the same, the original file will be safely overwritten.

    Args:
        input_path (Union[str, Path]): Path to the input video.
        output_path (Union[str, Path]): Path to the output video.
        width (int): Target width.
        height (int): Target height.
        keep_aspect_ratio (bool): If True, preserves aspect ratio by scaling and padding.

    Raises:
        FileNotFoundError: If the input file does not exist.
        RuntimeError: If ffmpeg fails.
    """
    input_path = Path(input_path).expanduser().resolve()
    output_path = Path(output_path).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Determine if we need to overwrite
    if input_path == output_path:
        tmp_output = output_path.with_name(f"{output_path.stem}_tmp{output_path.suffix}")
    else:
        tmp_output = output_path

    stream = ffmpeg.input(str(input_path))

    if keep_aspect_ratio:
        # Scale while keeping aspect ratio, pad to fit exact width/height
        stream = (
            stream.filter('scale', width, height, force_original_aspect_ratio='decrease')
                  .filter('pad', width, height, '(ow-iw)/2', '(oh-ih)/2', color='black')
        )
    else:
        # Scale to exact width/height, ignoring aspect ratio
        stream = stream.filter('scale', width, height)

    try:
        stream.output(str(tmp_output), vcodec='libx264', pix_fmt='yuv420p').overwrite_output().run(quiet=True)
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}") from e

    # Overwrite original if needed
    if input_path == output_path:
        shutil.move(str(tmp_output), str(output_path))

def reverse_video(input: Union[str, Path], output: Optional[Union[str, Path]] = None) -> None:
    """
    Reverse a video using ffmpeg-python.

    Args:
        input (Union[str, Path]): Path to input video (str or Path).
        output (Optional[Union[str, Path]]): Path to output video (str or Path).
                                             If None or same as input, overwrite input.

    Raises:
        FileNotFoundError: If input file does not exist.
        RuntimeError: If ffmpeg fails.
    """
    input = Path(input).expanduser().resolve()
    output = Path(output).expanduser().resolve() if output is not None else None

    if not input.exists():
        raise FileNotFoundError(f"Input file not found: {input}")

    # Case: overwrite input
    overwrite_input = (output is None) or (output == input)
    if overwrite_input:
        output = input.with_name(f"{input.stem}_tmp{input.suffix}")

    try:
        (
            ffmpeg
            .input(str(input))
            .output(str(output), vf="reverse", af="areverse")
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}") from e

    # Replace input if overwriting
    if overwrite_input:
        shutil.move(str(output), str(input))

def concatenate_videos(inputs: List[Union[str, Path]],
                       output: Union[str, Path]) -> None:
    """
    Concatenate multiple videos into one using ffmpeg-python.

    Args:
        inputs (Union[str, Path, List[str|Path]]): Input video(s).
        output (Union[str, Path]): Output video (cannot be None).

    Raises:
        FileNotFoundError: If any input file does not exist.
        RuntimeError: If ffmpeg fails.
    """
    # Normalize to list of Path
    inputs = [Path(i).expanduser().resolve() for i in inputs]
    output = Path(output).expanduser().resolve()

    # Validate
    for inp in inputs:
        if not inp.exists():
            raise FileNotFoundError(f"Input file not found: {inp}")

    # Handle case where output == one of inputs
    overwrite_input = output in inputs
    if overwrite_input:
        tmp_output = output.with_name(f"{output.stem}_tmp{output.suffix}")
    else:
        tmp_output = output

    # Build input streams
    streams = [ffmpeg.input(str(inp)) for inp in inputs]

    try:
        (
            ffmpeg
            .concat(*streams, v=1, a=1)  # concatenate video+audio
            .output(str(tmp_output))
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}") from e

    # If overwriting, replace original
    if overwrite_input:
        shutil.move(str(tmp_output), str(output))

from pathlib import Path
from typing import Union, Optional
import ffmpeg


def extract_frame(video: Union[str, Path],
                  output: Union[str, Path],
                  frame_number: Optional[int] = None,
                  time_sec: Optional[float] = None) -> None:
    """
    Extract a single frame from a video, either by frame number or by time in seconds.

    Args:
        video (Union[str, Path]): Input video file.
        output (Union[str, Path]): Output image file (e.g., PNG or JPG).
        frame_number (Optional[int]): Frame index to extract (0-based).
        time_sec (Optional[float]): Time in seconds to extract frame.

    Raises:
        FileNotFoundError: If input video does not exist.
        ValueError: If neither frame_number nor time_sec is provided.
        RuntimeError: If ffmpeg fails.
    """
    video = Path(video).expanduser().resolve()
    output = Path(output).expanduser().resolve()

    if not video.exists():
        raise FileNotFoundError(f"Input video not found: {video}")

    if frame_number is None and time_sec is None:
        raise ValueError("Either frame_number or time_sec must be provided.")

    try:
        stream = ffmpeg.input(str(video))
        
        if time_sec is not None:
            # Seek to the closest keyframe before time_sec
            stream = ffmpeg.input(str(video), ss=time_sec)
        elif frame_number is not None:
            # Convert frame number to time using fps
            # Get fps first
            probe = ffmpeg.probe(str(video))
            fps = eval(probe['streams'][0]['r_frame_rate'])  # e.g. "30/1" -> 30.0
            time_sec = frame_number / fps
            stream = ffmpeg.input(str(video), ss=time_sec)
        
        (
            ffmpeg
            .output(stream, str(output), vframes=1)  # extract 1 frame
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}") from e

def trim_video(input: Union[str, Path],
               output: Union[str, Path],
               start_time: Optional[float] = None,
               end_time: Optional[float] = None) -> None:
    """
    Trim a video between start_time and end_time.

    Args:
        input (Union[str, Path]): Input video path.
        output (Union[str, Path]): Output video path.
        start_time (Optional[float]): Start time in seconds.
        end_time (Optional[float]): End time in seconds.

    Raises:
        FileNotFoundError: If input video does not exist.
        RuntimeError: If ffmpeg fails.
    """
    input = Path(input).expanduser().resolve()
    output = Path(output).expanduser().resolve()

    if not input.exists():
        raise FileNotFoundError(f"Input video not found: {input}")

    kwargs = {}
    if start_time is not None:
        kwargs['ss'] = start_time
    if end_time is not None:
        kwargs['to'] = end_time

    try:
        (
            ffmpeg
            .input(str(input), **kwargs)
            .output(str(output))
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode()}") from e

def download_video(url: str, output_path: Union[str, Path]) -> None:
    output_path = Path(output_path).expanduser().resolve()
    
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
