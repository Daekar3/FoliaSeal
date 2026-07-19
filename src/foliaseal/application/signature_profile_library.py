"""Application boundary for reusable signing-profile library management."""

from __future__ import annotations

from dataclasses import dataclass

from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import ConfigValidationError


@dataclass(frozen=True)
class SignatureProfileLibraryItem:
    """A display-ready reusable signing object."""

    kind: str
    display_name: str
    details: str


@dataclass
class SignatureProfileLibrary:
    """Own profile-library queries and mutations above persistent storage."""

    store: SignaturePresetCatalogStore

    def items(self) -> tuple[SignatureProfileLibraryItem, ...]:
        """Return saved objects with their reference-safe descriptions."""
        catalog = self.store.load_catalog()
        appearances = {
            item.appearance_profile_id: item.display_name
            for item in catalog.appearance_profiles
        }
        placements = {
            item.placement_profile_id: item.display_name
            for item in catalog.placement_profiles
        }
        return (
            *(SignatureProfileLibraryItem(
                kind="appearance",
                display_name=item.display_name,
                details="Reusable component; referenced presets cannot be deleted.",
            ) for item in catalog.appearance_profiles),
            *(SignatureProfileLibraryItem(
                kind="placement",
                display_name=item.display_name,
                details="Reusable component; referenced presets cannot be deleted.",
            ) for item in catalog.placement_profiles),
            *(SignatureProfileLibraryItem(
                kind="preset",
                display_name=item.display_name,
                details=(
                    f"Appearance: {appearances.get(item.appearance_profile_id, 'none')}; "
                    f"placement: {placements.get(item.placement_profile_id, 'none')}; "
                    f"certificate configuration id: {item.certificate_configuration_id or 'none'}."
                ),
            ) for item in catalog.signature_presets),
        )

    def rename(self, kind: str, name: str, new_name: str) -> None:
        """Rename an object while preserving its stable references."""
        self._operation(kind, "rename")(name, new_name)

    def delete(self, kind: str, name: str) -> None:
        """Delete an object, subject to catalog reference guards."""
        self._operation(kind, "delete")(name)

    def _operation(self, kind: str, operation: str):
        methods = {
            ("appearance", "rename"): self.store.rename_appearance_profile,
            ("placement", "rename"): self.store.rename_placement_profile,
            ("preset", "rename"): self.store.rename_preset,
            ("appearance", "delete"): self.store.delete_appearance_profile,
            ("placement", "delete"): self.store.delete_placement_profile,
            ("preset", "delete"): self.store.delete_preset,
        }
        try:
            return methods[(kind, operation)]
        except KeyError as exc:
            raise ConfigValidationError(f"Unknown signing profile object kind: {kind!r}.") from exc
