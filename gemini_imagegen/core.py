"""Core image generation functionality."""

import io
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from PIL.PngImagePlugin import PngInfo


# Load .env file if present
load_dotenv()


MODELS = {
    'flash': 'gemini-2.5-flash-image',      # Nano Banana
    'pro': 'gemini-3-pro-image-preview',     # Nano Banana Pro
}

ASPECT_RATIOS = ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9']
OUTPUT_FORMATS = ['png', 'webp']


def generate_image(
    prompt: str,
    model: str = 'flash',
    aspect_ratio: str = '1:1',
    output_dir: str = 'output',
    images: list[Path] | None = None,
    number: int = 1,
    temperature: float | None = None,
    output_format: str = 'png',
) -> list[Path]:
    """
    Generate images from a text prompt using Gemini.

    Args:
        prompt: Text description of the image to generate
        model: 'flash' (Nano Banana) or 'pro' (Nano Banana Pro)
        aspect_ratio: Image aspect ratio (e.g., '1:1', '16:9')
        output_dir: Directory to save generated images
        images: Optional list of reference image paths (up to 14)
        number: Number of images to generate (default: 1)
        temperature: Generation temperature 0.0-2.0 (default: model default)
        output_format: Output format 'png' or 'webp' (default: 'png')

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

    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Invalid output format. Choose from: {OUTPUT_FORMATS}")

    if number < 1:
        raise ValueError("Number of images must be at least 1")

    if temperature is not None and (temperature < 0.0 or temperature > 2.0):
        raise ValueError("Temperature must be between 0.0 and 2.0")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize client
    client = genai.Client(api_key=api_key)

    print(f"Generating {number} image(s) with {model_id}...")
    print(f"  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  Aspect ratio: {aspect_ratio}")
    if temperature is not None:
        print(f"  Temperature: {temperature}")

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

    # Build generation config
    gen_config = types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio,
        )
    )
    if temperature is not None:
        gen_config.temperature = temperature

    # Generate images
    saved_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    image_count = 0

    for i in range(number):
        if number > 1:
            print(f"\n  Generating image {i + 1}/{number}...")

        response = client.models.generate_content(
            model=model_id,
            contents=contents,
            config=gen_config,
        )

        for part in response.parts:
            if part.text is not None:
                print(f"\nModel response: {part.text}")
            elif part.inline_data is not None:
                gemini_image = part.as_image()
                image_count += 1

                # Convert Gemini Image to PIL Image
                pil_image = Image.open(io.BytesIO(gemini_image.image_bytes))

                # Determine extension and save
                ext = output_format
                filename = output_path / f"gemini_{timestamp}_{image_count}.{ext}"

                if output_format == 'png':
                    # Add prompt metadata to PNG
                    metadata = PngInfo()
                    metadata.add_text("prompt", prompt)
                    metadata.add_text("model", model_id)
                    metadata.add_text("aspect_ratio", aspect_ratio)
                    if temperature is not None:
                        metadata.add_text("temperature", str(temperature))
                    pil_image.save(filename, pnginfo=metadata)
                else:
                    # WEBP format
                    pil_image.save(filename, format='WEBP')

                saved_files.append(filename)
                print(f"  Saved: {filename}")

    if not saved_files:
        print("No images were generated. The model may have declined the request.")

    return saved_files
