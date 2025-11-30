# Gemini Image Generation CLI

Generate images using Google's Gemini Nano Banana models.

## Installation

```bash
pip install -e .
```

## Setup

Get an API key from https://aistudio.google.com/apikey

Set it via environment variable:
```bash
export GOOGLE_GENERATIVE_AI_API_KEY="your-api-key"
```

Or create a `.env` file in your project directory:
```
GOOGLE_GENERATIVE_AI_API_KEY=your-api-key
```

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
```

## Models

| Flag | Model ID | Description |
|------|----------|-------------|
| `--model flash` | `gemini-2.5-flash-image` | Nano Banana - fast, efficient (default) |
| `--model pro` | `gemini-3-pro-image-preview` | Nano Banana Pro - higher quality |

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--model` | `-m` | Model to use (`flash` or `pro`) |
| `--aspect` | `-a` | Aspect ratio (`1:1`, `16:9`, `9:16`, `4:3`, etc.) |
| `--file` | `-f` | Read prompt from a file |
| `--image` | `-i` | Reference image(s) for editing/style transfer |
| `--number` | `-n` | Number of images to generate |
| `--temperature` | `-t` | Creativity (0.0-2.0, higher = more creative) |
| `--format` | | Output format (`png` or `webp`) |
| `--output` | `-o` | Output directory (default: `output/`) |

## PNG Metadata

Generated PNG files include metadata with the prompt, model, aspect ratio, and temperature used. View with:

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
    output_format="png",
)
```
