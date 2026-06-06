from __future__ import annotations

import json
from pathlib import Path

from foliaseal.presentation.qt.phase3_preview_matrix_runner import (
    Phase3PreviewMatrixRunner,
)


def _runner(*, scenario_result):
    return Phase3PreviewMatrixRunner(
        load_preview_matrix_manifest=lambda _path: {
            "scenarios": [{"name": "Scenario A"}, {"name": "Scenario B"}]
        },
        execute_headless_preview_matrix_scenario=scenario_result,
        preview_matrix_error_result=lambda **kwargs: {
            "name": kwargs["scenario"]["name"],
            "error": type(kwargs["error"]).__name__,
        },
        preview_matrix_diagnostic_summary=lambda results: {
            "text_risk_count": sum(1 for item in results if item.get("text_risk"))
        },
        jsonable_capture=lambda payload: payload,
    )


def test_preview_matrix_runner_writes_summary_for_small_batch(tmp_path: Path) -> None:
    source_pdf = tmp_path / "fixture.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% fixture\n")
    artifacts_dir = tmp_path / "artifacts"

    runner = _runner(
        scenario_result=lambda **kwargs: {
            "scenario_name": kwargs["scenario"]["name"],
            "preview": {"can_submit": True},
            "render_capture": {},
            "backend_reservation_snapshot": {"layout_template": "multi_line"},
        }
    )

    summary = runner.run(
        pdf_path=str(source_pdf),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        scenario_manifest_path=str(tmp_path / "manifest.json"),
        artifacts_dir=str(artifacts_dir),
    )

    summary_path = artifacts_dir / "summary.json"
    assert summary_path.exists()
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    assert payload["scenario_count"] == 2
    assert payload["successful_scenario_count"] == 2
    assert [item["scenario_name"] for item in payload["results"]] == ["Scenario A", "Scenario B"]
    assert summary["scenario_count"] == 2


def test_preview_matrix_runner_records_error_results(tmp_path: Path) -> None:
    source_pdf = tmp_path / "fixture.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% fixture\n")
    artifacts_dir = tmp_path / "artifacts"

    def execute(**kwargs):
        if kwargs["scenario"]["name"] == "Scenario B":
            raise RuntimeError("boom")
        return {"name": kwargs["scenario"]["name"]}

    runner = _runner(scenario_result=execute)

    summary = runner.run(
        pdf_path=str(source_pdf),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        scenario_manifest_path=str(tmp_path / "manifest.json"),
        artifacts_dir=str(artifacts_dir),
    )

    assert summary["successful_scenario_count"] == 1
    assert summary["error_scenario_count"] == 1
    assert summary["results"][1]["error"] == "RuntimeError"


def test_preview_matrix_runner_preserves_canonical_render_capture_fields(
    tmp_path: Path,
) -> None:
    source_pdf = tmp_path / "fixture.pdf"
    source_pdf.write_bytes(b"%PDF-1.4\n% fixture\n")
    artifacts_dir = tmp_path / "artifacts"

    runner = Phase3PreviewMatrixRunner(
        load_preview_matrix_manifest=lambda _path: {"scenarios": [{"name": "Scenario A"}]},
        execute_headless_preview_matrix_scenario=lambda **_kwargs: {
            "name": "Scenario A",
            "preview_snapshot": {
                "can_submit": True,
                "render_capture": {
                    "card_bounds_px": {"x": 0, "y": 0, "width": 320, "height": 120},
                    "text_widget_bounds_px": {"x": 10, "y": 20, "width": 180, "height": 30},
                    "stamp_band_bounds_px": {"x": 10, "y": 60, "width": 100, "height": 24},
                    "text_rendered_content_bounds_px": {
                        "x": 12,
                        "y": 22,
                        "width": 160,
                        "height": 24,
                    },
                    "stamp_rendered_content_bounds_px": {
                        "x": 14,
                        "y": 62,
                        "width": 72,
                        "height": 18,
                    },
                },
            },
            "preview_text": "Ready",
            "validation_text": "Ready to sign.",
            "sign_request_snapshot": None,
            "backend_reservation_snapshot": None,
        },
        preview_matrix_error_result=lambda **kwargs: {
            "name": kwargs["scenario"]["name"],
            "error": type(kwargs["error"]).__name__,
        },
        preview_matrix_diagnostic_summary=lambda _results: {},
        jsonable_capture=lambda payload: payload,
    )

    summary = runner.run(
        pdf_path=str(source_pdf),
        certificate_path=str(tmp_path / "cert.p12"),
        passphrase="secret",
        scenario_manifest_path=str(tmp_path / "manifest.json"),
        artifacts_dir=str(artifacts_dir),
    )

    render_capture = summary["results"][0]["preview_snapshot"]["render_capture"]
    assert render_capture["card_bounds_px"]["width"] == 320
    assert render_capture["text_widget_bounds_px"]["height"] == 30
    assert render_capture["stamp_band_bounds_px"]["height"] == 24
    assert render_capture["text_rendered_content_bounds_px"]["width"] == 160
    assert render_capture["stamp_rendered_content_bounds_px"]["width"] == 72
