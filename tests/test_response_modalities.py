"""Each model requests the response modalities from its ModelSpec."""

import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from PIL import Image

from gemini_imagegen import core


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buf, format="PNG")
    return buf.getvalue()


def _image_part():
    data = _png_bytes()
    return SimpleNamespace(
        text=None,
        inline_data=SimpleNamespace(data=data, mime_type="image/png"),
        as_image=lambda: SimpleNamespace(image_bytes=data),
    )


def _run(tmp_path, model):
    """Run generate_image against a fake client; return the configs it was called with."""
    configs = []

    def generate_content(**kwargs):
        configs.append(kwargs["config"])
        return SimpleNamespace(parts=[_image_part()])

    client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
    with patch.object(core, "_create_client", return_value=client):
        saved = core.generate_image("prompt", model=model, output_dir=str(tmp_path))
    return configs, saved


def test_nb21_requests_image_only(tmp_path):
    # With TEXT requested, nb21 returns every image twice (October 2026).
    configs, saved = _run(tmp_path, "nb21")
    assert [c.response_modalities for c in configs] == [["IMAGE"]]
    assert len(saved) == 1


@pytest.mark.parametrize("model", [m for m in core.MODEL_SPECS if m != "nb21"])
def test_other_models_request_text_and_image(tmp_path, model):
    configs, _ = _run(tmp_path, model)
    assert [c.response_modalities for c in configs] == [["TEXT", "IMAGE"]]
