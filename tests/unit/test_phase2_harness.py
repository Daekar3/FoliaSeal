from foliaseal.presentation.qt.phase2_harness import (
    HarnessCapture,
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
    assert "--qa-checklist-file phase2_manual_qa_checklist.md" in command


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
