#!/usr/bin/env python3
"""
Gemini Image Generation

Generate images using Google's Gemini models:
- Nano Banana (gemini-2.5-flash-image): Fast, efficient
- Nano Banana Pro (gemini-3-pro-image-preview): Higher quality

Usage:
    python gemini_imagegen.py "A cat wearing a top hat"
    python gemini_imagegen.py --model pro --aspect 16:9 "A sunset over mountains"
    python gemini_imagegen.py -f prompt.txt
    python gemini_imagegen.py -i photo.jpg "Convert to watercolor painting"
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image


MODELS = {
    'flash': 'gemini-2.5-flash-image',      # Nano Banana
    'pro': 'gemini-3-pro-image-preview',     # Nano Banana Pro
}

ASPECT_RATIOS = ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9']


def generate_image(
    prompt: str,
    model: str = 'flash',
    aspect_ratio: str = '1:1',
    output_dir: str = 'output',
    images: list[Path] | None = None,
) -> list[Path]:
    """
    Generate images from a text prompt using Gemini.

    Args:
        prompt: Text description of the image to generate
        model: 'flash' (Nano Banana) or 'pro' (Nano Banana Pro)
        aspect_ratio: Image aspect ratio (e.g., '1:1', '16:9')
        output_dir: Directory to save generated images
        images: Optional list of reference image paths (up to 14)

    Returns:
        List of paths to saved images
    """
    api_key = os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')
    if not api_key:
        raise ValueError(
            "GOOGLE_GENERATIVE_AI_API_KEY environment variable not set. "
            "Get a key at https://aistudio.google.com/apikey"
        )

    model_id = MODELS.get(model)
    if not model_id:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(MODELS.keys())}")

    if aspect_ratio not in ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect ratio. Choose from: {ASPECT_RATIOS}")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize client and generate
    client = genai.Client(api_key=api_key)

    print(f"Generating image with {model_id}...")
    print(f"  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  Aspect ratio: {aspect_ratio}")

    # Build contents list with prompt and optional reference images
    contents: list = [prompt]
    if images:
        if len(images) > 14:
            raise ValueError("Maximum 14 reference images allowed")
        print(f"  Reference images: {len(images)}")
        for img_path in images:
            if not img_path.exists():
                raise ValueError(f"Image not found: {img_path}")
            contents.append(Image.open(img_path))

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            )
        )
    )

    # Process response and save images
    saved_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_count = 0

    for part in response.parts:
        if part.text is not None:
            print(f"\nModel response: {part.text}")
        elif part.inline_data is not None:
            image = part.as_image()
            image_count += 1
            filename = output_path / f"gemini_{timestamp}_{image_count}.png"
            image.save(filename)
            saved_files.append(filename)
            print(f"  Saved: {filename}")

    if not saved_files:
        print("No images were generated. The model may have declined the request.")

    return saved_files


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
