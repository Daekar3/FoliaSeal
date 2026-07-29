#!/usr/bin/env python3
"""Exercise a built FoliaSeal .deb without importing the checkout or virtualenv."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path


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


def _gui_startup(wrapper: Path, pdf: Path, *, cwd: Path, env: dict[str, str]) -> dict[str, object]:
    process = subprocess.Popen(
        [str(wrapper), "gui", "--pdf-path", str(pdf)],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        time.sleep(3.0)
        returncode = process.poll()
        if returncode is not None:
            stdout, stderr = process.communicate(timeout=5)
            raise RuntimeError(
                f"packaged GUI exited during startup (code={returncode}): {stderr or stdout}"
            )
        return {"started": True, "pid": process.pid}
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def audit(package: Path, artifacts_dir: Path) -> dict[str, object]:
    package = package.resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="foliaseal-deb-audit-") as temp_name:
        root = Path(temp_name)
        extract_root = root / "extracted"
        _run(
            ["dpkg-deb", "--extract", str(package), str(extract_root)],
            cwd=root,
            env=os.environ.copy(),
        )
        wrapper = extract_root / "usr/bin/foliaseal"
        executable = extract_root / "usr/lib/foliaseal/foliaseal"
        if not wrapper.is_file() or not executable.is_file():
            raise RuntimeError("package payload is missing the installed wrapper or executable")

        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env["HOME"] = str(root / "home")
        env["XDG_CONFIG_HOME"] = str(root / "config")
        env["XDG_DATA_HOME"] = str(root / "data")
        env["XDG_CACHE_HOME"] = str(root / "cache")
        env["QT_QPA_PLATFORM"] = "offscreen"
        (root / "home").mkdir()
        (root / "config").mkdir()
        (root / "data").mkdir()
        (root / "cache").mkdir()
        fixture = root / "audit.pdf"
        _fixture_pdf(fixture)
        help_result = _run([str(wrapper), "--help"], cwd=root, env=env)
        gui_result = _gui_startup(wrapper, fixture, cwd=root, env=env)

        evidence_root = root / "package-evidence"
        matrix_result = _run(
            [
                str(wrapper),
                "phase3-signing-acceptance-evidence",
                "--artifacts-root",
                str(evidence_root),
            ],
            cwd=root,
            env=env,
            timeout=240.0,
        )
        summary_path = evidence_root / "artifacts/phase3_signed_acceptance_evidence_summary.md"
        summaries = sorted(evidence_root.glob("**/summary.json"))
        report = {
            "status": "passed",
            "package": str(package),
            "extracted_root": str(extract_root),
            "wrapper": str(wrapper),
            "executable": str(executable),
            "executable_under_extracted_usr": str(executable).startswith(str(extract_root / "usr")),
            "help_contains_usage": "usage:" in help_result.stdout.lower(),
            "gui_startup": gui_result,
            "signing_evidence_command": " ".join(matrix_result.args),
            "signing_evidence_summary": str(summary_path) if summary_path.exists() else None,
            "signing_summary_json_count": len(summaries),
            "signing_evidence_stdout_tail": matrix_result.stdout[-1000:],
        }
        (artifacts_dir / "audit.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.package, args.artifacts_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
