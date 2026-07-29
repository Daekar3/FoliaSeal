"""Build and inspect the supported Debian-family FoliaSeal package."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

PACKAGE_NAME = "foliaseal"
MAINTAINER = "FoliaSeal Team <maintainers@foliaseal.invalid>"
DESCRIPTION = "Linux desktop PDF signing application"
ICON_RELATIVE_PATH = "usr/share/icons/hicolor/scalable/apps/foliaseal.svg"


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def project_version(root: Path | None = None) -> str:
    metadata_path = (root or project_root()) / "pyproject.toml"
    metadata = tomllib.loads(metadata_path.read_text(encoding="utf-8"))
    return str(metadata["project"]["version"])


def debian_version(version: str) -> str:
    """Return a deterministic Debian-safe version for a PEP 440-ish version."""

    normalized = re.sub(r"[^0-9A-Za-z.+:~-]", "-", version)
    normalized = normalized.replace("+", "~")
    if not normalized or normalized[0] in ".-":
        raise ValueError(f"Invalid package version: {version!r}")
    return normalized


def package_filename(version: str, architecture: str) -> str:
    return f"{PACKAGE_NAME}_{debian_version(version)}_{architecture}.deb"


def control_text(version: str, architecture: str) -> str:
    return (
        f"Package: {PACKAGE_NAME}\n"
        f"Version: {debian_version(version)}\n"
        f"Architecture: {architecture}\n"
        f"Maintainer: {MAINTAINER}\n"
        "Depends: poppler-utils\n"
        f"Description: {DESCRIPTION}\n"
        " FoliaSeal provides a desktop workflow for reviewing and digitally signing "
        "PDF documents.\n"
    )


def desktop_entry() -> str:
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=FoliaSeal\n"
        "Comment=Review and digitally sign PDF documents\n"
        "Exec=/usr/bin/foliaseal gui\n"
        "Icon=foliaseal\n"
        "Terminal=false\n"
        "Categories=Office;Security;\n"
        "MimeType=application/pdf;\n"
    )


def _run(command: list[str], *, cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def stage_package(
    *, root: Path, bundle: Path, staging: Path, version: str, architecture: str
) -> None:
    if not bundle.is_dir() or not (bundle / "foliaseal").is_file():
        raise FileNotFoundError(f"PyInstaller bundle is missing: {bundle}")
    if staging.exists():
        shutil.rmtree(staging)
    payload = staging / "usr/lib/foliaseal"
    (staging / "DEBIAN").mkdir(parents=True)
    payload.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle, payload)

    wrapper = staging / "usr/bin/foliaseal"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "if [ -x /usr/lib/foliaseal/foliaseal ]; then\n"
        "  exec /usr/lib/foliaseal/foliaseal \"$@\"\n"
        "fi\n"
        "prefix=$(CDPATH= cd -- \"$(dirname -- \"$0\")/../..\" && pwd)\n"
        "exec \"$prefix/usr/lib/foliaseal/foliaseal\" \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)

    desktop = staging / "usr/share/applications/foliaseal.desktop"
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text(desktop_entry(), encoding="utf-8")
    desktop.chmod(0o644)

    icon = root / "packaging/foliaseal.svg"
    if not icon.is_file():
        raise FileNotFoundError(f"Package icon is missing: {icon}")
    icon_destination = staging / ICON_RELATIVE_PATH
    icon_destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(icon, icon_destination)
    icon_destination.chmod(0o644)

    control = staging / "DEBIAN/control"
    control.write_text(control_text(version, architecture), encoding="utf-8")
    control.chmod(0o644)
    (staging / "DEBIAN/md5sums").unlink(missing_ok=True)


def build_deb(*, root: Path | None = None, output_dir: Path | None = None) -> Path:
    root = (root or project_root()).resolve()
    output_dir = (output_dir or root / "dist").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    version = project_version(root)
    architecture = subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip()
    filename = package_filename(version, architecture)
    output = output_dir / filename
    staging = root / "build/deb-staging"

    _run([str(root / "scripts/build_pyinstaller.sh")], cwd=root)
    stage_package(
        root=root,
        bundle=root / "dist/foliaseal",
        staging=staging,
        version=version,
        architecture=architecture,
    )
    if output.exists():
        output.unlink()
    _run(["dpkg-deb", "--build", "--root-owner-group", str(staging), str(output)], cwd=root)
    candidates = sorted(output_dir.glob(f"{PACKAGE_NAME}_*.deb"))
    if candidates != [output]:
        raise RuntimeError(
            "Expected exactly one deterministic package artifact, found: "
            f"{candidates}"
        )
    return output


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--print-metadata", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    root = project_root()
    if args.print_metadata:
        version = project_version(root)
        architecture = subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip()
        print(control_text(version, architecture), end="")
        print(desktop_entry(), end="")
        return 0
    print(build_deb(root=root, output_dir=args.output_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
