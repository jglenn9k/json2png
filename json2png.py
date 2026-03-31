#!/usr/bin/env python3
"""Convert any JSON file into a unique PNG image.

Each character's raw UTF-8 byte value drives the pixel colors directly.
Every 3 bytes become one RGB pixel. Really tired of looking at JSON files?
Get a fresh perspective with a little bit of color.
"""

import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image


def json_to_bytes(data: object) -> bytes:
    """Serialize JSON data to a deterministic byte stream."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pick_dimensions(pixel_count: int) -> tuple[int, int]:
    """Choose width x height that is roughly square and fits pixel_count exactly."""
    side = math.isqrt(pixel_count)
    if side * side == pixel_count:
        return side, side
    width = side + 1
    height = math.ceil(pixel_count / width)
    return width, height


def brighten(data: bytes, shift: int) -> bytes:
    """Left-shift each byte by *shift* bits, clamping at 255."""
    if shift <= 0:
        return data
    return bytes(min(b << shift, 255) for b in data)


def json_to_image(data: object, shift: int = 1) -> Image.Image:
    """
    Turn arbitrary JSON data into an RGB image.

    Each character's UTF-8 byte value maps directly to a color channel.
    Every 3 consecutive bytes become one RGB pixel. The image size is
    determined entirely by the JSON content — no padding or tiling.
    Byte values are left-shifted by *shift* bits to brighten colors.
    """
    raw = json_to_bytes(data)

    pixel_count = max(math.ceil(len(raw) / 3), 1)
    width, height = pick_dimensions(pixel_count)
    total_bytes = width * height * 3

    # Zero-pad only the bytes needed to complete the last pixel row
    pixel_data = brighten(raw.ljust(total_bytes, b"\x00"), shift)

    img = Image.frombytes("RGB", (width, height), pixel_data)
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert a JSON file to a PNG image.")
    parser.add_argument("input", help="Path to the JSON file")
    parser.add_argument(
        "-o", "--output",
        help="Output PNG path (default: <input>.png)",
    )
    parser.add_argument(
        "--shift",
        type=int,
        default=1,
        help="Left-shift each byte by N bits to brighten colors (default: 1, 0 = off)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with input_path.open("rb") as fb:
        header = fb.read(8)
    if header[:4] == b"\x89PNG":
        print(
            f"Error: {input_path} is a PNG image, not a JSON file.",
            file=sys.stderr,
        )
        sys.exit(1)

    with input_path.open() as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            print(f"Error: {input_path} is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)
        except UnicodeDecodeError:
            print(
                f"Error: {input_path} is not a text file (binary data detected).",
                file=sys.stderr,
            )
            sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".png")

    img = json_to_image(data, shift=args.shift)
    img.save(output_path, "PNG")
    print(f"Saved {output_path}  ({img.width}x{img.height}, {img.width * img.height} pixels)")


if __name__ == "__main__":
    main()
