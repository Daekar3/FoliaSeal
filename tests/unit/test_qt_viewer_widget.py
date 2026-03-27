import importlib

import pytest

from pdf_signer.application.viewer_session import ViewerSession
from pdf_signer.application.viewer_workflow import ViewerWorkflow
from pdf_signer.presentation.qt import PdfViewerWidgetAdapter, QtViewerBindingsUnavailable


class _FakeRenderBackend:
    def render_page(self, request):  # pragma: no cover - not used in this suite
        raise NotImplementedError

    def get_page_geometry(self, document_path: str, page_index: int):  # pragma: no cover
        raise NotImplementedError

    def diagnostics(self):  # pragma: no cover
        raise NotImplementedError


def _build_workflow() -> ViewerWorkflow:
    return ViewerWorkflow(
        document_path="/tmp/sample.pdf",
        render_backend=_FakeRenderBackend(),
        session=ViewerSession(page_count=1),
    )


def test_qt_viewer_widget_adapter_raises_actionable_error_without_pyside6(monkeypatch):
    original_import_module = importlib.import_module

    def _raise_for_pyside6(module_name: str):
        if module_name.startswith("PySide6"):
            raise ModuleNotFoundError("PySide6 is not installed")
        return original_import_module(module_name)

    monkeypatch.setattr(importlib, "import_module", _raise_for_pyside6)

    with pytest.raises(QtViewerBindingsUnavailable, match="PySide6"):
        PdfViewerWidgetAdapter().create(workflow=_build_workflow())
