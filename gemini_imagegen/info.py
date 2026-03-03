"""Display metadata from generated images."""

import argparse
import sys

from PIL import Image


def main():
    parser = argparse.ArgumentParser(
        description='Display metadata from Gemini-generated images'
    )
    parser.add_argument(
        'image',
        help='Path to a PNG image file'
    )

    args = parser.parse_args()

    try:
        img = Image.open(args.image)
    except FileNotFoundError:
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error opening image: {e}", file=sys.stderr)
        sys.exit(1)

    metadata = img.info
    if not metadata:
        print("No metadata found.")
        sys.exit(0)

    for key, value in metadata.items():
        print(f"{key}: {value}")


if __name__ == '__main__':
    main()
