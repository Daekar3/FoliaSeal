"""Application-layer coordinator for signing-shell signature properties."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from foliaseal.application.certificate_catalog_repository import (
    CertificateCatalogRepository,
    InMemoryCertificateCatalogRepository,
    default_certificate_managed_dir,
)
from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
)
from foliaseal.application.reusable_signing_models import (
    PlacementProfileRect,
    ResolvedSignaturePreset,
    SignaturePreset,
    SignaturePresetCatalog,
)
from foliaseal.application.reusable_signing_models import (
    ReusableObjectValidationError as ConfigValidationError,
)
from foliaseal.application.reusable_signing_objects import (
    CatalogRepository,
    DeleteObject,
    InMemoryCatalogRepository,
    ReusableObjectKind,
    ReusableObjectRef,
    ReusableSigningObjects,
    SaveAppearance,
    SavePlacement,
    SavePreset,
)
from foliaseal.application.signing_draft_contracts import (
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
)
from foliaseal.application.signing_draft_workflow import (
    SigningDraftWorkflow,
)
from foliaseal.application.signing_material_resolver import (
    CertificateSecretProvider,
    CertificateSigningMaterialResolver,
    SigningMaterialResolutionError,
)
from foliaseal.domain.models import (
    SignatureAppearance,
    SignaturePlacementDefaults,
    SignatureRect,
)


class SignaturePropertiesCoordinatorError(ValueError):
    """Raised when a coordinator command cannot be completed."""


@dataclass(frozen=True)
class VisibleSignaturePlacementDraft:
    """Qt-independent visible-signature placement form state."""

    page_number: int
    left_pt: float
    bottom_pt: float
    width_pt: float
    height_pt: float
    enabled: bool = False


@dataclass(frozen=True)
class VisibleSignatureSetupDraft:
    """Qt-independent visible-signature setup state."""

    appearance: SignatureAppearance
    placement: VisibleSignaturePlacementDraft


@dataclass(frozen=True)
class SignaturePropertiesViewState:
    """Immutable state rendered by the signature-properties panel."""

    selected_certificate_configuration_name: str | None
    selected_signature_preset_name: str | None
    certificate_configuration_names: tuple[str, ...]
    signature_preset_names: tuple[str, ...]
    appearance_profile_names: tuple[str, ...]
    placement_profile_names: tuple[str, ...]
    visible_signature_setup_draft: VisibleSignatureSetupDraft
    validation_text: str
    ready_to_sign: bool
    preview: SigningDraftPreview


@dataclass(frozen=True)
class ApplyCertificateConfiguration:
    """Apply a named certificate configuration to the current draft."""

    selected_name: str
    passphrase: str | None = None


@dataclass(frozen=True)
class ApplySignaturePreset:
    """Apply a named signature preset to the current draft."""

    selected_name: str
    passphrase: str | None = None


@dataclass(frozen=True)
class SaveCurrentPreset:
    """Persist the current draft as a reusable signature preset."""

    name: str
    overwrite: bool = False


@dataclass(frozen=True)
class SaveCurrentAppearanceProfile:
    """Persist the current appearance as a named reusable profile."""

    name: str
    appearance: SignatureAppearance | None = None
    overwrite: bool = False


@dataclass(frozen=True)
class ComposeSignaturePreset:
    """Persist a preset that references existing reusable component profiles."""

    name: str
    appearance_profile_name: str
    placement_profile_name: str | None = None
    certificate_configuration_id: str | None = None
    overwrite: bool = False


@dataclass(frozen=True)
class SaveCurrentPlacementProfile:
    """Persist a reusable rectangle from the contextual placement draft."""

    name: str
    placement: VisibleSignaturePlacementDraft
    overwrite: bool = False


@dataclass(frozen=True)
class DeletePreset:
    """Delete a named reusable signature preset."""

    name: str


@dataclass(frozen=True)
class RefreshCatalogs:
    """Reload certificate and preset catalogs from local storage."""


@dataclass(frozen=True)
class ClearSelectedSignaturePreset:
    """Clear the currently selected preset name without mutating the workflow."""


@dataclass(frozen=True)
class ApplyVisibleSignatureSetup:
    """Apply the current visible-signature setup draft to the workflow."""

    draft: VisibleSignatureSetupDraft


@dataclass(frozen=True)
class SetSignatureAppearance:
    """Apply a signature appearance without mutating placement state."""

    signature_appearance: SignatureAppearance | None


SignaturePropertiesCommand = (
    ApplyVisibleSignatureSetup
    | SetSignatureAppearance
    | ApplyCertificateConfiguration
    | ApplySignaturePreset
    | SaveCurrentPreset
    | SaveCurrentAppearanceProfile
    | ComposeSignaturePreset
    | SaveCurrentPlacementProfile
    | DeletePreset
    | RefreshCatalogs
    | ClearSelectedSignaturePreset
)


class SignaturePropertiesCoordinator(Protocol):
    """Behavioral boundary for signing-properties state reconciliation."""

    def load(
        self,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState: ...

    def apply_visible_setup(
        self,
        draft: VisibleSignatureSetupDraft,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState: ...

    def set_signature_appearance(
        self,
        signature_appearance: SignatureAppearance | None,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState: ...

    def apply_signature_preset(
        self,
        selected_name: str,
        *,
        passphrase: str | None = None,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState: ...

    def apply_certificate_configuration(
        self,
        selected_name: str,
        *,
        passphrase: str | None = None,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState: ...

    def certificate_configuration_name_for_preset(
        self,
        preset_name: str,
    ) -> str | None: ...

    def reconcile(
        self,
        command: SignaturePropertiesCommand,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState: ...


@dataclass
class DefaultSignaturePropertiesCoordinator:
    """Default application-layer coordinator for signing-shell properties."""

    workflow: SigningDraftWorkflow
    certificate_catalog: CertificateCatalog | None = None
    certificate_catalog_store: CertificateCatalogRepository | None = None
    certificate_secret_provider: CertificateSecretProvider | None = None
    preset_catalog: SignaturePresetCatalog | None = None
    preset_catalog_store: CatalogRepository | None = None
    reusable_objects: ReusableSigningObjects | None = None

    def __post_init__(self) -> None:
        if self.certificate_catalog_store is None:
            self.certificate_catalog_store = InMemoryCertificateCatalogRepository(
                catalog=self.certificate_catalog or CertificateCatalog(schema_version=1),
                storage_dir=default_certificate_managed_dir().parent,
                managed_certificate_dir=default_certificate_managed_dir(),
            )
        if self.certificate_catalog is not None:
            self.certificate_catalog = self.certificate_catalog
        else:
            self.certificate_catalog = self.certificate_catalog_store.load_catalog()
        if self.reusable_objects is None:
            repository = self.preset_catalog_store or InMemoryCatalogRepository(
                self.preset_catalog or SignaturePresetCatalog(schema_version=1)
            )
            self.reusable_objects = ReusableSigningObjects(repository)
        self.preset_catalog = self._reusable_catalog()
        self._certificate_material_resolver = CertificateSigningMaterialResolver(
            managed_certificate_dir=self.certificate_catalog_store.managed_certificate_dir,
            secret_provider=self.certificate_secret_provider,
        )
        self._selected_certificate_configuration_name: str | None = None
        self._selected_signature_preset_name: str | None = None

    def load(
        self,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        self._selected_certificate_configuration_name = (
            self._resolve_selected_certificate_configuration_name()
        )
        self._selected_signature_preset_name = self._resolve_selected_signature_preset_name()
        preview = self.workflow.preview()
        validation_text = _format_validation_text(
            preview,
            control_issue=control_issue,
        )
        partial_preset_notice = self._partial_preset_notice()
        if partial_preset_notice is not None:
            validation_text = f"{partial_preset_notice}\n{validation_text}"
        return SignaturePropertiesViewState(
            selected_certificate_configuration_name=self._selected_certificate_configuration_name,
            selected_signature_preset_name=self._selected_signature_preset_name,
            certificate_configuration_names=tuple(
                configuration.display_name
                for configuration in self.certificate_catalog.certificate_configurations
            ),
            signature_preset_names=self.reusable_objects.view().preset_names,
            appearance_profile_names=self.reusable_objects.view().appearance_names,
            placement_profile_names=self.reusable_objects.view().placement_names,
            visible_signature_setup_draft=self._current_visible_signature_setup_draft(),
            validation_text=validation_text,
            ready_to_sign=_ready_to_sign(preview, control_issue=control_issue),
            preview=preview,
        )

    def reconcile(
        self,
        command: SignaturePropertiesCommand,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        if isinstance(command, ApplyVisibleSignatureSetup):
            self._apply_visible_signature_setup(command)
        elif isinstance(command, SetSignatureAppearance):
            self._apply_signature_appearance(command)
        elif isinstance(command, ApplyCertificateConfiguration):
            self._apply_certificate_configuration(command)
        elif isinstance(command, ApplySignaturePreset):
            self._apply_signature_preset(command)
        elif isinstance(command, SaveCurrentPreset):
            self._save_current_preset(command)
        elif isinstance(command, SaveCurrentAppearanceProfile):
            self._save_current_appearance_profile(command)
        elif isinstance(command, ComposeSignaturePreset):
            self._compose_signature_preset(command)
        elif isinstance(command, SaveCurrentPlacementProfile):
            self._save_current_placement_profile(command)
        elif isinstance(command, DeletePreset):
            self._delete_preset(command)
        elif isinstance(command, RefreshCatalogs):
            self._refresh_catalogs()
        elif isinstance(command, ClearSelectedSignaturePreset):
            self._selected_signature_preset_name = None
        else:  # pragma: no cover - defensive branch
            raise TypeError(f"Unsupported signature properties command: {type(command)!r}")
        return self.load(control_issue=control_issue)

    def apply_visible_setup(
        self,
        draft: VisibleSignatureSetupDraft,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        self._apply_visible_signature_setup(ApplyVisibleSignatureSetup(draft=draft))
        return self.load(control_issue=control_issue)

    def set_signature_appearance(
        self,
        signature_appearance: SignatureAppearance | None,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        self._apply_signature_appearance(
            SetSignatureAppearance(signature_appearance=signature_appearance)
        )
        return self.load(control_issue=control_issue)

    def apply_signature_preset(
        self,
        selected_name: str,
        *,
        passphrase: str | None = None,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        self._apply_signature_preset(
            ApplySignaturePreset(
                selected_name=selected_name,
                passphrase=passphrase,
            )
        )
        return self.load(control_issue=control_issue)

    def apply_certificate_configuration(
        self,
        selected_name: str,
        *,
        passphrase: str | None = None,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        self._apply_certificate_configuration(
            ApplyCertificateConfiguration(
                selected_name=selected_name,
                passphrase=passphrase,
            )
        )
        return self.load(control_issue=control_issue)

    def certificate_configuration_name_for_preset(
        self,
        preset_name: str,
    ) -> str | None:
        ref = self._ref_for_name(ReusableObjectKind.PRESET, preset_name)
        if ref is None:
            return None
        try:
            preset = self.reusable_objects.resolve(ref)
        except (ConfigValidationError, KeyError):
            return None
        configuration_id = preset.preset.certificate_configuration_id
        if configuration_id is None:
            return None
        try:
            return self.certificate_catalog.configuration_by_id(configuration_id).display_name
        except KeyError:
            return None

    def _apply_visible_signature_setup(self, command: ApplyVisibleSignatureSetup) -> None:
        self.workflow.set_signature_appearance(command.draft.appearance)
        placement = command.draft.placement
        if placement.enabled:
            self.workflow.set_signature_rect(
                SignatureRect(
                    page_index=placement.page_number - 1,
                    left_pt=placement.left_pt,
                    bottom_pt=placement.bottom_pt,
                    width_pt=placement.width_pt,
                    height_pt=placement.height_pt,
                )
            )
        if self._selected_signature_preset_name is not None:
            self._selected_signature_preset_name = None

    def _apply_signature_appearance(self, command: SetSignatureAppearance) -> None:
        self.workflow.set_signature_appearance(command.signature_appearance)
        if self._selected_signature_preset_name is not None:
            self._selected_signature_preset_name = None

    def _apply_certificate_configuration(self, command: ApplyCertificateConfiguration) -> None:
        selected_name = _require_name(
            command.selected_name,
            "Select a certificate configuration before applying it.",
        )
        try:
            configuration = self.certificate_catalog.configuration_named(selected_name)
        except KeyError as exc:
            self._selected_certificate_configuration_name = None
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        signing_material = self._resolve_signing_material(
            configuration,
            passphrase=command.passphrase,
        )
        self.workflow.apply_certificate_configuration(configuration, signing_material)
        self._selected_certificate_configuration_name = configuration.display_name

    def _apply_signature_preset(self, command: ApplySignaturePreset) -> None:
        selected_name = _require_name(
            command.selected_name,
            "Select a signature preset before applying it.",
        )
        ref = self._ref_for_name(ReusableObjectKind.PRESET, selected_name)
        if ref is None:
            self._selected_signature_preset_name = None
            raise SignaturePropertiesCoordinatorError(
                f"Signature preset '{selected_name}' is not available."
            )
        try:
            preset = self.reusable_objects.resolve(ref)
        except (ConfigValidationError, KeyError) as exc:
            self._selected_signature_preset_name = None
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        certificate_configuration_id = preset.preset.certificate_configuration_id
        if certificate_configuration_id is not None:
            try:
                configuration = self.certificate_catalog.configuration_by_id(
                    certificate_configuration_id
                )
            except KeyError as exc:
                self._selected_signature_preset_name = None
                raise SignaturePropertiesCoordinatorError(str(exc)) from exc
            signing_material = self._resolve_signing_material(
                configuration,
                passphrase=command.passphrase,
            )
            self.workflow.apply_certificate_configuration(configuration, signing_material)
            self._selected_certificate_configuration_name = configuration.display_name
        try:
            appearance = preset.appearance
            placement_defaults = preset.placement_defaults
        except (ConfigValidationError, KeyError) as exc:
            self._selected_signature_preset_name = None
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self.workflow.apply_signature_preset_values(
            appearance=appearance,
            placement_defaults=placement_defaults,
            signature_preset_id=preset.preset.signature_preset_id,
            appearance_profile_id=preset.preset.appearance_profile_id,
            placement_profile_id=preset.preset.placement_profile_id,
            certificate_configuration_id=preset.preset.certificate_configuration_id,
        )
        self._selected_signature_preset_name = preset.name

    def _save_current_preset(self, command: SaveCurrentPreset) -> None:
        name = _require_name(command.name, "Preset name is required before saving.")
        try:
            self.preset_catalog.preset_named(name)
        except KeyError:
            existing = None
        else:
            existing = name
        if existing is not None and not command.overwrite:
            raise SignaturePropertiesCoordinatorError(
                f"Signature preset '{name}' already exists."
            )
        try:
            preset = self._build_current_preset(name)
        except ValueError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self.reusable_objects.execute(
            SavePreset(
                name=name,
                appearance=preset.appearance,
                placement_defaults=preset.placement_defaults,
                certificate_configuration_id=preset.preset.certificate_configuration_id,
                overwrite=command.overwrite,
            )
        )
        self._refresh_catalogs()
        self._selected_signature_preset_name = preset.name

    def _save_current_appearance_profile(self, command: SaveCurrentAppearanceProfile) -> None:
        name = _require_name(command.name, "Appearance profile name is required before saving.")
        appearance = command.appearance or self.workflow.current_signature_appearance
        if appearance is None:
            raise SignaturePropertiesCoordinatorError(
                "A signature appearance must exist before saving an appearance profile."
            )
        try:
            self.reusable_objects.execute(
                SaveAppearance(name=name, appearance=appearance, overwrite=command.overwrite)
            )
        except ValueError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self._refresh_catalogs()

    def _compose_signature_preset(self, command: ComposeSignaturePreset) -> None:
        name = _require_name(command.name, "Preset name is required before saving.")
        try:
            self.preset_catalog.preset_named(name)
        except KeyError:
            pass
        else:
            if not command.overwrite:
                raise SignaturePropertiesCoordinatorError(
                    f"Signature preset '{name}' already exists."
                )
        try:
            appearance = self.preset_catalog.appearance_profile_named(
                command.appearance_profile_name
            )
            placement = (
                self.preset_catalog.placement_profile_named(command.placement_profile_name)
                if command.placement_profile_name
                else None
            )
        except KeyError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        preset = SignaturePreset.from_profile_parts(
            display_name=name,
            appearance_profile_id=appearance.appearance_profile_id,
            placement_profile_id=(placement.placement_profile_id if placement else None),
            certificate_configuration_id=command.certificate_configuration_id,
        )
        self.reusable_objects.execute(
            SavePreset(
                name=name,
                appearance_profile_id=preset.appearance_profile_id,
                placement_profile_id=preset.placement_profile_id,
                certificate_configuration_id=preset.certificate_configuration_id,
                overwrite=command.overwrite,
            )
        )
        self._refresh_catalogs()
        self._selected_signature_preset_name = preset.display_name

    def _save_current_placement_profile(self, command: SaveCurrentPlacementProfile) -> None:
        name = _require_name(command.name, "Placement profile name is required before saving.")
        placement = command.placement
        if not placement.enabled:
            raise SignaturePropertiesCoordinatorError(
                "Place a signature on the page before saving a placement profile."
            )
        try:
            self.reusable_objects.execute(
                SavePlacement(
                    name=name,
                    rect=PlacementProfileRect(
                        left_pt=placement.left_pt,
                        bottom_pt=placement.bottom_pt,
                        width_pt=placement.width_pt,
                        height_pt=placement.height_pt,
                    ),
                    overwrite=command.overwrite,
                )
            )
        except ValueError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self._refresh_catalogs()

    def _build_current_preset(self, name: str) -> ResolvedSignaturePreset:
        appearance = self.workflow.current_signature_appearance
        if appearance is None:
            raise ValueError(
                "A signature appearance must exist before saving a signature preset."
            )
        placement_defaults = self.workflow.signature_placement_defaults
        if placement_defaults is None and self.workflow.signature_rect is not None:
            placement_defaults = SignaturePlacementDefaults(
                width_pt=self.workflow.signature_rect.width_pt,
                height_pt=self.workflow.signature_rect.height_pt,
            )
        return ResolvedSignaturePreset.from_parts(
            name=name,
            appearance=appearance,
            placement_defaults=placement_defaults,
            certificate_configuration_id=self.workflow.selected_certificate_configuration_id,
        )

    def _delete_preset(self, command: DeletePreset) -> None:
        name = _require_name(command.name, "Select a signature preset before deleting it.")
        ref = self._ref_for_name(ReusableObjectKind.PRESET, name)
        if ref is None:
            raise SignaturePropertiesCoordinatorError(
                f"Signature preset '{name}' is not available."
            )
        self.reusable_objects.execute(DeleteObject(ref=ref))
        self._refresh_catalogs()
        if self._selected_signature_preset_name == name:
            self._selected_signature_preset_name = None

    def _refresh_catalogs(self) -> None:
        self.certificate_catalog = self.certificate_catalog_store.load_catalog()
        self.preset_catalog = self._reusable_catalog()

    def _reusable_catalog(self) -> SignaturePresetCatalog:
        if self.preset_catalog_store is not None:
            return self.preset_catalog_store.load_catalog()
        repository = getattr(self.reusable_objects, "_repository", None)
        if repository is not None:
            return repository.load_catalog()
        return self.preset_catalog or SignaturePresetCatalog(schema_version=1)

    def _ref_for_name(
        self,
        kind: ReusableObjectKind,
        name: str,
    ) -> ReusableObjectRef | None:
        for item in self.reusable_objects.view().all_items:
            if item.ref.kind is kind and item.display_name == name:
                return item.ref
        return None

    def _partial_preset_notice(self) -> str | None:
        if (
            self._selected_signature_preset_name is None
            or self._selected_certificate_configuration_name is not None
        ):
            return None
        ref = self._ref_for_name(
            ReusableObjectKind.PRESET,
            self._selected_signature_preset_name,
        )
        if ref is None:
            return None
        try:
            preset = self.reusable_objects.resolve(ref)
        except (ConfigValidationError, KeyError):
            return None
        if preset.preset.certificate_configuration_id is not None:
            return None
        return (
            f"Selected preset '{preset.name}' does not define a certificate; "
            "choose a certificate configuration before signing."
        )

    def _resolve_signing_material(
        self,
        configuration: CertificateConfiguration,
        *,
        passphrase: str | None,
    ):
        try:
            return self._certificate_material_resolver.resolve(
                self.certificate_catalog,
                configuration,
                passphrase=passphrase,
            )
        except (SigningMaterialResolutionError, ValueError) as exc:
            self._selected_certificate_configuration_name = None
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc

    def _resolve_selected_certificate_configuration_name(self) -> str | None:
        names = {
            configuration.display_name
            for configuration in self.certificate_catalog.certificate_configurations
        }
        if self._selected_certificate_configuration_name in names:
            return self._selected_certificate_configuration_name
        selected_id = self.workflow.selected_certificate_configuration_id
        if selected_id is None:
            return None
        try:
            configuration = self.certificate_catalog.configuration_by_id(selected_id)
        except KeyError:
            return None
        return configuration.display_name

    def _resolve_selected_signature_preset_name(self) -> str | None:
        preset_names = set(self.preset_catalog.preset_names())
        if self._selected_signature_preset_name in preset_names:
            return self._selected_signature_preset_name
        selected_id = self.workflow.selected_signature_preset_id
        if selected_id is None:
            return None
        preset = _preset_by_id(self.preset_catalog, selected_id)
        if preset is None:
            return None
        return preset.display_name

    def _current_visible_signature_setup_draft(self) -> VisibleSignatureSetupDraft:
        appearance = self.workflow.signature_appearance or SignatureAppearance()
        rect = self.workflow.signature_rect
        if rect is not None:
            placement = VisibleSignaturePlacementDraft(
                page_number=rect.page_index + 1,
                left_pt=rect.left_pt,
                bottom_pt=rect.bottom_pt,
                width_pt=rect.width_pt,
                height_pt=rect.height_pt,
                enabled=True,
            )
        else:
            placement_defaults = self.workflow.signature_placement_defaults
            placement = VisibleSignaturePlacementDraft(
                page_number=1,
                left_pt=24.0,
                bottom_pt=18.0,
                width_pt=(
                    placement_defaults.width_pt
                    if placement_defaults is not None
                    else 72.0
                ),
                height_pt=(
                    placement_defaults.height_pt
                    if placement_defaults is not None
                    else 24.0
                ),
                enabled=False,
            )
        return VisibleSignatureSetupDraft(
            appearance=appearance,
            placement=placement,
        )


def _preset_by_id(
    catalog: SignaturePresetCatalog,
    signature_preset_id: str,
) -> SignaturePreset | None:
    for preset in catalog.signature_presets:
        if preset.signature_preset_id == signature_preset_id:
            return preset
    return None


def _ready_to_sign(
    preview: SigningDraftPreview,
    *,
    control_issue: SigningDraftValidationIssue | None,
) -> bool:
    if not preview.can_submit:
        return False
    if control_issue is None:
        return True
    return control_issue.severity != SigningDraftValidationSeverity.ERROR


def _format_validation_text(
    preview: SigningDraftPreview,
    *,
    control_issue: SigningDraftValidationIssue | None,
) -> str:
    issues = preview.issues if control_issue is None else preview.issues + (control_issue,)
    blocking_issues = [
        issue for issue in issues if issue.severity == SigningDraftValidationSeverity.ERROR
    ]
    if (
        len(blocking_issues) == 1
        and control_issue is None
        and blocking_issues[0].code == "signature_rect_missing"
    ):
        return "Place a signature on the page to continue."
    if not blocking_issues:
        return "Ready to sign."
    if (
        len(blocking_issues) == 1
        and blocking_issues[0].code == "visible_signature_layout_unavailable"
    ):
        return f"Will fail to sign: {blocking_issues[0].message}"
    return "\n".join(
        f"{issue.severity.value.upper()} {issue.code}: {issue.message}"
        for issue in blocking_issues
    )


def _require_name(value: str, message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise SignaturePropertiesCoordinatorError(message)
    return normalized
