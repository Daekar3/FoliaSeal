from pathlib import Path

import pytest

from foliaseal.__main__ import main
from foliaseal.application.help_catalog import HelpCatalog


def test_help_list_and_markdown_use_the_canonical_catalog(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["help", "--list"]) == 0
    listed = capsys.readouterr().out
    assert "getting-started\tGetting started" in listed
    assert "signing-basics\tSigning basics" in listed

    assert main(["help", "signing-basics", "--format", "markdown"]) == 0
    assert capsys.readouterr().out == HelpCatalog.default().markdown("signing-basics")


def test_help_path_prints_the_packaged_markdown_path(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["help", "getting-started", "--path"]) == 0

    path = Path(capsys.readouterr().out.strip())
    assert path.name == "getting-started.md"
    assert path.read_text(encoding="utf-8").startswith("# Getting started")


def test_help_unknown_topic_is_a_parser_error(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(["help", "missing"])

    assert error.value.code == 2
    assert "Unknown help topic: missing" in capsys.readouterr().err
