"""Domain models and contracts for document operations and signing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Protocol

from foliaseal.domain.errors import FailureCode


class RevisionStrategy(str, Enum):  # noqa: UP042
    """How an operation writes output revisions."""

    INCREMENTAL = "incremental"
    FULL_REWRITE = "full_rewrite"


class DocumentOperationType(str, Enum):  # noqa: UP042
    """Supported operation categories."""

    SIGN = "sign"
    ADD_PAGE = "add_page"
    REMOVE_PAGE = "remove_page"
    MOVE_PAGE = "move_page"
    CROP_PAGE = "crop_page"


class SignatureFieldKey(str, Enum):  # noqa: UP042
    """Named fields that can appear in a visible signature block."""

    DISTINGUISHED_NAME = "distinguished_name"
    COMMON_NAME = "common_name"
    EMAIL = "email"
    SIGNING_TIME = "signing_time"
    REASON = "reason"
    LOCATION = "location"
    TITLE = "title"
    COMPANY = "company"


class SignatureFieldSource(str, Enum):  # noqa: UP042
    """Where a visible signature field gets its text/value from."""

    DERIVED = "derived"
    OVERRIDE = "override"
    HIDDEN = "hidden"


class SignatureLayoutTemplate(str, Enum):  # noqa: UP042
    """Supported text layout presets for the visible appearance."""

    SINGLE_LINE = "single_line"
    MULTI_LINE = "multi_line"
    WRAPPED_BLOCK = "wrapped_block"


class SignatureTimezoneDisplayMode(str, Enum):  # noqa: UP042
    """How signing-time timestamps should be displayed."""

    LOCAL = "local"
    UTC = "utc"


class SignatureAnchor(str, Enum):  # noqa: UP042
    """Anchor positions for preset rectangle defaults."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    MIDDLE_LEFT = "middle_left"
    CENTER = "center"
    MIDDLE_RIGHT = "middle_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


def _require_non_empty_str(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


def _require_optional_non_empty_str(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_str(value, field_name)


def _require_bool(value: object, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field_name} must be a bool.")
    return value


def _require_positive_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number.")
    number = float(value)
    if not isfinite(number) or number <= 0:
        raise ValueError(f"{field_name} must be a positive finite number.")
    return number


def _require_finite_number(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be a number.")
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{field_name} must be finite.")
    return number


def _require_color_hex(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    normalized = value.strip()
    if len(normalized) not in (7, 9) or not normalized.startswith("#"):
        raise ValueError(
            f"{field_name} must be a hex color in #RRGGBB or #RRGGBBAA format."
        )

    hex_digits = normalized[1:]
    if any(character not in "0123456789abcdefABCDEF" for character in hex_digits):
        raise ValueError(
            f"{field_name} must be a hex color in #RRGGBB or #RRGGBBAA format."
        )

    return normalized.upper()


def _enum_values(enum_cls: type[Enum]) -> tuple[str, ...]:
    return tuple(member.value for member in enum_cls)


def _require_enum(value: object, field_name: str, enum_cls: type[Enum]) -> Enum:
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be one of {', '.join(_enum_values(enum_cls))}."
        )
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be one of {', '.join(_enum_values(enum_cls))}."
        ) from exc


def _require_tuple_of_keys(value: object, field_name: str) -> tuple[SignatureFieldKey, ...]:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple of signature field keys.")
    keys: list[SignatureFieldKey] = []
    for entry in value:
        if not isinstance(entry, SignatureFieldKey):
            raise ValueError(f"{field_name} must contain signature field keys only.")
        keys.append(entry)
    return tuple(keys)


@dataclass(frozen=True)
class SignatureRect:
    """PDF-space rectangle used for a visible signature widget.

    Coordinates are stored in PDF points using a bottom-left origin.
    """

    page_index: int
    left_pt: float
    bottom_pt: float
    width_pt: float
    height_pt: float

    def __post_init__(self) -> None:
        if isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be zero or greater.")
        object.__setattr__(self, "left_pt", _require_finite_number(self.left_pt, "left_pt"))
        object.__setattr__(self, "bottom_pt", _require_finite_number(self.bottom_pt, "bottom_pt"))
        object.__setattr__(self, "width_pt", _require_positive_number(self.width_pt, "width_pt"))
        object.__setattr__(self, "height_pt", _require_positive_number(self.height_pt, "height_pt"))
        object.__setattr__(self, "page_index", int(self.page_index))


@dataclass(frozen=True)
class SignaturePlacementDefaults:
    """Reusable preset defaults for signature box size and anchor choice."""

    width_pt: float
    height_pt: float
    anchor: SignatureAnchor = SignatureAnchor.BOTTOM_RIGHT

    def __post_init__(self) -> None:
        object.__setattr__(self, "width_pt", _require_positive_number(self.width_pt, "width_pt"))
        object.__setattr__(self, "height_pt", _require_positive_number(self.height_pt, "height_pt"))
        if not isinstance(self.anchor, SignatureAnchor):
            raise ValueError(
                "anchor must be a SignatureAnchor value."
            )
        self.validate()

    def validate(self) -> None:
        """Validate the default size and anchor."""
        if self.width_pt <= 0 or self.height_pt <= 0:
            raise ValueError("placement defaults must have positive dimensions.")


@dataclass(frozen=True)
class SignatureTextStyle:
    """Typography settings for the visible signature text."""

    font_family: str = "Sans Serif"
    font_size_pt: float = 10.0
    bold: bool = False
    italic: bool = False
    text_color_hex: str = "#000000"

    def __post_init__(self) -> None:
        font_family = _require_non_empty_str(self.font_family, "font_family")
        font_size_pt = _require_positive_number(self.font_size_pt, "font_size_pt")
        text_color_hex = _require_color_hex(self.text_color_hex, "text_color_hex")
        object.__setattr__(self, "font_family", font_family)
        object.__setattr__(self, "font_size_pt", font_size_pt)
        object.__setattr__(self, "bold", _require_bool(self.bold, "bold"))
        object.__setattr__(self, "italic", _require_bool(self.italic, "italic"))
        object.__setattr__(self, "text_color_hex", text_color_hex)
        self.validate()

    def validate(self) -> None:
        """Validate text styling values."""
        if self.font_size_pt <= 0:
            raise ValueError("font_size_pt must be positive.")


@dataclass(frozen=True)
class SignatureBoxStyle:
    """Border and background settings for the visible signature widget."""

    show_border: bool = True
    border_color_hex: str = "#000000"
    border_width_pt: float = 1.0
    background_color_hex: str = "#FFFFFF"

    def __post_init__(self) -> None:
        border_color_hex = _require_color_hex(self.border_color_hex, "border_color_hex")
        border_width_pt = _require_positive_number(self.border_width_pt, "border_width_pt")
        background_color_hex = _require_color_hex(
            self.background_color_hex,
            "background_color_hex",
        )
        object.__setattr__(self, "show_border", _require_bool(self.show_border, "show_border"))
        object.__setattr__(self, "border_color_hex", border_color_hex)
        object.__setattr__(self, "border_width_pt", border_width_pt)
        object.__setattr__(self, "background_color_hex", background_color_hex)
        self.validate()

    def validate(self) -> None:
        """Validate box styling values."""
        if self.border_width_pt <= 0:
            raise ValueError("border_width_pt must be positive.")


@dataclass(frozen=True)
class SignatureFieldBinding:
    """Binding for one field that may appear in the signature appearance."""

    source: SignatureFieldSource = SignatureFieldSource.DERIVED
    show_in_visible_appearance: bool = True
    override_text: str | None = None
    display_label: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, SignatureFieldSource):
            raise ValueError("source must be a SignatureFieldSource value.")
        object.__setattr__(
            self,
            "show_in_visible_appearance",
            _require_bool(self.show_in_visible_appearance, "show_in_visible_appearance"),
        )
        object.__setattr__(
            self,
            "override_text",
            _require_optional_non_empty_str(self.override_text, "override_text"),
        )
        object.__setattr__(
            self,
            "display_label",
            _require_optional_non_empty_str(self.display_label, "display_label"),
        )
        self.validate()

    def validate(self) -> None:
        """Validate the field-source contract."""
        if self.source == SignatureFieldSource.OVERRIDE and self.override_text is None:
            raise ValueError("override_text is required when source is OVERRIDE.")
        if self.source != SignatureFieldSource.OVERRIDE and self.override_text is not None:
            raise ValueError("override_text is only allowed when source is OVERRIDE.")
        if self.source == SignatureFieldSource.HIDDEN and self.show_in_visible_appearance:
            raise ValueError("Hidden fields cannot be shown in the visible appearance.")


@dataclass(frozen=True)
class SignatureAppearance:
    """Normalized visible-signature appearance contract."""

    signer_label_prefix: str = "Digitally signed by"
    layout_template: SignatureLayoutTemplate = SignatureLayoutTemplate.SINGLE_LINE
    timezone_display_mode: SignatureTimezoneDisplayMode = SignatureTimezoneDisplayMode.LOCAL
    datetime_format: str = "%Y-%m-%d %H:%M:%S %Z"
    field_order: tuple[SignatureFieldKey, ...] = (
        SignatureFieldKey.DISTINGUISHED_NAME,
        SignatureFieldKey.COMMON_NAME,
        SignatureFieldKey.EMAIL,
        SignatureFieldKey.SIGNING_TIME,
        SignatureFieldKey.REASON,
        SignatureFieldKey.LOCATION,
        SignatureFieldKey.TITLE,
        SignatureFieldKey.COMPANY,
    )
    distinguished_name: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    common_name: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    email: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    signing_time: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    reason: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    location: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    title: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    company: SignatureFieldBinding = field(default_factory=SignatureFieldBinding)
    text_style: SignatureTextStyle = field(default_factory=SignatureTextStyle)
    box_style: SignatureBoxStyle = field(default_factory=SignatureBoxStyle)
    image_stamp_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "signer_label_prefix",
            _require_non_empty_str(self.signer_label_prefix, "signer_label_prefix"),
        )
        if not isinstance(self.layout_template, SignatureLayoutTemplate):
            raise ValueError("layout_template must be a SignatureLayoutTemplate value.")
        if not isinstance(self.timezone_display_mode, SignatureTimezoneDisplayMode):
            raise ValueError(
                "timezone_display_mode must be a SignatureTimezoneDisplayMode value."
            )
        object.__setattr__(
            self,
            "datetime_format",
            _require_non_empty_str(self.datetime_format, "datetime_format"),
        )
        object.__setattr__(
            self,
            "field_order",
            _require_tuple_of_keys(self.field_order, "field_order"),
        )
        object.__setattr__(
            self,
            "image_stamp_path",
            _require_optional_non_empty_str(self.image_stamp_path, "image_stamp_path"),
        )
        self.validate()

    def validate(self) -> None:
        """Validate appearance settings and field ordering."""
        required_keys = {
            SignatureFieldKey.DISTINGUISHED_NAME,
            SignatureFieldKey.COMMON_NAME,
            SignatureFieldKey.EMAIL,
            SignatureFieldKey.SIGNING_TIME,
            SignatureFieldKey.REASON,
            SignatureFieldKey.LOCATION,
            SignatureFieldKey.TITLE,
            SignatureFieldKey.COMPANY,
        }
        if set(self.field_order) != required_keys or len(self.field_order) != len(required_keys):
            raise ValueError(
                "field_order must contain each signature field key exactly once."
            )

        self.text_style.validate()
        self.box_style.validate()
        self.distinguished_name.validate()
        self.common_name.validate()
        self.email.validate()
        self.signing_time.validate()
        self.reason.validate()
        self.location.validate()
        self.title.validate()
        self.company.validate()

    def binding_for(self, field_key: SignatureFieldKey) -> SignatureFieldBinding:
        """Return the configured binding for a field key."""
        match field_key:
            case SignatureFieldKey.DISTINGUISHED_NAME:
                return self.distinguished_name
            case SignatureFieldKey.COMMON_NAME:
                return self.common_name
            case SignatureFieldKey.EMAIL:
                return self.email
            case SignatureFieldKey.SIGNING_TIME:
                return self.signing_time
            case SignatureFieldKey.REASON:
                return self.reason
            case SignatureFieldKey.LOCATION:
                return self.location
            case SignatureFieldKey.TITLE:
                return self.title
            case SignatureFieldKey.COMPANY:
                return self.company

    def iter_field_bindings(self) -> tuple[tuple[SignatureFieldKey, SignatureFieldBinding], ...]:
        """Return the fields in configured display order."""
        return tuple((key, self.binding_for(key)) for key in self.field_order)


@dataclass(frozen=True)
class SigningRequest:
    """Headless signing request payload used by the phase 1 pipeline."""

    input_pdf_path: str
    output_pdf_path: str
    certificate_path: str
    passphrase: str
    tsa_url: str
    timestamp_required: bool = True
    certificate_alias: str | None = None
    signature_rect: SignatureRect | None = None
    signature_appearance: SignatureAppearance | None = None

    def __post_init__(self) -> None:
        input_pdf_path = _require_non_empty_str(self.input_pdf_path, "input_pdf_path")
        output_pdf_path = _require_non_empty_str(self.output_pdf_path, "output_pdf_path")
        certificate_path = _require_non_empty_str(
            self.certificate_path,
            "certificate_path",
        )
        tsa_url = _require_non_empty_str(self.tsa_url, "tsa_url")
        timestamp_required = _require_bool(self.timestamp_required, "timestamp_required")
        certificate_alias = _require_optional_non_empty_str(
            self.certificate_alias,
            "certificate_alias",
        )
        object.__setattr__(self, "input_pdf_path", input_pdf_path)
        object.__setattr__(self, "output_pdf_path", output_pdf_path)
        object.__setattr__(self, "certificate_path", certificate_path)
        object.__setattr__(self, "tsa_url", tsa_url)
        object.__setattr__(self, "timestamp_required", timestamp_required)
        object.__setattr__(self, "certificate_alias", certificate_alias)
        if self.signature_rect is not None and not isinstance(self.signature_rect, SignatureRect):
            raise ValueError("signature_rect must be a SignatureRect value.")
        if self.signature_appearance is not None and not isinstance(
            self.signature_appearance, SignatureAppearance
        ):
            raise ValueError("signature_appearance must be a SignatureAppearance value.")

    def has_visible_signature_settings(self) -> bool:
        """Return whether the request includes visible signature instructions."""
        return self.signature_rect is not None and self.signature_appearance is not None


@dataclass(frozen=True)
class SigningOutput:
    """Produced PDF bytes and related standards metadata."""

    output_bytes: bytes
    output_pdf_version: str
    signature_subfilter: str
    timestamp_present: bool


@dataclass(frozen=True)
class VerificationSummary:
    """Post-sign verification summary for reporting."""

    signature_count: int
    timestamp_present: bool


@dataclass(frozen=True)
class SigningResult:
    """Stable success/failure result for UI and logging layers."""

    success: bool
    failure_code: FailureCode | None
    message: str
    output_pdf_version: str | None = None
    signature_subfilter: str | None = None
    timestamp_present: bool | None = None
    standards_summary: str | None = None


class DocumentOperation(Protocol):
    """Contract implemented by each operation capability."""

    operation_type: DocumentOperationType
    revision_strategy: RevisionStrategy

    def execute(self, request: DocumentOperationRequest) -> DocumentOperationResult:
        """Execute a document operation."""


@dataclass(frozen=True)
class DocumentOperationRequest:
    """Generic request envelope used by operation handlers."""

    operation_type: DocumentOperationType
    input_pdf_path: str
    output_pdf_path: str


@dataclass(frozen=True)
class DocumentOperationResult:
    """Generic operation result envelope."""

    success: bool
    operation_type: DocumentOperationType
    revision_strategy: RevisionStrategy
    message: str
