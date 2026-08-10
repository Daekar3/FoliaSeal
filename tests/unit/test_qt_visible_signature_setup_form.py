from foliaseal.application.signature_properties_coordinator import (
    VisibleSignaturePlacementDraft,
    VisibleSignatureSetupDraft,
)
from foliaseal.domain.models import (
    SignatureFieldKey,
    SignatureFieldSource,
    SignatureImageProminence,
    SignatureTextStyle,
)
from foliaseal.presentation.qt import visible_signature_setup_form as form_module
from foliaseal.presentation.qt.visible_signature_setup_form import (
    QtVisibleSignatureSetupForm,
)
from tests.support.signing_builders import build_signature_appearance
from tests.unit.test_qt_signing_shell import _fake_bindings


def test_setup_form_loads_visible_signature_draft_into_controls() -> None:
    form = QtVisibleSignatureSetupForm(bindings=_fake_bindings())
    appearance = build_signature_appearance(
        signer_label_prefix="Signed by Team",
        show_field_names=True,
        image_stamp_path="/tmp/stamp.png",
    )

    form.load(
        VisibleSignatureSetupDraft(
            appearance=appearance,
            placement=VisibleSignaturePlacementDraft(
                page_number=2,
                left_pt=40.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=54.0,
                enabled=True,
            ),
        )
    )

    assert form.appearance_controls.signer_label_prefix.text() == "Signed by Team"
    assert form.appearance_controls.show_field_names.isChecked() is True
    assert form.appearance_controls.font_family.currentText() == "Source Sans 3"
    assert form.placement_controls.page_spin.value() == 2
    assert form.placement_controls.width_spin.value() == 180.0
    assert (
        form.visible_text_controls.detail_label.text()
        == "Showing 7 of 8 standard signing fields with labels on."
    )
    assert form.build_draft().placement.enabled is True
    assert not hasattr(form, "field_controls")
    assert not hasattr(form.visible_text_controls, "advanced_toggle")
    assert not hasattr(form.visible_text_controls, "advanced_container")
    assert form.appearance_controls.datetime_format.currentText() == "%Y-%m-%d %H:%M"
    assert form.appearance_controls.field_order.count() == 8
    assert form.appearance_controls.text_color.text() == "#123456"
    assert form.appearance_controls.border_show.isChecked() is True
    assert form.appearance_controls.border_color.text() == "#333333"
    assert form.appearance_controls.background_color.text() == "#FFFFFF"
    assert form.appearance_controls.image_path_label.text() == "/tmp/stamp.png"
    assert form.appearance_controls.image_prominence.currentText() == "Primary"
    assert form.appearance_controls.preserve_image_alpha.isChecked() is True
    assert not hasattr(form.appearance_controls, "image_stamp_path")


def test_setup_form_builds_draft_and_normalizes_legacy_field_customizations() -> None:
    change_calls: list[str] = []
    page_changes: list[int] = []
    form = QtVisibleSignatureSetupForm(
        bindings=_fake_bindings(),
        on_change=lambda: change_calls.append("changed"),
        on_page_change=page_changes.append,
    )
    form.load(
        VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=False,
            ),
        )
    )

    form.appearance_controls.signer_label_prefix.setText("Signed by Product")
    form.appearance_controls.font_family.setCurrentText("Serif")
    form.appearance_controls.show_field_names.setChecked(True)
    form._field_visibility_checks[SignatureFieldKey.EMAIL].setChecked(False)
    form.placement_controls.page_spin.setValue(3)
    form.placement_controls.left_spin.setValue(55.0)
    form.placement_controls.bottom_spin.setValue(21.0)
    form.placement_controls.width_spin.setValue(144.0)
    form.placement_controls.height_spin.setValue(36.0)

    draft = form.build_draft()

    assert change_calls
    assert page_changes[-1] == 3
    assert draft.appearance.signer_label_prefix == "Signed by Product"
    assert draft.appearance.text_style.font_family == "Serif"
    assert draft.appearance.show_field_names is True
    assert draft.appearance.email.source == SignatureFieldSource.HIDDEN
    assert draft.appearance.email.show_in_visible_appearance is False
    assert draft.appearance.email.override_text is None
    assert draft.appearance.location.source == SignatureFieldSource.HIDDEN
    assert draft.appearance.location.show_in_visible_appearance is False
    assert draft.appearance.location.override_text is None
    for field_key, binding in draft.appearance.iter_field_bindings():
        if field_key in (SignatureFieldKey.EMAIL, SignatureFieldKey.LOCATION):
            continue
        assert binding.source == SignatureFieldSource.DERIVED
        assert binding.show_in_visible_appearance is True
        assert binding.override_text is None
    assert draft.placement == VisibleSignaturePlacementDraft(
        page_number=3,
        left_pt=55.0,
        bottom_pt=21.0,
        width_pt=144.0,
        height_pt=36.0,
        enabled=True,
    )


def test_setup_form_preserves_hidden_loaded_appearance_values_on_rebuild() -> None:
    form = QtVisibleSignatureSetupForm(bindings=_fake_bindings())
    appearance = build_signature_appearance(
        datetime_format="custom-format",
        image_stamp_path="/tmp/stamp.png",
        text_style=SignatureTextStyle(
            font_family="Source Sans 3",
            font_size_pt=9.5,
            bold=True,
            italic=False,
            text_color_hex="#ABCDEF",
        ),
    )

    form.load(
        VisibleSignatureSetupDraft(
            appearance=appearance,
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=False,
            ),
        )
    )

    form.appearance_controls.font_family.setCurrentText("Serif")
    draft = form.build_draft()

    assert draft.appearance.text_style.font_family == "Serif"
    assert draft.appearance.text_style.text_color_hex == "#ABCDEF"
    assert draft.appearance.datetime_format == "custom-format"
    assert draft.appearance.image_stamp_path == "/tmp/stamp.png"
    assert draft.appearance.box_style == appearance.box_style


def test_setup_form_round_trips_changed_image_and_text_controls() -> None:
    form = QtVisibleSignatureSetupForm(bindings=_fake_bindings())
    form.load(
        VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(image_stamp_path=None),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=False,
            ),
        )
    )

    form.appearance_controls.text_color.setText("#AABBCC")
    form.appearance_controls.image_prominence.setCurrentText("Balanced")
    form.appearance_controls.preserve_image_alpha.setChecked(False)
    form.set_image_stamp_path("/managed/signature.png")

    appearance = form.build_draft().appearance

    assert appearance.text_style.text_color_hex == "#AABBCC"
    assert appearance.image_stamp_path == "/managed/signature.png"
    assert appearance.image_prominence is SignatureImageProminence.BALANCED
    assert appearance.preserve_image_alpha is False


def test_setup_form_disables_unsupported_font_styles() -> None:
    form = QtVisibleSignatureSetupForm(bindings=_fake_bindings())

    def _reject_font_variant(
        family: str,
        *,
        bold: bool,
        italic: bool,
    ) -> str | None:
        if family != "Limited Font":
            return None
        if bold or italic:
            return "unsupported"
        return None

    appearance = build_signature_appearance(
        text_style=SignatureTextStyle(
            font_family="Limited Font",
            font_size_pt=9.5,
            bold=False,
            italic=False,
            text_color_hex="#123456",
        )
    )
    monkeypatch_target = "validate_signature_font_request"
    original = getattr(form_module, monkeypatch_target)
    setattr(form_module, monkeypatch_target, _reject_font_variant)
    try:
        form.load(
            VisibleSignatureSetupDraft(
                appearance=appearance,
                placement=VisibleSignaturePlacementDraft(
                    page_number=1,
                    left_pt=24.0,
                    bottom_pt=18.0,
                    width_pt=180.0,
                    height_pt=48.0,
                    enabled=False,
                ),
            )
        )
    finally:
        setattr(form_module, monkeypatch_target, original)

    assert form.appearance_controls.bold.enabled is False
    assert form.appearance_controls.italic.enabled is False


def test_setup_form_show_field_names_updates_visible_text_summary() -> None:
    change_calls: list[str] = []
    form = QtVisibleSignatureSetupForm(
        bindings=_fake_bindings(),
        on_change=lambda: change_calls.append("changed"),
    )
    form.load(
        VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=False,
            ),
        )
    )

    change_calls.clear()
    form.appearance_controls.show_field_names.setChecked(True)

    assert change_calls == ["changed"]
    assert (
        form.visible_text_controls.detail_label.text()
        == "Showing 7 of 8 standard signing fields with labels on."
    )


def test_setup_form_preserves_loaded_field_order_when_rebuilding_draft() -> None:
    form = QtVisibleSignatureSetupForm(bindings=_fake_bindings())
    custom_field_order = (
        SignatureFieldKey.SIGNING_TIME,
        SignatureFieldKey.DISTINGUISHED_NAME,
        SignatureFieldKey.COMMON_NAME,
        SignatureFieldKey.EMAIL,
        SignatureFieldKey.TITLE,
        SignatureFieldKey.COMPANY,
        SignatureFieldKey.REASON,
        SignatureFieldKey.LOCATION,
    )

    form.load(
        VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(field_order=custom_field_order),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=False,
            ),
        )
    )

    draft = form.build_draft()

    assert draft.appearance.field_order == custom_field_order


def test_setup_form_edits_bounded_time_color_border_and_field_order_controls() -> None:
    form = QtVisibleSignatureSetupForm(bindings=_fake_bindings())
    form.load(
        VisibleSignatureSetupDraft(
            appearance=build_signature_appearance(),
            placement=VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=180.0,
                height_pt=48.0,
                enabled=False,
            ),
        )
    )

    controls = form.appearance_controls
    controls.datetime_format.setCurrentText("Aug 8, 2026, 2:35 PM UTC")
    controls.text_color.setText("#123456")
    controls.border_show.setChecked(False)
    controls.border_color.setText("#654321")
    controls.border_width.setValue(2.5)
    controls.background_color.setText("#F0F0F0")
    controls.move_field_down.click()

    draft = form.build_draft().appearance

    assert draft.datetime_format == "%b %-d, %Y, %-I:%M %p %Z"
    assert draft.text_style.text_color_hex == "#123456"
    assert draft.box_style.show_border is False
    assert draft.box_style.border_color_hex == "#654321"
    assert draft.box_style.border_width_pt == 2.5
    assert draft.box_style.background_color_hex == "#F0F0F0"
    assert draft.field_order[:2] == (
        SignatureFieldKey.COMMON_NAME,
        SignatureFieldKey.DISTINGUISHED_NAME,
    )
