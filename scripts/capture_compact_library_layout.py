"""Capture deterministic compact Signature Library states on a real Qt display."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PySide6.QtGui import QColor, QFontMetrics, QImage, QPainter, QPalette
from PySide6.QtWidgets import QApplication

from foliaseal.application.signature_library_session import LibraryCatalog
from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter

CAPTURE_STATES = (
    "presets",
    "empty",
    "certificates",
    "appearance-default",
    "appearance-reordered",
    "appearance-image",
    "appearance-scrolled",
)


def _rect(widget: Any | None, ancestor: Any) -> dict[str, int | bool] | None:
    if widget is None:
        return None
    point = widget.mapTo(ancestor, widget.rect().topLeft())
    return {
        "x": point.x(),
        "y": point.y(),
        "width": widget.width(),
        "height": widget.height(),
        "visible": widget.isVisible(),
    }


def _click_create(library: Any) -> None:
    button = library.controls.create_button
    if not button.isVisible() and library.controls.empty_create_button is not None:
        button = library.controls.empty_create_button
    button.click()


def _select_catalog(library: Any, app: QApplication, catalog: LibraryCatalog) -> None:
    library.controls.catalog_selector.setCurrentText(catalog.value)
    app.processEvents()
    if library.controls.catalog_selector.currentText() != catalog.value:
        raise RuntimeError(f"could not select the {catalog.value!r} catalog")


def _open_appearance(library: Any, app: QApplication) -> Any:
    _select_catalog(library, app, LibraryCatalog.APPEARANCES)
    _click_create(library)
    app.processEvents()
    editor = library.controls.appearance_editor
    if editor is None:
        raise RuntimeError("Appearance editor did not open")
    return editor


def _write_synthetic_image(path: Path) -> None:
    sample = QImage(360, 72, QImage.Format.Format_ARGB32)
    sample.fill(QColor("white"))
    painter = QPainter(sample)
    painter.setPen(QColor("#17365d"))
    painter.drawLine(12, 52, 348, 12)
    painter.drawLine(12, 59, 210, 59)
    painter.end()
    if not sample.save(str(path), "PNG"):
        raise RuntimeError("could not create the synthetic signature image")


def _prepare_state(
    state: str,
    *,
    app: QApplication,
    library: Any,
    storage: Path,
) -> Any | None:
    if state == "presets":
        appearance = _open_appearance(library, app)
        appearance.controls.name_input.setText("Synthetic approval appearance")
        appearance.controls.save_button.click()
        app.processEvents()
        if library.controls.appearance_editor is not None:
            raise RuntimeError("synthetic Appearance did not save")
        _select_catalog(library, app, LibraryCatalog.PRESETS)
        _click_create(library)
        app.processEvents()
        if library.controls.preset_editor is None:
            raise RuntimeError("Preset editor did not open")
        library.controls.preset_editor.controls.name_input.setText("Synthetic approval preset")
        return library.controls.preset_editor
    if state == "empty":
        _select_catalog(library, app, LibraryCatalog.PLACEMENTS)
        return None
    if state == "certificates":
        _select_catalog(library, app, LibraryCatalog.CERTIFICATES)
        return None

    editor = _open_appearance(library, app)
    editor.controls.name_input.setText("Synthetic approval appearance")
    if state == "appearance-reordered":
        field_order = editor.controls.setup_form.appearance_controls.field_order
        field_order.setCurrentIndex(0)
        editor.controls.setup_form.appearance_controls.move_field_down.click()
        app.processEvents()
    if state == "appearance-image":
        image_path = storage / "synthetic-signature.png"
        _write_synthetic_image(image_path)
        editor.controls.setup_form.set_image_stamp_path(str(image_path))
        app.processEvents()
    if state == "appearance-scrolled":
        bar = editor.controls.form_scroll_area.verticalScrollBar()
        if bar.maximum() <= 0:
            raise RuntimeError("Appearance form does not scroll")
        bar.setValue(bar.maximum())
        app.processEvents()
    return editor


def _state_widgets(library: Any, active_editor: Any | None) -> dict[str, Any]:
    dialog = library.controls.dialog
    controls = library.controls
    widgets: dict[str, Any] = {
        "catalog_selector": _rect(controls.catalog_selector, dialog),
        "object_selector": _rect(controls.object_selector, dialog),
        "sort_selector": _rect(controls.sort_selector, dialog),
        "create": _rect(controls.create_button, dialog),
        "rename": _rect(controls.rename_button, dialog),
        "duplicate": _rect(controls.duplicate_button, dialog),
        "pin": _rect(controls.pin_button, dialog),
        "delete": _rect(controls.delete_button, dialog),
        "detail": _rect(controls.detail_container, dialog),
        "detail_view": _rect(controls.detail_view, dialog),
        "empty_create": _rect(controls.empty_create_button, dialog),
        "footer": _rect(controls.library_footer_host, dialog),
        "cancel": _rect(controls.cancel_button, dialog),
        "save": _rect(controls.save_button, dialog),
    }
    if active_editor is not None and active_editor is library.controls.appearance_editor:
        editor = active_editor.controls
        widgets.update(
            {
                "editor": _rect(editor.container, dialog),
                "breadcrumb": _rect(editor.breadcrumb_label, dialog),
                "sample_text": _rect(editor.sample_preview_label, dialog),
                "sample_image": _rect(editor.sample_preview_image, dialog),
                "name": _rect(editor.name_input, dialog),
                "scroll_area": _rect(editor.form_scroll_area, dialog),
            }
        )
    elif active_editor is not None and active_editor is library.controls.preset_editor:
        editor = active_editor.controls
        widgets.update(
            {
                "editor": _rect(editor.container, dialog),
                "breadcrumb": _rect(editor.breadcrumb_label, dialog),
                "name": _rect(editor.name_input, dialog),
                "appearance_selector": _rect(editor.appearance_selector, dialog),
                "placement_selector": _rect(editor.placement_selector, dialog),
                "certificate_selector": _rect(editor.certificate_selector, dialog),
            }
        )
    return widgets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--state", required=True, choices=CAPTURE_STATES)
    args = parser.parse_args()
    if re.fullmatch(r"[a-z][a-z0-9-]*", args.phase) is None:
        parser.error("--phase must contain only lower-case letters, digits, and hyphens")

    root = args.artifacts_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    app = QApplication(["foliaseal-compact-library-layout-capture"])
    if app.platformName() != "xcb":
        raise RuntimeError("display-backed capture requires the Qt xcb platform")

    original_cwd = Path.cwd()
    with TemporaryDirectory(prefix="foliaseal-compact-library-capture-") as temp:
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
            certificate_catalog_store=CertificateCatalogStore(
                storage_dir=storage / "certificates"
            ),
            preset_catalog_store=SignaturePresetCatalogStore(
                storage_dir=storage / "profiles"
            ),
        )
        library = None
        try:
            os.chdir(storage)
            frame.window.show()
            library = frame.show_reusable_object_library()
            app.processEvents()
            active_editor = _prepare_state(
                args.state, app=app, library=library, storage=storage
            )
            dialog = library.controls.dialog
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
            appearance = library.controls.appearance_editor
            appearance_bar = (
                appearance.controls.form_scroll_area.verticalScrollBar()
                if appearance is not None
                else None
            )
            image_pixmap = (
                appearance.controls.sample_preview_image.pixmap()
                if appearance is not None
                else None
            )
            sample_scroll = (
                appearance.controls.sample_preview_scroll_area
                if appearance is not None
                else None
            )
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
                "catalog": library.controls.catalog_selector.currentText(),
                "saved_object_count": library.controls.object_selector.count(),
                "saved_object_text": library.controls.object_selector.currentText(),
                "active_splitter": library.controls.splitter is not None,
                "scrollbar": (
                    {"value": appearance_bar.value(), "maximum": appearance_bar.maximum()}
                    if appearance_bar is not None
                    else None
                ),
                "sample_pixmap": (
                    [image_pixmap.width(), image_pixmap.height()]
                    if image_pixmap is not None
                    else None
                ),
                "sample_horizontal_scroll": (
                    {
                        "maximum": sample_scroll.horizontalScrollBar().maximum(),
                        "viewport_width": sample_scroll.viewport().width(),
                    }
                    if sample_scroll is not None
                    else None
                ),
                "appearance_field_order": (
                    [
                        field.value
                        for field in (
                            appearance.controls.setup_form.build_draft().appearance.field_order
                        )
                    ]
                    if appearance is not None
                    else None
                ),
                "widgets": _state_widgets(library, active_editor),
            }
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"image": str(image_path), "report": str(report_path)}))
        finally:
            os.chdir(original_cwd)
            if library is not None:
                # Teardown must not enter the production dirty-close resolver:
                # capture states intentionally contain unsaved synthetic drafts.
                library.controls.dialog.hide()
                library.controls.dialog.deleteLater()
            frame.window.hide()
            frame.window.deleteLater()
            app.processEvents()
            app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
