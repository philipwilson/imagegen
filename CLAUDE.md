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

Requires `GOOGLE_GENERATIVE_AI_API_KEY` - can be set via:
- Environment variable
- `.env` file (auto-loaded via python-dotenv)

Get a key from https://aistudio.google.com/apikey

## Architecture

This is a CLI tool for generating images using Google's Gemini API (Nano Banana models).

- `gemini_imagegen/core.py` - Core `generate_image()` function that handles Gemini API calls, uses `google-genai` SDK
- `gemini_imagegen/cli.py` - Argument parsing and CLI entry point (`gemini-imagegen` command)
- `gemini_imagegen/__init__.py` - Package exports, exposes `generate_image` and `__version__`

The API supports text-to-image and image editing (passing reference images via the `images` parameter, up to 14 images).

## Models

- `flash` → `gemini-2.5-flash-image` (Nano Banana) - default, fast
- `pro` → `gemini-3-pro-image-preview` (Nano Banana Pro) - higher quality
