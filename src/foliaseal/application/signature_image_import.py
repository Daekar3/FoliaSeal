"""Typed import and managed-storage policy for reusable signature images."""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageCms, ImageOps

SUPPORTED_IMAGE_FORMATS = frozenset({"PNG", "JPEG", "GIF"})
MAX_IMAGE_PIXELS = 25_000_000
MAX_IMAGE_BYTES = 20 * 1024 * 1024
OPTIMIZED_IMAGE_MAX_EDGE = 2048


class SignatureImageImportError(ValueError):
    """Raised when an image cannot be used as a visible signature image."""


class SignatureImageOptimizationRequired(SignatureImageImportError):
    """Raised when a valid image needs explicit confirmation before downsizing."""

    def __init__(self, inspection: SignatureImageInspection) -> None:
        self.inspection = inspection
        super().__init__(
            "This image is larger than 2048 pixels on one edge. "
            "Confirm optimization to continue."
        )


@dataclass(frozen=True)
class SignatureImageInspection:
    """Content facts gathered before a source image is copied into managed storage."""

    source_path: Path
    format: str
    width_px: int
    height_px: int
    frame_count: int
    file_size_bytes: int
    has_alpha: bool
    has_visible_pixels: bool
    requires_optimization: bool

    @property
    def pixel_count(self) -> int:
        return self.width_px * self.height_px


@dataclass(frozen=True)
class ManagedSignatureImageStore:
    """Own the catalog-local directory where normalized signature images live."""

    storage_dir: Path
    directory_name: str = "signature-images"

    @property
    def managed_dir(self) -> Path:
        return Path(self.storage_dir) / self.directory_name

    def inspect(self, source_path: str | Path) -> SignatureImageInspection:
        """Validate format, dimensions, frames, and visible content without writing."""

        source = Path(source_path)
        try:
            file_size = source.stat().st_size
        except OSError as exc:
            raise SignatureImageImportError(f"Image source is not readable: {source}") from exc
        if file_size > MAX_IMAGE_BYTES:
            raise SignatureImageImportError("Image exceeds the 20 MB size limit.")

        try:
            with Image.open(source) as image:
                image_format = (image.format or "").upper()
                if image_format not in SUPPORTED_IMAGE_FORMATS:
                    raise SignatureImageImportError(
                        "Only content-validated PNG, JPEG, and static GIF images are supported."
                    )
                frame_count = int(getattr(image, "n_frames", 1))
                if frame_count != 1:
                    raise SignatureImageImportError(
                        "Animated or multiframe images are not supported."
                    )
                image.verify()

            with Image.open(source) as image:
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
                    raise SignatureImageImportError("Image exceeds the 25 megapixel limit.")
                normalized = ImageOps.exif_transpose(image)
                rgba = normalized.convert("RGBA")
                alpha = rgba.getchannel("A")
                has_visible_pixels = alpha.getbbox() is not None
                has_alpha = "A" in image.getbands() or "transparency" in image.info
        except SignatureImageImportError:
            raise
        except (OSError, ValueError) as exc:
            raise SignatureImageImportError("Image is malformed or unreadable.") from exc

        if not has_visible_pixels:
            raise SignatureImageImportError("Image contains no visible pixels.")
        return SignatureImageInspection(
            source_path=source,
            format=image_format,
            width_px=width,
            height_px=height,
            frame_count=frame_count,
            file_size_bytes=file_size,
            has_alpha=has_alpha,
            has_visible_pixels=has_visible_pixels,
            requires_optimization=(
                width > OPTIMIZED_IMAGE_MAX_EDGE or height > OPTIMIZED_IMAGE_MAX_EDGE
            ),
        )

    def import_image(
        self,
        source_path: str | Path,
        *,
        preserve_alpha: bool = True,
        allow_optimization: bool = False,
    ) -> Path:
        """Normalize a source image and atomically store a managed PNG."""

        inspection = self.inspect(source_path)
        if inspection.requires_optimization and not allow_optimization:
            raise SignatureImageOptimizationRequired(inspection)

        source = inspection.source_path
        try:
            with Image.open(source) as image:
                normalized = ImageOps.exif_transpose(image)
                normalized = _convert_to_srgb_rgba(normalized)
                alpha = normalized.getchannel("A")
                if alpha.getbbox() is None:
                    raise SignatureImageImportError("Image contains no visible pixels.")
                if not preserve_alpha:
                    flattened = Image.new("RGBA", normalized.size, (255, 255, 255, 255))
                    flattened.alpha_composite(normalized)
                    normalized = flattened
                if inspection.requires_optimization:
                    normalized.thumbnail(
                        (OPTIMIZED_IMAGE_MAX_EDGE, OPTIMIZED_IMAGE_MAX_EDGE),
                        Image.Resampling.LANCZOS,
                    )
                normalized.load()
        except SignatureImageImportError:
            raise
        except (OSError, ValueError) as exc:
            raise SignatureImageImportError("Image could not be normalized.") from exc

        self.managed_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
        target = self.managed_dir / f"{digest}-{uuid4().hex}.png"
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=self.managed_dir,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
            normalized.save(temporary, format="PNG", optimize=True)
            temporary.replace(target)
        except (OSError, ValueError) as exc:
            raise SignatureImageImportError("Managed image storage failed.") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return target

    def delete_managed_image(self, image_path: str | Path) -> None:
        """Remove one staged managed image, refusing paths outside this store."""

        candidate = Path(image_path)
        managed_root = self.managed_dir.resolve()
        try:
            resolved = candidate.resolve()
            resolved.relative_to(managed_root)
        except ValueError as exc:
            raise SignatureImageImportError(
                "Managed image cleanup refused a path outside image storage."
            ) from exc
        resolved.unlink(missing_ok=True)


def _convert_to_srgb_rgba(image: Image.Image) -> Image.Image:
    """Convert an image to sRGB with an explicit alpha channel and no profile metadata."""

    icc_profile = image.info.get("icc_profile")
    if icc_profile:
        try:
            srgb_profile = ImageCms.createProfile("sRGB")
            image = ImageCms.profileToProfile(
                image,
                ImageCms.ImageCmsProfile(icc_profile),
                srgb_profile,
                outputMode="RGBA",
            )
        except (OSError, ValueError, ImageCms.PyCMSError) as exc:
            raise SignatureImageImportError("Image contains an invalid color profile.") from exc
    return image.convert("RGBA")


__all__ = [
    "MAX_IMAGE_BYTES",
    "MAX_IMAGE_PIXELS",
    "OPTIMIZED_IMAGE_MAX_EDGE",
    "ManagedSignatureImageStore",
    "SignatureImageImportError",
    "SignatureImageInspection",
    "SignatureImageOptimizationRequired",
]
