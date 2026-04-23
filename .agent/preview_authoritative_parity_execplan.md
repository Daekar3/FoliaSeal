# Preview-Authoritative Appearance Parity

## Summary

The current manual harness case is no longer failing on fit or placement. The text content matches the final signed output, and the annotation rect matches the requested rectangle. Two parity blockers remain:

1. The harness was still comparing a borderless preview surface against a bordered signed-output surface.
2. The signed PDF itself still used pyHanko's default square border, while the preview showed rounded corners.

This slice keeps the preview UI authoritative. The GUI preview stays transparent and borderless. The harness gets a separate bordered analysis preview for parity work, and the canonical stamp engine is updated to draw the rounded border itself so the preview and the signed PDF can actually converge.

## Decisions

- The preview UI is the appearance target for this slice.
- GUI preview artifacts and analysis artifacts are separate on purpose:
  - GUI preview artifact: transparent RGBA surface, what the user actually sees.
  - Analysis preview artifact: a bordered, white-flattened canonical render of the same preview state for stable parity analysis.
- Signed-output parity compares the flattened analysis preview against a signed crop normalized into preview-space dimensions.
- Rounded border rendering must move into the canonical/signed stamp engine; a Qt-only rounded border is not sufficient for parity.
- No fit-policy or font-metric changes are in scope unless bordered, normalized comparison still proves a real rendering defect afterward.

## Implementation

- Extend preview render-capture payloads in the harness to include `analysis_preview_image_path` alongside `preview_image_path`.
- For interactive canonical preview captures:
  - keep copying the transparent GUI preview artifact to `preview_image_path`
  - write a bordered, white-flattened canonical companion artifact to `analysis_preview_image_path`
- For headless preview captures:
  - keep using the existing flattened canonical image
  - set `analysis_preview_image_path` equal to `preview_image_path`
- Replace the stock square border path in the canonical stamp engine with a rounded border path that is used by:
  - signed PDF visible appearances
  - canonical preview rendering
- In signed-output parity:
  - use `analysis_preview_image_path` as the preview-side input when available
  - keep the raw signed crop artifact
  - add a normalized signed crop artifact resized to the preview crop dimensions
  - run text-bounds detection and side-by-side comparison against the normalized signed crop

## Acceptance

- The current manual `single_line` no-stamp harness case should reach:
  - `preview_vs_signed_output_passed = true`
  - `output_text_bounds_match_preview = true`
  - `annotation_rect_matches_request = true`
- The signed PDF for that case must visibly retain the rounded-corner border.
- Harness tests must prove:
  - analysis preview images are preserved separately from GUI preview images
  - signed-output text detection uses the normalized signed crop
  - normalized signed crop dimensions match the preview crop dimensions
  - canonical/signed border rendering uses the rounded path instead of the default square rectangle

## Verification

- `python -m ruff check src/foliaseal/presentation/qt/phase3_harness.py tests/unit/test_phase3_harness.py`
- `pytest -q tests/unit/test_phase3_harness.py tests/unit/test_phase3_signing_backend.py tests/unit/test_signing_preview_renderer.py`
- Then rerun the same manual harness case and inspect:
  - `artifacts/phase3_harness_capture.json`
  - `artifacts/phase3_harness_capture_artifacts/*signed_output*`
