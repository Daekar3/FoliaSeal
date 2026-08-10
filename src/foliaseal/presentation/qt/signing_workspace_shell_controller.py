"""Typed ownership boundary for signing-shell composition and bootstrap."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from foliaseal.presentation.qt.signing_workspace_composition import SigningWorkspaceComposition


@dataclass
class SigningWorkspaceShellController:
    """Own composition installation, one-time bootstrap, and container close delegation."""

    widget: Any
    composition: SigningWorkspaceComposition
    _bootstrapped: bool = False

    @classmethod
    def build(
        cls,
        *,
        widget: Any,
        compose: Callable[[], SigningWorkspaceComposition],
    ) -> SigningWorkspaceShellController:
        return cls(widget=widget, composition=compose())

    def install_into(self, shell: Any) -> None:
        composition = self.composition
        for name in (
            "document_review_inspector",
            "viewer_interaction_session",
            "document_review_workspace",
            "workspace_interaction_session",
            "viewer_navigation_controls",
            "viewer_widget",
            "properties_panel",
            "sidebar",
            "document_text_controls",
            "properties_scroll",
            "sign_button",
            "result_label",
            "review_bridge",
            "signing_action_coordinator",
            "signing_action_boundary",
            "action_bridge",
            "interaction_bridge",
            "orchestrator",
            "runtime",
            "testing_adapter",
            "shell_surface",
            "main_row",
        ):
            setattr(shell, f"_{name}", getattr(composition, name))
        rail_splitter = getattr(composition, "rail_splitter", None)
        if rail_splitter is not None:
            shell._rail_splitter = rail_splitter
        destroyed_signal = getattr(shell, "destroyed", None)
        destroy_connect = getattr(destroyed_signal, "connect", None)
        if callable(destroy_connect):
            destroy_connect(lambda *_args: composition.properties_panel.dispose())

    def bootstrap(self) -> None:
        if self._bootstrapped:
            return
        self.composition.bootstrap()
        self._bootstrapped = True

    def close(self) -> Any:
        return self.widget.close()


__all__ = ["SigningWorkspaceShellController"]
