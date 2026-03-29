from pathlib import Path

from foliaseal.presentation.qt.phase3_harness import (
    Phase3HarnessCapture,
    _instructions_text,
    build_phase3_checklist_results_markdown,
)


def test_phase3_checklist_results_markdown_auto_checks_supported_items(
    tmp_path: Path,
) -> None:
    template = tmp_path / "phase3_template.md"
    template.write_text(
        "\n".join(
            [
                (
                    "- [ ] Confirm the signature properties flow is reachable from the "
                    "main signing UI."
                ),
                (
                    "- [ ] Confirm the selected PDF can be used without unexpected "
                    "dependency or backend errors."
                ),
                "- [ ] The user can draw a signature rectangle on the preview.",
                "- [ ] The sign action is available from the properties flow.",
                "- [ ] Reused settings preserve layout and style choices.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    capture = Phase3HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        first_render_ms=52.4,
        selection_count=1,
        sign_request_count=1,
        last_signature_page_index=0,
        last_signature_page_number=1,
        last_signature_has_visible_appearance=True,
        last_signature_output_path="/tmp/sample-signed.pdf",
        preview_available=True,
        validation_text="Ready to sign.",
        interaction_counts={"selection_success": 1},
        errors=(),
    )

    markdown = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=str(template),
    )

    assert "Phase 3 FR-3B Acceptance Results" in markdown
    assert "- Last signature page number: 1" in markdown
    assert (
        "- [x] Confirm the signature properties flow is reachable from the main signing UI."
        in markdown
    )
    assert (
        "- [x] Confirm the selected PDF can be used without unexpected dependency or backend "
        "errors." in markdown
    )
    assert "- [x] The user can draw a signature rectangle on the preview." in markdown
    assert "- [x] The sign action is available from the properties flow." in markdown
    assert "- [ ] Reused settings preserve layout and style choices." in markdown


def test_phase3_checklist_results_markdown_leaves_manual_items_unchecked(
    tmp_path: Path,
) -> None:
    template = tmp_path / "phase3_template.md"
    template.write_text(
        "- [ ] The placed rectangle can be resized or repositioned in the workflow.\n",
        encoding="utf-8",
    )
    capture = Phase3HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        first_render_ms=None,
        selection_count=0,
        sign_request_count=0,
        last_signature_page_index=None,
        last_signature_page_number=None,
        last_signature_has_visible_appearance=False,
        last_signature_output_path=None,
        preview_available=False,
        validation_text="",
        interaction_counts={},
        errors=("render failed",),
    )

    markdown = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=str(template),
    )

    assert "- [ ] The placed rectangle can be resized or repositioned in the workflow." in markdown


def test_phase3_harness_instructions_do_not_embed_pdf_path() -> None:
    text = _instructions_text()
    assert "Loaded PDF:" not in text
    assert "signature draft" in text
