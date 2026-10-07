"""Command-line interface for Gemini image generation."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import (
    ASPECT_RATIOS,
    DEFAULT_MODEL,
    EXTREME_ASPECT_RATIOS,
    IMAGE_SIZES,
    MODEL_SPECS,
    OUTPUT_FORMATS,
    generate_image,
    models_supporting,
)


def _model_help() -> str:
    lines = ', '.join(f"{alias} ({spec.description})" for alias, spec in MODEL_SPECS.items())
    return f"Model: {lines}. Default: {DEFAULT_MODEL}"


def main():
    model_choices = list(MODEL_SPECS)
    parser = argparse.ArgumentParser(
        description='Generate images using Gemini (Nano Banana) image models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "A serene Japanese garden at sunset"
  %(prog)s --model pro "A cyberpunk cityscape"
  %(prog)s --aspect 16:9 "Mountain landscape"
  %(prog)s -f prompt.txt --model pro
  %(prog)s -i photo.jpg "Convert to watercolor painting"
  %(prog)s -n 4 "Generate four variations"
  %(prog)s -t 1.5 "More creative output"
  %(prog)s --format webp "Save as WebP"
  %(prog)s --model nb21 --image-size 4K "Ultra high-res poster"
  %(prog)s --model nb21 --aspect 8:1 --image-size 2K "Panoramic skyline banner"
        """
    )
    parser.add_argument(
        '--version', '-V',
        action='version',
        version=f'%(prog)s {__version__}'
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
        help='Reference image(s) for editing (max 14)'
    )
    parser.add_argument(
        '--model', '-m',
        choices=model_choices,
        default=DEFAULT_MODEL,
        help=_model_help()
    )
    parser.add_argument(
        '--aspect', '-a',
        choices=ASPECT_RATIOS,
        default='1:1',
        help=(
            'Aspect ratio. Default: 1:1. Panoramic ratios '
            f"({', '.join(EXTREME_ASPECT_RATIOS)}) are supported by: "
            f"{', '.join(models_supporting(lambda s: EXTREME_ASPECT_RATIOS[0] in s.aspect_ratios))}"
        )
    )
    parser.add_argument(
        '--number', '-n',
        type=int,
        default=1,
        help='Number of images to generate. Default: 1'
    )
    parser.add_argument(
        '--temperature', '-t',
        type=float,
        help='Generation temperature 0.0-2.0'
    )
    parser.add_argument(
        '--format',
        choices=OUTPUT_FORMATS,
        default='png',
        help='Output format. Default: png'
    )
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='Output directory. Default: output'
    )
    parser.add_argument(
        '--image-size',
        choices=IMAGE_SIZES,
        help=(
            f"Output image size. 4K is supported by: "
            f"{', '.join(models_supporting(lambda s: '4K' in s.image_sizes))}; "
            f"not supported by: {', '.join(models_supporting(lambda s: not s.image_sizes))}"
        )
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
            number=args.number,
            temperature=args.temperature,
            output_format=args.format,
            image_size=args.image_size,
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
