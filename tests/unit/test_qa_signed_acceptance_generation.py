import json
from pathlib import Path

from cryptography.hazmat.primitives.serialization import pkcs12
from pyhanko.pdf_utils.reader import PdfFileReader

from foliaseal.application.qa_preview_stress_fixtures import (
    STRESS_VISIBLE_APPEARANCE_PROFILE,
)
from foliaseal.application.qa_signed_acceptance_assets import (
    SIGNED_ACCEPTANCE_FIXTURE_PDF,
    SIGNED_ACCEPTANCE_IDENTITY_P12,
    SIGNED_ACCEPTANCE_SCENARIO_MANIFEST,
    SIGNED_FIT_REJECTION_SCENARIO_MANIFEST,
    SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST,
)
from foliaseal.application.qa_signed_acceptance_generation import (
    SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE,
    SIGNED_ACCEPTANCE_STAMP_IMAGE,
    build_signed_acceptance_manifest,
    build_signed_fit_rejection_manifest,
    build_signed_preview_parity_manifest,
    generate_signed_acceptance_assets,
)
from foliaseal.presentation.qt.interactive_harness import _load_preview_matrix_manifest


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_generate_signed_acceptance_assets_writes_parseable_pdf_identity_and_manifests(
    tmp_path: Path,
) -> None:
    assets = generate_signed_acceptance_assets(root=tmp_path)

    assert assets.fixture_pdf == tmp_path / SIGNED_ACCEPTANCE_FIXTURE_PDF
    assert assets.identity_p12 == tmp_path / SIGNED_ACCEPTANCE_IDENTITY_P12
    assert assets.stamp_image == tmp_path / SIGNED_ACCEPTANCE_STAMP_IMAGE
    assert assets.signed_acceptance_manifest == tmp_path / SIGNED_ACCEPTANCE_SCENARIO_MANIFEST
    assert (
        assets.signed_preview_parity_manifest
        == tmp_path / SIGNED_PREVIEW_PARITY_SCENARIO_MANIFEST
    )
    assert assets.signed_fit_rejection_manifest == tmp_path / SIGNED_FIT_REJECTION_SCENARIO_MANIFEST

    with assets.fixture_pdf.open("rb") as handle:
        reader = PdfFileReader(handle)
        assert len(list(reader.root["/Pages"]["/Kids"])) == 1

    key, cert, extra_certs = pkcs12.load_key_and_certificates(
        assets.identity_p12.read_bytes(),
        SIGNED_ACCEPTANCE_IDENTITY_PASSPHRASE,
    )
    assert key is not None
    assert cert is not None
    assert extra_certs == []

    for manifest_path in (
        assets.signed_acceptance_manifest,
        assets.signed_preview_parity_manifest,
        assets.signed_fit_rejection_manifest,
    ):
        manifest = _load_preview_matrix_manifest(str(manifest_path))
        assert manifest["fixture_profile"] == STRESS_VISIBLE_APPEARANCE_PROFILE
        assert manifest["timestamping_mode"] == "dummy"
        assert manifest["acceptance_expectations"]["scenario_count"] == len(
            manifest["scenarios"]
        )
        assert any(
            scenario["appearance_overrides"]["image_stamp_path"] == str(assets.stamp_image)
            for scenario in manifest["scenarios"]
        )


def test_signed_acceptance_manifest_matches_current_positive_and_negative_contract() -> None:
    manifest = build_signed_acceptance_manifest(SIGNED_ACCEPTANCE_STAMP_IMAGE)
    names = {scenario["name"] for scenario in manifest["scenarios"]}
    outcomes = {
        scenario["name"]: scenario["expected_outcome"] for scenario in manifest["scenarios"]
    }

    assert manifest["fixture_role"] == "signed_acceptance"
    assert manifest["fixture_profile"] == STRESS_VISIBLE_APPEARANCE_PROFILE
    assert manifest["timestamping_mode"] == "dummy"
    assert manifest["acceptance_expectations"]["minimum_successful_signing_run_count"] == 7
    assert manifest["acceptance_expectations"]["expected_intentional_rejection_count"] == 3
    assert manifest["acceptance_expectations"]["scenario_count"] == 10
    assert {
        "single_line_top_label_success",
        "single_line_bottom_label_success",
        "single_line_left_label_reject",
        "multi_line_top_medium_success",
        "multi_line_bottom_medium_success",
        "multi_line_right_medium_reject",
        "wrapped_block_left_plain_success",
        "wrapped_block_right_plain_reject",
        "wrapped_block_top_plain_success",
    } <= names
    assert outcomes["single_line_left_label_reject"] == "validation_rejection"
    assert outcomes["multi_line_right_medium_reject"] == "validation_rejection"
    assert outcomes["wrapped_block_right_plain_reject"] == "validation_rejection"
    assert any(scenario.get("timestamp_required") is True for scenario in manifest["scenarios"])


def test_signed_preview_parity_manifest_covers_expected_success_matrix() -> None:
    manifest = build_signed_preview_parity_manifest(SIGNED_ACCEPTANCE_STAMP_IMAGE)
    names = {scenario["name"] for scenario in manifest["scenarios"]}
    positions = {
        scenario["appearance_overrides"]["stamp_position"] for scenario in manifest["scenarios"]
    }
    families = {
        scenario["appearance_overrides"]["layout_template"] for scenario in manifest["scenarios"]
    }

    assert manifest["fixture_role"] == "signed_preview_parity"
    assert manifest["acceptance_expectations"]["scenario_count"] == 18
    assert manifest["acceptance_expectations"]["minimum_successful_signing_run_count"] == 18
    assert manifest["acceptance_expectations"]["expected_intentional_rejection_count"] == 0
    assert all(scenario["expected_outcome"] == "success" for scenario in manifest["scenarios"])
    assert families == {"single_line", "multi_line", "wrapped_block"}
    assert {"top", "bottom", "left", "right"} <= positions
    assert {
        "single_line_top_no_stamp_sparse_large",
        "single_line_bottom_no_stamp_sparse_relaxed",
        "single_line_left_stamp_sparse_relaxed",
        "single_line_right_no_stamp_sparse_relaxed",
        "multi_line_bottom_sparse_large",
        "multi_line_top_medium_relaxed",
        "multi_line_bottom_medium_relaxed",
        "wrapped_block_left_sparse_large",
        "multi_line_right_medium_large",
        "wrapped_block_top_sparse_relaxed",
        "wrapped_block_right_medium_relaxed",
    } <= names
    assert {
        "single_line_left_stamp_sparse_large",
        "single_line_right_stamp_sparse_large",
        "wrapped_block_top_dense_large",
    }.isdisjoint(names)


def test_signed_fit_rejection_manifest_covers_boundary_rejections() -> None:
    parity = build_signed_preview_parity_manifest(SIGNED_ACCEPTANCE_STAMP_IMAGE)
    rejection = build_signed_fit_rejection_manifest(SIGNED_ACCEPTANCE_STAMP_IMAGE)
    rejection_names = {scenario["name"] for scenario in rejection["scenarios"]}
    parity_names = {scenario["name"] for scenario in parity["scenarios"]}

    assert rejection["fixture_role"] == "signed_fit_rejection"
    assert rejection["acceptance_expectations"]["scenario_count"] == 3
    assert rejection["acceptance_expectations"]["minimum_successful_signing_run_count"] == 0
    assert rejection["acceptance_expectations"]["expected_intentional_rejection_count"] == 3
    assert rejection_names == {
        "single_line_left_stamp_sparse_large",
        "single_line_right_stamp_sparse_large",
        "wrapped_block_top_dense_large",
    }
    assert all(
        scenario["expected_outcome"] == "validation_rejection"
        for scenario in rejection["scenarios"]
    )
    assert rejection_names.isdisjoint(parity_names)


def test_generated_manifests_match_builder_payloads(tmp_path: Path) -> None:
    assets = generate_signed_acceptance_assets(root=tmp_path)

    assert _read_json(assets.signed_acceptance_manifest) == build_signed_acceptance_manifest(
        str(assets.stamp_image)
    )
    assert _read_json(
        assets.signed_preview_parity_manifest
    ) == build_signed_preview_parity_manifest(str(assets.stamp_image))
    assert _read_json(assets.signed_fit_rejection_manifest) == build_signed_fit_rejection_manifest(
        str(assets.stamp_image)
    )
