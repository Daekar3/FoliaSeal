"""Shared signed-output evidence shaping for Acceptance QA."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from foliaseal.domain.models import TimestampTrustPolicy

CountEmbeddedSignatures = Callable[[Path], int | None]
SnapshotOutputSignature = Callable[[Path], dict[str, Any] | None]
SnapshotOutputVerification = Callable[
    [Path, TimestampTrustPolicy | None],
    dict[str, Any] | None,
]
SnapshotVisibleSignatureAppearance = Callable[[Path], dict[str, Any] | None]
SnapshotSignedOutputRender = Callable[..., dict[str, Any] | None]


def signed_output_preview_comparison_snapshot(
    signed_output_render_snapshot: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if signed_output_render_snapshot is None:
        return None
    return {
        "page_render_path": signed_output_render_snapshot.get("page_render_path"),
        "signature_crop_path": signed_output_render_snapshot.get("signature_crop_path"),
        "normalized_signature_crop_path": signed_output_render_snapshot.get(
            "normalized_signature_crop_path"
        ),
        "comparison_path": signed_output_render_snapshot.get("comparison_path"),
        "preview_crop_bounds_px": signed_output_render_snapshot.get("preview_crop_bounds_px"),
        "signed_crop_bounds_px": signed_output_render_snapshot.get("signed_crop_bounds_px"),
        "preview_vs_signed_output_change_ratio": signed_output_render_snapshot.get(
            "preview_vs_signed_output_change_ratio"
        ),
        "preview_vs_signed_output_aspect_ratio_delta": signed_output_render_snapshot.get(
            "preview_vs_signed_output_aspect_ratio_delta"
        ),
        "preview_text_fragments_match_output": signed_output_render_snapshot.get(
            "preview_text_fragments_match_output"
        ),
        "annotation_rect_matches_request": signed_output_render_snapshot.get(
            "annotation_rect_matches_request"
        ),
        "output_text_bounds_match_preview": signed_output_render_snapshot.get(
            "output_text_bounds_match_preview"
        ),
        "output_image_presence_matches_preview": signed_output_render_snapshot.get(
            "output_image_presence_matches_preview"
        ),
        "preview_vs_signed_output_passed": signed_output_render_snapshot.get(
            "preview_vs_signed_output_passed"
        ),
        "preview_vs_signed_output_error": signed_output_render_snapshot.get("comparison_error")
        or signed_output_render_snapshot.get("signature_crop_error")
        or signed_output_render_snapshot.get("page_render_error"),
        "appearance_layer_comparison": signed_output_render_snapshot.get(
            "appearance_layer_comparison"
        ),
    }


@dataclass(frozen=True)
class AcceptanceSignedOutputSnapshotter:
    """Own the stable signed-output evidence bundle for successful signing."""

    count_embedded_signatures: CountEmbeddedSignatures
    snapshot_output_signature: SnapshotOutputSignature
    snapshot_output_verification: SnapshotOutputVerification
    snapshot_visible_signature_appearance: SnapshotVisibleSignatureAppearance
    snapshot_signed_output_render: SnapshotSignedOutputRender

    def snapshot_successful_signed_output(
        self,
        *,
        output_file: Path,
        page_index: int | None,
        preview_snapshot: dict[str, Any],
        preview_text: str,
        trust_policy: TimestampTrustPolicy | None,
        artifacts_dir: str | None,
        artifact_basename: str | None,
    ) -> dict[str, Any]:
        output_signature_count = self.count_embedded_signatures(output_file)
        output_signature_snapshot = self.snapshot_output_signature(output_file)
        output_verification_snapshot = self.snapshot_output_verification(
            output_file,
            trust_policy,
        )
        output_visible_appearance_snapshot = self.snapshot_visible_signature_appearance(
            output_file
        )
        signed_output_render_snapshot = self.snapshot_signed_output_render(
            output_pdf_path=str(output_file),
            page_index=page_index,
            preview_snapshot=preview_snapshot,
            preview_text=preview_text,
            output_visible_appearance_snapshot=output_visible_appearance_snapshot,
            artifacts_dir=artifacts_dir,
            artifact_basename=artifact_basename,
        )
        return {
            "output_file_exists": True,
            "output_file_size_bytes": output_file.stat().st_size,
            "output_signature_count": output_signature_count,
            "output_signature_snapshot": output_signature_snapshot,
            "output_verification_snapshot": output_verification_snapshot,
            "output_visible_appearance_snapshot": output_visible_appearance_snapshot,
            "signed_output_render_snapshot": signed_output_render_snapshot,
            "signed_output_preview_comparison": signed_output_preview_comparison_snapshot(
                signed_output_render_snapshot
            ),
        }
