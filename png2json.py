#!/usr/bin/env python3
"""Convert a PNG image (created by json2png) back into JSON.

Reverses the encoding process: extracts RGB pixel data, undoes the
brightness shift, strips padding, and decodes the UTF-8 JSON content.
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image


def unshift(data: bytes, shift: int) -> bytes:
    """Right-shift each byte to reverse the brighten() transform."""
    if shift <= 0:
        return data
    return bytes(b >> shift for b in data)


def image_to_json(img: Image.Image, shift: int = 1) -> object:
    """
    Extract JSON data from an RGB image created by json2png.

    Reverses the pixel encoding: reads raw RGB bytes, undoes the
    brightness shift, strips trailing zero-padding, and parses JSON.
    Note: for non-ASCII content, use shift=0 in both json2png and
    png2json to guarantee a lossless round-trip.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")

    raw = img.tobytes()
    unshifted = unshift(raw, shift)

    text = unshifted.rstrip(b"\x00").decode("utf-8")
    return json.loads(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PNG image (from json2png) back to JSON.",
    )
    parser.add_argument("input", help="Path to the PNG image")
    parser.add_argument(
        "-o", "--output",
        help="Output JSON path (default: <input>.json)",
    )
    parser.add_argument(
        "--shift",
        type=int,
        default=1,
        help="Right-shift to reverse brightness (must match the shift used in json2png, default: 1)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level (default: 2, 0 = compact)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    img = Image.open(input_path)
    data = image_to_json(img, shift=args.shift)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".json")

    indent = args.indent if args.indent > 0 else None
    with output_path.open("w") as f:
        json.dump(data, f, indent=indent, sort_keys=True)
        f.write("\n")

    print(f"Saved {output_path}")


if __name__ == "__main__":
    main()
