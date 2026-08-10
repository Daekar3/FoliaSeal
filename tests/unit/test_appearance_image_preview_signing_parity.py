from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PIL import Image

from foliaseal.application.reusable_signing_models import AppearanceProfile, _serialize_appearance
from foliaseal.application.reusable_signing_objects import (
    ReusableObjectKind,
    ReusableSigningObjects,
    SaveAppearance,
)
from foliaseal.application.sign_pdf_use_case import SigningBackendAppearance
from foliaseal.application.signature_image_import import ManagedSignatureImageStore
from foliaseal.application.stamp_background import stamp_background_for_path
from foliaseal.application.visible_signature_layout import (
    VisibleSignatureLayoutOptions,
    VisibleSignatureLayoutRequest,
    VisibleSignatureLayoutService,
)
from foliaseal.domain.models import (
    SignatureImageProminence,
    SignatureLayoutTemplate,
    SignatureRect,
)
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from tests.support.signing_builders import build_signature_appearance


class _RecordingMaterializer:
    def __init__(self) -> None:
        self.image_paths: list[str | None] = []

    def build_stamp_style(self, **kwargs: object) -> object:
        appearance = kwargs["appearance"]
        self.image_paths.append(getattr(appearance, "image_stamp_path"))
        return type(
            "_MaterializedStyle",
            (),
            {
                "inner_content_layout": object(),
                "background_layout": object(),
            },
        )()


def test_saved_and_reloaded_managed_image_reaches_preview_and_signing(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (96, 48), (0, 80, 160, 190)).save(source)
    catalog_dir = tmp_path / "catalog"
    catalog_store = SignaturePresetCatalogStore(storage_dir=catalog_dir)
    image_store = ManagedSignatureImageStore(catalog_dir)
    managed = image_store.import_asset(source)
    managed_path = managed.path
    appearance = replace(
        build_signature_appearance(
            layout_template=SignatureLayoutTemplate.MULTI_LINE,
        ),
        image_prominence=SignatureImageProminence.BALANCED,
        image_asset=managed.asset,
    )
    # Exercise the JSON persistence edge explicitly before constructing the reloaded service.
    serialized = _serialize_appearance(appearance)
    assert serialized["image_asset"]["storage_filename"] == managed_path.name
    assert "image_stamp_path" not in serialized
    writer = ReusableSigningObjects(catalog_store)
    writer.execute(SaveAppearance("Parity", appearance))

    reloaded = ReusableSigningObjects(
        SignaturePresetCatalogStore(storage_dir=catalog_dir),
        image_store=ManagedSignatureImageStore(catalog_dir),
    )
    ref = reloaded.resolve_name(ReusableObjectKind.APPEARANCE, "Parity")
    assert ref is not None
    persisted_profile = reloaded.resolve(ref)
    assert isinstance(persisted_profile, AppearanceProfile)
    assert persisted_profile.schema_version == 2
    persisted = persisted_profile.appearance
    assert persisted.image_stamp_path == str(managed_path)
    assert persisted.image_asset == managed.asset
    assert persisted.image_prominence is SignatureImageProminence.BALANCED

    backend_appearance = SigningBackendAppearance.from_signature_appearance(persisted)
    primary_backend = SigningBackendAppearance.from_signature_appearance(
        replace(persisted, image_prominence=SignatureImageProminence.PRIMARY)
    )
    assert primary_backend.image_prominence is SignatureImageProminence.PRIMARY
    recorder = _RecordingMaterializer()
    preparation = VisibleSignatureLayoutService(
        appearance_materializer=recorder,
    ).prepare(
        VisibleSignatureLayoutRequest(
            appearance=backend_appearance,
            signature_rect=SignatureRect(
                page_index=0,
                left_pt=24.0,
                bottom_pt=36.0,
                width_pt=260.0,
                height_pt=90.0,
            ),
            stamp_text="Digitally signed by Alice",
            stamp_background=stamp_background_for_path(backend_appearance.image_stamp_path),
            options=VisibleSignatureLayoutOptions(allow_fit_issues=True),
        )
    )
    preview = preparation.preview()
    signing = preparation.signing()

    assert recorder.image_paths == [str(managed_path), str(managed_path)]
    assert preview.layout_plan == signing.layout_plan
    assert preview.layout_plan.has_visible_stamp_image
    assert preview.layout_plan.stamp_image is not None
