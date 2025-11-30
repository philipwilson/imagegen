"""Command-line interface for Gemini image generation."""

import argparse
import sys
from pathlib import Path

from .core import ASPECT_RATIOS, generate_image


def main():
    parser = argparse.ArgumentParser(
        description='Generate images using Gemini Nano Banana models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "A serene Japanese garden at sunset"
  %(prog)s --model pro "A cyberpunk cityscape"
  %(prog)s --aspect 16:9 "Mountain landscape"
  %(prog)s -f prompt.txt --model pro
  %(prog)s -i photo.jpg "Convert to watercolor painting"
  %(prog)s -i ref1.jpg -i ref2.jpg "Combine these styles"
        """
    )
    parser.add_argument(
        'prompt',
        nargs='?',
        help='Text description of the image to generate'
    )
    parser.add_argument(
        '--file', '-f',
        type=Path,
        help='Read prompt from a file'
    )
    parser.add_argument(
        '--image', '-i',
        type=Path,
        action='append',
        dest='images',
        help='Reference image(s) to include. Can be specified multiple times (max 14)'
    )
    parser.add_argument(
        '--model', '-m',
        choices=['flash', 'pro'],
        default='flash',
        help='Model to use: flash (Nano Banana) or pro (Nano Banana Pro). Default: flash'
    )
    parser.add_argument(
        '--aspect', '-a',
        choices=ASPECT_RATIOS,
        default='1:1',
        help='Aspect ratio. Default: 1:1'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory. Default: output'
    )

    args = parser.parse_args()

    # Determine the prompt source
    if args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        prompt = args.file.read_text().strip()
        if not prompt:
            print(f"Error: File is empty: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.error("Either provide a prompt or use --file/-f to read from a file")

    try:
        saved_files = generate_image(
            prompt=prompt,
            model=args.model,
            aspect_ratio=args.aspect,
            output_dir=args.output,
            images=args.images,
        )

        if saved_files:
            print(f"\nGenerated {len(saved_files)} image(s)")
            sys.exit(0)
        else:
            sys.exit(1)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error generating image: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
