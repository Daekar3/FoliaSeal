"""Qt presentation adapters for interactive viewer workflows."""

from .app_frame import (
    QtAppFrameAdapter,
    QtAppFrameBindingsUnavailable,
    build_qt_app_frame,
    build_qt_app_frame_host,
    launch_qt_app_frame,
)
from .phase2_harness import (
    HarnessCapture,
    build_phase2_evidence_command,
    run_phase2_viewer_harness,
)
from .phase3_harness import (
    DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH,
    DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH,
    Phase3HarnessCapture,
    build_phase3_checklist_results_markdown,
    run_phase3_signing_harness,
)
from .signing_shell import (
    QtSigningBindingsUnavailable,
    SigningShellAdapter,
    build_qt_signing_shell,
)
from .viewer_widget import (
    PdfViewerWidgetAdapter,
    QtViewerBindingsUnavailable,
    build_qt_pdf_viewer_widget,
)

__all__ = [
    "HarnessCapture",
    "Phase3HarnessCapture",
    "PdfViewerWidgetAdapter",
    "QtAppFrameAdapter",
    "QtAppFrameBindingsUnavailable",
    "QtSigningBindingsUnavailable",
    "QtViewerBindingsUnavailable",
    "SigningShellAdapter",
    "build_qt_pdf_viewer_widget",
    "build_qt_app_frame",
    "build_qt_app_frame_host",
    "launch_qt_app_frame",
    "build_qt_signing_shell",
    "build_phase2_evidence_command",
    "build_phase3_checklist_results_markdown",
    "DEFAULT_PHASE3_CHECKLIST_RESULTS_PATH",
    "DEFAULT_PHASE3_CHECKLIST_TEMPLATE_PATH",
    "run_phase2_viewer_harness",
    "run_phase3_signing_harness",
]
