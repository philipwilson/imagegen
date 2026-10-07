# Gemini Image Generation CLI

Generate images using Google's Gemini (Nano Banana) image models.

## Installation

```bash
pip install -e .
```

## Setup

Authenticate with either an API key or Google Cloud Application Default
Credentials. An API key takes precedence if both are available.

### Option 1: API key

Get an API key from https://aistudio.google.com/apikey

Set it via environment variable:
```bash
export GOOGLE_GENERATIVE_AI_API_KEY="your-api-key"
```

Or create a `.env` file in your project directory:
```
GOOGLE_GENERATIVE_AI_API_KEY=your-api-key
```

### Option 2: Application Default Credentials (Vertex AI)

Requires a Google Cloud project with the Vertex AI API enabled.

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="your-project-id"   # optional if ADC has a default project
export GOOGLE_CLOUD_LOCATION="global"           # optional, defaults to global
```

To use ADC even when an API key is set, set `GOOGLE_GENAI_USE_VERTEXAI=true`.

## Usage

```bash
# Basic text-to-image
gemini-imagegen "A cat wearing a top hat"

# Use Nano Banana Pro for higher quality
gemini-imagegen --model pro "A serene Japanese garden"

# Custom aspect ratio
gemini-imagegen --aspect 16:9 "Mountain landscape at sunset"

# Read prompt from file
gemini-imagegen -f prompt.txt

# Edit/transform an existing image
gemini-imagegen -i photo.jpg "Convert to watercolor painting"

# Multiple reference images (up to 14)
gemini-imagegen -i ref1.jpg -i ref2.jpg "Combine these styles"

# Generate multiple images
gemini-imagegen -n 4 "A whimsical steampunk teapot"

# Adjust creativity with temperature
gemini-imagegen -t 1.5 "An abstract painting"

# Save as WebP instead of PNG
gemini-imagegen --format webp "A crystal ball"

# Nano Banana 2.1 with 4K output
gemini-imagegen --model nb21 --image-size 4K "A detailed botanical poster"

# Panoramic banner (flash2, flash-lite, nb21 only; pair with 2K or 4K for usable height)
gemini-imagegen --model nb21 --aspect 8:1 --image-size 2K "City skyline at dusk"
```

## Models

All models support text-to-image and image editing with reference images.

| Flag | Model ID | Description |
|------|----------|-------------|
| `--model flash` | `gemini-2.5-flash-image` | Nano Banana - fast, efficient (default) |
| `--model flash2` | `gemini-3.1-flash-image` | Nano Banana 2 |
| `--model flash-lite` | `gemini-3.1-flash-lite-image` | Nano Banana 2 Lite |
| `--model pro` | `gemini-3-pro-image` | Nano Banana Pro - higher quality |
| `--model nb21` | `gemini-nano-banana-2.1` | Nano Banana 2.1 - latest, flash-speed with improved quality, text rendering and up to 4K output |

Imagen 4 support was removed in October 2026: Google discontinued the Imagen 4
models on Vertex AI (June 30, 2026) and the Gemini API (August 17, 2026) and
recommends Nano Banana 2.1 as the replacement.

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--model` | `-m` | Model to use (see above) |
| `--aspect` | `-a` | Aspect ratio (see below; allowed values depend on the model) |
| `--file` | `-f` | Read prompt from a file |
| `--image` | `-i` | Reference image(s) for editing (up to 14) |
| `--number` | `-n` | Number of images to generate |
| `--temperature` | `-t` | Creativity 0.0-2.0 |
| `--format` | | Output format (`png` or `webp`) |
| `--output` | `-o` | Output directory (default: `output/`) |
| `--image-size` | | Output size `1K`, `2K` or `4K` (`flash2`, `flash-lite`, `pro`, `nb21`). Not supported by `flash`. |

### Aspect ratios

- **`flash2`, `flash-lite`, `nb21`**: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`, plus the panoramic ratios `1:4`, `4:1`, `1:8`, `8:1`
- **`flash` and `pro`**: the ten standard ratios above only. The API rejects panoramic ratios for these models.

At the default `1K` size a panoramic image is short on its narrow side (an `8:1` image is roughly 2928×352). Use `--image-size 2K` or `4K` for panoramas you intend to display at full width.

Per-model capabilities (aspect ratios, image sizes, reference images, temperature) are defined in one place, the `MODEL_SPECS` table in `gemini_imagegen/core.py`. Adding a model is a single new entry there.

## PNG Metadata

Generated PNG files include metadata with the prompt, model, aspect ratio, and temperature used. View with:

```bash
gemini-imageinfo output/gemini_20231130_123456_1.png
```

Or via Python:
```python
from PIL import Image
img = Image.open("output/gemini_20231130_123456_1.png")
print(img.info)  # {'prompt': '...', 'model': '...', ...}
```

## Python API

```python
from gemini_imagegen import generate_image

saved_files = generate_image(
    prompt="A cyberpunk cityscape",
    model="pro",
    aspect_ratio="16:9",
    number=2,
    temperature=1.2,
)

# Nano Banana 2.1 panorama at 4K
saved_files = generate_image(
    prompt="A mountain range at dawn",
    model="nb21",
    aspect_ratio="8:1",
    image_size="4K",
)
```
