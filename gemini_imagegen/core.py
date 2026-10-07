"""Core image generation functionality (Gemini image models via generate_content)."""

import io
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
from PIL.PngImagePlugin import PngInfo


# Load .env file if present
load_dotenv()


GEMINI_ASPECT_RATIOS = ('1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9')
# Wide/tall panoramic ratios. Accepted by gemini-3.1-flash-image,
# gemini-3.1-flash-lite-image and gemini-nano-banana-2.1; rejected (HTTP 400)
# by gemini-2.5-flash-image and gemini-3-pro-image as of October 2026.
EXTREME_ASPECT_RATIOS = ('1:4', '4:1', '1:8', '8:1')
GEMINI3_ASPECT_RATIOS = GEMINI_ASPECT_RATIOS + EXTREME_ASPECT_RATIOS

OUTPUT_FORMATS = ['png', 'webp']
TEMPERATURE_RANGE = (0.0, 2.0)
MAX_REFERENCE_IMAGES = 14


@dataclass(frozen=True)
class ModelSpec:
    """Capabilities of one model alias. All validation in generate_image() reads from this."""

    model_id: str
    description: str
    aspect_ratios: tuple[str, ...]
    image_sizes: tuple[str, ...] = ()     # empty: --image-size not accepted
    max_reference_images: int = MAX_REFERENCE_IMAGES   # 0: reference images not accepted
    supports_temperature: bool = True
    deprecated: str | None = None         # Google deprecation note; shown in help and warned at runtime


def _gemini3(
    model_id: str,
    description: str,
    aspect_ratios: tuple[str, ...] = GEMINI3_ASPECT_RATIOS,
    deprecated: str | None = None,
) -> ModelSpec:
    """Shared capabilities of the Gemini 3 image family."""
    return ModelSpec(
        model_id=model_id,
        description=description,
        aspect_ratios=aspect_ratios,
        image_sizes=('1K', '2K', '4K'),
        deprecated=deprecated,
    )


MODEL_SPECS: dict[str, ModelSpec] = {
    # The original Nano Banana: no --image-size and no panoramic ratios.
    'flash': ModelSpec(
        model_id='gemini-2.5-flash-image',
        description='Nano Banana - original model',
        aspect_ratios=GEMINI_ASPECT_RATIOS,
        deprecated='shutdown 2027-03-15, use flash-lite or nb21',
    ),
    'flash2': _gemini3('gemini-3.1-flash-image', 'Nano Banana 2',
                       deprecated='since 2026-10-06, no shutdown date yet, use nb21'),
    'flash-lite': _gemini3('gemini-3.1-flash-lite-image', 'Nano Banana 2 Lite'),
    # Pro accepts --image-size but not the panoramic ratios (verified against the API).
    'pro': _gemini3('gemini-3-pro-image', 'Nano Banana Pro - higher quality',
                    aspect_ratios=GEMINI_ASPECT_RATIOS),
    'nb21': _gemini3('gemini-nano-banana-2.1', 'Nano Banana 2.1 - latest'),
}

DEFAULT_MODEL = 'nb21'

# Alias -> model ID, kept for callers that only need the mapping.
MODELS = {alias: spec.model_id for alias, spec in MODEL_SPECS.items()}


def _union(attr: str) -> list[str]:
    """Ordered union of a tuple-valued spec attribute across all models."""
    seen: dict[str, None] = {}
    for spec in MODEL_SPECS.values():
        for value in getattr(spec, attr):
            seen.setdefault(value, None)
    return list(seen)


ASPECT_RATIOS = _union('aspect_ratios')   # every ratio some model accepts
IMAGE_SIZES = _union('image_sizes')       # every size some model accepts


def models_supporting(predicate) -> list[str]:
    """Aliases whose spec satisfies predicate(spec). Used to build CLI help."""
    return [alias for alias, spec in MODEL_SPECS.items() if predicate(spec)]


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
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = '1:1',
    output_dir: str = 'output',
    images: list[Path] | None = None,
    number: int = 1,
    temperature: float | None = None,
    output_format: str = 'png',
    image_size: str | None = None,
) -> list[Path]:
    """
    Generate images from a text prompt using a Gemini image model.

    Args:
        prompt: Text description of the image to generate
        model: Model alias, a key of MODEL_SPECS (default: 'nb21')
        aspect_ratio: Image aspect ratio (e.g., '1:1', '16:9'); allowed values
            depend on the model, see MODEL_SPECS[model].aspect_ratios
        output_dir: Directory to save generated images
        images: Optional list of reference image paths (up to 14)
        number: Number of images to generate (default: 1)
        temperature: Generation temperature 0.0-2.0
        output_format: Output format 'png' or 'webp' (default: 'png')
        image_size: Output image size '1K', '2K' or '4K'; allowed values depend
            on the model, see MODEL_SPECS[model].image_sizes

    Returns:
        List of paths to saved images
    """
    spec = MODEL_SPECS.get(model)
    if not spec:
        raise ValueError(f"Unknown model '{model}'. Choose from: {list(MODEL_SPECS)}")
    model_id = spec.model_id
    label = f"'{model}' ({model_id})"

    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Invalid output format. Choose from: {OUTPUT_FORMATS}")

    if number < 1:
        raise ValueError("Number of images must be at least 1")

    if aspect_ratio not in spec.aspect_ratios:
        raise ValueError(
            f"Aspect ratio '{aspect_ratio}' is not supported by {label}. "
            f"Choose from: {list(spec.aspect_ratios)}"
        )

    if image_size is not None:
        if not spec.image_sizes:
            raise ValueError(f"--image-size is not supported by {label}")
        if image_size not in spec.image_sizes:
            raise ValueError(
                f"Image size '{image_size}' is not supported by {label}. "
                f"Choose from: {list(spec.image_sizes)}"
            )

    if images:
        if not spec.max_reference_images:
            raise ValueError(f"Reference images are not supported by {label}")
        if len(images) > spec.max_reference_images:
            raise ValueError(f"{label} accepts at most {spec.max_reference_images} reference images")

    if temperature is not None:
        if not spec.supports_temperature:
            raise ValueError(f"Temperature is not supported by {label}")
        lo, hi = TEMPERATURE_RANGE
        if not (lo <= temperature <= hi):
            raise ValueError(f"Temperature must be between {lo} and {hi}")

    client = _create_client()

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if spec.deprecated:
        print(f"Warning: model {label} is deprecated by Google ({spec.deprecated}).", file=sys.stderr)

    print(f"Generating {number} image(s)...")
    print(f"  Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  Model: {model_id}")
    print(f"  Aspect ratio: {aspect_ratio}")
    if temperature is not None:
        print(f"  Temperature: {temperature}")
    if image_size:
        print(f"  Image size: {image_size}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_files = _generate_gemini(
        client, model_id, prompt, number, aspect_ratio,
        temperature, output_format, images, image_size,
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
    image_size: str | None,
    output_path: Path,
    timestamp: str,
) -> list[Path]:
    """Generate images using Gemini models."""
    # Build contents list with prompt and optional reference images
    contents: list = [prompt]
    if images:
        print(f"  Reference images: {len(images)}")
        for img_path in images:
            if not img_path.exists():
                raise ValueError(f"Image not found: {img_path}")
            contents.append(Image.open(img_path))

    # Build generation config
    image_config = types.ImageConfig(aspect_ratio=aspect_ratio)
    if image_size:
        image_config.image_size = image_size
    gen_config = types.GenerateContentConfig(
        response_modalities=['TEXT', 'IMAGE'],
        image_config=image_config,
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

