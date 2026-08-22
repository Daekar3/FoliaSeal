# Remove schema terminology from ordinary GUI copy

This ExecPlan is a living document maintained according to
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It defines one focused presentation-layer
cleanup. It must be updated as findings, tests, and decisions accumulate.

## Purpose / Big Picture

The GUI currently exposes internal persistence vocabulary such as “certificate configuration”,
“managed certificate”, “appearance profile”, and “placement profile”. `docs/UI_SPEC.md` reserves
those phrases for technical explanations and requires ordinary UI to speak in the user-facing
concepts Certificate, Appearance, Placement, and Signature placement. After this slice, a person
opening the certificate dialogs, signing rail, or refinement dialog will see consistent product
language without any change to stored data, signing behavior, or schema identifiers.

The change is observable by opening Settings → Manage Certificates, choosing a certificate in the
signing rail, and opening Refine Current PDF Setup. Labels, helper text, message-box titles, menu
actions, and save prompts will use the approved vocabulary. Existing persistence files remain
readable because domain and schema names are deliberately unchanged.

## Child ExecPlan Dependencies

- [x] The governing authority is available in `docs/SPEC.md`, `docs/SCHEMAS.md`, and
  `docs/UI_SPEC.md` §3. `SPEC.md` and `SCHEMAS.md` retain authority over product and persistence
  semantics; this slice changes only Qt presentation copy.
- [x] Explorer review completed on 2026-08-22 and identified all affected Qt surfaces, tests, and
  the distinction between a user-facing Certificate and its stored certificate file.
- [x] The prior X11 GUI audit is committed at `c50a6802c`; this slice starts from a clean checkout.

## Progress

- [x] (2026-08-22) Read the dev-loop and ExecPlan instructions and reviewed `UI_SPEC.md` §3,
  `SPEC.md`, `SCHEMAS.md`, `ARCHITECTURE.md`, and the prior GUI audit plan.
- [x] (2026-08-22) Explorer mapped visible violations in the command model, signing properties
  panel, certificate-management dialogs, refinement dialog, appearance editor, and focused Qt tests.
- [x] (2026-08-22) Wrote and applied the Qt-facing vocabulary across commands, dialogs, rail copy,
  refinement prompts, and application-generated readiness/error messages without renaming domain or
  schema identifiers or persistence keys.
- [x] (2026-08-22) Updated focused tests and added a source-level guard covering Qt presentation files
  plus application modules whose messages are rendered directly in the GUI.
- [x] (2026-08-22) Focused validation passed (`269 passed` before the final assertion-only update),
  Ruff/compile/diff checks passed, and the clean full suite passed `1606 passed, 20 skipped, 1 warning`
  in 61.72s.
- [x] (2026-08-22) The final X11 audit passed 23 rendered checkpoints, including the new Manage
  Certificates dialog, and the native X11 accessibility audit passed with the renamed Settings action,
  F1 Help, 1100×700 geometry, and owned-root cleanup.
- [x] (2026-08-22) Completed architecture/spec compliance review and documentation reconciliation.
  The remaining schema identifiers are unchanged; the terminology guard covers Qt plus direct GUI
  message producers. The bounded slice was committed as `81f15c9e9`; the worktree and owned GUI
  process/temp-root checks are clean.

## Surprises & Discoveries

- Observation: the certificate-management UI intentionally distinguishes a signing identity from
  the stored certificate file it references.
  Evidence: `app_frame_certificate_management.py` renders separate selectors and helper text for
  certificate configurations and managed certificates.
- Observation: `docs/SCHEMAS.md` canonicalizes `ManagedCertificate`, `CertificateConfiguration`,
  `AppearanceProfile`, and `PlacementProfile` as persisted object types.
  Evidence: the explorer review and schema search. These identifiers must remain unchanged.
- Observation: visible title capitalization was corrected in the prior audit, but several labels and
  accessible names still use forbidden schema terminology.
  Evidence: `app_frame_command_model.py`, `signing_workspace_properties_panel.py`,
  `app_frame_certificate_management.py`, `signing_workspace_refinement_dialog.py`, and
  `appearance_profile_editor_widget.py`.
- Observation: the first post-change live audit failed only because the harness still expected the old
  “Certificate configuration” group label; updating the harness expectation to “Certificate” restored
  the audit and exposed no product failure.
  Evidence: `/tmp/foliaseal-terminology-x11-audit-CBvSH1` failure followed by the passing 23-checkpoint
  run under `/tmp/foliaseal-terminology-x11-audit-tZioTz`.
- Observation: rendered review showed that technically compliant capitalization could still sound
  unnatural (“those Certificates”, “No Certificates”). The final copy uses natural prose while keeping
  concise title-case labels such as Certificate and Certificate file.
  Evidence: final screenshots 03, 04, 07, and 08 from the final X11 run.

## Decision Log

- Decision: perform the migration at the Qt presentation boundary and the small set of application
  readiness/error producers whose messages are rendered directly by that boundary.
  Rationale: UI_SPEC controls user-facing language, while SCHEMAS controls persisted object names;
  changing only Qt labels would leave visible readiness and error messages noncompliant, while changing
  schema identifiers would create unnecessary migration risk.
  Date/Author: 2026-08-22 / Codex.
- Decision: call the user-facing signing identity “Certificate” or “Signing certificate”, and call
  the underlying stored file “Certificate file” where the distinction is necessary.
  Rationale: UI_SPEC defines Certificate as the managed signing identity and forbids “Managed
  Certificate”; the certificate-management surface still needs an unambiguous file distinction.
  Date/Author: 2026-08-22 / Codex.
- Decision: replace “Appearance Profile” with “Appearance” and “Placement Profile” with “Placement”
  in labels, prompts, errors, and helper text, while preserving class/module names and storage keys.
  Rationale: these are exactly the approved UI concepts in UI_SPEC §3, and the existing editor already
  describes reusable objects rather than requiring the backend suffix.
  Date/Author: 2026-08-22 / Codex.
- Decision: add a test guard that scans Qt presentation source and the selected application message
  producers for forbidden ordinary-copy phrases, excluding docstrings and identifiers.
  Rationale: the guard must cover text that is actually shown by the GUI without falsely requiring a
  domain-wide vocabulary rewrite of technical storage and persistence diagnostics.
  Date/Author: 2026-08-22 / Codex.

## Outcomes & Retrospective

At completion, all ordinary Qt copy and directly rendered application readiness/error messages in the
affected surfaces use the approved vocabulary. Persisted schema identifiers and catalog keys remain
unchanged. Focused tests prove the new labels and messages, the source guard prevents reintroduction,
and the real X11 audit shows the revised dialogs and rail. The only remaining forbidden phrase in the
scanned scope is an explicitly allowlisted technical schema-validation diagnostic; ordinary visible
copy no longer violates UI_SPEC §3.

Final evidence (2026-08-22): the updated parent audit passed 23 checkpoints, two signatures, and
reopen/verify after capturing Manage Certificates. The native X11 accessibility audit passed with
`Manage certificates` in Settings, F1 Help delivery, 1100×700 geometry, and no owned process/window
or temporary root after cleanup. The full suite passed `1606 passed, 20 skipped, 1 warning`.

## Context and Orientation

`src/foliaseal/presentation/qt/app_frame_command_model.py` defines menu text and accessible names.
`app_frame_certificate_management.py` owns import, creation, and management dialogs. The signing
rail’s certificate selector and readiness messages live in `signing_workspace_properties_panel.py`.
`signing_workspace_refinement_dialog.py` owns the contextual editor’s reusable-object controls and
save prompts. `appearance_profile_editor_widget.py` supplies validation messages for the standalone
editor. These modules call domain/application services, but the strings rendered by their Qt widgets
are presentation copy and may be changed independently of schema identifiers.

The approved vocabulary is: Certificate for the reusable signing identity; Certificate file when
the stored PKCS#12 file itself is the subject; Appearance for reusable visible-signature styling;
Placement for reusable page/rectangle placement; Signature placement for the pending rectangle in
the open document. “Certificate configuration”, “Managed certificate”, “PKCS#12 object”,
“Appearance profile”, and “Placement profile” are prohibited in ordinary UI copy.

## Plan of Work

First introduce small Qt-facing constants or helper text at the presentation boundary only where
the same phrase appears in multiple controls. Replace command text and accessible names in the
Settings menu with “Manage Certificates…”, preserving its action identifier and command routing.
In the signing properties panel, change the selector placeholder, group title, helper text, and
message-box title to Certificate/Signing certificate language; use Certificate file only when
describing the stored file.

Next update certificate import and creation introductions, management-dialog title, labels, helper
text, errors, information messages, and export prompts. Keep the two concepts distinct: the first
selector is a Certificate (the signing identity), while the second is a Certificate file. Do not
rename `CertificateConfigurationManagementDialogControls`, manager methods, request types, or IDs.

Then update refinement labels, empty-choice text, save-dialog titles, and validation messages from
profile terminology to Appearance and Placement. Update standalone appearance-editor validation
copy in the same way. Preserve `appearance_profile_names`, `placement_profile_names`, coordinator
methods, and all serialized fields because those are internal contracts.

Finally update focused assertions to the new visible copy and add a narrow regression test that
searches the Qt presentation modules for the prohibited ordinary phrases. The guard must ignore
Python identifiers, comments/docstrings, and explicitly technical error text where changing the
wording would alter a domain contract; visible widget labels, button text, menu text, accessible
names, and message-box titles must not be ignored.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    git status --short
    rg -n -i "certificate configuration|managed certificate|pkcs.?12 object|appearance profile|placement profile|manage certificate" src/foliaseal/presentation/qt tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_signing_shell.py

Edit only the Qt presentation copy and its focused tests. After each surface, run the narrow tests:

    .venv/bin/pytest -q tests/unit/test_qt_app_frame_certificate_management.py tests/unit/test_qt_signing_shell.py

Then run the source guard and all project checks:

    .venv/bin/pytest -q tests/unit/test_ui_terminology_compliance.py
    .venv/bin/pytest -q
    .venv/bin/ruff check src tests scripts
    .venv/bin/python -m compileall -q src scripts
    git diff --check

For rendered proof, run the bounded source-tree GUI audit on Cinnamon/X11 with a fresh temporary
artifact root, inspect the updated certificate-management, refinement, and signing-rail screenshots,
and remove the exact owned root and any owned process after review. The audit must still report
`status: passed` and all existing workflow checkpoints.

## Validation and Acceptance

The slice passes when focused certificate-management and signing-shell tests pass with the new
user-facing strings; the terminology guard reports no prohibited phrase in ordinary Qt copy; the
full suite, Ruff, compilation, and diff checks pass; and the real X11 audit shows “Certificate”,
“Certificate file”, “Appearance”, and “Placement” in the affected dialogs and rail. Stored catalog
files, schema identifiers, action IDs, and signing behavior must remain unchanged. A remaining
technical-only phrase is acceptable only when the test guard’s allowlist explains why it is not
ordinary UI copy.

## Idempotence and Recovery

This slice changes source and tests only; no user data or catalog migration is required. If a test
fails because an expected string is a domain error rather than visible copy, classify it before
changing it and preserve the domain contract. GUI audit artifacts must use a unique `/tmp` root and
must be deleted after review. Never kill an unrelated FoliaSeal process. Reverting the focused commit
is sufficient to restore the prior vocabulary because no persistence format changes are made.

## Artifacts and Notes

Allowed changes are Qt presentation copy, directly rendered application readiness/error copy, focused
tests, the terminology guard, the audit harness checkpoint/expectation refresh, this ExecPlan, and
necessary architecture/status documentation. Do not mix schema migrations, signing behavior changes,
GUI topology changes, packaging changes, or unrelated refactors into this commit.

## Interfaces and Dependencies

Use the existing Qt widget constructors, command definitions, certificate-management callbacks, and
coordinator interfaces. Do not alter persistence schemas in `src/foliaseal/infra/config`, JSON keys,
catalog filenames, or public command IDs. The small application message changes are limited to
readiness/error text that is displayed by the Qt surfaces; domain object shapes and persistence remain
unchanged. The regression guard is a normal pytest test under `tests/unit/` and inspects repository-
relative Qt presentation files plus the selected direct GUI message producers deterministically.

## Revision Note

Created on 2026-08-22 after the focused terminology review of the prior X11 audit. Updated after the
compliance review to include direct application-generated GUI messages, an explicit technical-diagnostic
allowlist, the Manage Certificates rendered checkpoint, and the final natural-language corrections.
