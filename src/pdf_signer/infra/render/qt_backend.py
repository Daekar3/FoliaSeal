"""Qt-based render backend adapter with graceful fallback diagnostics."""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pdf_signer.infra.render.base import (
    PdfPageGeometry,
    RenderBackendDiagnostic,
    RenderPageRequest,
    RenderPageResult,
)


@dataclass(frozen=True)
class _QtBindings:
    qpdf_document: type[Any]
    qimage: type[Any]
    qsize: type[Any]
    qpdf_document_render_options: type[Any]


@dataclass(frozen=True)
class _PdfIndirectRef:
    object_number: int
    generation: int = 0


_WHITESPACE = b" \t\r\n\x0c\x00"
_DELIMITERS = b"()<>[]{}/%"


class QtPdfRenderBackend:
    """Render backend using QtPdf + QImage conversion APIs.

    This adapter performs late imports so the project can run in environments
    where Qt bindings are not installed yet.
    """

    def __init__(self) -> None:
        self._bindings_error: str | None = None
        self._bindings: _QtBindings | None = self._load_bindings()
        self._metadata_cache: dict[str, _PdfMetadataCacheEntry] = {}

    def diagnostics(self) -> RenderBackendDiagnostic:
        if self._bindings is None:
            return RenderBackendDiagnostic(
                backend_name="qtpdf-render-backend",
                available=False,
                message=(
                    "Qt render backend is unavailable. Install PySide6 with QtPdf support. "
                    f"Details: {self._bindings_error}"
                ),
            )
        return RenderBackendDiagnostic(
            backend_name="qtpdf-render-backend",
            available=True,
            message="QtPdf render backend is available.",
        )

    def get_page_geometry(self, document_path: str, page_index: int) -> PdfPageGeometry:
        document = self._open_document(document_path)
        page_index = self._validated_page_index(document, page_index)
        metadata = self._get_cached_page_metadata(
            document_path=document_path,
            page_index=page_index,
            document=document,
        )
        return PdfPageGeometry(
            media_box=metadata.media_box,
            crop_box=metadata.crop_box,
            rotation=metadata.rotation,
        )

    def render_page(self, request: RenderPageRequest) -> RenderPageResult:
        if request.zoom <= 0:
            raise ValueError("zoom must be greater than zero.")

        document = self._open_document(request.document_path)
        page_index = self._validated_page_index(document, request.page_index)

        width_pts, height_pts = (
            float(v) for v in document.pagePointSize(page_index).toTuple()
        )
        target_width = max(1, int(round(width_pts * request.zoom)))
        target_height = max(1, int(round(height_pts * request.zoom)))

        image = self._bindings.qimage(  # type: ignore[union-attr]
            target_width,
            target_height,
            self._bindings.qimage.Format_RGBA8888,  # type: ignore[union-attr]
        )
        image.fill(0)

        render_opts = self._bindings.qpdf_document_render_options()  # type: ignore[union-attr]
        rendered = document.render(  # type: ignore[no-untyped-call]
            page_index,
            self._bindings.qsize(target_width, target_height),  # type: ignore[union-attr]
            render_opts,
        )
        image = rendered.convertToFormat(self._bindings.qimage.Format_RGBA8888)  # type: ignore[union-attr]

        raw = self._extract_image_bytes(
            image=image,
            expected_size=target_width * target_height * 4,
        )
        return RenderPageResult(width_px=target_width, height_px=target_height, rgba_bytes=raw)

    def _open_document(self, document_path: str) -> Any:
        if not Path(document_path).exists():
            raise FileNotFoundError(f"Document does not exist: {document_path}")
        self._require_available()
        document = self._bindings.qpdf_document()  # type: ignore[union-attr]
        status = document.load(document_path)
        error_none = self._import_type("PySide6.QtPdf", "QPdfDocument").Error.None_
        if status != error_none:
            raise RuntimeError(f"Failed to load PDF document: {document_path}")
        return document

    def _validated_page_index(self, document: Any, page_index: int) -> int:
        page_count = int(document.pageCount())
        if page_index < 0 or page_index >= page_count:
            raise ValueError(f"page_index out of range for document: {page_index}")
        return page_index

    def _require_available(self) -> None:
        if self._bindings is None:
            raise RuntimeError(self.diagnostics().message)

    def _get_cached_page_metadata(
        self,
        *,
        document_path: str,
        page_index: int,
        document: Any,
    ) -> _PdfPageMetadata:
        cache = getattr(self, "_metadata_cache", None)
        if cache is None:
            cache = {}
            self._metadata_cache = cache
        path = Path(document_path)
        signature = _document_signature(path)
        cache_key = str(path.resolve())
        entry = cache.get(cache_key)
        if entry is None or entry.signature != signature:
            entry = _PdfMetadataCacheEntry(signature=signature)
            cache[cache_key] = entry

        metadata = entry.page_metadata.get(page_index)
        if metadata is None:
            try:
                metadata = _load_pdf_page_metadata(
                    document_path=document_path,
                    page_index=page_index,
                )
            except Exception:
                metadata = self._fallback_page_metadata(
                    document=document,
                    page_index=page_index,
                )
            entry.page_metadata[page_index] = metadata
        return metadata

    @staticmethod
    def _fallback_page_metadata(*, document: Any, page_index: int) -> _PdfPageMetadata:
        width_pts, height_pts = (
            float(v) for v in document.pagePointSize(page_index).toTuple()
        )
        media_box = (0.0, 0.0, width_pts, height_pts)
        return _PdfPageMetadata(
            media_box=media_box,
            crop_box=media_box,
            rotation=0,
        )

    @staticmethod
    def _extract_image_bytes(*, image: Any, expected_size: int) -> bytes:
        """Extract RGBA bytes from a QImage-like object across binding variants."""

        if expected_size <= 0:
            raise ValueError("expected_size must be greater than zero.")

        bit_pointer = image.bits()
        tobytes = getattr(bit_pointer, "tobytes", None)
        if callable(tobytes):
            return bytes(tobytes(expected_size))

        setsize = getattr(bit_pointer, "setsize", None)
        if callable(setsize):
            setsize(expected_size)
            return bytes(bit_pointer)

        raw = bytes(bit_pointer)
        if len(raw) < expected_size:
            raise ValueError("Rendered image buffer is smaller than expected.")
        return raw[:expected_size]

    def _load_bindings(self) -> _QtBindings | None:
        try:
            qpdf_document = self._import_type("PySide6.QtPdf", "QPdfDocument")
            qimage = self._import_type("PySide6.QtGui", "QImage")
            qsize = self._import_type("PySide6.QtCore", "QSize")
            qpdf_document_render_options = self._import_type(
                "PySide6.QtPdf", "QPdfDocumentRenderOptions"
            )
        except Exception as exc:  # pragma: no cover - driven by environment
            self._bindings_error = str(exc)
            return None
        return _QtBindings(
            qpdf_document=qpdf_document,
            qimage=qimage,
            qsize=qsize,
            qpdf_document_render_options=qpdf_document_render_options,
        )

    @staticmethod
    def _import_type(module: str, symbol: str) -> Any:
        imported = importlib.import_module(module)
        return getattr(imported, symbol)


@dataclass(frozen=True)
class _PdfPageMetadata:
    media_box: tuple[float, float, float, float]
    crop_box: tuple[float, float, float, float]
    rotation: int


@dataclass
class _PdfMetadataCacheEntry:
    signature: tuple[int, int]
    page_metadata: dict[int, _PdfPageMetadata] = field(default_factory=dict)


def _document_signature(path: Path) -> tuple[int, int]:
    stat_result = path.stat()
    return (stat_result.st_mtime_ns, stat_result.st_size)


def _load_pdf_page_metadata(*, document_path: str, page_index: int) -> _PdfPageMetadata:
    path = Path(document_path)
    data = path.read_bytes()
    parser = _PdfObjectParser(data)
    return parser.page_metadata(page_index=page_index)


class _PdfObjectParser:
    """Parse enough of the PDF object graph for page geometry metadata."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._objects = self._extract_objects(data)
        self._parsed_cache: dict[int, Any] = {}

    def page_metadata(self, *, page_index: int) -> _PdfPageMetadata:
        page_ref = self._ordered_page_refs()[page_index]
        page_dict = self._require_dict(self._resolve(page_ref))

        media_box = self._resolve_box_from_chain(page_dict, key="MediaBox")
        crop_box = self._resolve_box_from_chain(page_dict, key="CropBox") or media_box
        rotation = self._resolve_rotation_from_chain(page_dict)

        return _PdfPageMetadata(
            media_box=media_box,
            crop_box=crop_box,
            rotation=rotation,
        )

    def _ordered_page_refs(self) -> list[_PdfIndirectRef]:
        catalog_ref = self._find_catalog_ref()
        if catalog_ref is not None:
            catalog = self._require_dict(self._resolve(catalog_ref))
            pages_ref = catalog.get("Pages")
            if isinstance(pages_ref, _PdfIndirectRef):
                return self._walk_pages_tree(pages_ref)

        fallback = [
            _PdfIndirectRef(object_number=object_number)
            for object_number, body in sorted(self._objects.items())
            if self._dict_type(self._parse_object(object_number)) == "Page"
        ]
        if not fallback:
            raise ValueError("PDF page metadata could not be determined from the document.")
        return fallback

    def _walk_pages_tree(self, root_ref: _PdfIndirectRef) -> list[_PdfIndirectRef]:
        node = self._require_dict(self._resolve(root_ref))
        node_type = self._dict_type(node)
        if node_type == "Page":
            return [root_ref]
        if node_type != "Pages":
            raise ValueError(f"Unexpected page tree node type: {node_type!r}")

        page_refs: list[_PdfIndirectRef] = []
        for child in node.get("Kids", []):
            if not isinstance(child, _PdfIndirectRef):
                continue
            page_refs.extend(self._walk_pages_tree(child))
        return page_refs

    def _find_catalog_ref(self) -> _PdfIndirectRef | None:
        for object_number in sorted(self._objects):
            parsed = self._parse_object(object_number)
            if self._dict_type(parsed) == "Catalog":
                return _PdfIndirectRef(object_number=object_number)
        return None

    def _resolve_box_from_chain(
        self,
        page_dict: dict[str, Any],
        *,
        key: str,
    ) -> tuple[float, float, float, float] | None:
        current = page_dict
        while True:
            raw_value = current.get(key)
            if raw_value is not None:
                resolved = self._resolve(raw_value)
                return self._coerce_box(resolved, key=key)
            parent = current.get("Parent")
            if not isinstance(parent, _PdfIndirectRef):
                return None
            current = self._require_dict(self._resolve(parent))

    def _resolve_rotation_from_chain(self, page_dict: dict[str, Any]) -> int:
        current = page_dict
        while True:
            raw_value = current.get("Rotate")
            if raw_value is not None:
                resolved = self._resolve(raw_value)
                if not isinstance(resolved, int):
                    raise ValueError("Rotate entry must resolve to an integer.")
                return resolved % 360
            parent = current.get("Parent")
            if not isinstance(parent, _PdfIndirectRef):
                return 0
            current = self._require_dict(self._resolve(parent))

    def _resolve(self, value: Any) -> Any:
        if isinstance(value, _PdfIndirectRef):
            return self._parse_object(value.object_number)
        return value

    def _parse_object(self, object_number: int) -> Any:
        cached = self._parsed_cache.get(object_number)
        if cached is not None:
            return cached

        body = self._objects[object_number]
        parser = _PdfValueParser(body)
        parsed = parser.parse_value()
        self._parsed_cache[object_number] = parsed
        return parsed

    @staticmethod
    def _extract_objects(data: bytes) -> dict[int, bytes]:
        object_pattern = re.compile(
            rb"(?ms)(\d+)\s+(\d+)\s+obj\b(.*?)\bendobj\b"
        )
        objects: dict[int, bytes] = {}
        for match in object_pattern.finditer(data):
            object_number = int(match.group(1))
            body = match.group(3).strip()
            stream_marker = body.find(b"stream")
            if stream_marker != -1 and body.lstrip().startswith(b"<<"):
                body = body[:stream_marker].rstrip()
            objects[object_number] = body
        return objects

    @staticmethod
    def _dict_type(value: Any) -> str | None:
        if isinstance(value, dict):
            raw_type = value.get("Type")
            if isinstance(raw_type, str):
                return raw_type
        return None

    @staticmethod
    def _require_dict(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("Expected PDF dictionary while resolving page metadata.")
        return value

    @staticmethod
    def _coerce_box(value: Any, *, key: str) -> tuple[float, float, float, float]:
        if not isinstance(value, list) or len(value) != 4:
            raise ValueError(f"{key} entry must resolve to a four-number array.")
        try:
            left, bottom, right, top = (float(component) for component in value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} entry must resolve to numeric coordinates.") from exc
        return (left, bottom, right, top)


class _PdfValueParser:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0

    def parse_value(self) -> Any:
        self._skip_ws_and_comments()
        if self._position >= len(self._data):
            raise ValueError("Unexpected end of PDF object while parsing metadata.")

        token = self._peek(2)
        if token == b"<<":
            return self._parse_dict()

        current = self._data[self._position : self._position + 1]
        if current == b"[":
            return self._parse_array()
        if current == b"/":
            return self._parse_name()
        if current == b"(":
            return self._parse_literal_string()

        return self._parse_scalar()

    def _parse_dict(self) -> dict[str, Any]:
        self._consume(b"<<")
        result: dict[str, Any] = {}
        while True:
            self._skip_ws_and_comments()
            if self._peek(2) == b">>":
                self._consume(b">>")
                return result
            key = self._parse_name()
            result[key] = self.parse_value()

    def _parse_array(self) -> list[Any]:
        self._consume(b"[")
        result: list[Any] = []
        while True:
            self._skip_ws_and_comments()
            if self._peek(1) == b"]":
                self._consume(b"]")
                return result
            result.append(self.parse_value())

    def _parse_name(self) -> str:
        self._consume(b"/")
        start = self._position
        while self._position < len(self._data):
            current = self._data[self._position]
            if current in _WHITESPACE or current in _DELIMITERS:
                break
            self._position += 1
        return self._data[start:self._position].decode("latin-1")

    def _parse_literal_string(self) -> str:
        self._consume(b"(")
        depth = 1
        chunks: list[int] = []
        while self._position < len(self._data) and depth > 0:
            current = self._data[self._position]
            self._position += 1
            if current == 0x5C and self._position < len(self._data):
                chunks.append(self._data[self._position])
                self._position += 1
                continue
            if current == 0x28:
                depth += 1
            elif current == 0x29:
                depth -= 1
                if depth == 0:
                    break
            chunks.append(current)
        return bytes(chunks).decode("latin-1", errors="replace")

    def _parse_scalar(self) -> Any:
        first = self._read_token()
        if first == b"true":
            return True
        if first == b"false":
            return False
        if first == b"null":
            return None
        if first == b"R":
            raise ValueError("Unexpected indirect reference marker.")

        second_position = self._position
        self._skip_ws_and_comments()
        second = self._try_read_token()
        if second is not None and _is_integer_token(first) and _is_integer_token(second):
            self._skip_ws_and_comments()
            marker = self._try_read_token()
            if marker == b"R":
                return _PdfIndirectRef(
                    object_number=int(first),
                    generation=int(second),
                )
            self._position = second_position

        return _coerce_pdf_scalar(first)

    def _read_token(self) -> bytes:
        token = self._try_read_token()
        if token is None:
            raise ValueError("Unexpected end of PDF object while reading token.")
        return token

    def _try_read_token(self) -> bytes | None:
        self._skip_ws_and_comments()
        if self._position >= len(self._data):
            return None
        start = self._position
        while self._position < len(self._data):
            current = self._data[self._position]
            if current in _WHITESPACE or current in _DELIMITERS:
                break
            self._position += 1
        if self._position == start:
            return None
        return self._data[start:self._position]

    def _skip_ws_and_comments(self) -> None:
        while self._position < len(self._data):
            current = self._data[self._position]
            if current in _WHITESPACE:
                self._position += 1
                continue
            if current == 0x25:
                while (
                    self._position < len(self._data)
                    and self._data[self._position] not in b"\r\n"
                ):
                    self._position += 1
                continue
            return

    def _peek(self, size: int) -> bytes:
        return self._data[self._position : self._position + size]

    def _consume(self, token: bytes) -> None:
        if self._peek(len(token)) != token:
            raise ValueError(f"Expected token {token!r} while parsing PDF metadata.")
        self._position += len(token)


def _is_integer_token(token: bytes) -> bool:
    return re.fullmatch(rb"[+-]?\d+", token) is not None


def _coerce_pdf_scalar(token: bytes) -> Any:
    if re.fullmatch(rb"[+-]?\d+", token):
        return int(token)
    if re.fullmatch(rb"[+-]?(?:\d+\.\d*|\d*\.\d+)", token):
        return float(token)
    return token.decode("latin-1")
