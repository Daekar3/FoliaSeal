from foliaseal.presentation.qt.phase2_harness import (
    DEFAULT_CHECKLIST_RESULTS_PATH,
    HarnessCapture,
    build_checklist_results_markdown,
    build_phase2_evidence_command,
)


def test_build_phase2_evidence_command_includes_captured_timings() -> None:
    capture = HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        first_render_ms=42.345,
        navigation_samples_ms=(21.2, 22.3),
        selection_count=1,
        last_selection_pdf_rect=(10.0, 20.0, 30.0, 40.0),
        interaction_counts={"key_zoom_in": 1, "selection_success": 1},
        errors=(),
    )

    command = build_phase2_evidence_command(capture)

    assert "--first-render-ms 42.34" in command
    assert "--navigation-ms 21.20" in command
    assert "--navigation-ms 22.30" in command
    assert "--collect-runtime-footprint" in command
    assert f"--qa-checklist-file {DEFAULT_CHECKLIST_RESULTS_PATH}" in command


def test_build_phase2_evidence_command_omits_first_render_when_missing() -> None:
    capture = HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        first_render_ms=None,
        navigation_samples_ms=(),
        selection_count=0,
        last_selection_pdf_rect=None,
        interaction_counts={},
        errors=(),
    )

    command = build_phase2_evidence_command(capture)

    assert "--first-render-ms" not in command


def test_harness_capture_json_includes_interaction_counts() -> None:
    capture = HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        first_render_ms=10.0,
        navigation_samples_ms=(1.0,),
        selection_count=2,
        last_selection_pdf_rect=(1.0, 2.0, 3.0, 4.0),
        interaction_counts={"key_jump_home": 1, "selection_error": 1},
        errors=("example",),
    )

    rendered = capture.to_json()

    assert '"interaction_counts"' in rendered
    assert '"key_jump_home": 1' in rendered


def test_build_checklist_results_markdown_prefills_detected_checks(tmp_path) -> None:
    template_path = tmp_path / "checklist.md"
    template_path.write_text(
        "\n".join(
            [
                "# Template",
                "- [ ] Initial render succeeds on page 1.",
                "- [ ] Keyboard zoom shortcuts work (`+`, `-`, `0` reset).",
                "- [ ] Drag-selection overlay is visible while dragging.",
                "- [ ] Record at least 10 navigation samples in milliseconds.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    capture = HarnessCapture(
        pdf_path="/tmp/sample.pdf",
        first_render_ms=10.0,
        navigation_samples_ms=tuple(float(i) for i in range(10)),
        selection_count=0,
        last_selection_pdf_rect=None,
        interaction_counts={"key_zoom_in": 1, "key_zoom_out": 1, "key_zoom_reset": 1},
        errors=(),
    )

    rendered = build_checklist_results_markdown(
        capture,
        checklist_template_path=str(template_path),
    )

    assert "Source checklist" in rendered
    assert "- [x] Initial render succeeds on page 1." in rendered
    assert "- [x] Keyboard zoom shortcuts work (`+`, `-`, `0` reset)." in rendered
    assert "- [ ] Drag-selection overlay is visible while dragging." in rendered
    assert "- [x] Record at least 10 navigation samples in milliseconds." in rendered
