from pathlib import Path

from foliaseal.build.debian_packaging import (
    ICON_RELATIVE_PATH,
    control_text,
    debian_version,
    desktop_entry,
    package_filename,
    stage_package,
)


def test_debian_version_and_filename_are_deterministic() -> None:
    assert debian_version("1.2.3+local") == "1.2.3~local"
    assert package_filename("1.2.3+local", "amd64") == "foliaseal_1.2.3~local_amd64.deb"


def test_control_declares_required_runtime_dependency() -> None:
    control = control_text("0.1.0", "amd64")

    assert "Package: foliaseal\n" in control
    assert "Version: 0.1.0\n" in control
    assert "Architecture: amd64\n" in control
    assert "Depends: poppler-utils\n" in control
    assert "Description: Linux desktop PDF signing application\n" in control


def test_desktop_entry_launches_installed_gui() -> None:
    entry = desktop_entry()

    assert "Type=Application\n" in entry
    assert "Exec=/usr/bin/foliaseal gui\n" in entry
    assert "Icon=foliaseal\n" in entry
    assert "Terminal=false\n" in entry


def test_stage_package_contains_relocated_bundle_and_metadata(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    bundle = root / "dist/foliaseal"
    (bundle / "resources").mkdir(parents=True)
    (bundle / "foliaseal").write_text("#!/bin/sh\necho package\n", encoding="utf-8")
    (root / "packaging").mkdir(parents=True)
    (root / "packaging/foliaseal.svg").write_text("<svg />\n", encoding="utf-8")
    staging = root / "build/deb-staging"

    stage_package(
        root=root,
        bundle=bundle,
        staging=staging,
        version="0.1.0",
        architecture="amd64",
    )

    wrapper = staging / "usr/bin/foliaseal"
    wrapper_text = wrapper.read_text(encoding="utf-8")
    assert 'exec /usr/lib/foliaseal/foliaseal "$@"' in wrapper_text
    assert 'exec "$prefix/usr/lib/foliaseal/foliaseal" "$@"' in wrapper_text
    assert wrapper.stat().st_mode & 0o111
    assert (staging / "usr/lib/foliaseal/foliaseal").is_file()
    assert (staging / "DEBIAN/control").is_file()
    assert (staging / "usr/share/applications/foliaseal.desktop").is_file()
    icon = staging / ICON_RELATIVE_PATH
    assert icon.read_text(encoding="utf-8") == "<svg />\n"
