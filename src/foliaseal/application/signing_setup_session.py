"""Application-layer session for common signing-setup orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from foliaseal.application.signature_properties_coordinator import (
    ClearSelectedSignaturePreset,
    DefaultSignaturePropertiesCoordinator,
    RefreshCatalogs,
    SignaturePropertiesCoordinatorError,
    SignaturePropertiesViewState,
    VisibleSignatureSetupDraft,
)
from foliaseal.application.signing_draft_workflow import SigningDraftValidationIssue


class CertificatePassphrasePrompter(Protocol):
    """Prompt for a certificate passphrase when manual entry is required."""

    def prompt(self, label: str) -> str | None:
        """Return a passphrase or ``None`` if prompting was canceled."""


@dataclass
class SigningSetupSession:
    """Own common signing-setup orchestration above the coordinator."""

    coordinator: DefaultSignaturePropertiesCoordinator
    passphrase_prompter: CertificatePassphrasePrompter | None = None
    _session_certificate_passphrases: dict[str, str] = field(default_factory=dict)

    def load(
        self,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        return self.coordinator.load(control_issue=control_issue)

    def apply_visible_setup(
        self,
        draft: VisibleSignatureSetupDraft,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        return self.coordinator.apply_visible_setup(
            draft,
            control_issue=control_issue,
        )

    def select_signature_preset(
        self,
        selected_name: str,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState | None:
        configuration_name = self._certificate_configuration_name_for_preset(selected_name)
        prompt_label = (
            f"Enter the certificate password for '{configuration_name}'."
            if configuration_name
            else "Enter the certificate password required by this signature preset."
        )
        return self._run_with_manual_certificate_password_retry(
            cache_key=configuration_name,
            prompt_label=prompt_label,
            action=lambda passphrase: self.coordinator.apply_signature_preset(
                selected_name,
                passphrase=passphrase,
                control_issue=control_issue,
            ),
        )

    def clear_selected_signature_preset(
        self,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        return self.coordinator.reconcile(
            ClearSelectedSignaturePreset(),
            control_issue=control_issue,
        )

    def select_certificate_configuration(
        self,
        selected_name: str,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState | None:
        prompt_label = (
            f"Enter the certificate password for '{selected_name}'."
            if selected_name
            else "Enter the certificate password."
        )
        return self._run_with_manual_certificate_password_retry(
            cache_key=selected_name or None,
            prompt_label=prompt_label,
            action=lambda passphrase: self.coordinator.apply_certificate_configuration(
                selected_name,
                passphrase=passphrase,
                control_issue=control_issue,
            ),
        )

    def refresh_catalogs(
        self,
        *,
        control_issue: SigningDraftValidationIssue | None = None,
    ) -> SignaturePropertiesViewState:
        return self.coordinator.reconcile(
            RefreshCatalogs(),
            control_issue=control_issue,
        )

    def _run_with_manual_certificate_password_retry(
        self,
        *,
        cache_key: str | None,
        prompt_label: str,
        action,
    ) -> SignaturePropertiesViewState | None:
        cached_passphrase = (
            self._session_certificate_passphrases.get(cache_key)
            if cache_key is not None
            else None
        )
        try:
            return action(cached_passphrase)
        except SignaturePropertiesCoordinatorError as exc:
            if not _should_prompt_for_certificate_password(str(exc)):
                raise
        if self.passphrase_prompter is None:
            return None
        prompted_passphrase = self.passphrase_prompter.prompt(prompt_label)
        if prompted_passphrase is None:
            return None
        state = action(prompted_passphrase)
        if cache_key is not None and prompted_passphrase:
            self._session_certificate_passphrases[cache_key] = prompted_passphrase
        return state

    def _certificate_configuration_name_for_preset(self, preset_name: str) -> str | None:
        try:
            preset = self.coordinator.preset_catalog.preset_named(preset_name)
        except KeyError:
            return None
        configuration_id = preset.preset.certificate_configuration_id
        if configuration_id is None:
            return None
        try:
            return self.coordinator.certificate_catalog.configuration_by_id(
                configuration_id
            ).display_name
        except KeyError:
            return None


def _should_prompt_for_certificate_password(message: str) -> bool:
    lowered = message.lower()
    return "enter the password" in lowered or "enter the certificate password" in lowered
