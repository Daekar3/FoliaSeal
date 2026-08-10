from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

from foliaseal.application import signature_image_import as image_import
from foliaseal.application.signature_image_import import (
    ManagedSignatureImageStore,
    SignatureImageImportError,
    SignatureImageOptimizationRequired,
)


def test_import_normalizes_metadata_and_preserves_or_flattens_alpha(tmp_path: Path) -> None:
    source = tmp_path / "stamp.png"
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Comment", "private source metadata")
    Image.new("RGBA", (32, 20), (12, 34, 56, 128)).save(source, pnginfo=metadata)
    store = ManagedSignatureImageStore(tmp_path / "catalog")

    preserved = store.import_image(source, preserve_alpha=True)
    flattened = store.import_image(source, preserve_alpha=False)

    with Image.open(preserved) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"
        assert image.getchannel("A").getextrema() == (128, 128)
        assert "comment" not in image.info
    with Image.open(flattened) as image:
        assert image.mode == "RGBA"
        assert image.getchannel("A").getextrema() == (255, 255)
        assert image.getpixel((0, 0))[:3] == (133, 144, 155)


@pytest.mark.parametrize("suffix", [".jpg", ".gif"])
def test_import_accepts_supported_static_raster_formats(tmp_path: Path, suffix: str) -> None:
    source = tmp_path / f"stamp{suffix}"
    image = Image.new("RGB", (20, 20), "black")
    image.save(source, format="JPEG" if suffix == ".jpg" else "GIF")

    target = ManagedSignatureImageStore(tmp_path / "catalog").import_image(source)

    assert target.suffix == ".png"
    assert target.parent.name == "signature-images"


def test_import_rejects_animation_malformed_and_empty_alpha(tmp_path: Path) -> None:
    animated = tmp_path / "animated.gif"
    Image.new("RGB", (10, 10), "black").save(
        animated,
        save_all=True,
        append_images=[Image.new("RGB", (10, 10), "white")],
        format="GIF",
    )
    malformed = tmp_path / "bad.png"
    malformed.write_bytes(b"not an image")
    empty_alpha = tmp_path / "empty.png"
    Image.new("RGBA", (10, 10), (0, 0, 0, 0)).save(empty_alpha)
    store = ManagedSignatureImageStore(tmp_path / "catalog")

    with pytest.raises(SignatureImageImportError, match="multiframe"):
        store.inspect(animated)
    with pytest.raises(SignatureImageImportError, match="malformed"):
        store.inspect(malformed)
    with pytest.raises(SignatureImageImportError, match="visible pixels"):
        store.inspect(empty_alpha)


def test_import_requires_explicit_optimization_and_caps_managed_copy(tmp_path: Path) -> None:
    source = tmp_path / "large.png"
    Image.new("RGB", (3000, 100), "black").save(source)
    store = ManagedSignatureImageStore(tmp_path / "catalog")

    with pytest.raises(SignatureImageOptimizationRequired):
        store.import_image(source)
    target = store.import_image(source, allow_optimization=True)

    with Image.open(target) as image:
        assert max(image.size) == 2048


def test_import_enforces_pixel_and_byte_limits(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "stamp.png"
    Image.new("RGB", (20, 20), "black").save(source)
    store = ManagedSignatureImageStore(tmp_path / "catalog")
    monkeypatch.setattr(image_import, "MAX_IMAGE_PIXELS", 100)
    with pytest.raises(SignatureImageImportError, match="25 megapixel"):
        store.inspect(source)
    monkeypatch.setattr(image_import, "MAX_IMAGE_PIXELS", 25_000_000)
    monkeypatch.setattr(image_import, "MAX_IMAGE_BYTES", 1)
    with pytest.raises(SignatureImageImportError, match="20 MB"):
        store.inspect(source)
