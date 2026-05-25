"""Application-layer coordinator for signing-shell signature properties."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from foliaseal.application.signing_draft_workflow import (
    SigningDraftPreview,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
    SigningDraftWorkflow,
)
from foliaseal.application.signing_material_resolver import (
    CertificateSecretProvider,
    CertificateSigningMaterialResolver,
    SigningMaterialResolutionError,
)
from foliaseal.domain.models import SignatureAppearance, SignatureRect
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import (
    CertificateCatalog,
    CertificateConfiguration,
    SignaturePreset,
    SignaturePresetCatalog,
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


SignaturePropertiesCommand = (
    ApplyVisibleSignatureSetup
    | ApplyCertificateConfiguration
    | ApplySignaturePreset
    | SaveCurrentPreset
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
    certificate_catalog_store: CertificateCatalogStore | None = None
    certificate_secret_provider: CertificateSecretProvider | None = None
    preset_catalog: SignaturePresetCatalog | None = None
    preset_catalog_store: SignaturePresetCatalogStore | None = None

    def __post_init__(self) -> None:
        if self.certificate_catalog is not None:
            self.certificate_catalog = self.certificate_catalog
        elif self.certificate_catalog_store is not None:
            self.certificate_catalog = self.certificate_catalog_store.load_catalog()
        else:
            self.certificate_catalog = CertificateCatalog(schema_version=1)
        if self.preset_catalog is not None:
            self.preset_catalog = self.preset_catalog
        elif self.preset_catalog_store is not None:
            self.preset_catalog = self.preset_catalog_store.load_catalog()
        else:
            self.preset_catalog = SignaturePresetCatalog(schema_version=1)
        resolver_store = self.certificate_catalog_store or CertificateCatalogStore.default()
        self._certificate_material_resolver = CertificateSigningMaterialResolver(
            managed_certificate_dir=resolver_store.managed_certificate_dir,
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
        return SignaturePropertiesViewState(
            selected_certificate_configuration_name=self._selected_certificate_configuration_name,
            selected_signature_preset_name=self._selected_signature_preset_name,
            certificate_configuration_names=tuple(
                configuration.display_name
                for configuration in self.certificate_catalog.certificate_configurations
            ),
            signature_preset_names=self.preset_catalog.preset_names(),
            visible_signature_setup_draft=self._current_visible_signature_setup_draft(),
            validation_text=_format_validation_text(
                preview,
                control_issue=control_issue,
            ),
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
        elif isinstance(command, ApplyCertificateConfiguration):
            self._apply_certificate_configuration(command)
        elif isinstance(command, ApplySignaturePreset):
            self._apply_signature_preset(command)
        elif isinstance(command, SaveCurrentPreset):
            self._save_current_preset(command)
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
        try:
            preset = self.preset_catalog.preset_named(selected_name)
        except KeyError as exc:
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
        self.workflow.apply_resolved_signature_preset(preset)
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
            preset = self.workflow.capture_current_signature_setup(name)
        except ValueError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self.preset_catalog = self.preset_catalog.upsert_preset(preset)
        if self.preset_catalog_store is not None:
            self.preset_catalog_store.save_preset(preset)
        self._selected_signature_preset_name = preset.name

    def _delete_preset(self, command: DeletePreset) -> None:
        name = _require_name(command.name, "Select a signature preset before deleting it.")
        try:
            self.preset_catalog.preset_named(name)
        except KeyError as exc:
            raise SignaturePropertiesCoordinatorError(
                f"Signature preset '{name}' is not available."
            ) from exc
        self.preset_catalog = self.preset_catalog.remove_preset(name)
        if self.preset_catalog_store is not None:
            self.preset_catalog_store.delete_preset(name)
        if self._selected_signature_preset_name == name:
            self._selected_signature_preset_name = None

    def _refresh_catalogs(self) -> None:
        if self.certificate_catalog_store is not None:
            self.certificate_catalog = self.certificate_catalog_store.load_catalog()
        if self.preset_catalog_store is not None:
            self.preset_catalog = self.preset_catalog_store.load_catalog()

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
