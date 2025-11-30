"""Core image generation functionality."""

import os
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
