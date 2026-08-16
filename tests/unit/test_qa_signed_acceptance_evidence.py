import logging
from pathlib import Path

import pytest

from foliaseal.application.evidence_core import (
    validate_signed_acceptance_matrix_summary,
)
from foliaseal.application.evidence_service import (
    EvidenceMatrixRequest,
    SignedAcceptanceEvidenceRequest,
)
from foliaseal.application.qa_signed_acceptance_assets import (
    SIGNED_FIT_REJECTION_SCENARIO_MANIFEST,
    SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST,
)
from foliaseal.application.qa_signed_acceptance_generation import (
    SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE,
    GeneratedSignedAcceptanceAssets,
)
from foliaseal.presentation.qt.signed_acceptance_evidence import (
    DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH,
    build_default_evidence_service,
)

_PYHANKO_LOGGER_NAME = "pyhanko.sign.validation.generic_cms"
_PYHANKO_LAYOUT_LOGGER_NAME = "pyhanko.pdf_utils.layout"


def _assets(root: Path) -> GeneratedSignedAcceptanceAssets:
    return GeneratedSignedAcceptanceAssets(
        fixture_pdf=root / "artifacts/generated_acceptance_assets/signed_acceptance_fixture.pdf",
        identity_p12=root / "artifacts/generated_acceptance_assets/signed_acceptance_identity.p12",
        stamp_image=root / "artifacts/generated_acceptance_assets/signed_acceptance_stamp.png",
        signed_acceptance_manifest=(
            root / "artifacts/preview_sweep_assets/signed_acceptance_matrix.json"
        ),
        signed_preview_parity_manifest=(
            root / "artifacts/preview_sweep_assets/signed_preview_parity_matrix.json"
        ),
        signed_fit_rejection_manifest=(
            root / "artifacts/preview_sweep_assets/signed_fit_rejection_matrix.json"
        ),
    )


def _passing_summary(*, artifacts_dir: str, scenario_count: int = 3) -> dict[str, object]:
    return {
        "acceptance_expectations_passed": True,
        "scenario_count": scenario_count,
        "successful_signing_run_count": scenario_count,
        "matched_expected_intentional_rejection_count": 0,
        "expected_outcome_mismatch_count": 0,
        "cryptographic_validation_failure_count": 0,
        "preview_output_comparison_failure_count": 0,
        "annotation_rect_mismatch_count": 0,
        "error_scenario_count": 0,
        "artifacts_dir": artifacts_dir,
    }


def _signed_acceptance_evidence(
    *,
    artifacts_root: Path,
    asset_generator,
    matrix_runner,
    suppress_known_runtime_chatter: bool = True,
):
    service = build_default_evidence_service(
        asset_generator=asset_generator,
        matrix_runner=matrix_runner,
    )
    return service.signed_acceptance_evidence(
        SignedAcceptanceEvidenceRequest(
            artifacts_root=artifacts_root,
            summary_markdown_path=(
                artifacts_root / DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH
            ),
            passphrase=SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE.decode("utf-8"),
            suppress_known_runtime_chatter=suppress_known_runtime_chatter,
            required_manifests=(
                SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST,
                SIGNED_FIT_REJECTION_SCENARIO_MANIFEST,
            ),
            default_summary_relative_path=DEFAULT_SIGNED_ACCEPTANCE_EVIDENCE_SUMMARY_PATH,
        )
    )


def test_signed_acceptance_evidence_generates_assets_runs_two_strict_gates_and_writes_summary(
    tmp_path: Path,
) -> None:
    generated_roots: list[Path] = []
    matrix_calls: list[EvidenceMatrixRequest] = []

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        generated_roots.append(root)
        return _assets(root)

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        matrix_calls.append(request)
        return _passing_summary(artifacts_dir=request.artifacts_dir)

    evidence = _signed_acceptance_evidence(
        artifacts_root=tmp_path,
        asset_generator=fake_asset_generator,
        matrix_runner=fake_matrix_runner,
    ).as_dict()

    assert generated_roots == [tmp_path]
    assert [Path(call.scenario_manifest_path).name for call in matrix_calls] == [
        "signed_preview_parity_matrix.json",
        "signed_fit_rejection_matrix.json",
    ]
    assert evidence["passed"] is True
    summary_path = Path(evidence["summary_markdown_path"])
    assert summary_path == tmp_path / "artifacts/signed_acceptance_evidence_summary.md"
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Overall result: PASS" in summary_text
    assert "signed_acceptance_matrix" not in summary_text
    assert "signed_preview_parity_matrix" in summary_text
    assert "signed_fit_rejection_matrix" in summary_text


def test_signed_acceptance_evidence_writes_failure_summary_and_raises(
    tmp_path: Path,
) -> None:
    call_count = 0

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        summary = _passing_summary(artifacts_dir=request.artifacts_dir)
        if call_count == 1:
            summary["preview_output_comparison_failure_count"] = 1
            summary["acceptance_expectations_passed"] = False
            summary["acceptance_expectation_errors"] = [
                "Expected zero preview/output comparison failures, observed 1."
            ]
        return summary

    with pytest.raises(RuntimeError, match="signed_preview_parity_matrix"):
        _signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    summary_path = tmp_path / "artifacts/signed_acceptance_evidence_summary.md"
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Overall result: FAIL" in summary_text
    assert "expected preview_output_comparison_failure_count=0, observed 1" in summary_text
    assert "Expected zero preview/output comparison failures, observed 1." in summary_text
    assert "Preview/output comparison failures: 1" in summary_text


def test_signed_acceptance_evidence_writes_failure_summary_when_matrix_raises(
    tmp_path: Path,
) -> None:
    call_count = 0

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("Qt renderer unavailable")
        return _passing_summary(artifacts_dir=request.artifacts_dir)

    with pytest.raises(RuntimeError, match="Qt renderer unavailable"):
        _signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    summary_path = tmp_path / "artifacts/signed_acceptance_evidence_summary.md"
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Overall result: FAIL" in summary_text
    assert (
        "matrix runner failed before returning a summary: Qt renderer unavailable" in summary_text
    )


def test_signed_acceptance_evidence_suppresses_known_dummy_tsa_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger(_PYHANKO_LOGGER_NAME)

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(_request: EvidenceMatrixRequest) -> dict[str, object]:
        logger.warning(
            "Validation error [cert context: Common Name: FoliaSeal TSA, "
            "Organization: FoliaSeal, Country: US]: The X.509 certificate "
            "provided is self-signed - test"
        )
        return _passing_summary(artifacts_dir="artifacts/run")

    with caplog.at_level(logging.WARNING, logger=_PYHANKO_LOGGER_NAME):
        _signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    assert "Validation error [cert context:" not in caplog.text


def test_signed_acceptance_evidence_keeps_unmatched_pyhanko_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger(_PYHANKO_LOGGER_NAME)

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(_request: EvidenceMatrixRequest) -> dict[str, object]:
        logger.warning("Validation error [cert context: Real TSA]: network timeout")
        return _passing_summary(artifacts_dir="artifacts/run")

    with caplog.at_level(logging.WARNING, logger=_PYHANKO_LOGGER_NAME):
        _signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    assert "Real TSA" in caplog.text


def test_signed_acceptance_evidence_suppresses_known_layout_warning(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger(_PYHANKO_LAYOUT_LOGGER_NAME)

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        if Path(request.scenario_manifest_path).name == "signed_fit_rejection_matrix.json":
            logger.warning(
                "Content box width/height 397 is too wide for container size 170 "
                "with margins (4, 4); post_margin will be ignored"
            )
        return _passing_summary(artifacts_dir=request.artifacts_dir)

    with caplog.at_level(logging.WARNING, logger=_PYHANKO_LAYOUT_LOGGER_NAME):
        _signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    assert "post_margin will be ignored" not in caplog.text


def test_signed_acceptance_evidence_keeps_layout_warning_outside_rejection_matrix(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger(_PYHANKO_LAYOUT_LOGGER_NAME)

    def fake_asset_generator(*, root: Path) -> GeneratedSignedAcceptanceAssets:
        return _assets(root)

    def fake_matrix_runner(request: EvidenceMatrixRequest) -> dict[str, object]:
        if Path(request.scenario_manifest_path).name == "signed_preview_parity_matrix.json":
            logger.warning(
                "Content box width/height 397 is too wide for container size 170 "
                "with margins (4, 4); post_margin will be ignored"
            )
        return _passing_summary(artifacts_dir=request.artifacts_dir)

    with caplog.at_level(logging.WARNING, logger=_PYHANKO_LAYOUT_LOGGER_NAME):
        _signed_acceptance_evidence(
            artifacts_root=tmp_path,
            asset_generator=fake_asset_generator,
            matrix_runner=fake_matrix_runner,
        )

    assert "post_margin will be ignored" in caplog.text


def test_validate_signed_acceptance_matrix_summary_rejects_missing_counter() -> None:
    summary = _passing_summary(artifacts_dir="artifacts/run")
    del summary["annotation_rect_mismatch_count"]

    errors = validate_signed_acceptance_matrix_summary(
        name="signed_acceptance_matrix",
        summary=summary,
    )

    assert errors == [
        "signed_acceptance_matrix: Matrix summary missing integer counter "
        "'annotation_rect_mismatch_count'."
    ]
