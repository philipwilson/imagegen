# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install in editable mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run the CLI
gemini-imagegen "prompt"

# Run tests
pytest

# Lint
ruff check .
```

## Environment

Authentication, in order of precedence (see `_create_client()` in `core.py`):
1. `GOOGLE_GENERATIVE_AI_API_KEY` - environment variable or `.env` file
   (auto-loaded via python-dotenv). Get a key from https://aistudio.google.com/apikey
2. Application Default Credentials via the Vertex AI backend
   (`gcloud auth application-default login`). Uses `GOOGLE_CLOUD_PROJECT`
   (falls back to the ADC default project) and `GOOGLE_CLOUD_LOCATION`
   (defaults to `global`).

Set `GOOGLE_GENAI_USE_VERTEXAI=true` to force ADC/Vertex even when an API key is set.

## Architecture

This is a CLI tool for generating images using Google's Gemini API and Imagen API, via the `google-genai` SDK.

- `gemini_imagegen/core.py` - Core `generate_image()` function with two code paths: `_generate_gemini()` (uses `generate_content`) and `_generate_imagen()` (uses `generate_images`)
- `gemini_imagegen/cli.py` - Argument parsing and CLI entry point (`gemini-imagegen` command)
- `gemini_imagegen/info.py` - Utility CLI (`gemini-imageinfo`) for reading PNG metadata
- `gemini_imagegen/__init__.py` - Package exports, exposes `generate_image` and `__version__`

Gemini models support text-to-image and image editing (reference images, up to 14). Imagen models support text-to-image only but offer native multi-image generation (up to 4) and configurable output size.

## Models

### Gemini
- `flash` → `gemini-2.5-flash-image` (Nano Banana) - default, fast
- `flash2` → `gemini-3.1-flash-image-preview` (Nano Banana Flash 3.1)
- `pro` → `gemini-3-pro-image-preview` (Nano Banana Pro) - higher quality

### Imagen 4
- `imagen` → `imagen-4.0-generate-001` (Standard)
- `imagen-fast` → `imagen-4.0-fast-generate-001` (Fast)
- `imagen-ultra` → `imagen-4.0-ultra-generate-001` (Ultra)
