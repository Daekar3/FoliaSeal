from foliaseal.application.signature_font_registry import (
    preview_font_family_supported,
    resolve_signature_font_face,
    validate_signature_font_request,
)


def test_resolve_signature_font_face_maps_legacy_source_sans_alias_to_bundled_sans() -> None:
    face = resolve_signature_font_face("Source Sans 3", bold=False, italic=False)

    assert face.canonical_family == "Sans Serif"
    assert face.preview_family_name == "Noto Sans"
    assert face.font_file.name == "NotoSans-Regular.ttf"


def test_resolve_signature_font_face_maps_serif_italic_to_bundled_otf_face() -> None:
    face = resolve_signature_font_face("Serif", bold=False, italic=True)

    assert face.preview_family_name == "Noto Serif"
    assert face.font_file.name == "NotoSerif-Italic.ttf"


def test_validate_signature_font_request_rejects_unsupported_cursive_italic() -> None:
    message = validate_signature_font_request("Cursive", bold=False, italic=True)

    assert message is not None
    assert "bundled italic face" in message


def test_preview_font_family_supported_reports_all_ui_families_as_direct() -> None:
    assert preview_font_family_supported("Sans Serif") is True
    assert preview_font_family_supported("Serif") is True
    assert preview_font_family_supported("Monospace") is True
    assert preview_font_family_supported("Cursive") is True
    assert preview_font_family_supported("Fantasy") is True
