from foliaseal.__main__ import _build_parser


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
