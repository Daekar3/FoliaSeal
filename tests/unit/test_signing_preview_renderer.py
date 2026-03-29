from pathlib import Path

from foliaseal.application import compare_preview_to_request, render_signing_preview
from foliaseal.application.signing_draft_workflow import SigningDraftWorkflow
from tests.support.phase3_builders import (
    build_signature_appearance,
    build_signature_rect,
    build_signing_request,
)


def _workflow(tmp_path: Path) -> SigningDraftWorkflow:
    return SigningDraftWorkflow(
        input_pdf_path=str(tmp_path / "input.pdf"),
        output_pdf_path=str(tmp_path / "output.pdf"),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        tsa_url="https://tsa.example.com",
        timestamp_required=True,
        certificate_alias="signing-cert",
    )


def test_preview_renderer_formats_semantics_deterministically(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    workflow.set_signature_appearance(build_signature_appearance())
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    snapshot = render_signing_preview(preview)

    assert snapshot == render_signing_preview(preview)
    assert snapshot.title == "Digitally signed by"
    assert snapshot.can_submit is True
    assert snapshot.field_count == 8
    assert snapshot.visible_field_count == 7
    assert snapshot.hidden_field_count == 1
    assert snapshot.issue_count == 0
    assert snapshot.lines[0].kind.value == "title"
    assert snapshot.lines[0].text == "Digitally signed by"
    assert any(line.text.startswith("Placement: page=2") for line in snapshot.lines)
    assert any(
        line.kind.value == "field" and "[visible] Email: alice@example.com (override)" in line.text
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "field" and line.text == "[hidden] Location"
        for line in snapshot.lines
    )
    assert any(
        line.kind.value == "summary" and "Text style: Source Sans 3" in line.text
        for line in snapshot.lines
    )


def test_preview_parity_report_matches_the_final_request(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance()
    rect = build_signature_rect(page_index=2)
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(rect)

    preview = workflow.preview()
    request = workflow.build_signing_request()
    report = compare_preview_to_request(preview, request)

    assert report.is_consistent is True
    assert report.issues == ()


def test_preview_parity_report_detects_request_drift(tmp_path: Path) -> None:
    workflow = _workflow(tmp_path)
    appearance = build_signature_appearance()
    workflow.set_signature_appearance(appearance)
    workflow.set_signature_rect(build_signature_rect(page_index=2))

    preview = workflow.preview()
    request = build_signing_request(
        tmp_path,
        signature_rect=build_signature_rect(page_index=3),
        signature_appearance=appearance,
    )
    report = compare_preview_to_request(preview, request)

    assert report.is_consistent is False
    assert {issue.code for issue in report.issues} == {"signature_rect_mismatch"}
