# Gemini Image Generation CLI

Generate images using Google's Gemini and Imagen models.

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

# Edit/transform an existing image (Gemini only)
gemini-imagegen -i photo.jpg "Convert to watercolor painting"

# Multiple reference images (up to 14, Gemini only)
gemini-imagegen -i ref1.jpg -i ref2.jpg "Combine these styles"

# Generate multiple images
gemini-imagegen -n 4 "A whimsical steampunk teapot"

# Adjust creativity with temperature (Gemini only)
gemini-imagegen -t 1.5 "An abstract painting"

# Save as WebP instead of PNG
gemini-imagegen --format webp "A crystal ball"

# Use Imagen 4 for high-fidelity generation
gemini-imagegen --model imagen "A robot on a skateboard"

# Imagen 4 Ultra with 2K output
gemini-imagegen --model imagen-ultra --image-size 2K "A detailed landscape"

# Imagen with person generation control
gemini-imagegen --model imagen --person-generation dont_allow "A park scene"
```

## Models

### Gemini (text-to-image + image editing)

| Flag | Model ID | Description |
|------|----------|-------------|
| `--model flash` | `gemini-2.5-flash-image` | Nano Banana - fast, efficient (default) |
| `--model flash2` | `gemini-3.1-flash-image-preview` | Nano Banana Flash 3.1 |
| `--model pro` | `gemini-3-pro-image-preview` | Nano Banana Pro - higher quality |

### Imagen 4 (text-to-image only)

| Flag | Model ID | Description |
|------|----------|-------------|
| `--model imagen` | `imagen-4.0-generate-001` | Imagen 4 Standard |
| `--model imagen-fast` | `imagen-4.0-fast-generate-001` | Imagen 4 Fast |
| `--model imagen-ultra` | `imagen-4.0-ultra-generate-001` | Imagen 4 Ultra - highest quality |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--model` | `-m` | Model to use (see above) |
| `--aspect` | `-a` | Aspect ratio (see below) |
| `--file` | `-f` | Read prompt from a file |
| `--image` | `-i` | Reference image(s) for editing (Gemini only) |
| `--number` | `-n` | Number of images to generate (Imagen max: 4) |
| `--temperature` | `-t` | Creativity 0.0-2.0 (Gemini only) |
| `--format` | | Output format (`png` or `webp`) |
| `--output` | `-o` | Output directory (default: `output/`) |
| `--person-generation` | | Person generation policy (Imagen only): `dont_allow`, `allow_adult`, `allow_all` |
| `--image-size` | | Output size `1K` or `2K` (Imagen only) |

### Aspect ratios

- **Gemini**: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`
- **Imagen**: `1:1`, `3:4`, `4:3`, `9:16`, `16:9`

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

# Gemini model with reference images
saved_files = generate_image(
    prompt="A cyberpunk cityscape",
    model="pro",
    aspect_ratio="16:9",
    number=2,
    temperature=1.2,
)

# Imagen 4 model
saved_files = generate_image(
    prompt="A photorealistic mountain lake",
    model="imagen-ultra",
    aspect_ratio="16:9",
    number=4,
    image_size="2K",
)
```
