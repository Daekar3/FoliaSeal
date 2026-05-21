import ast
from pathlib import Path

from foliaseal.application.signature_font_registry import bundled_font_root
from foliaseal.build.pyinstaller_support import collect_runtime_assets


def test_collect_runtime_assets_includes_every_bundled_font() -> None:
    expected_fonts = {font_path.name for font_path in bundled_font_root().glob("*.ttf")}

    collected_fonts = {
        Path(source).name
        for source, destination in collect_runtime_assets()
        if destination == "foliaseal/resources/fonts"
    }

    assert collected_fonts == expected_fonts


def test_collect_runtime_assets_preserves_package_font_destination() -> None:
    assets = collect_runtime_assets()

    assert assets
    assert {destination for _source, destination in assets} == {"foliaseal/resources/fonts"}


def test_pyinstaller_spec_uses_runtime_assets_helper_for_analysis_datas() -> None:
    spec_path = Path(__file__).resolve().parents[2] / "foliaseal.spec"
    module = ast.parse(spec_path.read_text(encoding="utf-8"), filename=str(spec_path))

    helper_import = next(
        (
            node
            for node in module.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "foliaseal.build.pyinstaller_support"
        ),
        None,
    )
    assert helper_import is not None
    assert any(alias.name == "collect_runtime_assets" for alias in helper_import.names)

    runtime_assets_assignment = next(
        (
            node
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "runtime_assets"
                for target in node.targets
            )
        ),
        None,
    )
    assert runtime_assets_assignment is not None
    assert isinstance(runtime_assets_assignment.value, ast.Call)
    assert isinstance(runtime_assets_assignment.value.func, ast.Name)
    assert runtime_assets_assignment.value.func.id == "collect_runtime_assets"

    analysis_assignment = next(
        (
            node
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "a" for target in node.targets)
        ),
        None,
    )
    assert analysis_assignment is not None
    assert isinstance(analysis_assignment.value, ast.Call)
    assert isinstance(analysis_assignment.value.func, ast.Name)
    assert analysis_assignment.value.func.id == "Analysis"

    datas_keyword = next(
        (keyword for keyword in analysis_assignment.value.keywords if keyword.arg == "datas"),
        None,
    )
    assert datas_keyword is not None
    assert isinstance(datas_keyword.value, ast.Name)
    assert datas_keyword.value.id == "runtime_assets"
