import importlib.util
import json
from pathlib import Path

import pytest


def _audit_module():
    script = Path(__file__).resolve().parents[2] / "scripts/deb_package_audit.py"
    spec = importlib.util.spec_from_file_location("foliaseal_deb_package_audit", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_control_fields_preserves_continuation_lines() -> None:
    audit = _audit_module()

    fields = audit.parse_control_fields(
        "Package: foliaseal\n"
        "Depends: poppler-utils\n"
        "Description: one line\n"
        " continuation\n"
    )

    assert fields == {
        "Package": "foliaseal",
        "Depends": "poppler-utils",
        "Description": "one line\ncontinuation",
    }


def test_desktop_entry_fields_extracts_application_contract() -> None:
    audit = _audit_module()

    fields = audit.desktop_entry_fields(
        "[Desktop Entry]\n"
        "Exec=/usr/bin/foliaseal gui\n"
        "Icon=foliaseal\n"
        "Terminal=false\n"
        "[Other]\nIgnored=value\n"
    )

    assert fields == {
        "Exec": "/usr/bin/foliaseal gui",
        "Icon": "foliaseal",
        "Terminal": "false",
    }


def test_help_markdown_validation_rejects_empty_and_remote_or_embedded_content() -> None:
    audit = _audit_module()

    audit.validate_help_markdown("# Local Help\n\nUse the signing workflow.")
    for unsafe in ("", "![remote](https://example.invalid/a.png)", "javascript:alert(1)"):
        with pytest.raises(ValueError):
            audit.validate_help_markdown(unsafe)


@pytest.mark.parametrize(
    "message",
    [
        "SingleInstanceUnavailable: A FoliaSeal owner is active but not accepting requests: /tmp/x",
        "SingleInstanceUnavailable: Unable to claim or reach the FoliaSeal "
        "instance endpoint: /tmp/x",
    ],
)
def test_classify_gui_result_accepts_only_known_isolated_endpoint_limit(message: str) -> None:
    audit = _audit_module()

    result = audit.classify_gui_result(1, message)

    assert result["status"] == "limited"


def test_classify_gui_result_does_not_hide_unrelated_failures() -> None:
    audit = _audit_module()

    result = audit.classify_gui_result(1, "ImportError: missing Qt library")

    assert result["status"] == "failed"
    assert audit.classify_gui_result(None, "", started=True)["status"] == "started"


def test_build_warning_lines_is_bounded_to_warning_records() -> None:
    audit = _audit_module()

    log = "INFO done\nWARNING missing libtiff.so.5\nWARNING optional\n"
    assert audit.build_warning_lines(log) == [
        "WARNING missing libtiff.so.5",
        "WARNING optional",
    ]
    assert audit.build_warning_lines(None) == []


def test_offline_environment_removes_ambient_proxy_hints() -> None:
    audit = _audit_module()

    env = audit.offline_environment(
        {
            "PYTHONPATH": "/checkout/src",
            "HTTPS_PROXY": "http://proxy.invalid",
            "NO_PROXY": "localhost",
            "PATH": "/usr/bin",
        }
    )

    assert "PYTHONPATH" not in env
    assert "HTTPS_PROXY" not in env
    assert env["NO_PROXY"] == "*"
    assert env["no_proxy"] == "*"
    assert env["PATH"] == "/usr/bin"


def test_validate_font_files_rejects_truncated_payload() -> None:
    audit = _audit_module()

    audit.validate_font_files(sorted(audit._REQUIRED_FONT_FILES))
    with pytest.raises(ValueError, match="missing"):
        audit.validate_font_files(sorted(audit._REQUIRED_FONT_FILES)[:-1])


def test_write_report_serializes_one_json_evidence_file(tmp_path: Path) -> None:
    audit = _audit_module()

    report_path = audit.write_report(
        {"status": "passed", "checks": ["help"]}, tmp_path / "evidence"
    )

    assert report_path == tmp_path / "evidence/audit.json"
    assert json.loads(report_path.read_text(encoding="utf-8")) == {
        "checks": ["help"],
        "status": "passed",
    }


@pytest.mark.parametrize("relative_root", ["foliaseal/resources", "_internal/foliaseal/resources"])
def test_runtime_resource_root_supports_pyinstaller_one_dir_layouts(
    tmp_path: Path, relative_root: str
) -> None:
    audit = _audit_module()
    resource_root = tmp_path / relative_root
    (resource_root / "help").mkdir(parents=True)
    (resource_root / "help/index.json").write_text("[]\n", encoding="utf-8")

    assert audit._runtime_resource_root(tmp_path) == resource_root.resolve()
