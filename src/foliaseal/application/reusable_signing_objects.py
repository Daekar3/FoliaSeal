"""Typed application boundary for reusable signing-object catalog operations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType
from typing import Protocol
from uuid import uuid4

from foliaseal.application.reusable_signing_models import (
    AppearanceProfile,
    PlacementProfile,
    PlacementProfileRect,
    PlacementProfileSourcePage,
    ResolvedSignaturePreset,
    SignaturePreset,
    SignaturePresetCatalog,
    _stable_id,
)
from foliaseal.application.reusable_signing_models import (
    ReusableObjectValidationError as ConfigValidationError,
)
from foliaseal.application.signature_image_import import (
    ManagedSignatureImageStore,
    SignatureImageImportError,
)
from foliaseal.domain.models import SignatureAppearance, SignaturePlacementDefaults


class ReusableObjectKind(Enum):
    """The persisted kind represented by a typed reusable-object reference."""

    APPEARANCE = "appearance"
    PLACEMENT = "placement"
    PRESET = "preset"


@dataclass(frozen=True)
class ReusableObjectRef:
    """Stable identity for one reusable object; display names are not identity."""

    kind: ReusableObjectKind
    object_id: str


@dataclass(frozen=True)
class ReusableObjectSummary:
    """Display-ready description paired with its typed identity."""

    ref: ReusableObjectRef
    display_name: str
    details: str
    pinned: bool = False


@dataclass(frozen=True)
class ReusableObjectsView:
    """Current reusable-object choices for application and Qt callers."""

    appearances: tuple[ReusableObjectSummary, ...]
    placements: tuple[ReusableObjectSummary, ...]
    presets: tuple[ReusableObjectSummary, ...]

    @property
    def all_items(self) -> tuple[ReusableObjectSummary, ...]:
        return self.appearances + self.placements + self.presets

    @property
    def appearance_names(self) -> tuple[str, ...]:
        return tuple(item.display_name for item in self.appearances)

    @property
    def placement_names(self) -> tuple[str, ...]:
        return tuple(item.display_name for item in self.placements)

    @property
    def preset_names(self) -> tuple[str, ...]:
        return tuple(item.display_name for item in self.presets)


@dataclass(frozen=True)
class ReusableCatalogSnapshot:
    """Immutable, service-owned view of one committed catalog state."""

    view: ReusableObjectsView
    _resolved_by_ref: Mapping[ReusableObjectRef, ResolvedReusableObject]
    _refs_by_name: Mapping[ReusableObjectKind, Mapping[str, ReusableObjectRef]]

    @property
    def appearances(self) -> tuple[ReusableObjectSummary, ...]:
        return self.view.appearances

    @property
    def placements(self) -> tuple[ReusableObjectSummary, ...]:
        return self.view.placements

    @property
    def presets(self) -> tuple[ReusableObjectSummary, ...]:
        return self.view.presets

    @property
    def appearance_names(self) -> tuple[str, ...]:
        return self.view.appearance_names

    @property
    def placement_names(self) -> tuple[str, ...]:
        return self.view.placement_names

    @property
    def preset_names(self) -> tuple[str, ...]:
        return self.view.preset_names

    def resolve(self, ref: ReusableObjectRef) -> ResolvedReusableObject:
        try:
            return self._resolved_by_ref[ref]
        except KeyError as exc:
            raise ConfigValidationError(
                f"{ref.kind.value.title()} object '{ref.object_id}' is not available."
            ) from exc

    def resolve_name(self, kind: ReusableObjectKind, name: str) -> ReusableObjectRef | None:
        return self._refs_by_name[kind].get(name.strip().casefold())

    def resolve_preset_selection(
        self, preferred_name: str | None = None, selected_id: str | None = None
    ) -> PresetSelection | None:
        ref = (
            self.resolve_name(ReusableObjectKind.PRESET, preferred_name)
            if preferred_name is not None
            else None
        )
        if ref is None and selected_id is not None:
            ref = ReusableObjectRef(ReusableObjectKind.PRESET, selected_id)
        if ref is None:
            return None
        try:
            preset = self.resolve(ref)
            if not isinstance(preset, ResolvedSignaturePreset):
                return None
            return PresetSelection(name=preset.name, ref=ref, preset=preset)
        except ConfigValidationError:
            return None

    def ensure_name_available(
        self, kind: ReusableObjectKind, name: str, overwrite: bool = False
    ) -> None:
        normalized = _require_name(name, f"{kind.value.title()} name is required.")
        if self.resolve_name(kind, normalized) is not None and not overwrite:
            label = (
                "Signature preset"
                if kind is ReusableObjectKind.PRESET
                else f"{kind.value.title()} profile"
            )
            raise ConfigValidationError(f"{label} '{normalized}' already exists.")


@dataclass(frozen=True)
class SaveAppearance:
    name: str
    appearance: SignatureAppearance
    appearance_profile_id: str | None = None
    overwrite: bool = False


@dataclass(frozen=True)
class SavePlacement:
    name: str
    rect: PlacementProfileRect
    source_page: PlacementProfileSourcePage
    page_number: int
    pinned: bool = False
    placement_profile_id: str | None = None
    overwrite: bool = False


@dataclass(frozen=True)
class SavePreset:
    name: str
    appearance: SignatureAppearance | None = None
    placement_defaults: SignaturePlacementDefaults | None = None
    placement_source_page: PlacementProfileSourcePage | None = None
    placement_page_number: int = 1
    appearance_profile_id: str | None = None
    placement_profile_id: str | None = None
    certificate_configuration_id: str | None = None
    signature_preset_id: str | None = None
    overwrite: bool = False


@dataclass(frozen=True)
class RenameObject:
    ref: ReusableObjectRef
    new_name: str


@dataclass(frozen=True)
class DeleteObject:
    ref: ReusableObjectRef


@dataclass(frozen=True)
class DuplicateObject:
    """Copy one reusable object under a new stable identity, initially unpinned."""

    ref: ReusableObjectRef
    new_name: str


@dataclass(frozen=True)
class SetPinned:
    """Set persistent pin state without changing object identity or name."""

    ref: ReusableObjectRef
    pinned: bool


ReusableObjectCommand = (
    SaveAppearance
    | SavePlacement
    | SavePreset
    | RenameObject
    | DeleteObject
    | DuplicateObject
    | SetPinned
)
ResolvedReusableObject = AppearanceProfile | PlacementProfile | ResolvedSignaturePreset


@dataclass(frozen=True)
class PresetSelection:
    """One resolved preset paired with its stable typed reference."""

    name: str
    ref: ReusableObjectRef
    preset: ResolvedSignaturePreset


class CatalogRepository(Protocol):
    """Minimal persistence port used by the reusable-object application boundary."""

    def load_catalog(self) -> SignaturePresetCatalog:
        """Load the current catalog."""

    def save_catalog(self, catalog: SignaturePresetCatalog) -> None:
        """Atomically persist a catalog."""


@dataclass
class InMemoryCatalogRepository:
    """Small repository stand-in for coordinator and boundary tests."""

    catalog: SignaturePresetCatalog

    def load_catalog(self) -> SignaturePresetCatalog:
        return self.catalog

    def save_catalog(self, catalog: SignaturePresetCatalog) -> None:
        self.catalog = catalog


class ReusableSigningObjects:
    """Own reusable-object policy while hiding catalog persistence details."""

    def __init__(
        self,
        repository: CatalogRepository,
        *,
        certificate_configuration_exists: Callable[[str], bool] | None = None,
        image_store: ManagedSignatureImageStore | None = None,
    ) -> None:
        self._repository = repository
        self._certificate_configuration_exists = certificate_configuration_exists
        self._image_store = image_store
        self._snapshot: ReusableCatalogSnapshot | None = None

    def snapshot(self) -> ReusableCatalogSnapshot:
        if self._snapshot is None:
            self._snapshot = self._snapshot_for(self._repository.load_catalog())
        return self._snapshot

    def refresh(self) -> ReusableCatalogSnapshot:
        self._snapshot = self._snapshot_for(self._repository.load_catalog())
        return self._snapshot

    def view(self) -> ReusableObjectsView:
        return self.snapshot().view

    def resolve(self, ref: ReusableObjectRef) -> ResolvedReusableObject:
        return self.snapshot().resolve(ref)

    def resolve_name(self, kind: ReusableObjectKind, name: str) -> ReusableObjectRef | None:
        return self.snapshot().resolve_name(kind, name)

    def resolve_preset_selection(
        self, preferred_name: str | None = None, selected_id: str | None = None
    ) -> PresetSelection | None:
        return self.snapshot().resolve_preset_selection(preferred_name, selected_id)

    def ensure_name_available(
        self, kind: ReusableObjectKind, name: str, overwrite: bool = False
    ) -> None:
        self.snapshot().ensure_name_available(kind, name, overwrite)

    def compose_preset(
        self,
        name: str,
        appearance_name: str,
        placement_name: str | None = None,
        certificate_configuration_id: str | None = None,
        overwrite: bool = False,
    ) -> PresetSelection:
        current = self.snapshot()
        current.ensure_name_available(ReusableObjectKind.PRESET, name, overwrite)
        appearance_ref = current.resolve_name(ReusableObjectKind.APPEARANCE, appearance_name)
        if appearance_ref is None:
            raise ConfigValidationError(f"Appearance profile '{appearance_name}' is not available.")
        placement_ref = (
            current.resolve_name(ReusableObjectKind.PLACEMENT, placement_name)
            if placement_name
            else None
        )
        if placement_name and placement_ref is None:
            raise ConfigValidationError(f"Placement profile '{placement_name}' is not available.")
        snapshot = self.execute(
            SavePreset(
                name=name,
                appearance_profile_id=appearance_ref.object_id,
                placement_profile_id=placement_ref.object_id if placement_ref else None,
                certificate_configuration_id=certificate_configuration_id,
                overwrite=overwrite,
            )
        )
        selection = snapshot.resolve_preset_selection(preferred_name=name)
        if selection is None:
            raise ConfigValidationError(f"Signature preset '{name}' was not committed.")
        return selection

    def execute(self, command: ReusableObjectCommand) -> ReusableCatalogSnapshot:
        catalog = self._repository.load_catalog()
        updated = self._apply(catalog, command)
        if updated is not catalog:
            self._repository.save_catalog(updated)
        self._snapshot = self._snapshot_for(updated)
        return self._snapshot

    def _snapshot_for(self, catalog: SignaturePresetCatalog) -> ReusableCatalogSnapshot:
        view = self._view(catalog)
        resolved: dict[ReusableObjectRef, ResolvedReusableObject] = {}
        for profile in catalog.appearance_profiles:
            ref = ReusableObjectRef(ReusableObjectKind.APPEARANCE, profile.appearance_profile_id)
            resolved[ref] = self._resolve_image_asset(profile)
        for profile in catalog.placement_profiles:
            ref = ReusableObjectRef(ReusableObjectKind.PLACEMENT, profile.placement_profile_id)
            resolved[ref] = profile
        for preset in catalog.signature_presets:
            ref = ReusableObjectRef(ReusableObjectKind.PRESET, preset.signature_preset_id)
            resolved[ref] = self._resolve_preset_image_asset(catalog.resolve_preset(preset))
        refs_by_name = {
            ReusableObjectKind.APPEARANCE: {
                item.display_name.casefold(): item.ref for item in view.appearances
            },
            ReusableObjectKind.PLACEMENT: {
                item.display_name.casefold(): item.ref for item in view.placements
            },
            ReusableObjectKind.PRESET: {
                item.display_name.casefold(): item.ref for item in view.presets
            },
        }
        return ReusableCatalogSnapshot(
            view=view,
            _resolved_by_ref=MappingProxyType(resolved),
            _refs_by_name=MappingProxyType(
                {kind: MappingProxyType(index) for kind, index in refs_by_name.items()}
            ),
        )

    def _resolve_image_asset(self, profile: AppearanceProfile) -> AppearanceProfile:
        appearance = profile.appearance
        if appearance.image_asset is None or self._image_store is None:
            return profile
        try:
            path = self._image_store.resolve_asset(appearance.image_asset)
        except SignatureImageImportError:
            # Keep the canonical metadata visible to callers so the UI can report a missing asset;
            # do not silently turn a persisted asset into an arbitrary source path.
            return profile
        return replace(profile, appearance=replace(appearance, image_stamp_path=str(path)))

    def _resolve_preset_image_asset(
        self,
        preset: ResolvedSignaturePreset,
    ) -> ResolvedSignaturePreset:
        if preset.appearance_profile is None:
            return preset
        return replace(
            preset,
            appearance_profile=self._resolve_image_asset(preset.appearance_profile),
        )

    def _apply(
        self,
        catalog: SignaturePresetCatalog,
        command: ReusableObjectCommand,
    ) -> SignaturePresetCatalog:
        if isinstance(command, SaveAppearance):
            name = _require_name(command.name, "Appearance profile name is required.")
            existing_by_id = (
                next(
                    (
                        item
                        for item in catalog.appearance_profiles
                        if item.appearance_profile_id == command.appearance_profile_id
                    ),
                    None,
                )
                if command.appearance_profile_id is not None
                else None
            )
            if command.appearance_profile_id is not None and existing_by_id is None:
                raise ConfigValidationError("The appearance profile being edited no longer exists.")
            existing_by_name = next(
                (
                    item
                    for item in catalog.appearance_profiles
                    if item.display_name.casefold() == name.casefold()
                ),
                None,
            )
            if (
                existing_by_name is not None
                and existing_by_id is not None
                and existing_by_name.appearance_profile_id != existing_by_id.appearance_profile_id
            ):
                raise ConfigValidationError(f"Appearance '{name}' already exists.")
            existing = existing_by_id or existing_by_name
            profile = AppearanceProfile(
                schema_version=2,
                appearance_profile_id=(
                    command.appearance_profile_id
                    or (existing.appearance_profile_id if existing is not None else None)
                    if existing is not None
                    else _stable_id("appearance", name)
                ),
                display_name=name,
                appearance=command.appearance,
                pinned=existing.pinned if existing is not None else False,
            )
            self._check_duplicate(
                catalog.appearance_profiles,
                name,
                command.overwrite,
                "Appearance",
            )
            return catalog.upsert_appearance_profile(profile)
        if isinstance(command, SavePlacement):
            name = _require_name(command.name, "Placement profile name is required.")
            profile = PlacementProfile(
                schema_version=2,
                placement_profile_id=(
                    command.placement_profile_id
                    or next(
                        (
                            item.placement_profile_id
                            for item in catalog.placement_profiles
                            if item.display_name.casefold() == name.casefold()
                        ),
                        None,
                    )
                    or _stable_id("placement", name)
                ),
                display_name=name,
                pinned=command.pinned,
                page_number=command.page_number,
                source_page=command.source_page,
                rect=command.rect,
            )
            self._check_duplicate(catalog.placement_profiles, name, command.overwrite, "Placement")
            return catalog.upsert_placement_profile(profile)
        if isinstance(command, SavePreset):
            name = _require_name(command.name, "Signature preset name is required.")
            if (
                command.certificate_configuration_id is not None
                and self._certificate_configuration_exists is not None
                and not self._certificate_configuration_exists(command.certificate_configuration_id)
            ):
                raise ConfigValidationError(
                    "Signature preset references a missing certificate configuration."
                )
            existing_by_id = next(
                (
                    item
                    for item in catalog.signature_presets
                    if item.signature_preset_id == command.signature_preset_id
                ),
                None,
            )
            existing_by_name = next(
                (
                    item
                    for item in catalog.signature_presets
                    if item.display_name.casefold() == name.casefold()
                ),
                None,
            )
            if command.signature_preset_id is not None and existing_by_id is None:
                raise ConfigValidationError("Signature preset is no longer available.")
            if (
                existing_by_name is not None
                and existing_by_id is not None
                and existing_by_name.signature_preset_id != existing_by_id.signature_preset_id
            ):
                raise ConfigValidationError(f"Signature preset '{name}' already exists.")
            if existing_by_name is not None and existing_by_id is None and not command.overwrite:
                raise ConfigValidationError(f"Signature preset '{name}' already exists.")
            existing = existing_by_id or existing_by_name
            if command.appearance is not None:
                appearance_id = (
                    existing.appearance_profile_id
                    if existing is not None and existing.appearance_profile_id is not None
                    else _stable_id("appearance", name)
                )
                appearance_profile = AppearanceProfile(
                    schema_version=2,
                    appearance_profile_id=appearance_id,
                    display_name=(
                        _appearance_by_id(catalog, appearance_id).display_name
                        if _appearance_by_id(catalog, appearance_id) is not None
                        else name
                    ),
                    appearance=command.appearance,
                    pinned=(_appearance_by_id(catalog, appearance_id).pinned
                            if _appearance_by_id(catalog, appearance_id) is not None else False),
                )
                updated = catalog.upsert_appearance_profile(appearance_profile)
                placement_id = existing.placement_profile_id if existing is not None else None
                if command.placement_defaults is not None:
                    if command.placement_source_page is None:
                        raise ConfigValidationError(
                            "A placement source page is required when saving placement defaults."
                        )
                    placement_id = placement_id or _stable_id("placement", name)
                    existing_placement = (
                        _placement_by_id(catalog, placement_id)
                        if _placement_by_id(catalog, placement_id) is not None
                        else None
                    )
                    updated = updated.upsert_placement_profile(
                        PlacementProfile(
                            schema_version=2,
                            placement_profile_id=placement_id,
                            display_name=(
                                existing_placement.display_name
                                if existing_placement is not None
                                else name
                            ),
                            pinned=(
                                existing_placement.pinned
                                if existing_placement is not None
                                else False
                            ),
                            page_number=(
                                existing_placement.page_number
                                if existing_placement is not None
                                else command.placement_page_number
                            ),
                            source_page=(
                                existing_placement.source_page
                                if existing_placement is not None
                                else command.placement_source_page
                            ),
                            rect=PlacementProfileRect(
                                left_pt=0.0,
                                top_pt=0.0,
                                width_pt=command.placement_defaults.width_pt,
                                height_pt=command.placement_defaults.height_pt,
                            ),
                        )
                    )
                preset = SignaturePreset.from_profile_parts(
                    display_name=name,
                    appearance_profile_id=appearance_id,
                    placement_profile_id=placement_id,
                    certificate_configuration_id=command.certificate_configuration_id,
                    signature_preset_id=(
                        existing.signature_preset_id if existing is not None else None
                    ),
                    pinned=existing.pinned if existing is not None else False,
                )
                return updated.upsert_reference_preset(preset)
            if command.appearance_profile_id is None:
                raise ConfigValidationError(
                    "A preset must include an appearance or appearance profile reference."
                )
            appearance = self._resolve_by_id(
                catalog.appearance_profiles,
                command.appearance_profile_id,
                ReusableObjectKind.APPEARANCE,
            )
            if command.placement_profile_id is not None:
                self._resolve_by_id(
                    catalog.placement_profiles,
                    command.placement_profile_id,
                    ReusableObjectKind.PLACEMENT,
                )
            preset = SignaturePreset.from_profile_parts(
                display_name=name,
                appearance_profile_id=appearance.appearance_profile_id,
                placement_profile_id=command.placement_profile_id,
                certificate_configuration_id=command.certificate_configuration_id,
                signature_preset_id=(
                    existing.signature_preset_id if existing is not None else None
                ),
                pinned=existing.pinned if existing is not None else False,
            )
            return catalog.upsert_reference_preset(preset)
        if isinstance(command, RenameObject):
            name = self._name_for_ref(catalog, command.ref)
            new_name = _require_name(command.new_name, "New reusable-object name is required.")
            if command.ref.kind is ReusableObjectKind.APPEARANCE:
                return catalog.rename_appearance_profile(name, new_name)
            if command.ref.kind is ReusableObjectKind.PLACEMENT:
                return catalog.rename_placement_profile(name, new_name)
            return catalog.rename_preset(name, new_name)
        if isinstance(command, DuplicateObject):
            entries_by_kind = {
                ReusableObjectKind.APPEARANCE: catalog.appearance_profiles,
                ReusableObjectKind.PLACEMENT: catalog.placement_profiles,
                ReusableObjectKind.PRESET: catalog.signature_presets,
            }
            source = self._resolve_by_id(
                entries_by_kind[command.ref.kind],
                command.ref.object_id,
                command.ref.kind,
            )
            name = _require_name(command.new_name, "Duplicate name is required.")
            entries = entries_by_kind[command.ref.kind]
            self._check_duplicate(entries, name, False, command.ref.kind.value.title())
            if command.ref.kind is ReusableObjectKind.APPEARANCE:
                duplicate = replace(
                    source,
                    appearance_profile_id=f"appearance-{uuid4().hex}",
                    display_name=name,
                    pinned=False,
                )
                return catalog.upsert_appearance_profile(duplicate)
            if command.ref.kind is ReusableObjectKind.PLACEMENT:
                duplicate = replace(
                    source,
                    placement_profile_id=f"placement-{uuid4().hex}",
                    display_name=name,
                    pinned=False,
                )
                return catalog.upsert_placement_profile(duplicate)
            duplicate = replace(
                source,
                signature_preset_id=f"preset-{uuid4().hex}",
                display_name=name,
                pinned=False,
            )
            return catalog.upsert_reference_preset(duplicate)
        if isinstance(command, SetPinned):
            source = self._resolve_by_id(
                {
                    ReusableObjectKind.APPEARANCE: catalog.appearance_profiles,
                    ReusableObjectKind.PLACEMENT: catalog.placement_profiles,
                    ReusableObjectKind.PRESET: catalog.signature_presets,
                }[command.ref.kind],
                command.ref.object_id,
                command.ref.kind,
            )
            if command.ref.kind is ReusableObjectKind.APPEARANCE:
                return catalog.upsert_appearance_profile(replace(source, pinned=command.pinned))
            if command.ref.kind is ReusableObjectKind.PLACEMENT:
                return catalog.upsert_placement_profile(replace(source, pinned=command.pinned))
            return catalog.upsert_reference_preset(replace(source, pinned=command.pinned))
        if isinstance(command, DeleteObject):
            name = self._name_for_ref(catalog, command.ref)
            if command.ref.kind is ReusableObjectKind.APPEARANCE:
                return catalog.remove_appearance_profile(name)
            if command.ref.kind is ReusableObjectKind.PLACEMENT:
                return catalog.remove_placement_profile(name)
            return catalog.remove_preset(name)
        raise TypeError(f"Unsupported reusable-object command: {type(command)!r}")

    @staticmethod
    def _check_duplicate(
        entries: tuple[object, ...], name: str, overwrite: bool, label: str
    ) -> None:
        if (
            any(getattr(entry, "display_name").casefold() == name.casefold() for entry in entries)
            and not overwrite
        ):
            raise ConfigValidationError(f"{label} '{name}' already exists.")

    @staticmethod
    def _resolve_by_id(entries: tuple[object, ...], object_id: str, kind: ReusableObjectKind):
        for entry in entries:
            if getattr(entry, f"{kind.value}_profile_id", None) == object_id:
                return entry
            if (
                kind is ReusableObjectKind.PRESET
                and getattr(entry, "signature_preset_id", None) == object_id
            ):
                return entry
        raise ConfigValidationError(f"{kind.value.title()} object '{object_id}' is not available.")

    def _name_for_ref(self, catalog: SignaturePresetCatalog, ref: ReusableObjectRef) -> str:
        return self._resolve_by_id(
            {
                ReusableObjectKind.APPEARANCE: catalog.appearance_profiles,
                ReusableObjectKind.PLACEMENT: catalog.placement_profiles,
                ReusableObjectKind.PRESET: catalog.signature_presets,
            }[ref.kind],
            ref.object_id,
            ref.kind,
        ).display_name

    @staticmethod
    def _view(catalog: SignaturePresetCatalog) -> ReusableObjectsView:
        appearances = {
            profile.appearance_profile_id: profile.display_name
            for profile in catalog.appearance_profiles
        }
        placements = {
            profile.placement_profile_id: profile.display_name
            for profile in catalog.placement_profiles
        }
        return ReusableObjectsView(
            appearances=tuple(
                ReusableObjectSummary(
                    ref=ReusableObjectRef(
                        ReusableObjectKind.APPEARANCE,
                        profile.appearance_profile_id,
                    ),
                    display_name=profile.display_name,
                    details="Reusable component; referenced presets cannot be deleted.",
                    pinned=profile.pinned,
                )
                for profile in catalog.appearance_profiles
            ),
            placements=tuple(
                ReusableObjectSummary(
                    ref=ReusableObjectRef(
                        ReusableObjectKind.PLACEMENT,
                        profile.placement_profile_id,
                    ),
                    display_name=profile.display_name,
                    details="Reusable component; referenced presets cannot be deleted.",
                    pinned=profile.pinned,
                )
                for profile in catalog.placement_profiles
            ),
            presets=tuple(
                ReusableObjectSummary(
                    ref=ReusableObjectRef(ReusableObjectKind.PRESET, preset.signature_preset_id),
                    display_name=preset.display_name,
                    details=(
                        f"Appearance: {appearances.get(preset.appearance_profile_id, 'none')}; "
                        f"placement: {placements.get(preset.placement_profile_id, 'none')}; "
                        "certificate configuration id: "
                        f"{preset.certificate_configuration_id or 'none'}."
                    ),
                    pinned=preset.pinned,
                )
                for preset in catalog.signature_presets
            ),
        )


def _require_name(value: str, message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ConfigValidationError(message)
    return normalized


def _appearance_by_id(
    catalog: SignaturePresetCatalog,
    profile_id: str,
) -> AppearanceProfile | None:
    return next(
        (
            profile
            for profile in catalog.appearance_profiles
            if profile.appearance_profile_id == profile_id
        ),
        None,
    )


def _placement_by_id(
    catalog: SignaturePresetCatalog,
    profile_id: str,
) -> PlacementProfile | None:
    return next(
        (
            profile
            for profile in catalog.placement_profiles
            if profile.placement_profile_id == profile_id
        ),
        None,
    )
