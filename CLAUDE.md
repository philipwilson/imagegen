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

This is a CLI tool for generating images using Google's Gemini image models, via the `google-genai` SDK.

- `gemini_imagegen/core.py` - Core `generate_image()` function; validates against `MODEL_SPECS` and calls `_generate_gemini()` (uses `generate_content`)
- `gemini_imagegen/cli.py` - Argument parsing and CLI entry point (`gemini-imagegen` command)
- `gemini_imagegen/info.py` - Utility CLI (`gemini-imageinfo`) for reading PNG metadata
- `gemini_imagegen/__init__.py` - Package exports, exposes `generate_image` and `__version__`

All models support text-to-image and image editing (reference images, up to 14). Multiple images are produced by looping one `generate_content` call per image.

Every per-model capability lives in the `MODEL_SPECS` table in `core.py` (a `ModelSpec` per alias: model ID, aspect ratios, image sizes, max reference images, temperature). `generate_image()` validates purely against that table, and the CLI derives its `--model`, `--aspect` and `--image-size` choices from it. To add a model, add one entry (use the `_gemini3()` helper if it shares that family's capabilities) and a README row. Gemini 3 models accept `--image-size` 1K/2K/4K. The panoramic ratios 1:4, 4:1, 1:8, 8:1 are accepted by `flash2`, `flash-lite` and `nb21` but rejected by the API for `flash` and `pro` (verified October 2026). The original `flash` model accepts neither size nor panoramic ratios.

## Models

- `flash` → `gemini-2.5-flash-image` (Nano Banana) - original model; Google shutdown date March 15, 2027
- `flash2` → `gemini-3.1-flash-image` (Nano Banana 2)
- `flash-lite` → `gemini-3.1-flash-lite-image` (Nano Banana 2 Lite)
- `pro` → `gemini-3-pro-image` (Nano Banana Pro) - higher quality
- `nb21` → `gemini-nano-banana-2.1` (Nano Banana 2.1) - **default**, latest, GA, supports `--image-size` up to 4K

The default is `DEFAULT_MODEL` in `core.py`; the CLI and `generate_image()` both read it.

Imagen 4 support was removed in October 2026 after Google discontinued those models on both Vertex AI and the Gemini API.
