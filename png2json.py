#!/usr/bin/env python3
"""Convert a PNG image back into JSON (or raw text).

Works on any PNG: images created by json2png round-trip back to
structured JSON; arbitrary images produce a raw text dump wrapped
in a JSON string.
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


def image_to_text(img: Image.Image, shift: int = 1) -> str:
    """
    Extract text from an RGB image's pixel data.

    Reads raw RGB bytes, undoes the brightness shift, strips trailing
    zero-padding, and decodes to a string.  Uses latin-1 as a fallback
    so every possible byte sequence produces output.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")

    raw = img.tobytes()
    unshifted = unshift(raw, shift)
    stripped = unshifted.rstrip(b"\x00")

    if not stripped:
        return ""

    try:
        return stripped.decode("utf-8")
    except UnicodeDecodeError:
        return stripped.decode("latin-1")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PNG image back to JSON (or raw text).",
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

    try:
        img = Image.open(input_path)
    except Exception as exc:
        print(f"Error: cannot open {input_path} as an image: {exc}", file=sys.stderr)
        sys.exit(1)

    text = image_to_text(img, shift=args.shift)

    structured = None
    try:
        structured = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    output_path = Path(args.output) if args.output else input_path.with_suffix(".json")
    indent = args.indent if args.indent > 0 else None

    with output_path.open("w") as f:
        if structured is not None:
            json.dump(structured, f, indent=indent, sort_keys=True)
        else:
            json.dump({"invalid_json": text}, f, indent=indent, ensure_ascii=False)
        f.write("\n")

    kind = "structured JSON" if structured is not None else "raw text"
    print(f"Saved {output_path}  ({kind}, {len(text)} chars)")


if __name__ == "__main__":
    main()
