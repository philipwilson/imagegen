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


GEMINI_MODELS = {
    'flash': 'gemini-2.5-flash-image',              # Nano Banana
    'flash2': 'gemini-3.1-flash-image-preview',     # Nano Banana Flash 3.1
    'pro': 'gemini-3-pro-image-preview',             # Nano Banana Pro
}

IMAGEN_MODELS = {
    'imagen': 'imagen-4.0-generate-001',             # Imagen 4 Standard
    'imagen-fast': 'imagen-4.0-fast-generate-001',   # Imagen 4 Fast
    'imagen-ultra': 'imagen-4.0-ultra-generate-001', # Imagen 4 Ultra
}

MODELS = {**GEMINI_MODELS, **IMAGEN_MODELS}

ASPECT_RATIOS = ['1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9']
IMAGEN_ASPECT_RATIOS = ['1:1', '3:4', '4:3', '9:16', '16:9']
OUTPUT_FORMATS = ['png', 'webp']
PERSON_GENERATION_OPTIONS = ['dont_allow', 'allow_adult', 'allow_all']


def _save_image(
    pil_image: Image.Image,
    filename: Path,
    output_format: str,
    prompt: str,
    model_id: str,
    aspect_ratio: str,
    temperature: float | None = None,
) -> None:
    """Save a PIL image with optional PNG metadata."""
    if output_format == 'png':
        metadata = PngInfo()
        metadata.add_text("prompt", prompt)
        metadata.add_text("model", model_id)
        metadata.add_text("aspect_ratio", aspect_ratio)
        if temperature is not None:
            metadata.add_text("temperature", str(temperature))
        pil_image.save(filename, pnginfo=metadata)
    else:
        pil_image.save(filename, format='WEBP')


def _create_client() -> genai.Client:
    """
    Create a Gemini client using the first available auth method:

    1. API key from GOOGLE_GENERATIVE_AI_API_KEY (Gemini Developer API),
       unless GOOGLE_GENAI_USE_VERTEXAI is set to force Vertex AI.
    2. Application Default Credentials via the Vertex AI backend
       (set up with `gcloud auth application-default login`).
    """
    use_vertex = os.environ.get('GOOGLE_GENAI_USE_VERTEXAI', '').lower() in ('true', '1', 'yes')
    api_key = os.environ.get('GOOGLE_GENERATIVE_AI_API_KEY')

    if api_key and not use_vertex:
        return genai.Client(api_key=api_key)

    project = os.environ.get('GOOGLE_CLOUD_PROJECT')
    location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'global')

    try:
        import google.auth
        import google.auth.exceptions

        credentials, adc_project = google.auth.default()
    except google.auth.exceptions.DefaultCredentialsError:
        raise ValueError(
            "No credentials found. Either set GOOGLE_GENERATIVE_AI_API_KEY "
            "(get a key at https://aistudio.google.com/apikey) or run "
            "`gcloud auth application-default login` to use Application "
            "Default Credentials."
        )

    project = project or adc_project
    if not project:
        raise ValueError(
            "Application Default Credentials found, but no project is set. "
            "Set GOOGLE_CLOUD_PROJECT or run "
            "`gcloud auth application-default set-quota-project PROJECT_ID`."
        )

    return genai.Client(
        vertexai=True, project=project, location=location, credentials=credentials
    )


def generate_image(
    prompt: str,
    model: str = 'flash',
    aspect_ratio: str = '1:1',
    output_dir: str = 'output',
    images: list[Path] | None = None,
    number: int = 1,
    temperature: float | None = None,
    output_format: str = 'png',
    person_generation: str | None = None,
    image_size: str | None = None,
) -> list[Path]:
    """
    Generate images from a text prompt using Gemini or Imagen.

    Args:
        prompt: Text description of the image to generate
        model: Model alias (e.g., 'flash', 'pro', 'imagen', 'imagen-ultra')
        aspect_ratio: Image aspect ratio (e.g., '1:1', '16:9')
        output_dir: Directory to save generated images
        images: Optional list of reference image paths (up to 14, Gemini only)
        number: Number of images to generate (default: 1)
        temperature: Generation temperature 0.0-2.0 (Gemini only)
        output_format: Output format 'png' or 'webp' (default: 'png')
        person_generation: Person generation policy (Imagen only)
        image_size: Output image size '1K' or '2K' (Imagen only)

    Returns:
        List of paths to saved images
    """
    client = _create_client()

    model_id = MODELS.get(model)
    if not model_id:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(MODELS.keys())}")

    is_imagen = model in IMAGEN_MODELS

    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Invalid output format. Choose from: {OUTPUT_FORMATS}")

    if number < 1:
        raise ValueError("Number of images must be at least 1")

    # Validate aspect ratio against model-specific options
    if is_imagen:
        if aspect_ratio not in IMAGEN_ASPECT_RATIOS:
            raise ValueError(f"Invalid aspect ratio for Imagen. Choose from: {IMAGEN_ASPECT_RATIOS}")
    else:
        if aspect_ratio not in ASPECT_RATIOS:
            raise ValueError(f"Invalid aspect ratio. Choose from: {ASPECT_RATIOS}")

    # Validate model-specific options
    if is_imagen:
        if images:
            raise ValueError("Reference images are not supported with Imagen models")
        if temperature is not None:
            raise ValueError("Temperature is not supported with Imagen models")
        if number > 4:
            raise ValueError("Imagen supports a maximum of 4 images per request")
        if person_generation and person_generation not in PERSON_GENERATION_OPTIONS:
            raise ValueError(f"Invalid person_generation. Choose from: {PERSON_GENERATION_OPTIONS}")
        if image_size and image_size not in ('1K', '2K'):
            raise ValueError("Invalid image_size. Choose from: 1K, 2K")
    else:
        if person_generation is not None:
            raise ValueError("--person-generation is only supported with Imagen models")
        if image_size is not None:
            raise ValueError("--image-size is only supported with Imagen models")
        if temperature is not None and (temperature < 0.0 or temperature > 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Generating {number} image(s)...")
    print(f"  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  Model: {model_id}")
    print(f"  Aspect ratio: {aspect_ratio}")
    if temperature is not None:
        print(f"  Temperature: {temperature}")
    if image_size:
        print(f"  Image size: {image_size}")
    if person_generation:
        print(f"  Person generation: {person_generation}")

    saved_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if is_imagen:
        saved_files = _generate_imagen(
            client, model_id, prompt, number, aspect_ratio,
            person_generation, image_size, output_format,
            output_path, timestamp,
        )
    else:
        saved_files = _generate_gemini(
            client, model_id, prompt, number, aspect_ratio,
            temperature, output_format, images,
            output_path, timestamp,
        )

    if not saved_files:
        print("No images were generated. The model may have declined the request.")

    return saved_files


def _generate_gemini(
    client: genai.Client,
    model_id: str,
    prompt: str,
    number: int,
    aspect_ratio: str,
    temperature: float | None,
    output_format: str,
    images: list[Path] | None,
    output_path: Path,
    timestamp: str,
) -> list[Path]:
    """Generate images using Gemini models."""
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

    saved_files = []
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

                pil_image = Image.open(io.BytesIO(gemini_image.image_bytes))
                ext = output_format
                filename = output_path / f"gemini_{timestamp}_{image_count}.{ext}"

                _save_image(pil_image, filename, output_format, prompt,
                            model_id, aspect_ratio, temperature)
                saved_files.append(filename)
                print(f"  Saved: {filename}")

    return saved_files


def _generate_imagen(
    client: genai.Client,
    model_id: str,
    prompt: str,
    number: int,
    aspect_ratio: str,
    person_generation: str | None,
    image_size: str | None,
    output_format: str,
    output_path: Path,
    timestamp: str,
) -> list[Path]:
    """Generate images using Imagen models."""
    config = types.GenerateImagesConfig(
        numberOfImages=number,
        aspectRatio=aspect_ratio,
        outputMimeType=f"image/{output_format}",
    )
    if person_generation:
        config.personGeneration = person_generation
    if image_size:
        config.imageSize = image_size

    response = client.models.generate_images(
        model=model_id,
        prompt=prompt,
        config=config,
    )

    saved_files = []
    if response.generated_images:
        for i, generated_image in enumerate(response.generated_images, 1):
            pil_image = Image.open(io.BytesIO(generated_image.image.image_bytes))
            ext = output_format
            filename = output_path / f"imagen_{timestamp}_{i}.{ext}"

            _save_image(pil_image, filename, output_format, prompt,
                        model_id, aspect_ratio)
            saved_files.append(filename)
            print(f"  Saved: {filename}")

    return saved_files
