from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from foliaseal.presentation.qt.phase3_harness_workspace import (
    Phase3HarnessCaptureCommand,
)
from foliaseal.presentation.qt.phase3_signed_acceptance_scenario_executor import (
    Phase3SignedAcceptanceScenarioExecutor,
)
from tests.support.phase3_builders import build_signature_rect, build_signing_request


class _FakeShell:
    pass


class _FakeWorkspace:
    def __init__(self, *, request=None, capture=None) -> None:
        self._request = request
        self._capture = capture or {
            "preview_snapshot": {"render_capture": {"rendered": True}},
            "preview_text": "Preview text",
            "validation_text": "Ready to sign.",
            "sign_request_snapshot": None if request is None else {"request": True},
            "backend_reservation_snapshot": None,
        }
        self.capture_commands: list[Phase3HarnessCaptureCommand] = []

    def current_request(self):
        return self._request

    def last_signing_result(self):
        return None

    def capture_state(self, command: Phase3HarnessCaptureCommand):
        self.capture_commands.append(command)
        return self._capture


def _executor(**overrides) -> Phase3SignedAcceptanceScenarioExecutor:
    defaults = {
        "apply_preview_matrix_scenario": lambda **_kwargs: None,
        "build_workspace": lambda **_kwargs: _FakeWorkspace(),
        "scenario_slug": lambda name: name.lower().replace(" ", "-"),
        "snapshot_signing_result_payload": lambda result: {"success": result.success},
        "snapshot_successful_signed_output": lambda **_kwargs: {
            "output_file_exists": True,
            "output_signature_count": 1,
            "output_signature_snapshot": {"embedded": True},
            "output_verification_snapshot": {"trusted": True},
            "output_visible_appearance_snapshot": {"visible": True},
            "signed_output_render_snapshot": {"preview_vs_signed_output_passed": True},
            "signed_output_preview_comparison": {"preview_vs_signed_output_passed": True},
        },
    }
    defaults.update(overrides)
    return Phase3SignedAcceptanceScenarioExecutor(**defaults)


def test_signed_acceptance_scenario_executor_returns_preview_only_result_without_request(
    tmp_path: Path,
) -> None:
    shell = _FakeShell()
    workspace = _FakeWorkspace()
    executor = _executor(build_workspace=lambda **_kwargs: workspace)
    execute_calls: list[object] = []
    sign_executor = SimpleNamespace(execute=lambda request: execute_calls.append(request))

    result = executor.run(
        shell=shell,
        scenario={"name": "Scenario A", "expected_outcome": "validation_rejection"},
        profile_store=object(),
        artifacts_dir=tmp_path,
        base_input_path=tmp_path / "input.pdf",
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        sign_executor=sign_executor,
    )

    assert result["name"] == "Scenario A"
    assert result["expected_outcome"] == "validation_rejection"
    assert result["preview_text"] == "Preview text"
    assert result["validation_text"] == "Ready to sign."
    assert result["preview_snapshot"]["render_capture"] == {"rendered": True}
    assert result["sign_request_snapshot"] is None
    assert result["backend_reservation_snapshot"] is None
    assert result["signing_result"] is None
    assert result["output_file_exists"] is False
    assert execute_calls == []
    assert workspace.capture_commands == [
        Phase3HarnessCaptureCommand(
            request=None,
            artifacts_dir=str(tmp_path),
            artifact_basename="scenario-a",
            capture_index=1,
            capture_kind="signed_acceptance_preview",
        )
    ]


def test_signed_acceptance_scenario_executor_rewrites_request_and_merges_output_snapshot(
    tmp_path: Path,
) -> None:
    request = build_signing_request(
        tmp_path,
        input_name="draft-input.pdf",
        output_name="draft-output.pdf",
        certificate_name="draft-cert.p12",
        passphrase="draft-secret",
        timestamp_required=False,
        signature_rect=build_signature_rect(page_index=2, width_pt=240.0, height_pt=72.0),
    )
    shell = _FakeShell()
    snapshot_calls: list[dict[str, object]] = []
    sign_requests: list[object] = []
    scenario_output = tmp_path / "scenario-b_signed.pdf"
    workspace = _FakeWorkspace(
        request=request,
        capture={
            "preview_snapshot": {"render_capture": {"rendered": True}},
            "preview_text": "Preview text",
            "validation_text": "Ready to sign.",
            "sign_request_snapshot": {
                "input_pdf_path": request.input_pdf_path,
                "output_pdf_path": request.output_pdf_path,
            },
            "backend_reservation_snapshot": {"reserved": True},
        },
    )

    def execute(request_obj):
        sign_requests.append(request_obj)
        scenario_output.write_bytes(b"%PDF-1.4\n")
        return SimpleNamespace(success=True)

    executor = _executor(
        build_workspace=lambda **_kwargs: workspace,
        snapshot_signing_result_payload=lambda result: {"success": result.success},
        snapshot_successful_signed_output=lambda **kwargs: snapshot_calls.append(kwargs)
        or {
            "output_file_exists": True,
            "output_signature_count": 2,
            "output_signature_snapshot": {"embedded": True},
            "output_verification_snapshot": {"trusted": True},
            "output_visible_appearance_snapshot": {"visible": True},
            "signed_output_render_snapshot": {"comparison_path": "cmp.png"},
            "signed_output_preview_comparison": {"comparison_path": "cmp.png"},
        },
    )

    result = executor.run(
        shell=shell,
        scenario={
            "name": "Scenario B",
            "profile_name": "Default",
            "expected_outcome": "success",
            "expected_failure_message_contains": "unused",
        },
        profile_store=object(),
        artifacts_dir=tmp_path,
        base_input_path=tmp_path / "source.pdf",
        certificate_path=str(tmp_path / "matrix-cert.p12"),
        passphrase="matrix-secret",
        sign_executor=SimpleNamespace(execute=execute),
    )

    assert len(sign_requests) == 1
    scenario_request = sign_requests[0]
    assert scenario_request.input_pdf_path == str(tmp_path / "source.pdf")
    assert scenario_request.output_pdf_path == str(scenario_output)
    assert scenario_request.certificate_path == str(tmp_path / "matrix-cert.p12")
    assert scenario_request.passphrase == "matrix-secret"
    assert scenario_request.signature_rect.page_index == 2

    assert snapshot_calls[0]["output_file"] == scenario_output
    assert snapshot_calls[0]["page_index"] == 2
    assert snapshot_calls[0]["preview_text"] == "Preview text"
    assert workspace.capture_commands == [
        Phase3HarnessCaptureCommand(
            request=request,
            artifacts_dir=str(tmp_path),
            artifact_basename="scenario-b",
            capture_index=1,
            capture_kind="signed_acceptance_preview",
        )
    ]

    assert result["profile_name"] == "Default"
    assert result["expected_outcome"] == "success"
    assert result["backend_reservation_snapshot"] == {"reserved": True}
    assert result["sign_request_snapshot"] == {
        "input_pdf_path": request.input_pdf_path,
        "output_pdf_path": request.output_pdf_path,
    }
    assert result["signing_result"] == {"success": True}
    assert result["output_file_exists"] is True
    assert result["output_signature_count"] == 2
    assert result["signed_output_preview_comparison"] == {"comparison_path": "cmp.png"}
