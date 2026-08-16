#!/usr/bin/env python3
"""Exercise a built FoliaSeal .deb without importing the checkout or virtualenv."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

_UNSAFE_MARKUP_PATTERN = re.compile(
    r"(?:https?://|//|javascript:|data:|file:|<script\b|QWebEngine|!\[)",
    re.IGNORECASE,
)
_GUI_LIMITED_SIGNATURES = (
    "SingleInstanceUnavailable: A FoliaSeal owner is active but not accepting requests:",
    "SingleInstanceUnavailable: Unable to claim or reach the FoliaSeal instance endpoint:",
)
_REQUIRED_HELP_TOPIC = "signing-basics"
_REQUIRED_HELP_COMMANDS = (
    "help --list",
    "help signing-basics --format markdown",
    "help signing-basics --path",
)
_REQUIRED_FONT_FILES = frozenset(
    {
        "Dancing_Script_Regular.ttf",
        "DejaVuSansMono-Bold.ttf",
        "DejaVuSansMono-BoldOblique.ttf",
        "DejaVuSansMono-Oblique.ttf",
        "DejaVuSansMono.ttf",
        "NotoSans-Bold.ttf",
        "NotoSans-BoldItalic.ttf",
        "NotoSans-Italic.ttf",
        "NotoSans-Regular.ttf",
        "NotoSerif-Bold.ttf",
        "NotoSerif-BoldItalic.ttf",
        "NotoSerif-Italic.ttf",
        "NotoSerif-Regular.ttf",
        "NotoSerifDisplay-Bold.ttf",
        "NotoSerifDisplay-BoldItalic.ttf",
        "NotoSerifDisplay-Italic.ttf",
        "NotoSerifDisplay-Regular.ttf",
        "Segoe_Script_Bold.ttf",
    }
)


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"command failed ({exc.returncode}): {' '.join(command)}\n"
            f"stdout={exc.stdout}\nstderr={exc.stderr}"
        ) from exc


def parse_control_fields(text: str) -> dict[str, str]:
    """Parse the single-record Debian control fields used by the package audit."""

    fields: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith((" ", "\t")):
            if current is not None:
                fields[current] += "\n" + line[1:]
            continue
        if not line.strip():
            continue
        name, separator, value = line.partition(":")
        if not separator or not name or name in fields:
            raise ValueError(f"invalid Debian control line: {line!r}")
        current = name
        fields[name] = value.lstrip()
    return fields


def desktop_entry_fields(text: str) -> dict[str, str]:
    """Return key/value pairs from the application desktop-entry section."""

    fields: dict[str, str] = {}
    in_entry = False
    for line in text.splitlines():
        if line == "[Desktop Entry]":
            in_entry = True
            continue
        if line.startswith("["):
            in_entry = False
            continue
        if not in_entry or not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        if separator:
            fields[name] = value
    return fields


def validate_help_markdown(markdown: str) -> None:
    """Reject empty or unsafe local Help content using the catalog contract."""

    if not markdown.strip() or _UNSAFE_MARKUP_PATTERN.search(markdown):
        raise ValueError("Help topic is empty or contains unsafe markup")


def classify_gui_result(
    returncode: int | None,
    output: str,
    *,
    started: bool = False,
) -> dict[str, object]:
    """Classify packaged GUI startup without hiding unrelated runtime failures."""

    if started:
        return {"status": "started", "returncode": returncode, "output_tail": output[-1000:]}
    if returncode is not None and returncode != 0:
        for signature in _GUI_LIMITED_SIGNATURES:
            if signature in output:
                return {
                    "status": "limited",
                    "returncode": returncode,
                    "reason": signature,
                    "output_tail": output[-1000:],
                }
    reason = "packaged GUI exited before startup"
    if returncode not in (None, 0):
        reason = f"packaged GUI exited with code {returncode} before startup"
    return {
        "status": "failed",
        "returncode": returncode,
        "reason": reason,
        "output_tail": output[-1000:],
    }


def build_warning_lines(build_log: str | None) -> list[str]:
    """Extract warning lines from an optional package-build transcript."""

    if not build_log:
        return []
    return [line for line in build_log.splitlines() if "warning" in line.lower()]


def validate_font_files(fonts: list[str]) -> None:
    """Require the complete canonical font payload for the supported package."""

    if set(fonts) != _REQUIRED_FONT_FILES:
        missing = sorted(_REQUIRED_FONT_FILES - set(fonts))
        unexpected = sorted(set(fonts) - _REQUIRED_FONT_FILES)
        raise ValueError(f"bundled font set differs; missing={missing}, unexpected={unexpected}")


def offline_environment(base_env: dict[str, str]) -> dict[str, str]:
    """Create a child environment with ambient proxy/network hints removed."""

    env = dict(base_env)
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    for name in (
        "ALL_PROXY",
        "all_proxy",
        "HTTP_PROXY",
        "http_proxy",
        "HTTPS_PROXY",
        "https_proxy",
        "NO_PROXY",
        "no_proxy",
    ):
        env.pop(name, None)
    env["NO_PROXY"] = "*"
    env["no_proxy"] = "*"
    return env


def write_report(report: dict[str, object], artifacts_dir: Path) -> Path:
    """Write one deterministic JSON report under the caller-owned evidence root."""

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifacts_dir / "audit.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report_path


def _fixture_pdf(path: Path) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>",
        b"<< /Length 28 >>\nstream\nBT /F1 18 Tf 72 720 Td "
        b"(FoliaSeal package audit) Tj ET\nendstream",
    ]
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode())
        payload.extend(body)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode())
    payload.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    path.write_bytes(payload)


def _run_gui(
    wrapper: Path,
    pdf: Path,
    *,
    cwd: Path,
    env: dict[str, str],
) -> dict[str, object]:
    process = subprocess.Popen(
        [str(wrapper), "gui", "--pdf-path", str(pdf)],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        try:
            stdout, stderr = process.communicate(timeout=3.0)
        except subprocess.TimeoutExpired:
            # A still-running process has reached the startup boundary. Terminate it
            # so an acceptance audit never leaves a GUI or child process behind.
            returncode: int | None = None
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate(timeout=5.0)
            return classify_gui_result(
                returncode,
                f"{stdout}\n{stderr}",
                started=True,
            )
        return classify_gui_result(process.returncode, f"{stdout}\n{stderr}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5.0)


def _assert_inside(path: Path, root: Path, description: str) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"{description} escapes the extracted package") from exc


def _assert_dedicated_child(path: Path, root: Path, description: str) -> None:
    """Require ``path`` to be a strict child of the caller-owned root."""

    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if resolved_path == resolved_root:
        raise RuntimeError(f"{description} must be a dedicated child of its owner")
    _assert_inside(resolved_path, resolved_root, description)


def _expected_help_entries(index_path: Path) -> list[dict[str, Any]]:
    try:
        entries = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("packaged Help index is unreadable") from exc
    if (
        not isinstance(entries, list)
        or not entries
        or not all(isinstance(entry, dict) for entry in entries)
    ):
        raise RuntimeError("packaged Help index is not a non-empty list of records")
    required = {"id", "title", "keywords", "related", "filename"}
    for entry in entries:
        if set(entry) != required:
            raise RuntimeError("packaged Help index has an invalid record shape")
    return entries


def _runtime_resource_root(bundle_root: Path) -> Path:
    """Locate packaged resources in current or legacy PyInstaller one-dir layouts."""

    candidates = [
        bundle_root / "foliaseal/resources",
        bundle_root / "_internal/foliaseal/resources",
    ]
    candidates.extend(
        path.parent.parent
        for path in bundle_root.glob("**/foliaseal/resources/help/index.json")
    )
    roots = {path.resolve() for path in candidates if (path / "help/index.json").is_file()}
    if len(roots) != 1:
        raise RuntimeError(
            "package must contain exactly one PyInstaller FoliaSeal resource root; "
            f"found {sorted(str(root) for root in roots)}"
        )
    return next(iter(roots))


def _audit_help(
    wrapper: Path,
    *,
    help_root: Path,
    package_root: Path,
    cwd: Path,
    env: dict[str, str],
) -> dict[str, object]:
    index_path = help_root / "index.json"
    entries = _expected_help_entries(index_path)
    expected_list = [f"{entry['id']}\t{entry['title']}" for entry in entries]
    list_result = _run([str(wrapper), "help", "--list"], cwd=cwd, env=env)
    if list_result.stdout.strip().splitlines() != expected_list:
        raise RuntimeError("installed Help list differs from its packaged index")

    topic = next((entry for entry in entries if entry["id"] == _REQUIRED_HELP_TOPIC), None)
    if topic is None:
        raise RuntimeError(f"packaged Help index is missing {_REQUIRED_HELP_TOPIC}")
    topic_path = help_root / str(topic["filename"])
    markdown_result = _run(
        [str(wrapper), "help", _REQUIRED_HELP_TOPIC, "--format", "markdown"],
        cwd=cwd,
        env=env,
    )
    validate_help_markdown(markdown_result.stdout)
    if markdown_result.stdout != topic_path.read_text(encoding="utf-8"):
        raise RuntimeError("installed Help Markdown differs from its packaged topic file")
    path_result = _run(
        [str(wrapper), "help", _REQUIRED_HELP_TOPIC, "--path"],
        cwd=cwd,
        env=env,
    )
    returned_path = Path(path_result.stdout.strip()).resolve()
    _assert_inside(returned_path, package_root, "Help topic path")
    if returned_path != topic_path.resolve():
        raise RuntimeError("installed Help topic path does not point to the packaged topic")
    return {
        "commands": list(_REQUIRED_HELP_COMMANDS),
        "topic_count": len(entries),
        "topic_ids": [str(entry["id"]) for entry in entries],
        "markdown_safe": True,
        "topic_path_inside_extracted_package": True,
    }


def _audit_dependency(fixture: Path, *, cwd: Path, env: dict[str, str]) -> dict[str, object]:
    pdftoppm = shutil.which("pdftoppm", path=env.get("PATH"))
    if pdftoppm is None:
        raise RuntimeError("required poppler-utils command pdftoppm is unavailable")
    help_result = subprocess.run(
        [pdftoppm, "-h"],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30.0,
    )
    output_stem = cwd / "pdftoppm-output"
    conversion = subprocess.run(
        [pdftoppm, "-png", "-singlefile", str(fixture), str(output_stem)],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30.0,
    )
    help_output = help_result.stdout + help_result.stderr
    if not help_output.strip():
        raise RuntimeError("pdftoppm help probe returned no output")
    if conversion.returncode != 0 or not output_stem.with_suffix(".png").is_file():
        raise RuntimeError(
            "pdftoppm could not render the package audit fixture: "
            f"code={conversion.returncode}, stderr={conversion.stderr}"
        )
    return {
        "scope": "host-runtime",
        "command": pdftoppm,
        "help_returncode": help_result.returncode,
        "help_output_present": True,
        "fixture_conversion": True,
        "help_output_tail": help_output[-500:],
    }


def package_manager_install_command(
    package: Path,
    install_root: Path,
    *,
    fakeroot_path: str | None = None,
    effective_uid: int | None = None,
    launcher: str | None = None,
) -> list[str]:
    """Build a dpkg command whose database and payload are confined to ``install_root``."""

    root = install_root.resolve()
    admin_dir = root / "var/lib/dpkg"
    command: list[str] = []
    uid = os.geteuid() if effective_uid is None else effective_uid
    if uid != 0:
        selected_launcher = launcher
        if selected_launcher is None:
            selected_launcher = "unshare" if shutil.which("unshare") is not None else "fakeroot"
        if selected_launcher == "unshare":
            unshare = shutil.which("unshare")
            if unshare is None:
                raise RuntimeError("requested unshare launcher is unavailable")
            command.extend([unshare, "--user", "--map-root-user", "--"])
        elif selected_launcher == "fakeroot":
            fakeroot = fakeroot_path or shutil.which("fakeroot")
            if fakeroot is None:
                raise RuntimeError(
                    "unprivileged package-manager smoke requires unshare or fakeroot"
                )
            command.append(fakeroot)
        else:
            raise ValueError(f"unknown package-manager launcher: {selected_launcher}")
    command.extend(
        [
            "dpkg",
            f"--root={root}",
            f"--admindir={admin_dir}",
            f"--instdir={root}",
            f"--log={root / 'var/log/dpkg.log'}",
            "--unpack",
            str(package.resolve()),
        ]
    )
    return command


def _initialize_package_manager_root(install_root: Path) -> None:
    """Create the minimum private dpkg database layout required for ``dpkg --unpack``."""

    admin_dir = install_root / "var/lib/dpkg"
    (install_root / "var/log").mkdir(parents=True, exist_ok=True)
    for relative in ("updates", "info"):
        (admin_dir / relative).mkdir(parents=True, exist_ok=True)
    status_path = admin_dir / "status"
    status_path.touch(exist_ok=True)


def _prepare_package_manager_root(install_root: Path) -> None:
    """Reset a dedicated install root and create its private runtime directories."""

    if install_root.exists():
        for child in install_root.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    else:
        install_root.mkdir(parents=True)
    for directory in ("home", "config", "data", "cache"):
        (install_root / directory).mkdir()
    _initialize_package_manager_root(install_root)


def _audit_package_manager_install(
    package: Path,
    install_root: Path,
    *,
    fixture: Path,
    base_env: dict[str, str],
    owner_root: Path,
) -> dict[str, object]:
    """Install and exercise one package in a disposable, caller-owned root."""

    install_root = install_root.resolve()
    owner_root = owner_root.resolve()
    _assert_dedicated_child(install_root, owner_root, "package-manager install root")
    if install_root.exists() and any(install_root.iterdir()):
        raise RuntimeError(f"package-manager install root is not empty: {install_root}")
    env = offline_environment(base_env)
    env["HOME"] = str(install_root / "home")
    env["XDG_CONFIG_HOME"] = str(install_root / "config")
    env["XDG_DATA_HOME"] = str(install_root / "data")
    env["XDG_CACHE_HOME"] = str(install_root / "cache")
    env["QT_QPA_PLATFORM"] = "offscreen"
    try:
        _prepare_package_manager_root(install_root)
        command = package_manager_install_command(package, install_root)
        result = subprocess.run(
            command,
            cwd=install_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=120.0,
        )
        output = f"{result.stdout}\n{result.stderr}".strip()
        if result.returncode != 0:
            # User namespaces may be present but disabled by policy. Retry once
            # under fakeroot when the preferred unshare launcher failed at runtime.
            if command and Path(command[0]).name == "unshare" and shutil.which("fakeroot"):
                _prepare_package_manager_root(install_root)
                command = package_manager_install_command(
                    package,
                    install_root,
                    launcher="fakeroot",
                )
                result = subprocess.run(
                    command,
                    cwd=install_root,
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                    timeout=120.0,
                )
                output = f"{result.stdout}\n{result.stderr}".strip()
            if result.returncode != 0:
                raise RuntimeError(
                    "package-manager install failed: "
                    f"code={result.returncode}, output={output[-2000:]}"
                )
        wrapper = install_root / "usr/bin/foliaseal"
        executable = install_root / "usr/lib/foliaseal/foliaseal"
        if not wrapper.is_file() or not executable.is_file():
            raise RuntimeError("package-manager install omitted the wrapper or bundle executable")
        help_result = _run([str(wrapper), "--help"], cwd=install_root, env=env)
        if "usage:" not in help_result.stdout.lower():
            raise RuntimeError("package-manager installed wrapper --help did not emit usage text")
        bundle_root = install_root / "usr/lib/foliaseal"
        resource_root = _runtime_resource_root(bundle_root)
        fonts = sorted(path.name for path in (resource_root / "fonts").glob("*.ttf"))
        validate_font_files(fonts)
        help_result_report = _audit_help(
            wrapper,
            help_root=resource_root / "help",
            package_root=install_root,
            cwd=install_root,
            env=env,
        )
        gui_result = _run_gui(wrapper, fixture, cwd=install_root, env=env)
        if gui_result["status"] == "failed":
            raise RuntimeError(str(gui_result.get("reason", "installed GUI startup failed")))
        dependency_result = _audit_dependency(fixture, cwd=install_root, env=env)
        return {
            "status": "passed",
            "command": command,
            "dpkg_returncode": result.returncode,
            "wrapper": "usr/bin/foliaseal",
            "executable": "usr/lib/foliaseal/foliaseal",
            "resource_root": str(resource_root.relative_to(install_root)),
            "help": help_result_report,
            "fonts": {"count": len(fonts), "files": fonts},
            "dependency": dependency_result,
            "gui_startup": gui_result,
            "temporary_install_root_cleaned": False,
        }
    finally:
        shutil.rmtree(install_root, ignore_errors=True)


def audit(
    package: Path,
    artifacts_dir: Path,
    *,
    build_log: Path | None = None,
    package_manager_root: Path | None = None,
) -> dict[str, object]:
    """Extract and validate one Debian artifact, returning a bounded JSON report."""

    package = package.resolve()
    if not package.is_file():
        raise FileNotFoundError(package)
    artifacts_dir = artifacts_dir.resolve()
    report: dict[str, object]
    with tempfile.TemporaryDirectory(prefix="foliaseal-deb-audit-") as temp_name:
        root = Path(temp_name)
        extract_root = root / "extracted"
        control_root = root / "control"
        base_env = os.environ.copy()
        _run(
            ["dpkg-deb", "--extract", str(package), str(extract_root)],
            cwd=root,
            env=base_env,
        )
        _run(
            ["dpkg-deb", "--control", str(package), str(control_root)],
            cwd=root,
            env=base_env,
        )
        wrapper = extract_root / "usr/bin/foliaseal"
        executable = extract_root / "usr/lib/foliaseal/foliaseal"
        desktop = extract_root / "usr/share/applications/foliaseal.desktop"
        icon = extract_root / "usr/share/icons/hicolor/scalable/apps/foliaseal.svg"
        control = control_root / "control"
        if not wrapper.is_file() or not executable.is_file():
            raise RuntimeError("package payload is missing the installed wrapper or executable")
        if not os.access(wrapper, os.X_OK) or not os.access(executable, os.X_OK):
            raise RuntimeError("package wrapper or executable is not executable")
        if not desktop.is_file() or not icon.is_file() or not control.is_file():
            raise RuntimeError("package is missing desktop, icon, or Debian control metadata")

        control_fields = parse_control_fields(control.read_text(encoding="utf-8"))
        if control_fields.get("Package") != "foliaseal":
            raise RuntimeError("package control metadata has the wrong Package field")
        if "poppler-utils" not in control_fields.get("Depends", "").split(","):
            raise RuntimeError("package control metadata does not declare poppler-utils")
        desktop_fields = desktop_entry_fields(desktop.read_text(encoding="utf-8"))
        expected_desktop = {
            "Exec": "/usr/bin/foliaseal gui",
            "Icon": "foliaseal",
            "Terminal": "false",
        }
        if any(desktop_fields.get(key) != value for key, value in expected_desktop.items()):
            raise RuntimeError("desktop entry does not match the installed GUI launcher contract")

        env = offline_environment(base_env)
        env["HOME"] = str(root / "home")
        env["XDG_CONFIG_HOME"] = str(root / "config")
        env["XDG_DATA_HOME"] = str(root / "data")
        env["XDG_CACHE_HOME"] = str(root / "cache")
        env["QT_QPA_PLATFORM"] = "offscreen"
        for directory in ("home", "config", "data", "cache"):
            (root / directory).mkdir()
        fixture = root / "audit.pdf"
        _fixture_pdf(fixture)
        help_result = _run([str(wrapper), "--help"], cwd=root, env=env)
        if "usage:" not in help_result.stdout.lower():
            raise RuntimeError("installed wrapper --help did not emit usage text")

        bundle_root = extract_root / "usr/lib/foliaseal"
        resource_root = _runtime_resource_root(bundle_root)
        font_root = resource_root / "fonts"
        help_root = resource_root / "help"
        fonts = sorted(path.name for path in font_root.glob("*.ttf"))
        try:
            validate_font_files(fonts)
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
        if not (help_root / "index.json").is_file():
            raise RuntimeError("package is missing the bundled Help index")
        help_result_report = _audit_help(
            wrapper,
            help_root=help_root,
            package_root=extract_root,
            cwd=root,
            env=env,
        )
        gui_result = _run_gui(wrapper, fixture, cwd=root, env=env)
        if gui_result["status"] == "failed":
            raise RuntimeError(str(gui_result.get("reason", "packaged GUI startup failed")))
        dependency_result = _audit_dependency(fixture, cwd=root, env=env)
        report = {
            "status": "passed",
            "package": str(package),
            "package_version": control_fields.get("Version"),
            "package_architecture": control_fields.get("Architecture"),
            "payload": {
                "wrapper": "/usr/bin/foliaseal",
                "executable": "/usr/lib/foliaseal/foliaseal",
                "desktop_entry": "/usr/share/applications/foliaseal.desktop",
                "icon": "/usr/share/icons/hicolor/scalable/apps/foliaseal.svg",
                "wrapper_executable": True,
                "bundle_executable": True,
            },
            "desktop_entry": expected_desktop,
            "control": {
                "package": control_fields.get("Package"),
                "depends": control_fields.get("Depends"),
                "poppler_utils_declared": True,
            },
            "help": help_result_report,
            "fonts": {"count": len(fonts), "files": fonts},
            "resource_root": str(resource_root.relative_to(extract_root)),
            "dependency": dependency_result,
            "gui_startup": gui_result,
            "build_warnings": build_warning_lines(
                build_log.read_text(encoding="utf-8", errors="replace")
                if build_log is not None and build_log.is_file()
                else None
            ),
            "offline_environment": {
                "proxy_environment_removed": True,
                "network_requests_required": False,
            },
            "temporary_extraction_cleaned": True,
        }
        if package_manager_root is not None:
            report["package_manager_install"] = _audit_package_manager_install(
                package,
                package_manager_root,
                fixture=fixture,
                base_env=base_env,
                owner_root=artifacts_dir.parent,
            )
            report["package_manager_install"]["temporary_install_root_cleaned"] = not Path(
                package_manager_root
            ).exists()
    write_report(report, artifacts_dir)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument(
        "--build-log",
        type=Path,
        default=None,
        help="Optional build stderr transcript from which warning lines are recorded.",
    )
    parser.add_argument(
        "--package-manager-root",
        type=Path,
        default=None,
        help="Optional disposable root for an isolated dpkg/fakeroot install smoke check.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            audit(
                args.package,
                args.artifacts_dir,
                build_log=args.build_log,
                package_manager_root=args.package_manager_root,
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
