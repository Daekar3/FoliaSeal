from pathlib import Path

from PIL import Image

from foliaseal.application.reusable_signing_models import SignaturePresetCatalog
from foliaseal.application.reusable_signing_objects import (
    InMemoryCatalogRepository,
    ReusableSigningObjects,
)
from foliaseal.application.signature_image_import import ManagedSignatureImageStore
from foliaseal.presentation.qt.appearance_profile_editor_widget import (
    AppearanceProfileEditorWidget,
)
from tests.unit.test_qt_signing_shell import _fake_bindings


def test_browse_remove_and_discard_clean_staged_managed_images(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (24, 24), (0, 0, 0, 255)).save(source)
    bindings = _fake_bindings()
    bindings.q_file_dialog.next_open_file_name = str(source)
    service = ReusableSigningObjects(
        InMemoryCatalogRepository(SignaturePresetCatalog(schema_version=1))
    )
    store = ManagedSignatureImageStore(tmp_path / "catalog")
    editor = AppearanceProfileEditorWidget(
        bindings=bindings,
        parent=None,
        library=service,
        image_store=store,
    )

    editor.controls.setup_form.appearance_controls.browse_image_button.click()
    staged = editor.controls.setup_form.build_draft().appearance.image_stamp_path
    assert staged is not None
    assert Path(staged).exists()

    editor.controls.setup_form.appearance_controls.remove_image_button.click()
    assert editor.controls.setup_form.build_draft().appearance.image_stamp_path is None
    assert not Path(staged).exists()

    editor.controls.setup_form.appearance_controls.browse_image_button.click()
    staged_again = editor.controls.setup_form.build_draft().appearance.image_stamp_path
    assert staged_again is not None
    assert Path(staged_again).exists()
    editor.discard_staged_images()
    assert not Path(staged_again).exists()
