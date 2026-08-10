from pathlib import Path

from foliaseal.application.support_diagnostics import DiagnosticLogWriter, SupportLocations


def test_locations_follow_xdg_roots(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    locations = SupportLocations.for_environment()
    assert locations.config_dir == tmp_path / "config" / "FoliaSeal"
    assert locations.data_dir == tmp_path / "data" / "FoliaSeal"
    assert locations.logs_dir == tmp_path / "state" / "FoliaSeal" / "logs"


def test_log_writer_redacts_sensitive_values_and_rotates_owned_files(tmp_path: Path) -> None:
    locations = SupportLocations(tmp_path / "config", tmp_path / "data", tmp_path / "logs")
    writer = DiagnosticLogWriter(locations, max_bytes=180, backup_count=2)
    writer.write(
        level="error",
        error_code="TEST",
        stage="support",
        detail="password=hunter2 reason=private selected_text=words location=/private",
    )
    for index in range(4):
        writer.write(level="error", error_code="TEST", stage="support", detail=f"event={index}")

    paths = sorted(locations.logs_dir.glob("foliaseal.log*"))
    assert [path.name for path in paths] == ["foliaseal.log", "foliaseal.log.1", "foliaseal.log.2"]
    combined = "".join(path.read_text(encoding="utf-8") for path in paths)
    for secret in ("hunter2", "private", "words", "/private"):
        assert secret not in combined
    assert "[redacted]" in combined
