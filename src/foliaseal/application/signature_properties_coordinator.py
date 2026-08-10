"""Application-layer coordinator for signing-shell signature properties."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from foliaseal.application.certificate_catalog_repository import (
    CertificateCatalogRepository,
    InMemoryCertificateCatalogRepository,
)
from foliaseal.application.certificate_models import (
    CertificateCatalog,
    CertificateConfiguration,
)
from foliaseal.application.certificate_readiness import (
    CertificateReadiness,
    CertificateReadinessReader,
    CertificateReadinessStatus,
    Pkcs12CertificateReadinessReader,
)
from foliaseal.application.coordinate_transform import (
    PdfRect,
    pdf_rect_to_visible_page_rect,
    visible_page_dimensions,
)
from foliaseal.application.reusable_signing_models import (
    PlacementProfileRect,
    PlacementProfileSourcePage,
    ResolvedSignaturePreset,
)
from foliaseal.application.reusable_signing_models import (
    ReusableObjectValidationError as ConfigValidationError,
)
from foliaseal.application.reusable_signing_objects import (
    DeleteObject,
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
    CertificateSigningMaterialPort,
    RepositoryBackedCertificateSigningMaterialPort,
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
    source_page: PlacementProfileSourcePage | None = None


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
    certificate_readiness: CertificateReadiness | None = None


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
    reusable_objects: ReusableSigningObjects
    certificate_catalog: CertificateCatalog | None = None
    certificate_catalog_store: CertificateCatalogRepository | None = None
    certificate_material_port: CertificateSigningMaterialPort | None = None
    certificate_readiness_reader: CertificateReadinessReader | None = None

    def __post_init__(self) -> None:
        explicit_certificate_catalog = (
            self.certificate_catalog is not None or self.certificate_catalog_store is not None
        )
        if self.certificate_catalog_store is None:
            self.certificate_catalog_store = InMemoryCertificateCatalogRepository.for_catalog(
                self.certificate_catalog or CertificateCatalog(schema_version=1)
            )
        if self.certificate_catalog is not None:
            self.certificate_catalog = self.certificate_catalog
        else:
            self.certificate_catalog = self.certificate_catalog_store.load_catalog()
        self._certificate_material_port = self.certificate_material_port or (
            RepositoryBackedCertificateSigningMaterialPort(
                repository=self.certificate_catalog_store,
            )
        )
        self._certificate_catalog_is_explicit = explicit_certificate_catalog
        self._certificate_readiness_reader = (
            self.certificate_readiness_reader or Pkcs12CertificateReadinessReader()
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
        certificate_readiness = self._certificate_readiness()
        validation_text = _format_validation_text(
            preview,
            control_issue=control_issue,
            certificate_readiness=certificate_readiness,
        )
        partial_preset_notice = self._partial_preset_notice()
        if partial_preset_notice is not None:
            validation_text = f"{partial_preset_notice}\n{validation_text}"
        reusable_snapshot = self.reusable_objects.snapshot()
        return SignaturePropertiesViewState(
            selected_certificate_configuration_name=self._selected_certificate_configuration_name,
            selected_signature_preset_name=self._selected_signature_preset_name,
            certificate_configuration_names=tuple(
                configuration.display_name
                for configuration in self.certificate_catalog.certificate_configurations
            ),
            signature_preset_names=reusable_snapshot.preset_names,
            appearance_profile_names=reusable_snapshot.appearance_names,
            placement_profile_names=reusable_snapshot.placement_names,
            visible_signature_setup_draft=self._current_visible_signature_setup_draft(),
            validation_text=validation_text,
            ready_to_sign=_ready_to_sign(
                preview,
                control_issue=control_issue,
                certificate_readiness=certificate_readiness,
            ),
            preview=preview,
            certificate_readiness=certificate_readiness,
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
            self.reusable_objects.ensure_name_available(
                ReusableObjectKind.PRESET, name, command.overwrite
            )
        except ConfigValidationError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        try:
            preset = self._build_current_preset(name)
        except ValueError as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self.reusable_objects.execute(
            SavePreset(
                name=name,
                appearance=preset.appearance,
                placement_defaults=preset.placement_defaults,
                placement_source_page=(
                    None
                    if preset.placement_profile is None
                    else preset.placement_profile.source_page
                ),
                placement_page_number=(
                    1 if preset.placement_profile is None else preset.placement_profile.page_number
                ),
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
            self.reusable_objects.compose_preset(
                name=name,
                appearance_name=command.appearance_profile_name,
                placement_name=command.placement_profile_name,
                certificate_configuration_id=command.certificate_configuration_id,
                overwrite=command.overwrite,
            )
        except (ConfigValidationError, ValueError) as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self._refresh_catalogs()
        self._selected_signature_preset_name = name

    def _save_current_placement_profile(self, command: SaveCurrentPlacementProfile) -> None:
        name = _require_name(command.name, "Placement profile name is required before saving.")
        placement = command.placement
        if not placement.enabled:
            raise SignaturePropertiesCoordinatorError(
                "Place a signature on the page before saving a placement profile."
            )
        try:
            context = self.workflow.placement_context
            if context is None:
                raise SignaturePropertiesCoordinatorError(
                    "A visible page context is required before saving a placement profile."
                )
            visible_width_pt, visible_height_pt = visible_page_dimensions(
                context.page_box, context.rotation
            )
            left_pt, top_pt, width_pt, height_pt = pdf_rect_to_visible_page_rect(
                pdf_rect=PdfRect(
                    x1=placement.left_pt,
                    y1=placement.bottom_pt,
                    x2=placement.left_pt + placement.width_pt,
                    y2=placement.bottom_pt + placement.height_pt,
                ),
                page_box=context.page_box,
                rotation=context.rotation,
            )
            self.reusable_objects.execute(
                SavePlacement(
                    name=name,
                    rect=PlacementProfileRect(
                        left_pt=left_pt,
                        top_pt=top_pt,
                        width_pt=width_pt,
                        height_pt=height_pt,
                    ),
                    source_page=PlacementProfileSourcePage(
                        visible_width_pt=visible_width_pt,
                        visible_height_pt=visible_height_pt,
                        rotation_degrees=context.rotation,
                    ),
                    page_number=placement.page_number,
                    overwrite=command.overwrite,
                )
            )
        except (ValueError, SignaturePropertiesCoordinatorError) as exc:
            raise SignaturePropertiesCoordinatorError(str(exc)) from exc
        self._refresh_catalogs()

    def _build_current_preset(self, name: str) -> ResolvedSignaturePreset:
        appearance = self.workflow.current_signature_appearance
        if appearance is None:
            raise ValueError("A signature appearance must exist before saving a signature preset.")
        placement_defaults = self.workflow.signature_placement_defaults
        if placement_defaults is None and self.workflow.signature_rect is not None:
            placement_defaults = SignaturePlacementDefaults(
                width_pt=self.workflow.signature_rect.width_pt,
                height_pt=self.workflow.signature_rect.height_pt,
            )
        source_page = None
        page_number = 1
        if self.workflow.placement_context is not None:
            visible_width_pt, visible_height_pt = visible_page_dimensions(
                self.workflow.placement_context.page_box,
                self.workflow.placement_context.rotation,
            )
            source_page = PlacementProfileSourcePage(
                visible_width_pt=visible_width_pt,
                visible_height_pt=visible_height_pt,
                rotation_degrees=self.workflow.placement_context.rotation,
            )
            page_number = self.workflow.placement_context.page_index + 1
        return ResolvedSignaturePreset.from_parts(
            name=name,
            appearance=appearance,
            placement_defaults=placement_defaults,
            source_page=source_page,
            page_number=page_number,
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
        self.reusable_objects.refresh()

    def _ref_for_name(
        self,
        kind: ReusableObjectKind,
        name: str,
    ) -> ReusableObjectRef | None:
        return self.reusable_objects.resolve_name(kind, name)

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
            return self._certificate_material_port.resolve(
                certificate_configuration_id=configuration.certificate_configuration_id,
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

    def _certificate_readiness(self) -> CertificateReadiness:
        """Project the selected certificate into a non-secret rail status."""
        if not self._certificate_catalog_is_explicit:
            # Headless callers may intentionally provide direct signing material without
            # a catalog. Preserve that application boundary while the real GUI remains
            # catalog-backed and selection-first.
            if self.workflow.certificate_path:
                return CertificateReadiness(
                    status=CertificateReadinessStatus.READY,
                    detail="Ready to sign.",
                    blocking=False,
                )
            return self._certificate_readiness_reader.read(
                self.workflow.certificate_path,
                self.workflow.passphrase,
            )
        if self._selected_certificate_configuration_name is None:
            if self.workflow.certificate_path:
                return CertificateReadiness(
                    status=CertificateReadinessStatus.READY,
                    detail="Ready to sign.",
                    blocking=False,
                )
            return self._certificate_readiness_reader.read("", "")
        return self._certificate_readiness_reader.read(
            self.workflow.certificate_path,
            self.workflow.passphrase,
        )

    def _resolve_selected_signature_preset_name(self) -> str | None:
        snapshot = self.reusable_objects.snapshot()
        preset_names = set(snapshot.preset_names)
        if self._selected_signature_preset_name in preset_names:
            return self._selected_signature_preset_name
        selected_id = self.workflow.selected_signature_preset_id
        if selected_id is None:
            return None
        preset = snapshot.resolve_preset_selection(selected_id=selected_id)
        if preset is None:
            return None
        return preset.name

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
                width_pt=(placement_defaults.width_pt if placement_defaults is not None else 72.0),
                height_pt=(
                    placement_defaults.height_pt if placement_defaults is not None else 24.0
                ),
                enabled=False,
            )
        return VisibleSignatureSetupDraft(
            appearance=appearance,
            placement=placement,
        )


def _ready_to_sign(
    preview: SigningDraftPreview,
    *,
    control_issue: SigningDraftValidationIssue | None,
    certificate_readiness: CertificateReadiness | None = None,
) -> bool:
    if not preview.can_submit:
        return False
    if control_issue is None:
        return not (certificate_readiness is not None and certificate_readiness.blocking)
    return (
        control_issue.severity != SigningDraftValidationSeverity.ERROR
        and not (certificate_readiness is not None and certificate_readiness.blocking)
    )


def _format_validation_text(
    preview: SigningDraftPreview,
    *,
    control_issue: SigningDraftValidationIssue | None,
    certificate_readiness: CertificateReadiness | None = None,
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
    formatted = "\n".join(
        f"{issue.severity.value.upper()} {issue.code}: {issue.message}" for issue in blocking_issues
    )
    if certificate_readiness is not None and certificate_readiness.blocking:
        return (
            f"{formatted}\n{certificate_readiness.detail}"
            if formatted
            else certificate_readiness.detail
        )
    if not formatted and certificate_readiness is not None and certificate_readiness.warning:
        return f"Ready to sign.\n{certificate_readiness.detail}"
    return formatted


def _require_name(value: str, message: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise SignaturePropertiesCoordinatorError(message)
    return normalized
