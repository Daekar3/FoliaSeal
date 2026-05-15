from pathlib import Path

import pytest

from foliaseal.infra.config.app_settings_storage import (
    APP_SETTINGS_FILENAME,
    AppSettingsStore,
    default_app_settings_directory,
)
from foliaseal.infra.config.schemas import AppSettings, ConfigValidationError


def test_default_app_settings_directory_uses_xdg_config_home(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg-config"))

    directory = default_app_settings_directory()

    assert directory == tmp_path / "xdg-config" / "FoliaSeal"


def test_app_settings_store_loads_home_defaults_when_missing(tmp_path: Path) -> None:
    store = AppSettingsStore(
        storage_dir=tmp_path / "config",
        default_home_directory=tmp_path / "home",
    )

    settings = store.load_settings()

    assert settings == AppSettings.default(home_directory=tmp_path / "home")


def test_app_settings_store_saves_and_reloads_human_readable_json(
    tmp_path: Path,
) -> None:
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    settings = AppSettings(
        schema_version=1,
        default_output_directory=str(tmp_path / "out"),
        default_open_directory=str(tmp_path / "in"),
        linux_packaging_channel="primary",
        ui={"last_window_layout": "wide"},
    )

    store.save_settings(settings)

    payload_text = store.settings_path.read_text(encoding="utf-8")
    assert store.settings_path.name == APP_SETTINGS_FILENAME
    assert payload_text.startswith("{\n")
    assert '  "default_open_directory": ' in payload_text
    assert '  "default_output_directory": ' in payload_text
    assert payload_text.endswith("\n")
    assert store.load_settings() == settings


def test_app_settings_store_removes_temp_file_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    original_replace = Path.replace

    def fail_settings_replace(path: Path, target: Path) -> Path:
        if path.name == "settings.json.tmp":
            raise OSError("replace failed")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_settings_replace)

    with pytest.raises(OSError, match="replace failed"):
        store.save_settings(AppSettings.default(home_directory=tmp_path / "home"))

    assert not store.settings_path.with_name("settings.json.tmp").exists()


def test_app_settings_store_preserves_original_error_when_cleanup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    original_replace = Path.replace
    original_unlink = Path.unlink

    def fail_settings_replace(path: Path, target: Path) -> Path:
        if path.name == "settings.json.tmp":
            raise OSError("replace failed")
        return original_replace(path, target)

    def fail_settings_unlink(path: Path) -> None:
        if path.name == "settings.json.tmp":
            raise OSError("cleanup failed")
        original_unlink(path)

    monkeypatch.setattr(Path, "replace", fail_settings_replace)
    monkeypatch.setattr(Path, "unlink", fail_settings_unlink)

    with pytest.raises(OSError, match="replace failed"):
        store.save_settings(AppSettings.default(home_directory=tmp_path / "home"))


def test_app_settings_store_loads_home_defaults_when_blank(tmp_path: Path) -> None:
    store = AppSettingsStore(
        storage_dir=tmp_path / "config",
        default_home_directory=tmp_path / "home",
    )
    store.settings_path.parent.mkdir(parents=True)
    store.settings_path.write_text("\n", encoding="utf-8")

    settings = store.load_settings()

    assert settings == AppSettings.default(home_directory=tmp_path / "home")


def test_app_settings_store_rejects_invalid_json(tmp_path: Path) -> None:
    store = AppSettingsStore(storage_dir=tmp_path / "config")
    store.settings_path.parent.mkdir(parents=True)
    store.settings_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ConfigValidationError, match="not valid JSON"):
        store.load_settings()
