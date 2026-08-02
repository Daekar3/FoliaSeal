from foliaseal.__main__ import _build_parser


def test_gui_parser_accepts_optional_pdf_path() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "gui",
            "--pdf-path",
            "/tmp/example.pdf",
        ]
    )

    assert args.command == "gui"
    assert args.pdf_path == "/tmp/example.pdf"


def test_phase3_harness_parser_accepts_certificate_cli_arguments() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "phase3-signing-harness",
            "--pdf-path",
            "/tmp/example.pdf",
            "--certificate-path",
            "/tmp/example.p12",
            "--passphrase",
            "secret",
        ]
    )

    assert args.command == "phase3-signing-harness"
    assert args.pdf_path == "/tmp/example.pdf"
    assert args.certificate_path == "/tmp/example.p12"
    assert args.passphrase == "secret"


def test_phase3_harness_parser_accepts_artifacts_dir() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "phase3-signing-harness",
            "--pdf-path",
            "/tmp/example.pdf",
            "--certificate-path",
            "/tmp/example.p12",
            "--passphrase",
            "secret",
            "--artifacts-dir",
            "artifacts/phase3_preview_debug",
        ]
    )

    assert args.command == "phase3-signing-harness"
    assert args.artifacts_dir == "artifacts/phase3_preview_debug"


def test_phase3_preview_matrix_parser_accepts_manifest_and_artifacts_dir() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "phase3-signing-preview-matrix",
            "--pdf-path",
            "/tmp/example.pdf",
            "--certificate-path",
            "/tmp/example.p12",
            "--passphrase",
            "secret",
            "--scenario-manifest-path",
            "artifacts/phase3_preview_matrix.json",
            "--artifacts-dir",
            "artifacts/phase3_preview_matrix",
        ]
    )

    assert args.command == "phase3-signing-preview-matrix"
    assert args.scenario_manifest_path == "artifacts/phase3_preview_matrix.json"
    assert args.artifacts_dir == "artifacts/phase3_preview_matrix"


def test_signed_acceptance_evidence_parser_accepts_output_paths() -> None:
    parser = _build_parser()

    args = parser.parse_args(
        [
            "phase3-signing-acceptance-evidence",
            "--artifacts-root",
            "/tmp/foliaseal-evidence",
            "--summary-markdown-path",
            "/tmp/foliaseal-evidence/summary.md",
        ]
    )

    assert args.command == "phase3-signing-acceptance-evidence"
    assert args.artifacts_root == "/tmp/foliaseal-evidence"
    assert args.summary_markdown_path == "/tmp/foliaseal-evidence/summary.md"
