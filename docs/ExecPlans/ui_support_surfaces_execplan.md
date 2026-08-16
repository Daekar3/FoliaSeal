# Complete local support surfaces and diagnostics

This ExecPlan is a living document and must be maintained in accordance with
`.agents/skills/write-execplan/PLANS.md`. It is an AFK child of
`docs/ExecPlans/ui_product_support_and_release_execplan.md` and
`docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md`.

## Purpose / Big Picture

After this slice, a person using FoliaSeal can reach every Help command required by `docs/UI_SPEC.md`:
FoliaSeal Help, Keyboard Shortcuts, Data Locations, Open Diagnostic Logs Folder, and About. The
support commands use local, keyboard-accessible Qt surfaces and never expose private document or
credential data. Product-level diagnostics are written to a bounded per-user log directory with
privacy filtering and simple rotation; the existing evidence/harness diagnostics remain separate.
Application Settings also gains the required Restore defaults action while preserving Save/Cancel
transaction semantics.

The behavior is visible from a checkout by launching the GUI, opening Help, selecting each support
entry, and invoking `Open Diagnostic Logs Folder`; focused offscreen tests prove command metadata,
dialog contents, privacy filtering, path determinism, log rotation, and reset/cancel behavior. This
slice does not claim the final installed-package matrix, screen-reader certification, or broad
acceptance evidence nomenclature retirement.

## Child ExecPlan Dependencies

- [x] `docs/SPEC.md` and `docs/UI_SPEC.md` are frozen governing contracts; UI_SPEC sections 7, 13,
  14, and acceptance scenario 8 define the command, privacy, support, and keyboard requirements.
- [x] `docs/ExecPlans/ui_help_support_execplan.md` provides the canonical offline Help viewer and
  F1 command; this child adds the remaining Help-menu commands without duplicating Help topic bytes.
- [x] `docs/ExecPlans/ui_product_support_and_release_execplan.md` owns the broader release matrix;
  diagnostics and final package acceptance remain outside this child.

## Progress

- [x] (2026-08-10) Fresh explorer audit confirmed that product diagnostics/logging and four required
  Help-menu entries are absent, while existing harness diagnostics are not a safe product contract.
- [x] (2026-08-10) Created this bounded child plan covering local support surfaces, privacy-safe
  rotating logs, Help command metadata, and Settings Restore defaults.
- [x] (2026-08-10) Added the Qt-free support-location and privacy-filtered rotating-log contract.
- [x] (2026-08-10) Added typed command definitions and AppFrame routing for Keyboard Shortcuts, Data Locations,
  Open Diagnostic Logs Folder, and About.
- [x] (2026-08-10) Added accessible local support dialogs and safe folder-launch behavior; preserve one modeless
  instance per support surface and clean references on close.
- [x] (2026-08-10) Added Settings Restore defaults with explicit cancel-safe behavior.
- [x] (2026-08-10) Added focused XDG/privacy/rotation contract tests; `tests/unit/test_support_diagnostics.py`
  passes (2 tests), and the reconciled AppFrame/support set passes. The five-entry Help surface is
  now reflected in the typed command and real-Qt acceptance tests.
- [x] (2026-08-10) Committed the support slice as `4aad84ad8`; the full suite at that point was
  `1468 passed, 20 skipped, 1 warning`, with Ruff, pip check, and diff checks clean.
- [ ] Final installed-package, display-backed accessibility, and release-matrix evidence remain in
  the owning product-support/release plan.

## Surprises & Discoveries

- Observation: the repository has render/evidence diagnostic read models but no general product log
  writer or support-folder contract. Evidence: `src/foliaseal/presentation/qt/signing_workspace_diagnostics.py`
  and `src/foliaseal/presentation/qt/phase2_harness.py` are harness/runtime diagnostics and no
  logging package or file handler exists.
- Observation: `AppSettingsDialog` already has atomic Save/Cancel and Browse controls, but no
  Restore defaults operation. Evidence: `src/foliaseal/presentation/qt/app_frame.py`.
- Observation: `QtAppFrameBindings` already provides `QTextEdit`, `QDesktopServices`, and `QUrl`,
  so support dialogs and local folder opening can use existing dynamic Qt boundaries.

## Decision Log

- Decision: keep product diagnostics in a new Qt-free application/infra contract rather than
  exposing `SigningWorkspaceDiagnosticsPort` or any Acceptance harness type. Rationale: the product
  contract must be privacy-safe, bounded, and usable without an active document; harness state may
  contain richer evidence and has different ownership.
  Date/Author: 2026-08-10 / Codex.
- Decision: use `${XDG_STATE_HOME:-~/.local/state}/FoliaSeal/logs` for logs, `${XDG_CONFIG_HOME:-~/.config}/FoliaSeal`
  for configuration, and `${XDG_DATA_HOME:-~/.local/share}/FoliaSeal` for managed data. Rationale:
  these are deterministic Linux per-user locations already consistent with the settings store and
  keep logs separate from catalogs and secrets.
  Date/Author: 2026-08-10 / Codex.
- Decision: rotate by retaining one active file plus two numbered backups with a bounded byte limit,
  deleting only files owned by the FoliaSeal logger. Rationale: this provides predictable local
  retention without a daemon, background service, or deletion of unrelated user files.
  Date/Author: 2026-08-10 / Codex.
- Decision: make support surfaces modeless and reuse one instance per command, while the Settings
  dialog remains modal and transactional. Rationale: Help/support references should not block the
  signing workspace; Settings changes must still commit atomically only after Save.
  Date/Author: 2026-08-10 / Codex.

## Outcomes & Retrospective

The local support behavior is implemented and committed. The Help menu exposes all five required
commands; modeless support dialogs show keyboard shortcuts, data locations, and About; the
diagnostic writer is Qt-free, privacy-filtered, bounded, and rotated; Settings Restore defaults is
cancel-safe. Focused support/AppFrame tests and the full suite are green. Installed-package,
display-backed screen-reader/high-contrast/DPI, and final release-matrix evidence remain open and
must not be inferred from headless success.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame.py` owns the real `QMainWindow`, menu actions, Settings
dialog, and local URL launching boundary. `app_frame_command_model.py` is the typed registry that
provides stable IDs, mnemonics, shortcuts, and accessible names. `QtAppFrameBindings` dynamically
loads Qt classes so unit tests can use fakes. `AppSettingsStore` owns atomic JSON settings writes.
The new support-location/log service must not import Qt; the new support dialogs may use only the
existing bindings and must not read PDF contents, selected text, signing Reason/Location, passwords,
private keys, or certificate secrets.

“Privacy filter” means a deterministic redaction boundary applied before a message reaches the
product log. It must remove known secret fields and redact path/content values when a caller labels
them sensitive; it must never attempt to infer private data by parsing arbitrary PDF bytes. “Rotate”
means close the active log when its byte limit is exceeded, shift FoliaSeal-owned backups, and start
a fresh active file.

## Change Slice

Primary change class: behavior change plus the minimum architecture/status documentation required to
describe the new support boundary. Allowed changes are the new support-location/log module, support
dialogs, command model, AppFrame/Settings wiring, focused tests, and relevant README/architecture/
ExecPlan updates. Do not mix final Debian/package acceptance, screen-reader certification, broad
logging of every existing code path, or Acceptance evidence renaming.

## Plan of Work

First add a Qt-free support contract under `src/foliaseal/application/support_diagnostics.py` (or a
closely named application/infra module). Define immutable support locations, a privacy-filtered log
record operation, and a small rotating writer with explicit `max_bytes` and `backup_count` inputs.
The default writer must create only the per-user logs directory, write UTF-8 text with timestamp,
level, error code, stage, and actionable detail, and atomically rotate only its own `foliaseal.log`
files. Unit tests must prove that password, private-key, PDF-content, selected-text, Reason, and
Location values never appear and that rotation is deterministic.

Extend `AppFrameCommandId` and `HELP_COMMAND_DEFINITIONS` with stable IDs and unique mnemonics for
Keyboard Shortcuts, Data Locations, Open Diagnostic Logs Folder, and About. Keep the existing Help/F1
definition unchanged. In `FoliaSealAppFrame._install_menus`, route each action through a thin public
method; do not put dialog construction in the command registry. Folder opening must use the existing
`QDesktopServices.openUrl(QUrl.fromLocalFile(...))` boundary, create only the owned logs directory,
and report an unavailable launcher through the existing error/status callback.

Add `src/foliaseal/presentation/qt/support_dialogs.py` with small modeless dialog objects for the
keyboard shortcut list, data-location paths, and About content. Each dialog must have a descriptive
title, accessible text control, a keyboard-reachable Close button, and explicit object names. Build
the shortcut text from the typed command registry so visible labels and shortcuts cannot drift. Data
Locations must show config/data/log paths without secrets; About must show the installed version or a
truthful development-checkout label and links only to local Help, not remote resources. Reuse one
dialog instance per surface and clear it on `finished`.

Extend `AppSettingsDialogControls` with Restore defaults. The action resets both directory fields to
`AppSettings.default()` values and Appearance to System in the live dialog only; it does not write
until Save, and Cancel must restore the original persisted settings. Add accessible names and tests
for restore-then-cancel and restore-then-save.

Use the existing Help viewer for `FoliaSeal Help`; do not create a second topic renderer. Keep support
dialogs independent from an open PDF so they work from the no-document frame and do not reopen
documents or drafts.

## Milestones

### Milestone 1: prove the Qt-free support contract

Add red tests for locations, privacy filtering, log writes, and rotation. Implement the contract until
the tests pass without importing PySide6 or touching a PDF. The observable result is a temporary log
directory containing only the bounded FoliaSeal files and no sensitive fixture values.

### Milestone 2: expose all Help/support commands

Add typed command definitions, support dialog objects, AppFrame routing, local folder launching, and
offscreen tests for menu metadata, accessible names, keyboard reachability, dialog reuse, and no-
document invocation. The observable result is every UI_SPEC Help command present and usable from the
stable main frame.

### Milestone 3: finish Settings and acceptance

Add Restore defaults tests, run focused/full/Ruff/pip/package checks, audit local resource/privacy
strings, run a bounded GUI attempt with an owned temporary XDG root, clean processes/dialogs, update
architecture and parent/release plans, and commit.

## Concrete Steps

Run from `/home/daekar/FoliaSeal` with `.venv`.

    rg -n 'HELP_COMMAND_DEFINITIONS|AppSettingsDialogControls|q_desktop_services|q_text_edit' src/foliaseal/presentation/qt/app_frame.py src/foliaseal/presentation/qt/app_frame_command_model.py
    QT_QPA_PLATFORM=offscreen .venv/bin/pytest -q tests/unit/test_support_diagnostics.py tests/unit/test_qt_app_frame.py tests/integration/test_support_surfaces.py
    .venv/bin/ruff check src tests
    .venv/bin/python -m pip check
    .venv/bin/pytest -q
    git diff --check

For the bounded GUI attempt, use an owned temporary root and always clean it:

    audit_root=$(mktemp -d /tmp/foliaseal-support-XXXXXX)
    set +e
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_DATA_HOME="$audit_root/data" XDG_STATE_HOME="$audit_root/state" .venv/bin/python -m foliaseal gui >"$audit_root/gui.log" 2>&1
    rc=$?
    set -e
    printf 'gui_rc=%s\n' "$rc"
    ps -eo pid=,cmd= | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

## Validation and Acceptance

The slice is accepted when the Help menu visibly contains all five required entries with unique
keyboard mnemonics; Keyboard Shortcuts, Data Locations, and About open reusable modeless dialogs from
the no-document frame; Diagnostic Logs creates/opens only the owned local logs directory; Settings
Restore defaults changes the draft dialog values but Cancel leaves persisted settings untouched; and
all support text is reachable by keyboard and has accessible names. The log tests must prove bounded
rotation and absence of passwords, private keys, PDF contents, selected text, Reason, and Location.
Focused/offscreen tests, Ruff, pip check, full regression, and diff checks must pass. The display-backed
launch may remain limited by the known local single-instance endpoint; record that limitation without
leaving processes or dialogs.

## Idempotence and Recovery

All log/path tests use temporary XDG roots. Re-running them may recreate only those exact roots. If a
dialog or folder-launch test fails, close the created support dialog, remove the owned temporary root,
and rerun. Never delete a user configuration/data directory or broad workspace path. A failed Save
must leave the previous settings JSON intact; Restore defaults is only an in-memory edit until Save.

## Artifacts and Notes

Do not commit generated logs, private keys, PDFs, screenshots, or machine-local absolute paths. Keep
temporary logs and GUI output under `/tmp` or ignored `artifacts/`. Record concise test counts, the
redaction/rotation assertions, command IDs, and the bounded GUI return code in this plan.

## Interfaces and Dependencies

The Qt-free support module should expose deterministic interfaces equivalent to:

    @dataclass(frozen=True)
    class SupportLocations:
        config_dir: Path
        data_dir: Path
        logs_dir: Path

    class DiagnosticLogWriter:
        def write(self, *, level: str, error_code: str, stage: str, detail: str, sensitive: Mapping[str, str] = {}) -> Path: ...

`FoliaSealAppFrame` owns the writer and passes only sanitized technical details from its existing
error/status boundary. `SupportDialog` objects own Qt widget construction and expose `show()` and
`close()`; they must not import application signing workflows. `AppSettingsDialogControls` adds a
`restore_defaults_button` while preserving the existing Save/Cancel fields. No support module may
import the Acceptance harness or read private document/signing values.

Revision note: 2026-08-10 / Codex
Created after a fresh repository audit found the required Help-menu support commands and product-level
diagnostics/log contract missing while the offline Help viewer and package path were already complete.

Revision note: 2026-08-10 / Codex
Updated after implementation and commit `4aad84ad8` to record the complete local support behavior,
focused/full validation, and the remaining installed-package/display-backed release gates.
