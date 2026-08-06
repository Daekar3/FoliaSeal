"""Immutable contracts shared by signing-draft workflows and presentation callers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from foliaseal.application.coordinate_transform import PageBox
from foliaseal.domain.models import (
    SignatureBoxStyle,
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureLayoutTemplate,
    SignatureRect,
    SignatureStampPosition,
    SignatureTextStyle,
    SignatureTimezoneDisplayMode,
)


class SigningDraftValidationError(ValueError):
    """Raised when the signing draft cannot be converted into a final request."""

    def __init__(self, issues: tuple[SigningDraftValidationIssue, ...]) -> None:
        self.issues = issues
        message = "; ".join(issue.message for issue in issues) if issues else "Invalid draft."
        super().__init__(message)


class SigningDraftValidationSeverity(str, Enum):  # noqa: UP042
    """Severity levels for signing draft validation."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class SigningDraftValidationIssue:
    """A single validation problem surfaced to the UI."""

    code: str
    message: str
    field_name: str | None = None
    severity: SigningDraftValidationSeverity = SigningDraftValidationSeverity.ERROR


@dataclass(frozen=True)
class SignaturePlacementContext:
    """Page geometry and rotation used for placement validation."""

    page_index: int
    page_box: PageBox
    rotation: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.page_index, bool) or self.page_index < 0:
            raise ValueError("page_index must be zero or greater.")
        if self.rotation % 90 != 0:
            raise ValueError("rotation must be a multiple of 90 degrees.")
        self.page_box.validate()


@dataclass(frozen=True)
class SigningDraftPreviewField:
    """Normalized preview line for one visible signature field."""

    field_key: SignatureFieldKey
    label: str
    text: str
    visible: bool
    source: SignatureFieldSource
    hint: str | None = None


@dataclass(frozen=True)
class SigningDraftPreview:
    """Normalized preview payload for the UI layer."""

    title: str
    page_index: int | None
    signature_rect: SignatureRect | None
    signer_label_prefix: str | None
    layout_template: SignatureLayoutTemplate | None
    stamp_position: SignatureStampPosition | None
    timezone_display_mode: SignatureTimezoneDisplayMode | None
    show_field_names: bool
    datetime_format: str | None
    text_style: SignatureTextStyle | None
    box_style: SignatureBoxStyle | None
    image_stamp_path: str | None
    fields: tuple[SigningDraftPreviewField, ...]
    detail_text: str
    issues: tuple[SigningDraftValidationIssue, ...]
    can_submit: bool
    stamp_text: str | None = None


__all__ = [
    "SignaturePlacementContext",
    "SigningDraftPreview",
    "SigningDraftPreviewField",
    "SigningDraftValidationError",
    "SigningDraftValidationIssue",
    "SigningDraftValidationSeverity",
]
