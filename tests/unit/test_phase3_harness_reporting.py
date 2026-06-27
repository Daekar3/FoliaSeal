import json
from pathlib import Path
from types import SimpleNamespace

from foliaseal.application.qa_evidence_contract import (
    ENGINEERING_RUN,
    GATE_CANDIDATE,
    NON_GATING,
    PHASE3_EVIDENCE_CONTRACT_VERSION,
)
from foliaseal.presentation.qt.phase3_harness import Phase3HarnessCapture
from foliaseal.presentation.qt.phase3_harness_reporting import (
    Phase3HarnessReportRequest,
    build_phase3_checklist_results_markdown,
    finalize_phase3_harness_report,
)


class _FakeCapture:
    def __init__(self, *, payload, contract, summary_json_path, checklist_results_path):
        self.payload = payload
        self.contract = contract
        self.summary_json_path = summary_json_path
        self.checklist_results_path = checklist_results_path

    def to_json(self) -> str:
        return json.dumps(
            {
                "pdf_path": self.payload["pdf_path"],
                "contract_version": self.contract.contract_version,
            },
            sort_keys=True,
        )


def _capture_metadata_defaults(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "summary_json_path": "artifacts/phase3_harness_capture.json",
        "summary_json_written": True,
        "checklist_results_path": "artifacts/phase3_fr3b_acceptance_results.md",
        "checklist_results_written": True,
        "evidence_contract_version": PHASE3_EVIDENCE_CONTRACT_VERSION,
        "acceptance_tier": GATE_CANDIDATE,
        "gate_verdict": GATE_CANDIDATE,
        "evidence_validation_passed": True,
        "evidence_validation_errors": (),
        "evidence_validation_warnings": (),
    }
    payload.update(overrides)
    return payload


def test_finalize_phase3_harness_report_evaluates_renders_and_writes() -> None:
    calls = {"writes": []}

    def fake_evaluator(payload):
        calls["payload"] = payload
        return SimpleNamespace(contract_version="phase3_evidence_v1")

    def fake_capture_factory(
        *,
        capture_payload,
        contract,
        summary_json_path,
        checklist_results_path,
        checklist_results_written,
    ):
        calls["capture_written"] = checklist_results_written
        return _FakeCapture(
            payload=capture_payload,
            contract=contract,
            summary_json_path=summary_json_path,
            checklist_results_path=checklist_results_path,
        )

    def fake_renderer(capture, *, checklist_template_path):
        calls["render"] = (capture.summary_json_path, checklist_template_path)
        return "rendered checklist"

    def fake_writer(*, target_path, content):
        calls["writes"].append((target_path, content))

    result = finalize_phase3_harness_report(
        Phase3HarnessReportRequest(
            capture_payload={"pdf_path": "/tmp/sample.pdf"},
            summary_json_path="artifacts/summary.json",
            checklist_results_path="artifacts/results.md",
            checklist_template_path="artifacts/template.md",
        ),
        contract_evaluator=fake_evaluator,
        capture_factory=fake_capture_factory,
        checklist_renderer=fake_renderer,
        text_writer=fake_writer,
    )

    assert calls["payload"] == {"pdf_path": "/tmp/sample.pdf"}
    assert calls["capture_written"] is True
    assert calls["render"] == ("artifacts/summary.json", "artifacts/template.md")
    assert calls["writes"] == [
        (
            "artifacts/summary.json",
            '{"contract_version": "phase3_evidence_v1", "pdf_path": "/tmp/sample.pdf"}\n',
        ),
        ("artifacts/results.md", "rendered checklist"),
    ]
    assert result.capture.summary_json_path == "artifacts/summary.json"
    assert result.contract.contract_version == "phase3_evidence_v1"
    assert result.checklist_results == "rendered checklist"


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
        **_capture_metadata_defaults(),
        first_render_ms=52.4,
        selection_count=1,
        sign_request_count=1,
        last_signature_page_index=0,
        last_signature_page_number=1,
        last_signature_has_visible_appearance=True,
        last_signature_output_path="/tmp/sample-signed.pdf",
        last_signing_result_message="Signing completed successfully.",
        last_signing_result_success=True,
        preview_snapshot={
            "title": "Alice Example",
            "layout_template": "single_line",
            "stamp_position": "top",
            "show_field_names": False,
            "edge_distances_px": {
                "content_top_to_border_px": 7,
                "content_bottom_to_border_px": 5,
            },
            "signature_appearance": {
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "fields": [],
            },
        },
        sign_request_snapshot={
            "signature_appearance": {
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "fields": [],
            }
        },
        backend_reservation_snapshot={
            "layout_template": "single_line",
            "stamp_position": "top",
            "layout_plan": {
                "background_scaling": "stretch_to_fit",
                "content_scaling": "no_scaling",
                "content_bottom_margin_pt": 14,
            },
            "stamp_art_enabled": False,
            "stamp_text": "Digitally signed by Alice Example",
            "signature_appearance": {
                "layout_template": "single_line",
                "stamp_position": "top",
                "show_field_names": False,
                "fields": [],
            },
        },
        backend_reservation_error=None,
        output_file_exists=True,
        output_file_size_bytes=23456,
        output_signature_count=1,
        output_signature_snapshot={
            "field_name": "Signature1",
            "name": "Adam Smith <Secretary.LHI@Outlook.com>",
            "location": "Wytheville, Virginia, US",
            "contact_info": "Secretary.LHI@Outlook.com",
            "byte_range": [0, 123, 456, 789],
            "subfilter": "/adbe.pkcs7.detached",
            "md_algorithm": "sha256",
        },
        output_visible_appearance_snapshot={
            "field_name": "Signature1",
            "annotation_rect": [24.0, 18.0, 644.0, 198.0],
            "appearance_bbox": [0.0, 180.0, 620.0, 0.0],
            "appearance_stream_length": 650,
            "appearance_text_fragments": [
                "Digitally signed by",
                "Alice Example",
            ],
            "appearance_xobjects": [
                {
                    "name": "/Img4f98d153-5c97-4ad4-89f4-d08f26ccc303",
                    "subtype": "/Image",
                    "width": 96,
                    "height": 48,
                    "bbox": None,
                }
            ],
            "appearance_has_visible_text": True,
        },
        preview_available=True,
        preview_text="Digitally signed by\nAlice Example",
        validation_text="Ready to sign.",
        interaction_counts={"selection_success": 1},
        errors=(),
    )

    markdown = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=str(template),
    )

    assert "Phase 3 FR-3B Acceptance Results" in markdown
    assert "- Acceptance tier: `gate_candidate`" in markdown
    assert "- Automated gate verdict: `gate_candidate`" in markdown
    assert "- Evidence contract version: `phase3_evidence_v1`" in markdown
    assert "- Evidence validation passed: yes" in markdown
    assert "- Request snapshot origin: submitted request" in markdown
    assert "- Last signature page number: 1" in markdown
    assert "- Output embedded signature count: 1" in markdown
    assert "- Output signature field name: Signature1" in markdown
    assert "- Output signature name: Adam Smith <Secretary.LHI@Outlook.com>" in markdown
    assert "- Output signature location: Wytheville, Virginia, US" in markdown
    assert "- Output signature contact info: Secretary.LHI@Outlook.com" in markdown
    assert "- Output signature byte range: [0, 123, 456, 789]" in markdown
    assert "- Output signature subfilter: /adbe.pkcs7.detached" in markdown
    assert "- Output signature md algorithm: sha256" in markdown
    assert "- Output visible appearance field name: Signature1" in markdown
    assert "- Output visible appearance annotation rect: [24.0, 18.0, 644.0, 198.0]" in markdown
    assert "- Output visible appearance bbox: [0.0, 180.0, 620.0, 0.0]" in markdown
    assert "- Output visible appearance stream length: 650 bytes" in markdown
    assert "- Output visible appearance has visible text: yes" in markdown
    assert (
        "- Output visible appearance text fragments: "
        "['Digitally signed by', 'Alice Example']"
        in markdown
    )
    assert (
        "- Output visible appearance image XObjects: "
        "[/Img4f98d153-5c97-4ad4-89f4-d08f26ccc303:/Image 96x48]"
        in markdown
    )
    assert "- Output visible appearance error: none" in markdown
    assert "- Backend reservation layout template: single_line" in markdown
    assert "- Backend reservation stamp position: top" in markdown
    assert "- Backend reservation stamp text length: 33" in markdown
    assert "- Backend reservation stamp background: no" in markdown
    assert "- Backend reservation background scaling: stretch_to_fit" in markdown
    assert "- Backend reservation content scaling: no_scaling" in markdown
    assert "- Backend reservation content bottom margin: 14" in markdown
    assert "- Last request layout template: single_line" in markdown
    assert "- Last request stamp position: top" in markdown
    assert "- Last request show field names: no" in markdown
    assert "- Preview layout template: single_line" in markdown
    assert "- Preview stamp position: top" in markdown
    assert "- Preview show field names: no" in markdown
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
        **_capture_metadata_defaults(
            acceptance_tier=ENGINEERING_RUN,
            gate_verdict=NON_GATING,
            evidence_validation_warnings=("debug-only run",),
        ),
        first_render_ms=None,
        selection_count=0,
        sign_request_count=0,
        last_signature_page_index=None,
        last_signature_page_number=None,
        last_signature_has_visible_appearance=False,
        last_signature_output_path=None,
        last_signing_result_message=None,
        last_signing_result_success=None,
        preview_snapshot={
            "title": "Signature draft",
            "layout_template": None,
            "stamp_position": None,
            "show_field_names": False,
        },
        sign_request_snapshot=None,
        backend_reservation_snapshot=None,
        backend_reservation_error=None,
        output_file_exists=False,
        output_file_size_bytes=None,
        output_signature_count=None,
        output_signature_snapshot=None,
        output_visible_appearance_snapshot=None,
        preview_available=False,
        preview_text="",
        validation_text="",
        interaction_counts={},
        errors=("render failed",),
    )

    markdown = build_phase3_checklist_results_markdown(
        capture,
        checklist_template_path=str(template),
    )

    assert "- [ ] The placed rectangle can be resized or repositioned in the workflow." in markdown
    assert "- Automated gate verdict: `non_gating`" in markdown
    assert "- Evidence validation warnings: ['debug-only run']" in markdown
