# Certificate creation, export, remembered passwords, and deletion

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can create a certificate, export an encrypted backup, remember or clear its password, and delete it safely in the real FoliaSeal GUI. It is mapped to SPEC managed certificate workflow and UI_SPEC section 15. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_certificate_import_configuration_execplan.md — content inspection,
  atomic import, and retained-file Configure are committed in `ad712ad7e` and `498d5c791`.

## Progress

- [x] (2026-08-10) Audited the existing manager, secure-secret boundary, catalog repository,
  certificate dialogs, and governing UI_SPEC workflow. The existing create/export/delete paths
  are present, but creation is one-year and lacks confirmation/subject fields; management Save
  also clears remembered passwords instead of preserving or explicitly disabling them.
- [x] (2026-08-10) Added red focused tests for five-year identity construction, password
  confirmation, remembered-password preservation/disable, and export password validation; the
  pre-implementation run reported four failures for the missing request fields and behavior.
- [x] (2026-08-10) Implemented five-year self-signed creation with full-name, email, title, and
  organization subject fields; the Qt dialog now requires matching confirmation and pre-fills the
  display name. Management Save preserves remembered secrets, explicit disable removes them, and
  enabling validates the supplied password before secure storage. Export validates a supplied or
  remembered password before copying encrypted bytes and leaves managed state unchanged.
- [x] (2026-08-10) Reviewed changed source and tests for migrated compatibility or acceptance product
  cruft. No new acceptance nomenclature was introduced; the remaining dialog compatibility snapshot is
  still consumed by app-frame tests and has no safe retirement condition in this slice.
- [x] (2026-08-10) Ran focused manager/dialog/app-frame validation: Ruff and `git diff --check`
  are clean and the focused manager/dialog command reports 29 passed. Full-suite, bounded GUI,
  and cleanup evidence are recorded below.
- [x] (2026-08-10) Updated this plan, the parent compliance record, and `docs/ARCHITECTURE.md`;
  the behavior and documentation are ready for the commit gate.

## Surprises & Discoveries

- Observation: the current self-signed certificate builder uses a one-year validity period, so
  the five-year UI_SPEC recommendation is an explicit behavior change rather than a label-only
  adjustment.
  Evidence: src/foliaseal/application/certificate_manager.py:358-360.
- Observation: the existing management Save request has no password intent and always writes
  `save_password=False`, which can silently discard a remembered secret.
  Evidence: `CertificateManager.save_configuration()` reconstructs the configuration with a null
  `password_secret_ref`; the management dialog exposes only display name and notes.
- Observation: raw repository export already preserves the encrypted `.p12` bytes and managed
  state, but the application boundary does not yet validate the existing password before a GUI
  backup.
  Evidence: `CertificateManager.export()` delegates directly to
  `export_managed_certificate_by_id()` without a passphrase or certificate-content check.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible certificate creation, export, remembered
  passwords, and deletion outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: preserve the existing positional `display_name`/`passphrase` constructor shape for
  headless callers while adding optional subject fields and confirmation to the typed request.
  Rationale: the real GUI path will use the complete guided form, while existing application tests
  remain explicit callers rather than an excuse to keep a product-facing compatibility surface.
  Date/Author: 2026-08-10 / Codex
- Decision: make remembered-password intent explicit in `SaveConfigurationRequest`: omitted intent
  preserves current state, `False` removes the secure secret, and `True` requires secure storage
  plus a validated password before persistence.
  Rationale: a rename or notes edit must never erase a credential, and disabling must be a visible,
  deliberate user action as required by UI_SPEC section 15.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

This slice now provides the complete guided certificate lifecycle promised here: a five-year
self-signed certificate can be created with full-name identity fields and matching password
confirmation; the user is offered an encrypted backup whose supplied password is validated; and
the management dialog can preserve, enable, or explicitly disable a remembered password without
putting the secret in catalog JSON. Configuration deletion still preserves the managed file, while
managed-file deletion remains guarded by configuration references. Expiration sorting and password
change are separate product gaps and remain in their owning plans/out-of-scope boundaries.

## Context and Orientation

The relevant code is src/foliaseal/application/certificate_manager.py, certificate_secret_store.py,
certificate_storage.py, and the certificate dialogs. FoliaSeal is a Python/Qt Linux PDF signing
application. The
primary flow is open, review, select reusable setup, place one visible signature, preview
readiness, sign/save, verify, and reopen. V1 excludes tabs, printing, broad PDF editing, cloud
workflow, enterprise trust administration, and multiple pending signatures.

A compatibility surface is an adapter retained only for old callers. “acceptance” names identify legacy
evidence/harness infrastructure and must not be introduced into ordinary product UI or new primary
contracts; production backend/evidence imports may be renamed only after a neutral migration proves
the old name is no longer required.

## Change Slice

Primary change class: behavior change. Allowed changes are the named modules, focused tests,
bounded ignored local evidence, and minimum truthful documentation. Do not mix unrelated evidence
rebaselines, V2 features, or packaging work.

## Plan of Work

Implement the guided opinionated self-signed creation flow with fixed five-year validity, password confirmation, optional identity fields, encrypted .p12 backup export, secure remembered-password enable/disable, and deletion that keeps the file/configuration ownership rules explicit. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.
Keep remembered passwords exclusively in the secret store. If catalog fields change, add a
before/after serialized fixture and backward-read or deliberate rejection test; otherwise prove
existing catalog fixtures remain readable.

## Milestones

Milestone 1 audits the manager, secret store, and catalog transaction and adds failing validity and
password tests. Milestone 2 implements five-year creation, encrypted export, remembered-secret
toggle, and deletion through those authorities. Milestone 3 proves the GUI flow without leaking
secret material and records recovery evidence.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'create|export|password|delete' src/foliaseal/application/certificate_manager.py src/foliaseal/application/certificate_secret_store.py src/foliaseal/presentation/qt/app_frame_certificate_management.py
    .venv/bin/pytest -q tests/unit/test_certificate_manager.py tests/unit/test_secret_storage.py tests/unit/test_certificate_storage.py tests/unit/test_qt_app_frame_certificate_management.py
    .venv/bin/ruff check src tests
    .venv/bin/pytest -q
    git diff --check

Run this bounded walkthrough from /home/daekar/FoliaSeal with an isolated configuration root:

    audit_root=$(mktemp -d /tmp/foliaseal-plan-audit-XXXXXX)
    timeout --foreground 30s env QT_QPA_PLATFORM=offscreen XDG_CONFIG_HOME="$audit_root/config" XDG_CACHE_HOME="$audit_root/cache" .venv/bin/python -m foliaseal gui --pdf-path artifacts/preview_sweep_assets/sweep_fixture.pdf || test "$?" -eq 124
    ps -eo pid,cmd | rg 'FoliaSeal|foliaseal|PySide6|pytest' | rg -v 'rg ' || true
    rm -rf "$audit_root"
    test ! -e "$audit_root"

Expected evidence is the stated user-visible behavior plus a mandatory Qt-test or display-backed
walkthrough. Record the exact input sequence, widget state, expected observation, evidence path, and
cleanup result; the bounded timeout is only a lifecycle check. In this environment the bounded
offscreen launch reached its timeout (`launch_rc=124`) without leaving a process; the fake-binding
Qt tests are the authoritative visible-flow evidence and no display-backed success is claimed.

## Validation and Acceptance

Acceptance is behavioral: A non-expert can create a local certificate, export an encrypted backup through Save As, optionally remember its password securely, disable that secret, and delete the configuration without accidental key loss. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Creation uses the fixed five-year recommended certificate flavor and exposes no algorithm/key-size
controls. Export is encrypted, never emits an unencrypted key or sidecar secret, reports the exact
successful path, and does not mutate managed state. Missing or rejected remembered secrets fall back
to a manual prompt; disabling the secret removes only the stored secret.

## Evidence Record

Before completion, record the exact manager/storage/Qt test command and result, the GUI creation,
export, remember/disable, and delete sequence, evidence path, secret-clearing and cleanup results,
serialized catalog compatibility result, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

Evidence for this implementation:

- The red manager run reported four failures before the new request fields and behavior existed.
- Focused command `.venv/bin/pytest -q tests/unit/test_certificate_manager.py
  tests/unit/test_qt_app_frame_certificate_management.py` reports `29 passed`; the broader impacted
  command reports `93 passed`.
- Full repository command `.venv/bin/pytest -q` reports `1266 passed, 20 skipped, 1 warning` in
  48.49 seconds; the warning is the pre-existing Pillow `Image.getdata` deprecation.
- Visible fake-Qt scenarios cover full-name/subject-field creation, matching confirmation, the
  post-create encrypted-backup offer, password validation, and remember-password enablement. No
  passwords or generated certificate files were committed.
- Bounded offscreen launch under isolated XDG roots timed out at 30 seconds (`launch_rc=124`), the
  temporary root was removed, and the process audit found no FoliaSeal/PySide6/pytest process.
- No SVG was added: this Settings certificate surface uses existing dialog topology and does not
  alter the normative Library topology.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by tests/unit/test_certificate_manager.py tests/unit/test_certificate_storage.py tests/unit/test_secret_storage.py and tests/unit/test_qt_app_frame_certificate_management.py. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-10 / Codex
Completed the guided five-year create/export/password lifecycle, added red-to-green manager and
Qt evidence, and recorded the bounded GUI timeout/cleanup limitation.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.
