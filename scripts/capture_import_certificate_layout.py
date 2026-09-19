"""Capture the isolated Import Certificate dialog on a real Qt display."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from PySide6.QtGui import QFontMetrics, QPalette
from PySide6.QtWidgets import QApplication, QLabel

from foliaseal.infra.config.app_settings_storage import AppSettingsStore
from foliaseal.infra.config.certificate_storage import CertificateCatalogStore
from foliaseal.infra.config.profile_storage import SignaturePresetCatalogStore
from foliaseal.infra.config.schemas import AppSettings
from foliaseal.presentation.qt.app_frame import QtAppFrameAdapter
from foliaseal.presentation.qt.app_frame_certificate_management import CertificateImportDialog


def _rect(widget, ancestor) -> dict[str, int | bool]:
    point = widget.mapTo(ancestor, widget.rect().topLeft())
    return {
        "x": point.x(),
        "y": point.y(),
        "width": widget.width(),
        "height": widget.height(),
        "visible": widget.isVisible(),
    }


def _label(dialog, prefix: str):
    for label in dialog.findChildren(QLabel):
        if label.text().startswith(prefix):
            return label
    raise RuntimeError(f"could not find label starting with {prefix!r}")


def _write_synthetic_pkcs12(path: Path, passphrase: str) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Ada Example")])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    path.write_bytes(
        pkcs12.serialize_key_and_certificates(
            name=b"Ada Example",
            key=key,
            cert=certificate,
            cas=None,
            encryption_algorithm=serialization.BestAvailableEncryption(passphrase.encode()),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", required=True, type=Path)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--state", required=True, choices=("empty", "inspected"))
    args = parser.parse_args()
    if re.fullmatch(r"[a-z][a-z0-9-]*", args.phase) is None:
        parser.error("--phase must contain only lower-case letters, digits, and hyphens")
    root = args.artifacts_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    app = QApplication(["foliaseal-import-certificate-layout-capture"])
    if app.platformName() != "xcb":
        raise RuntimeError("display-backed capture requires the Qt xcb platform")

    original_cwd = Path.cwd()
    with TemporaryDirectory(prefix="foliaseal-import-certificate-capture-") as temp:
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
            preset_catalog_store=SignaturePresetCatalogStore(storage_dir=storage / "profiles"),
        )
        import_dialog = None
        try:
            frame.window.show()
            app.processEvents()
            import_dialog = CertificateImportDialog(
                bindings=frame._bindings,  # noqa: SLF001 - production bindings are capture input
                parent=frame.window,
                certificate_manager=frame._certificate_manager,  # noqa: SLF001
            )
            dialog = import_dialog.controls.dialog
            if args.state == "inspected":
                passphrase = "synthetic-passphrase"
                source = storage / "synthetic-certificate.p12"
                _write_synthetic_pkcs12(source, passphrase)
                os.chdir(storage)
                import_dialog.controls.certificate_path.setText(source.name)
                import_dialog.controls.display_name.setText("Synthetic signing certificate")
                import_dialog.controls.passphrase.setText(passphrase)
                if import_dialog.inspect_certificate() is None:
                    raise RuntimeError("synthetic certificate inspection failed")
            dialog.show()
            for _ in range(5):
                dialog.resize(600, 460)
                app.processEvents()
            if dialog.width() < 600 or dialog.height() < 460:
                raise RuntimeError("Import Certificate dialog is below its declared minimum")
            if not dialog.isVisible():
                raise RuntimeError("Import Certificate dialog is not visible")
            pixmap = dialog.grab()
            if pixmap.isNull():
                raise RuntimeError("Import Certificate capture is null")
            stem = f"{args.phase}-{args.state}"
            image_path = root / f"{stem}.png"
            report_path = root / f"{stem}.json"
            if not pixmap.save(str(image_path), "PNG"):
                raise RuntimeError("could not write Import Certificate PNG")
            font = app.font()
            screen = dialog.screen() or app.primaryScreen()
            report = {
                "phase": args.phase,
                "state": args.state,
                "requested_size": [600, 460],
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
                "password_echo_mode": int(import_dialog.controls.passphrase.echoMode().value),
                "widgets": {
                    "dialog": _rect(dialog, dialog),
                    "introduction": _rect(_label(dialog, "Import a certificate"), dialog),
                    "certificate_path": _rect(import_dialog.controls.certificate_path, dialog),
                    "choose": _rect(import_dialog.controls.choose_button, dialog),
                    "inspect": _rect(import_dialog.controls.inspect_button, dialog),
                    "inspection": _rect(import_dialog.controls.inspection_label, dialog),
                    "display_name": _rect(import_dialog.controls.display_name, dialog),
                    "password": _rect(import_dialog.controls.passphrase, dialog),
                    "remember_password": _rect(import_dialog.controls.save_password, dialog),
                    "cancel": _rect(import_dialog.controls.cancel_button, dialog),
                    "import": _rect(import_dialog.controls.import_button, dialog),
                },
            }
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"image": str(image_path), "report": str(report_path)}))
        finally:
            os.chdir(original_cwd)
            if import_dialog is not None:
                import_dialog.controls.dialog.close()
            frame.window.close()
            app.processEvents()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
