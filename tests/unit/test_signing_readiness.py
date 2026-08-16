import pytest

from foliaseal.application.signing_readiness import (
    SigningReadinessAction,
    SigningReadinessInputs,
    SigningReadinessMissingInput,
    SigningReadinessStage,
    project_signing_readiness,
)


def _inputs(**overrides) -> SigningReadinessInputs:
    values = dict(
        selected_preset_name="Approval",
        has_saved_presets=True,
        certificate_selected=True,
        certificate_blocking=False,
        certificate_detail="",
        certificate_warning=False,
        placement_present=True,
        validation_text="Ready to sign.",
        ready_to_sign=True,
    )
    values.update(overrides)
    return SigningReadinessInputs(**values)


@pytest.mark.parametrize(
    ("overrides", "stage", "action"),
    [
        (
            {"selected_preset_name": None, "has_saved_presets": False},
            SigningReadinessStage.SELECT_PRESET,
            SigningReadinessAction.CHOOSE_SETUP,
        ),
        (
            {"certificate_selected": False},
            SigningReadinessStage.SETUP_REQUIRED,
            SigningReadinessAction.COMPLETE_SETUP,
        ),
        (
            {"certificate_blocking": True, "certificate_detail": "Certificate is expired."},
            SigningReadinessStage.SETUP_REQUIRED,
            SigningReadinessAction.COMPLETE_SETUP,
        ),
        (
            {"placement_present": False},
            SigningReadinessStage.PLACE_SIGNATURE,
            SigningReadinessAction.PLACE_SIGNATURE,
        ),
        (
            {"ready_to_sign": False, "validation_text": "Appearance does not fit."},
            SigningReadinessStage.REVIEW_READINESS,
            SigningReadinessAction.REVIEW_READINESS,
        ),
    ],
)
def test_projection_evaluates_blockers_in_ui_spec_order(overrides, stage, action) -> None:
    readiness = project_signing_readiness(_inputs(**overrides))

    assert readiness.stage is stage
    assert readiness.recommended_action is action
    assert readiness.can_sign is False


def test_ready_projection_preserves_nonblocking_certificate_caveat() -> None:
    readiness = project_signing_readiness(
        _inputs(
            certificate_warning=True,
            certificate_detail="Self-signed certificate — ready for local signing.",
        )
    )

    assert readiness.stage is SigningReadinessStage.READY
    assert readiness.can_sign is True
    assert readiness.recommended_action is SigningReadinessAction.SIGN
    assert readiness.caveat == "Self-signed certificate — ready for local signing."
    assert readiness.detail.endswith(readiness.caveat)


def test_saved_catalog_does_not_force_preset_selection_after_manual_edit() -> None:
    readiness = project_signing_readiness(
        _inputs(
            selected_preset_name=None,
            has_saved_presets=True,
            ready_to_sign=False,
            validation_text="Appearance is incomplete.",
        )
    )

    assert readiness.stage is SigningReadinessStage.REVIEW_READINESS
    assert readiness.recommended_action is SigningReadinessAction.REVIEW_READINESS
    assert readiness.detail == "Appearance is incomplete."


def test_partial_preset_without_certificate_names_the_per_document_next_step() -> None:
    readiness = project_signing_readiness(
        _inputs(
            certificate_selected=False,
            selected_preset_name="Travel approval",
            selected_preset_missing_certificate=True,
            ready_to_sign=False,
        )
    )

    assert readiness.stage is SigningReadinessStage.SETUP_REQUIRED
    assert readiness.heading == "Choose a certificate for this preset"
    assert readiness.recommended_action is SigningReadinessAction.COMPLETE_SETUP
    assert readiness.missing_input is SigningReadinessMissingInput.CERTIFICATE
    assert "Travel approval" in readiness.detail
    assert "certificate configuration for this document" in readiness.detail


def test_blocking_certificate_error_takes_precedence_over_partial_preset_guidance() -> None:
    readiness = project_signing_readiness(
        _inputs(
            certificate_blocking=True,
            certificate_detail="Certificate is expired.",
            selected_preset_name="Travel approval",
            selected_preset_missing_certificate=True,
            ready_to_sign=False,
        )
    )

    assert readiness.stage is SigningReadinessStage.SETUP_REQUIRED
    assert readiness.heading == "Setup required"
    assert readiness.detail == "Certificate is expired."
    assert readiness.recommended_action is SigningReadinessAction.COMPLETE_SETUP
    assert readiness.missing_input is None


def test_partial_preset_without_placement_advances_after_certificate_selection() -> None:
    readiness = project_signing_readiness(
        _inputs(
            selected_preset_name="Travel approval",
            selected_preset_missing_placement=True,
            placement_present=False,
            ready_to_sign=False,
        )
    )

    assert readiness.stage is SigningReadinessStage.PLACE_SIGNATURE
    assert readiness.heading == "Place the signature for this preset"
    assert readiness.recommended_action is SigningReadinessAction.PLACE_SIGNATURE
    assert readiness.missing_input is SigningReadinessMissingInput.PLACEMENT
    assert "Travel approval" in readiness.detail
    assert "for this document" in readiness.detail


def test_existing_placement_suppresses_partial_preset_placement_guidance() -> None:
    readiness = project_signing_readiness(
        _inputs(
            selected_preset_name="Travel approval",
            selected_preset_missing_placement=True,
            placement_present=True,
        )
    )

    assert readiness.stage is SigningReadinessStage.READY
    assert readiness.missing_input is None
