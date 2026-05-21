# Bundle visible-signature fonts in PyInstaller

This ExecPlan is a living document. The sections `Progress`, `Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective` must be kept up to date as work proceeds.

This plan follows the requirements in `.agents/skills/write-execplan/PLANS.md`. It is self-contained so a contributor can restart this packaging slice from only this file and the repository working tree.

## Purpose / Big Picture

FoliaSeal lets users choose bundled fonts for visible PDF signatures. Normal Python installs include those font files through `pyproject.toml`, but the PyInstaller one-dir bundle currently lists no data files, so the packaged application can omit the fonts needed for preview and signing. After this change, the PyInstaller spec will collect every `src/foliaseal/resources/fonts/*.ttf` file into the packaged `foliaseal/resources/fonts` directory, and a unit test will fail if a future font is added without being included in the bundle asset list.

This slice does not build the final desktop application or add a GUI launcher. It only fixes the concrete bundled-font asset gap and aligns the packaging helper architecture with the code.

## Child ExecPlan Dependencies

- [x] Explorer audit of packaging drift completed. The audit found that `foliaseal.spec` has `datas=[]`, `pyproject.toml` includes the font package data for normal installs, and `docs/ARCHITECTURE.md` references PyInstaller helper code that did not yet exist.
- [x] Documentation update worker reviewed the completed packaging helper and updated `docs/ARCHITECTURE.md` and `docs/SPEC.md` to reflect the tested runtime-asset helper and the still-open GUI launcher packaging work.
- [x] Commit worker created the required git commit after code, tests, compliance review, and documentation updates were complete.

## Progress

- [x] (2026-05-20T23:30:02Z) Selected the packaging font-asset slice as the smaller high-leverage #3 task, leaving the larger viewer review/signature-inspection #2 task for a later ExecPlan.
- [x] (2026-05-20T23:30:02Z) Reviewed `foliaseal.spec`, `pyproject.toml`, bundled font files, and current font registry tests.
- [x] (2026-05-20T23:31:57Z) Added `foliaseal.build.pyinstaller_support.collect_runtime_assets()` to return PyInstaller data-file tuples for bundled font runtime assets.
- [x] (2026-05-20T23:31:57Z) Wired `foliaseal.spec` to use the helper instead of an empty `datas` list.
- [x] (2026-05-20T23:31:57Z) Added unit tests proving every bundled `.ttf` font is included in the helper output with the expected destination directory.
- [x] (2026-05-20T23:31:57Z) Ran focused validation: `pytest tests/unit/test_pyinstaller_support.py tests/unit/test_signature_font_registry.py` passed with 6 tests, and `ruff check foliaseal.spec src/foliaseal/build tests/unit/test_pyinstaller_support.py` passed.
- [x] (2026-05-20T23:35:00Z) Completed compliance review with multiple `explorer-light` reviewers. The initial review found one blocker: `src/foliaseal/build/` was hidden by the broad `build/` ignore rule, and the tests did not yet guard `foliaseal.spec` wiring.
- [x] (2026-05-20T23:35:00Z) Spawned a `worker-light` documentation updater, which aligned `docs/ARCHITECTURE.md` and `docs/SPEC.md` with the packaging slice and confirmed those docs no longer overstated helper usage.
- [x] (2026-05-21T00:00:00Z) Removed the `build/` ignore conflict by unignoring `src/foliaseal/build/`, so the helper package is visible to normal git workflows.
- [x] (2026-05-21T00:00:00Z) Added a spec-level AST regression test that proves `foliaseal.spec` imports `collect_runtime_assets()` and wires `runtime_assets` into `Analysis(datas=...)`.
- [x] (2026-05-21T00:00:00Z) Re-ran focused validation after the compliance-fix patch: `pytest tests/unit/test_pyinstaller_support.py tests/unit/test_signature_font_registry.py` passed with 7 tests, `ruff check foliaseal.spec src/foliaseal/build tests/unit/test_pyinstaller_support.py` passed, and `git diff --check` passed.
- [x] Spawned the worker-light commit worker after the slice was complete.
- [x] (2026-05-21T09:55:09Z) Created the required git commit for the slice after code, tests, compliance review, and documentation updates were complete.

## Surprises & Discoveries

- Observation: The normal Python packaging path already declares `foliaseal = ["resources/fonts/*.ttf"]` in `pyproject.toml`, so the gap is specific to PyInstaller data collection.
  Evidence: `pyproject.toml` contains `[tool.setuptools.package-data]` with the font glob, while `foliaseal.spec` passes `datas=[]` to `Analysis`.

- Observation: Ruff treats PyInstaller spec globals such as `Analysis`, `PYZ`, `EXE`, and `COLLECT` as undefined because PyInstaller injects them when executing the spec.
  Evidence: The first `ruff check foliaseal.spec src/foliaseal/build tests/unit/test_pyinstaller_support.py` run reported `F821 Undefined name` for those PyInstaller globals. The final spec keeps narrow `# noqa: F821` annotations only on those lines and passes lint.

- Observation: The broad `.gitignore` rule `build/` also matches `src/foliaseal/build/`, so the new helper package existed locally while remaining invisible to ordinary git add/commit flows.
  Evidence: Compliance reviewers and `git status --ignored` reported `src/foliaseal/build/` as ignored even though `foliaseal.spec` imports `foliaseal.build.pyinstaller_support`.

## Decision Log

- Decision: Implement the missing PyInstaller helper instead of deleting architecture references to that helper.
  Rationale: `docs/ARCHITECTURE.md` already describes a helper responsible for runtime assets, and a helper gives the project a simple test seam for bundle contents without running a full PyInstaller build.
  Date/Author: 2026-05-20 / Codex

- Decision: Keep this slice limited to font asset collection, not GUI launcher packaging.
  Rationale: The explorer audit found a larger V1 packaging gap around the packaged desktop app launcher, but bundled font omission is independently testable and small enough for a safe dev-loop slice.
  Date/Author: 2026-05-20 / Codex

- Decision: Fix the ignore rule in place instead of moving the helper to a different namespace.
  Rationale: `docs/ARCHITECTURE.md` already names `src/foliaseal/build/pyinstaller_support.py`, the helper path is conceptually correct for packaging support, and a narrow `.gitignore` exception resolves the repository-visibility bug with less churn.
  Date/Author: 2026-05-21 / Codex

## Outcomes & Retrospective

Implementation, focused validation, compliance review, documentation review, and the compliance-fix patch are complete. The required git commit has been created, and the slice is now closed.

## Context and Orientation

The bundled font assets live in `src/foliaseal/resources/fonts/`. The application code resolves those fonts through `src/foliaseal/application/signature_font_registry.py`; the preview and signing backend depend on those files being present at runtime.

`pyproject.toml` controls normal editable and wheel installs. It already includes `resources/fonts/*.ttf` as package data for the `foliaseal` package. PyInstaller is different: it builds a standalone one-dir bundle from `foliaseal.spec`, and the `Analysis(..., datas=...)` argument must explicitly list non-Python files to copy into the bundle. A PyInstaller data-file tuple is a pair of strings: the source file path on disk and the destination directory inside the bundle.

`foliaseal.spec` is the project’s PyInstaller one-dir spec. It currently collects Python submodules with `collect_submodules("foliaseal")` and sets `datas=[]`, so no bundled font files are copied.

The new helper should live at `src/foliaseal/build/pyinstaller_support.py`. The `build` package is a packaging-support namespace, not the build output directory. It will expose a small `collect_runtime_assets()` function that returns source/destination tuples for PyInstaller. Tests should live at `tests/unit/test_pyinstaller_support.py`.

## Plan of Work

First, create `src/foliaseal/build/__init__.py` and `src/foliaseal/build/pyinstaller_support.py`. The helper will locate the repository root from its own file location unless a `project_root` argument is supplied by a test. It will find all `*.ttf` files under `src/foliaseal/resources/fonts`, sort them for deterministic output, and return tuples in the form `(absolute_source_path, "foliaseal/resources/fonts")`.

Second, modify `foliaseal.spec` so it can import the helper from the source tree while the spec is executed from the repository root. Add the `src` path to `sys.path` if needed, import `collect_runtime_assets`, call it once, and pass the resulting list to `Analysis(..., datas=runtime_assets, ...)`.

Third, add tests in `tests/unit/test_pyinstaller_support.py`. One test should compare the set of collected source filenames to the actual set of font filenames from `bundled_font_root()`. Another test should assert every collected destination is exactly `foliaseal/resources/fonts` so PyInstaller preserves the package-resource layout expected by runtime code.

Fourth, run focused tests with `pytest tests/unit/test_pyinstaller_support.py tests/unit/test_signature_font_registry.py`. If available and fast, run `ruff check foliaseal.spec src/foliaseal/build tests/unit/test_pyinstaller_support.py`.

## Concrete Steps

Run all commands from `/home/daekar/FoliaSeal`.

Inspect the current packaging files:

    sed -n '1,220p' foliaseal.spec
    sed -n '1,80p' pyproject.toml
    find src/foliaseal/resources/fonts -maxdepth 1 -type f -name '*.ttf' -printf '%f\n' | sort

After editing, run:

    pytest tests/unit/test_pyinstaller_support.py tests/unit/test_signature_font_registry.py

Expected outcome: all tests pass, including the new helper tests.

Observed on 2026-05-20T23:31:57Z:

    collected 6 items
    tests/unit/test_pyinstaller_support.py ..                                [ 33%]
    tests/unit/test_signature_font_registry.py ....                          [100%]
    6 passed in 0.23s

Then run:

    ruff check foliaseal.spec src/foliaseal/build tests/unit/test_pyinstaller_support.py

Expected outcome: ruff reports no issues. If `ruff` is unavailable, record that validation gap in this plan.

Observed on 2026-05-20T23:31:57Z:

    All checks passed!

Revision note 2026-05-20T23:31:57Z: Updated the plan after implementing and validating the helper/spec/test change so the living document reflects the current state and remaining compliance/documentation/commit steps.

Revision note 2026-05-21: Updated the plan after compliance review discovered the ignored helper path and missing spec-wiring regression coverage. The plan now records the docs update completion and the narrow remediation steps required to finish the slice cleanly.

Revision note 2026-05-21 completion pass: Updated the plan after the remediation patch landed and validation passed so the only remaining open item is commit creation.

## Validation and Acceptance

Acceptance for this slice is not a built installer; it is a deterministic packaging input that can be validated without the cost and variability of a full PyInstaller run.

The new unit test `test_collect_runtime_assets_includes_every_bundled_font` must fail before the helper/spec change because there is no helper collecting fonts, and pass after the change. The test must prove that every current file under `src/foliaseal/resources/fonts/*.ttf` is represented in the helper output.

The new unit test `test_collect_runtime_assets_preserves_package_font_destination` must prove that the destination directory is `foliaseal/resources/fonts`, matching the package-resource path that runtime code expects.

Focused validation passes when:

    pytest tests/unit/test_pyinstaller_support.py tests/unit/test_signature_font_registry.py

reports all selected tests passing, and:

    ruff check foliaseal.spec src/foliaseal/build tests/unit/test_pyinstaller_support.py

reports no lint failures.

## Idempotence and Recovery

The helper is read-only and deterministic, so rerunning it or its tests is safe. Re-running PyInstaller after this change should overwrite normal PyInstaller build output in the usual project build directories, but this plan does not require running PyInstaller.

If a test fails because a font file was renamed or added, update the expected behavior by fixing the helper to include the actual files on disk rather than hard-coding filenames. If a PyInstaller spec import fails, verify that `foliaseal.spec` inserts the repository `src` directory into `sys.path` before importing `foliaseal.build.pyinstaller_support`.

## Artifacts and Notes

Current packaging evidence before implementation:

    foliaseal.spec: datas=[]
    pyproject.toml: foliaseal = ["resources/fonts/*.ttf"]
    bundled fonts: Dancing_Script_Regular.ttf, DejaVuSansMono-Bold.ttf, DejaVuSansMono-BoldOblique.ttf, DejaVuSansMono-Oblique.ttf, DejaVuSansMono.ttf, NotoSans-Bold.ttf, NotoSans-BoldItalic.ttf, NotoSans-Italic.ttf, NotoSans-Regular.ttf, NotoSerif-Bold.ttf, NotoSerif-BoldItalic.ttf, NotoSerif-Italic.ttf, NotoSerif-Regular.ttf, NotoSerifDisplay-Bold.ttf, NotoSerifDisplay-BoldItalic.ttf, NotoSerifDisplay-Italic.ttf, NotoSerifDisplay-Regular.ttf, Segoe_Script_Bold.ttf

## Interfaces and Dependencies

Create `src/foliaseal/build/pyinstaller_support.py` with this public function:

    def collect_runtime_assets(project_root: Path | None = None) -> list[tuple[str, str]]:
        ...

The optional `project_root` exists for tests and future build tooling. When omitted, the helper resolves the repository root from its own source path. The function returns PyInstaller-compatible data tuples. No PyInstaller import is needed inside the helper.

Update `foliaseal.spec` to import and use `collect_runtime_assets()`. The spec may continue using `PyInstaller.utils.hooks.collect_submodules` for hidden imports.
