"""Qt presentation adapters with lazy public exports.

Importing a focused Qt submodule must not construct the complete application
frame, signing shell, or Acceptance harness dependency graph. Public names remain
available through module-level lazy attribute resolution for callers that use
the package facade.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "HarnessCapture",
    "InteractiveHarnessCapture",
    "PdfViewerWidgetAdapter",
    "QtAppFrameAdapter",
    "QtAppFrameBindingsUnavailable",
    "QtSigningBindingsUnavailable",
    "QtViewerBindingsUnavailable",
    "SigningShellAdapter",
    "build_qt_pdf_viewer_widget",
    "build_qt_app_frame_host",
    "launch_qt_app_frame",
    "build_qt_signing_shell",
    "build_phase2_evidence_command",
    "DEFAULT_ACCEPTANCE_CHECKLIST_RESULTS_PATH",
    "DEFAULT_ACCEPTANCE_CHECKLIST_TEMPLATE_PATH",
    "run_phase2_viewer_harness",
]

_EXPORTS = {
    "HarnessCapture": ("phase2_harness", "HarnessCapture"),
    "build_phase2_evidence_command": ("phase2_harness", "build_phase2_evidence_command"),
    "run_phase2_viewer_harness": ("phase2_harness", "run_phase2_viewer_harness"),
    "QtAppFrameAdapter": ("app_frame", "QtAppFrameAdapter"),
    "QtAppFrameBindingsUnavailable": ("app_frame", "QtAppFrameBindingsUnavailable"),
    "build_qt_app_frame_host": ("app_frame", "build_qt_app_frame_host"),
    "launch_qt_app_frame": ("app_frame", "launch_qt_app_frame"),
    "InteractiveHarnessCapture": ("evidence_interactive_capture", "InteractiveHarnessCapture"),
    "DEFAULT_ACCEPTANCE_CHECKLIST_RESULTS_PATH": (
        "interactive_harness",
        "DEFAULT_ACCEPTANCE_CHECKLIST_RESULTS_PATH",
    ),
    "DEFAULT_ACCEPTANCE_CHECKLIST_TEMPLATE_PATH": (
        "interactive_harness",
        "DEFAULT_ACCEPTANCE_CHECKLIST_TEMPLATE_PATH",
    ),
    "SigningShellAdapter": ("signing_shell", "SigningShellAdapter"),
    "QtSigningBindingsUnavailable": ("signing_shell", "QtSigningBindingsUnavailable"),
    "build_qt_signing_shell": ("signing_shell", "build_qt_signing_shell"),
    "PdfViewerWidgetAdapter": ("viewer_widget", "PdfViewerWidgetAdapter"),
    "QtViewerBindingsUnavailable": ("viewer_widget", "QtViewerBindingsUnavailable"),
    "build_qt_pdf_viewer_widget": ("viewer_widget", "build_qt_pdf_viewer_widget"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(f"{__name__}.{module_name}"), attribute_name)
    globals()[name] = value
    return value
