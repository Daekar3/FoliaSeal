from foliaseal.build.pyinstaller_support import collect_runtime_assets


def test_collect_runtime_assets_includes_qt_runtime(monkeypatch) -> None:
    monkeypatch.setattr(
        "foliaseal.build.pyinstaller_support.collect_submodules",
        lambda package: ["foliaseal.__main__"] if package == "foliaseal" else [],
    )

    hiddenimports, datas, binaries = collect_runtime_assets()

    assert "foliaseal.__main__" in hiddenimports
    assert "PySide6" in hiddenimports
    assert "shiboken6" in hiddenimports
    assert "PySide6.QtCore" in hiddenimports
    assert "PySide6.QtGui" in hiddenimports
    assert "PySide6.QtWidgets" in hiddenimports
    assert "PySide6.QtPdf" in hiddenimports
    assert datas == []
    assert binaries == []
