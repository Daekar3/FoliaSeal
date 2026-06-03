import json
from types import SimpleNamespace

from foliaseal.presentation.qt.phase3_harness_reporting import (
    Phase3HarnessReportRequest,
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
