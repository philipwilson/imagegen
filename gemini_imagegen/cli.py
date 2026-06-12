"""Command-line interface for Gemini image generation."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import (
    ASPECT_RATIOS,
    MODELS,
    OUTPUT_FORMATS,
    PERSON_GENERATION_OPTIONS,
    generate_image,
)


def main():
    model_choices = list(MODELS.keys())
    parser = argparse.ArgumentParser(
        description='Generate images using Gemini or Imagen models',
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
  %(prog)s --model imagen "A robot on a skateboard"
  %(prog)s --model imagen-ultra --image-size 2K "High-res landscape"
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
        help='Reference image(s) for editing (Gemini only, max 14)'
    )
    parser.add_argument(
        '--model', '-m',
        choices=model_choices,
        default='flash',
        help='Model: flash, flash2, pro (Gemini) or imagen, imagen-fast, imagen-ultra (Imagen). Default: flash'
    )
    parser.add_argument(
        '--aspect', '-a',
        choices=ASPECT_RATIOS,
        default='1:1',
        help='Aspect ratio. Imagen supports: 1:1, 3:4, 4:3, 9:16, 16:9. Default: 1:1'
    )
    parser.add_argument(
        '--number', '-n',
        type=int,
        default=1,
        help='Number of images to generate (Imagen max: 4). Default: 1'
    )
    parser.add_argument(
        '--temperature', '-t',
        type=float,
        help='Generation temperature 0.0-2.0 (Gemini only)'
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
        '--person-generation',
        choices=PERSON_GENERATION_OPTIONS,
        help='Person generation policy (Imagen only): dont_allow, allow_adult, allow_all'
    )
    parser.add_argument(
        '--image-size',
        choices=['1K', '2K'],
        help='Output image size (Imagen only): 1K or 2K'
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
            person_generation=args.person_generation,
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
