from __future__ import annotations

from types import SimpleNamespace

import pytest

from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt import signing_workspace_composition as composition_module
from foliaseal.presentation.qt.signing_workspace_composition import (
    QtSigningWorkspaceComposition,
    QtSigningWorkspaceCompositionRequest,
    QtSigningWorkspaceHostActions,
)


def _request() -> QtSigningWorkspaceCompositionRequest:
    def no_arg():
        return None

    return QtSigningWorkspaceCompositionRequest(
        bindings=SimpleNamespace(),
        widget=SimpleNamespace(),
        layout=SimpleNamespace(),
        viewer_workflow=SimpleNamespace(),
        signing_workflow=SimpleNamespace(),
        app_settings=AppSettings.default(),
        reusable_objects=SimpleNamespace(),
        viewer_widget_builder=lambda **kwargs: None,
        host_actions=QtSigningWorkspaceHostActions(
            choose_output_pdf_path=no_arg,
            submit_sign_request=no_arg,
            open_signed_output=no_arg,
            search_document_text=no_arg,
            previous_document_text_match=no_arg,
            next_document_text_match=no_arg,
            copy_current_document_text_match=no_arg,
            set_document_text_selection_mode=lambda enabled: enabled,
            copy_selected_document_text=no_arg,
            clear_selected_document_text=no_arg,
            get_app_settings=lambda: AppSettings.default(),
            set_app_settings=lambda settings: None,
        ),
    )


def test_composition_builds_once_and_reuses_assembled_record(monkeypatch) -> None:
    calls = []
    assembled = object()

    def fake_assemble(*, request, runtime, register_disposable):
        calls.append(runtime)
        return assembled

    monkeypatch.setattr(
        composition_module,
        "_assemble_signing_workspace_composition",
        fake_assemble,
    )
    composition = QtSigningWorkspaceComposition.from_request(_request())

    assert composition.build() is assembled
    assert composition.build() is assembled
    assert len(calls) == 1


def test_composition_disposes_partial_resources_once(monkeypatch) -> None:
    class Resource:
        dispose_calls = 0

        def dispose(self):
            self.dispose_calls += 1

    resource = Resource()

    def failing_assemble(*, request, runtime, register_disposable):
        register_disposable(resource)
        raise RuntimeError("assembly failed")

    monkeypatch.setattr(
        composition_module,
        "_assemble_signing_workspace_composition",
        failing_assemble,
    )
    composition = QtSigningWorkspaceComposition.from_request(_request())

    with pytest.raises(RuntimeError, match="assembly failed"):
        composition.build()
    composition.dispose()

    assert resource.dispose_calls == 1
