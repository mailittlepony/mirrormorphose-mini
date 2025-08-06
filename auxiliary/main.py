#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2025 mailitruong <mailitruong@Mailis-MacBook-Pro.local>
#
# Distributed under terms of the MIT license.

import argparse
import logging
import os

from config import TEMP_DIR
from pipeline.fetch import fetch_assets, send_video, preload_videos
from pipeline.preprocess import remove_background_for_images
from pipeline.postprocess import reverse_video, concatenate_videos, add_vignette_video
from pipeline.monitor import monitor_gaze_stream
from pipeline.control import run_full_pipeline
from pipeline.morph_wrapper import generate_morph_specialized

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MirrorMini CLI")
    parser.add_argument(
        "--runway",
        type=str,
        default="true",
        help="Use Runway API if true. Set to false to skip.",
    )

    subparsers = parser.add_subparsers(dest="command", required=False)

    subparsers.add_parser("fetch", help="Fetch assets from camera and server")
    subparsers.add_parser("generate_morph", help="Generate morphing video")
    subparsers.add_parser("run_pipeline", help="Run the full morphing pipeline")
    subparsers.add_parser("monitor", help="Start gaze monitoring stream")
    subparsers.add_parser("load_videos", help="Preload videos on server")

    send_parser = subparsers.add_parser("send_video", help="Send video to server")
    send_parser.add_argument(
        "path",
        nargs="?",
        default=str(TEMP_DIR / "morph_video.mp4"),
        help="Path to the video file to send",
    )

    reverse_parser = subparsers.add_parser("reverse_video", help="Reverse a video")
    reverse_parser.add_argument(
        "path",
        nargs="?",
        default=str(TEMP_DIR / "video_generated.mp4"),
        help="Path to the video file to reverse",
    )

    concat_parser = subparsers.add_parser("concatenate_videos", help="Concatenate multiple videos")
    concat_parser.add_argument(
        "paths",
        nargs="*",
        default=[
            str(TEMP_DIR / "video_generated.mp4"),
            str(TEMP_DIR / "reversed_video.mp4"),
        ],
        help="Paths to videos to concatenate",
    )

    bg_parser = subparsers.add_parser("remove_background", help="Remove background from images")
    bg_parser.add_argument(
        "images",
        nargs="*",
        default=[
            str(TEMP_DIR / "capture.jpg"),
            str(TEMP_DIR / "user_image.jpg"),
        ],
        help="Paths to images to remove background from",
    )

    vignette_parser = subparsers.add_parser("add_vignette", help="Add vignette overlay to video")
    vignette_parser.add_argument(
        "input",
        nargs="?",
        default=str(TEMP_DIR / "concatenated_video.mp4"),
        help="Input video path",
    )
    vignette_parser.add_argument(
        "output",
        nargs="?",
        default=str(TEMP_DIR / "final_concatenated_video.mp4"),
        help="Output video path",
    )

    return parser


def main():
    os.makedirs(TEMP_DIR, exist_ok=True)
    parser = get_parser()
    args = parser.parse_args()

    use_runway = args.runway.lower() != "false"

    if args.command is None or args.command == "run_pipeline":
        run_full_pipeline(runway=use_runway)
    elif args.command == "fetch":
        fetch_assets()
    elif args.command == "generate_morph":
        generate_morph_specialized(runway=use_runway)
    elif args.command == "send_video":
        send_video(args.path)
    elif args.command == "reverse_video":
        reverse_video(args.path)
    elif args.command == "concatenate_videos":
        concatenate_videos(args.paths)
    elif args.command == "remove_background":
        remove_background_for_images(args.images)
    elif args.command == "add_vignette":
        add_vignette_video(args.input, args.output)
    elif args.command == "monitor":
        monitor_gaze_stream()
    elif args.command == "load_videos":
        preload_videos()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

