# Implement the offline packaged Help path

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_product_support_and_release_execplan.md` and the
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md` UI compliance corpus.

## Purpose / Big Picture

After this slice, a new user can discover and read FoliaSeal help without a network connection. The
same canonical Markdown topics are available from `foliaseal help --list`,
`foliaseal help <topic> --format markdown`, and `foliaseal help <topic> --path`, and from a modeless
in-app Help window. The window searches topic titles and keywords, follows local related-topic links,
supports Back and Forward, and opens from the Help command or F1. A keyboard user can reach the
window, search field, topic list, and content without relying on a pointer. A package or installed
PyInstaller bundle contains the exact same topic files; no JavaScript, remote URL, telemetry, or
private document data is involved.

The behavior is visible immediately from a checkout with the CLI commands above and, when Qt is
available, by launching `foliaseal gui`, choosing Help, searching for “certificate”, and opening a
topic. This plan deliberately stops at the first complete Help path. Diagnostics/log-folder views,
full release packaging acceptance, rail persistence, and unrelated V2 support features remain owned
by the release plan.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are the governing contracts; UI_SPEC sections 13, 14, and
  acceptance scenario 10 define offline Help, stable topic IDs, keyboard access, and no remote assets.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` owns the broader release tranche and
  explicitly identifies local Markdown Help as its second milestone.
- [x] `docs/ExecPlans/ui_command_model_shortcuts_execplan.md` provides the typed top-level command
  registry and native focus/shortcut precedence.
- [x] `docs/ExecPlans/ui_launch_no_document_execplan.md` and the existing AppFrame Qt binding seam
  provide a modeless top-level surface that can open without a document.

## Progress

- [x] (2026-08-10) Fresh explorer audit selected Help as the strongest remaining product-facing
  dependency-ready gap; it found no existing topic corpus, CLI command, Help command definition, or
  in-app viewer.
- [x] (2026-08-10) Created this focused child plan and recorded the exact UI_SPEC contract, resource
  boundary, CLI shape, Qt surface, packaging path, and acceptance evidence.
- [x] (2026-08-10) Added the canonical Markdown topic corpus and machine-readable index with stable
  IDs, keywords, related-topic links, safe topic links, and no network/JavaScript content.
- [x] (2026-08-10) Added the Qt-free catalog/service and CLI `help` command with list, Markdown, and
  path output; focused catalog/CLI validation is green (`6 passed`).
- [x] (2026-08-10) Added the typed Help command, F1 routing, and modeless searchable Qt viewer with
  local Back/Forward, local-link rejection, and keyboard-accessible controls; offscreen acceptance is
  green (`1 passed`) and AppFrame regressions are green (`61 passed`).
- [x] (2026-08-10) Added setuptools/PyInstaller resource parity declarations and focused asset tests
  (`10 passed` across catalog, CLI, and resource checks).
- [x] (2026-08-10) Built a disposable wheel and inspected its contents; all five Markdown topics,
  `index.json`, and the resource package initializer were present, then the temporary wheel root was
  removed.
- [x] (2026-08-10) Built a disposable PyInstaller one-dir bundle, verified all five Markdown topics
  and `index.json` under the bundled resource root, ran the bundled `help --list` and `--path` commands,
  and removed the generated `build/foliaseal` and `dist/foliaseal` directories after a clean process check.
- [x] (2026-08-10) Reconciled `docs/ARCHITECTURE.md` and the parent/release/command plans; focused
  Help/AppFrame/resource validation is green (`72 passed`), the repository full suite is green
  (`1465 passed, 20 skipped, 1 warning`), and the slice was committed.
- [x] (2026-08-10) Completed the bounded offline/resource audit: CLI list/path output is stable,
  the Help resource/viewer scan is clean, and setuptools/PyInstaller declarations include the same
  six packaged files. Broader diagnostics, final release packaging, and display-backed acceptance
  remain open in the parent release plan.

## Surprises & Discoveries

- Observation: the current CLI parser only exposes evidence, harness, and `gui` subcommands, and the
  command registry contains File, Edit, View, Signing, and Settings definitions but no Help entry.
  Evidence: `src/foliaseal/__main__.py` and `src/foliaseal/presentation/qt/app_frame_command_model.py`.
- Observation: setuptools currently packages only font data and PyInstaller receives only font files
  from `collect_runtime_assets()`.
  Evidence: `pyproject.toml` and `src/foliaseal/build/pyinstaller_support.py`.
- Observation: `QTextBrowser` is not currently in `QtAppFrameBindings`, but the bindings already carry
  dynamic Qt widget types and the AppFrame already owns modeless windows such as the Library and
  Document Signatures dialog. The Help viewer can follow that public binding pattern without adding a
  second application window manager.
  Evidence: `src/foliaseal/presentation/qt/app_frame.py` and existing modeless integration tests.
- Observation: display-backed GUI launches remain environment-limited by the isolated
  `SingleInstanceUnavailable`/xcb condition. CLI, offscreen widget, resource, and package-content
  evidence must therefore be first-class and must not be confused with a manual display walkthrough.

## Decision Log

- Decision: store Help topics as packaged Markdown resources under `src/foliaseal/resources/help/`
  with one `index.json` catalog.
  Rationale: `importlib.resources` gives checkout, wheel, and PyInstaller code one resource boundary;
  a machine-readable index makes stable IDs, titles, keywords, and related links inspectable without
  parsing arbitrary Markdown. A separate database or user-writable cache would violate offline,
  deterministic, and privacy requirements.
  Date/Author: 2026-08-10 / Codex.
- Decision: expose one application `HelpCatalog`/`HelpTopic` service to both CLI and Qt.
  Rationale: the CLI and viewer must prove parity from the same bytes, and Qt must not read repository
  paths or reach into private frame state. The service validates topic IDs and related links once and
  returns immutable records containing Markdown text and a resource path when available.
  Date/Author: 2026-08-10 / Codex.
- Decision: use Qt's local Markdown document renderer (`QTextBrowser`/`QTextDocument`) with external
  links disabled and a `help:` topic-link scheme for related topics.
  Rationale: this avoids a new Markdown/HTML/JavaScript dependency, keeps rendering local, and lets
  the viewer reject every non-topic URL. Markdown is the canonical artifact; generated HTML is only
  an in-memory presentation.
  Date/Author: 2026-08-10 / Codex.
- Decision: F1 opens the catalog's `getting-started` topic when no more specific context is available;
  the AppFrame may pass a stable context topic, but it must never infer a topic from PDF contents or
  selected text.
  Rationale: F1 must always do something useful and must not leak document data into help selection.
  A deterministic fallback is testable and leaves contextual mapping extensible.
  Date/Author: 2026-08-10 / Codex.
- Decision: `--path` prints the packaged Markdown file path only when the resource has a filesystem
  representation; otherwise it writes a clear unsupported-path error and returns non-zero, while
  `--format markdown` remains valid for zipped/imported resources.
  Rationale: a path is useful for editors and audits but is not guaranteed by Python resource loaders.
  The normal wheel/PyInstaller/development installs provide a real path and must be tested.
  Date/Author: 2026-08-10 / Codex.
- Decision: keep topic content short, task-oriented, and accurate to current V1 behavior. Initial
  topics are `getting-started`, `signing-basics`, `certificates`, `privacy`, and `troubleshooting`.
  Rationale: these cover onboarding, the primary signing story, credential safety, offline/privacy
  expectations, and recoverable failures without pretending that unfinished release diagnostics exist.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

Completed 2026-08-10. `foliaseal help --list` emits the five index-ordered topics (`getting-started`,
`signing-basics`, `certificates`, `privacy`, `troubleshooting`); `help signing-basics --path` resolves
`src/foliaseal/resources/help/signing-basics.md`; focused catalog/CLI/viewer/AppFrame/PyInstaller
tests pass (`72 passed`); the full suite passes (`1465 passed, 20 skipped, 1 warning`);
and the no-remote-assets scan over Help resources/viewer is clean. Offscreen viewer coverage proves
search/navigation/F1 and modeless reuse. Display-backed GUI, diagnostics/log-folder views, and the
full installed-package/release acceptance matrix remain open in `ui_product_support_and_release_execplan.md`.

## Context and Orientation

FoliaSeal is a Python 3.11+ Linux PDF-signing application. The command-line entry point is
`src/foliaseal/__main__.py`; it uses `argparse` and dispatches the offline `help`, evidence/harness,
and `gui` commands. The top-level Qt frame in `src/foliaseal/presentation/qt/app_frame.py` creates
File, Edit, View, Signing, Settings, and Help menus from the typed definitions in
`src/foliaseal/presentation/qt/app_frame_command_model.py`. `QtAppFrameBindings` dynamically imports
PySide6 types so unit tests can use fakes. Modeless UI surfaces already exist for the reusable-object
Library and document-signature review, and their tests prove reuse and cleanup behavior.

The resource package is `src/foliaseal/resources/`. Font files are already included through
`pyproject.toml` package data and `src/foliaseal/build/pyinstaller_support.py`. The Debian builder
copies the PyInstaller bundle, so adding Help data to both resource declarations makes it available
to an installed `.deb` without adding a second copy. “Local-only” means the viewer accepts only
`help:<stable-topic-id>` links; it must not fetch HTTP(S), `file:` URLs, scripts, images, or remote
stylesheets. “Modeless” means the Help window does not block the main frame; users can switch between
Help and the document.

## Change Slice

Primary change class: behavior change with the minimum package/resource declarations and governing
documentation needed to make the behavior demonstrably installed and offline. Allowed changes are
the new Help resources/service, CLI parser/dispatch, command model/AppFrame bindings and viewer,
PyInstaller/setuptools resource declarations, focused tests, architecture/ExecPlan status, and
ignored temporary evidence. Do not mix diagnostics/log-folder implementation, rail/Library geometry,
full packaging/release matrix work, new certificate/signing behavior, broad Markdown dependencies,
or acceptance-named product surfaces into this commit.

## Plan of Work

First create `src/foliaseal/resources/help/index.json` and the five Markdown topics named in the
Decision Log. Each index entry must contain `id`, `title`, `keywords`, `related`, and `filename`; IDs
are lowercase kebab-case, unique, and match filenames. Topic headings must be structured, links must
use `help:<id>` or ordinary fragment links, and prose must describe only checked-in/current commands
and workflows. Add a Qt-free catalog module, preferably
`src/foliaseal/application/help_catalog.py`, that loads the index and Markdown through an injected
resource reader or `importlib.resources`, validates the schema and links, exposes `list_topics()`,
`topic(topic_id)`, `markdown(topic_id)`, and a safe path context, and raises a stable `HelpTopicError`
for unknown or malformed topics.

Next add the CLI surface in `src/foliaseal/__main__.py`. The `help` subparser accepts `--list`, an
optional topic ID, `--format markdown` (the default when a topic is supplied), and `--path`. `--list`
prints one stable line per topic in index order with ID and title. A topic prints exactly its canonical
Markdown to stdout; `--path` prints only the resolved path. Missing topics, conflicting `--list`/
topic, and unsupported path resources produce argparse-style errors and non-zero exit codes. Keep the
existing phase2/acceptance command behavior unchanged, and add direct unit tests for parser/dispatch,
unknown IDs, list order, Markdown exactness, and path output.

Then add `HELP` to `AppFrameCommandId` and a `HELP_COMMAND_DEFINITIONS` tuple in
`app_frame_command_model.py` with menu `Help`, text `Help`, shortcut `F1`, stable object name, and an
accessible name. Include it in `ALL_COMMAND_DEFINITIONS`. Extend `QtAppFrameBindings` only with the
Qt types needed by the viewer (`QTextBrowser`, `QListWidget`, `QLineEdit`, layouts, and optionally
`QSplitter` already present); preserve fake-binding compatibility by making new fields optional where
the existing tests require it.

Create `src/foliaseal/presentation/qt/help_viewer.py` as a small modeless dialog. It receives a
`HelpCatalog`, parent, and optional context topic. It owns a search `QLineEdit`, a keyboard-label
`QListWidget`, a read-only `QTextBrowser`, Back/Forward buttons or actions, and a Close button. Search
filters title/keywords/ID case-insensitively and live; selecting a topic loads canonical Markdown,
records a bounded history entry, and updates an accessible title/status. Related `help:` links load
topics in the same viewer. Disable external links and reject every URL whose scheme is not `help`;
do not use JavaScript or remote resources. `show()`/`raise_()`/`activateWindow()` make repeated Help
invocations reuse one dialog; `closeEvent` clears only the frame-owned reference and does not persist
documents or Help state.

Wire `FoliaSealAppFrame.show_help(topic_id=None)` to reuse/create the viewer and add the Help menu
action in `_install_menus()`. Use the existing command registry/action helper, and ensure F1 works with
no document, an open document, and a focused native editor. A small `HelpContextResolver` may map only
stable AppFrame-owned states (for example settings dialog to `certificates`); otherwise use
`getting-started`. Do not inspect PDF text, credentials, or private child widgets to choose a topic.
Expose the viewer through a narrow test property if needed, following the existing modeless-surface
pattern rather than adding a compatibility export.

Finally update package data in `pyproject.toml` and `collect_runtime_assets()` so editable installs,
wheels, PyInstaller one-dir bundles, and the Debian wrapper all carry `resources/help/index.json` and
the Markdown files. Add tests that inspect the built/collected asset list and import the catalog from
the installed resource boundary; do not commit generated `dist/`, package, or build artifacts.

## Milestones

Milestone 1 is the resource/catalog tracer bullet. Add one topic and the index, write a public catalog
test, and prove the exact Markdown is readable from the checkout resource boundary. Add the remaining
four topics only after the first test is green; validate index order and related-link targets.

Milestone 2 is the CLI path. Add `help --list`, topic Markdown, and path output with red/green tests;
prove an unknown topic fails without a traceback and existing commands retain their behavior.

Milestone 3 is the modeless Qt path. Add the Help command/F1 action, viewer search, local related links,
Back/Forward, close/reopen reuse, focus/accessibility names, and offscreen integration tests. Prove
Help works with no PDF as well as with a PDF and native editor focus.

Milestone 4 is resource/package parity and release reconciliation. Add setuptools/PyInstaller data
tests, run the no-remote-assets audit, reconcile architecture and release/parent/command plans, run
full validation, perform the bounded GUI/process cleanup, and commit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` using `.venv` and do not fall back to system Python or system Qt.
Use the TDD tracer-bullet loop: add one behavior test, observe RED, implement the smallest public
path, observe GREEN, then continue to the next behavior.

    .venv/bin/pytest -q tests/unit/test_help_catalog.py
    .venv/bin/python -m foliaseal help --list
    .venv/bin/python -m foliaseal help signing-basics --format markdown
    .venv/bin/python -m foliaseal help signing-basics --path
    .venv/bin/pytest -q tests/unit/test_cli_help.py tests/unit/test_help_catalog.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/integration/test_help_viewer.py tests/unit/test_qt_app_frame.py
    .venv/bin/pytest -q tests/unit/test_pyinstaller_support.py
    .venv/bin/ruff check src tests
    git diff --check
    rg -n -e 'https?://|<script|javascript:|QWebEngine|QNetworkAccessManager' src/foliaseal/resources/help src/foliaseal/presentation/qt/help_viewer.py tests
    .venv/bin/pytest -q

For a bounded GUI lifecycle check, isolate configuration and always clean it:

    audit_root=$(mktemp -d /tmp/foliaseal-help-audit-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui >"$audit_root/gui.log" 2>&1
    gui_rc=$?
    set -e
    printf 'gui_rc=%s\n' "$gui_rc"
    sed -n '1,80p' "$audit_root/gui.log"
    if ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg '; then echo process-check=FOUND; else echo process-check=clean; fi
    rm -rf "$audit_root"
    test ! -e "$audit_root"

The known display-limited environment may return `gui_rc=1` with `SingleInstanceUnavailable`; this is
acceptable only when the log proves the isolated endpoint failure, the process check is clean, and the
temporary root is removed. Offscreen Help-window tests and CLI/package parity remain mandatory.

## Validation and Acceptance

The CLI acceptance path prints the five topics in stable index order, prints byte-for-byte canonical
Markdown for `signing-basics`, and prints an existing packaged path for `--path`. The in-app acceptance
path opens a modeless Help window without a PDF, focuses the search field, filters by `certificate`,
opens the Certificates topic, follows a related local link, navigates Back then Forward, and closes/reopens
the same window. F1 opens `getting-started` from the empty frame and remains usable with a document or
native editor focused. The viewer contains no external links/scripts/network classes, and tab/accessible
names expose search, topic list, content, navigation, and Close.

Tests must cover catalog validation, exact CLI output/errors, public Qt viewer behavior, F1/no-document
and native-focus routing, local-link rejection, search/history, resource declarations, and package
parity. Run the full suite and report any existing warning separately. No FoliaSeal/PySide6/pytest
process or temporary audit directory may remain.

## Idempotence and Recovery

Resource reads are immutable and safe to repeat. If a test creates a temporary package or resource
root, place it under `/tmp/foliaseal-help-audit-*` or pytest's `tmp_path` and remove only that explicit
root after the test. Do not edit user configuration, credentials, PDFs, generated `artifacts/`, or
checked-in build outputs. If Qt fails before the viewer closes, close the owned Help dialog and dispose
the QApplication/window through the fixture before retrying. If a packaged resource cannot provide a
filesystem path, keep `--format markdown` working and record the precise path limitation rather than
copying resources to an untracked cache.

## Artifacts and Notes

Allowed evidence is concise CLI output, test output, optional offscreen screenshots/JSON under ignored
`artifacts/`, and package-content listings under a temporary root. Do not commit generated `.deb`,
PyInstaller `dist/`, credentials, PDFs, clipboard contents, or machine-local absolute paths.

## Interfaces and Dependencies

The final Qt-free interfaces are:

    HelpTopic(id: str, title: str, keywords: tuple[str, ...], related: tuple[str, ...], markdown: str, path: Path | None)
    HelpCatalog.list_topics() -> tuple[HelpTopic, ...]
    HelpCatalog.topic(topic_id: str) -> HelpTopic
    HelpCatalog.markdown(topic_id: str) -> str
    HelpCatalog.topic_path(topic_id: str) -> Path | None

`HelpCatalog` must validate index IDs, filenames, duplicate IDs, missing files, and related-topic
targets once at construction. `HelpTopicError` is the stable user-facing failure type; CLI maps it to
non-zero parser errors without tracebacks. The Qt viewer consumes only `HelpCatalog` and Qt bindings;
it may not import `argparse`, inspect AppFrame private fields, or read repository-relative paths.
`AppFrameCommandId.HELP` and its definition use menu `Help`, text `Help`, shortcut `F1`, and accessible
name `Open FoliaSeal Help`. `FoliaSealAppFrame.show_help(topic_id: str | None = None)` is the public
frame operation and reuses one modeless viewer instance. `collect_runtime_assets()` includes every
Help Markdown/index file in the PyInstaller data tuples, and setuptools package data includes the same
resource directory.

## Evidence Record

Evidence for this completed child is: `foliaseal help --list` emitted the five stable topics; the
`signing-basics` Markdown and `--path` outputs matched the catalog; unknown topics returned argparse
status 2; focused catalog/CLI/PyInstaller/AppFrame/offscreen validation passed (`72 passed`); the
full suite passed (`1465 passed, 20 skipped, 1 warning`); a disposable wheel contained the six Help
resource files and a disposable PyInstaller bundle contained the same files and ran `help --list` and
`help --path`; the source Help/viewer no-remote scan was clean; and the bounded GUI launch returned
`gui_rc=1` with isolated `SingleInstanceUnavailable`, then left no matching process or audit root.
The governing UI_SPEC requirement is sections 13–14 plus acceptance scenario 10; no new SVG is
required because Help is a text/content surface rather than a topology change. The implementation and
plan updates were committed together.

## Revision Notes

Revision note: 2026-08-10 / Codex
Created after a fresh explorer-light audit found Help to be the strongest remaining explicit UI_SPEC
gap and confirmed that the existing release child was too broad to execute as one restartable vertical
slice. This child narrows the first Help milestone to one offline, packaged, CLI-and-modeless-Qt path;
diagnostics, final release packaging, and unrelated deferred UI behavior remain outside its boundary.
Revision note: 2026-08-10 / Codex
Post-pass compliance review tightened the catalog's blocked URL/resource schemes, made Help opening
focus the search field, bounded local history, strengthened empty-frame F1 and native-editor-focus
evidence, and recorded disposable wheel/PyInstaller parity plus the known isolated GUI launch limit.
