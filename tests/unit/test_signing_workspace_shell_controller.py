from types import SimpleNamespace

from foliaseal.presentation.qt.signing_workspace_shell_controller import (
    SigningWorkspaceShellController,
)


def _composition(*, bootstrap):
    names = (
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
    )
    values = {name: object() for name in names}
    values["bootstrap"] = bootstrap
    return SimpleNamespace(**values)


def test_controller_builds_installs_and_bootstraps_once() -> None:
    bootstrap_calls: list[None] = []
    compose_calls: list[None] = []
    composition = _composition(bootstrap=lambda: bootstrap_calls.append(None))
    controller = SigningWorkspaceShellController.build(
        widget=object(),
        compose=lambda: (compose_calls.append(None) or composition),
    )
    shell = SimpleNamespace()

    controller.install_into(shell)
    controller.bootstrap()
    controller.bootstrap()

    assert len(compose_calls) == 1
    assert len(bootstrap_calls) == 1
    assert shell._properties_panel is composition.properties_panel
    assert shell._runtime is composition.runtime
    assert shell._interaction_bridge is composition.interaction_bridge


def test_controller_close_delegates_to_container() -> None:
    class _Widget:
        def __init__(self) -> None:
            self.close_calls = 0

        def close(self) -> str:
            self.close_calls += 1
            return "closed"

    widget = _Widget()
    controller = SigningWorkspaceShellController(
        widget=widget,
        composition=_composition(bootstrap=lambda: None),
    )

    assert controller.close() == "closed"
    assert widget.close_calls == 1
