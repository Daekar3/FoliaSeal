"""Capture the isolated Signature Library Appearance editor on a real Qt display."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtGui import QFontMetrics, QPalette
from PySide6.QtWidgets import QApplication

from foliaseal.application.signature_library_session import LibraryCatalog
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter


def _rect(widget, ancestor) -> dict[str, int | bool]:
    point = widget.mapTo(ancestor, widget.rect().topLeft())
    return {
        "x": point.x(),
        "y": point.y(),
        "width": widget.width(),
        "height": widget.height(),
        "visible": widget.isVisible(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--state", required=True, choices=("default", "scrolled"))
    args = parser.parse_args()
    if re.fullmatch(r"[a-z][a-z0-9-]*", args.phase) is None:
        parser.error("--phase must contain only lower-case letters, digits, and hyphens")
    root = args.artifacts_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    app = QApplication(["foliaseal-appearance-layout-capture"])
    if app.platformName() != "xcb":
        raise RuntimeError("display-backed capture requires the Qt xcb platform")

    with TemporaryDirectory(prefix="foliaseal-appearance-capture-") as temp:
        storage = Path(temp)
        frame = QtAppFrameAdapter().create_frame(
            app_settings=AppSettings(
                schema_version=1,
                default_output_directory=str(storage / "home"),
                default_open_directory=str(storage / "home"),
                linux_packaging_channel="primary",
                ui={},
            ),
            app_settings_store=AppSettingsStore(storage_dir=storage / "config"),
            certificate_catalog_store=CertificateCatalogStore(storage_dir=storage / "certificates"),
            preset_catalog_store=SignaturePresetCatalogStore(storage_dir=storage / "profiles"),
        )
        try:
            frame.window.show()
            library = frame.show_reusable_object_library()
            app.processEvents()
            library.controls.catalog_selector.setCurrentRow(
                list(LibraryCatalog).index(LibraryCatalog.APPEARANCES)
            )
            app.processEvents()
            library.controls.create_button.click()
            app.processEvents()
            editor = library.controls.appearance_editor
            if editor is None:
                raise RuntimeError("Appearance editor did not open")
            dialog = library.controls.dialog
            dialog.resize(1000, 650)
            if library.controls.splitter is not None:
                library.controls.splitter.setSizes([120, 180, 700])
            app.processEvents()
            scroll_area = editor.controls.form_scroll_area
            if scroll_area is None:
                raise RuntimeError("Appearance form scroll area is unavailable")
            bar = scroll_area.verticalScrollBar()
            if args.state == "scrolled":
                if bar.maximum() <= 0:
                    raise RuntimeError("editor form does not scroll")
                bar.setValue(bar.maximum())
                app.processEvents()
            # X11 may deliver the initial 1100-by-700 show size after the first
            # resize request. Settle the window before recording either state.
            for _ in range(5):
                dialog.resize(1000, 650)
                app.processEvents()
            if (dialog.width(), dialog.height()) != (1000, 650):
                raise RuntimeError("window manager did not settle at 1000 by 650")
            if not dialog.isVisible():
                raise RuntimeError("Library dialog is not visible")
            pixmap = dialog.grab()
            if pixmap.isNull():
                raise RuntimeError("Library dialog capture is null")
            stem = f"{args.phase}-{args.state}"
            image_path = root / f"{stem}.png"
            report_path = root / f"{stem}.json"
            if not pixmap.save(str(image_path), "PNG"):
                raise RuntimeError("could not write Library PNG")
            font = app.font()
            screen = dialog.screen() or app.primaryScreen()
            report = {
                "phase": args.phase,
                "state": args.state,
                "requested_size": [1000, 650],
                "actual_size": [dialog.width(), dialog.height()],
                "image_pixels": [pixmap.width(), pixmap.height()],
                "screen": screen.name() if screen else None,
                "device_pixel_ratio": dialog.devicePixelRatioF(),
                "style": app.style().objectName(),
                "qt_platform": app.platformName(),
                "palette_window": app.palette().color(QPalette.ColorRole.Window).name(),
                "font": {
                    "family": font.family(),
                    "point_size": font.pointSize(),
                    "pixel_size": font.pixelSize(),
                    "height": QFontMetrics(font).height(),
                },
                "requested_splitter_sizes": [120, 180, 700],
                "actual_splitter_sizes": (
                    library.controls.splitter.sizes() if library.controls.splitter else None
                ),
                "scrollbar": {"value": bar.value(), "maximum": bar.maximum()},
                "widgets": {
                    "editor": _rect(editor.controls.container, dialog),
                    "breadcrumb": _rect(editor.controls.breadcrumb_label, dialog),
                    "sample_text": _rect(editor.controls.sample_preview_label, dialog),
                    "sample_image": _rect(editor.controls.sample_preview_image, dialog),
                    "name": _rect(editor.controls.name_input, dialog),
                    "scroll_area": _rect(scroll_area, dialog),
                    "cancel": _rect(editor.controls.cancel_button, dialog),
                    "save": _rect(editor.controls.save_button, dialog),
                },
            }
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"image": str(image_path), "report": str(report_path)}))
        finally:
            if "library" in locals():
                library.controls.dialog.close()
            frame.window.close()
            app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
