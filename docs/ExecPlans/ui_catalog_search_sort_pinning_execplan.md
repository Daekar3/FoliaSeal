# Catalog search, sort, pinning, naming, and deletion rules

This ExecPlan is a living document and must be maintained in accordance with
.agents/skills/write-execplan/PLANS.md. It is an AFK (agent can implement and validate without a
pending human product decision) child of
docs/ExecPlans/ui_spec_v1_compliance_parent_execplan.md.

## Purpose / Big Picture

After this slice, a user can search, sort, pin, rename, duplicate, and delete catalog entries safely across restarts in the real FoliaSeal GUI. It is mapped to UI_SPEC sections 6 and 14; SCHEMAS storage rules. The
slice is one vertical path through the relevant persistent model,
application workflow, Qt surface, focused tests, and observable acceptance.

## Child ExecPlan Dependencies

- [x] docs/SPEC.md and docs/UI_SPEC.md are frozen governing contracts.
- [x] docs/ExecPlans/ui_signature_library_topology_execplan.md (committed as `a4e97edab`; bounded
  modeless topology and typed session are available).
- [x] docs/ExecPlans/ui_window_theme_responsive_execplan.md (typed AppSettings UI projection and
  atomic persistence are available; this child adds only Library preference keys).

## Progress

- [x] (2026-08-10) Audited the governing catalog rules and live models. Only placements had pin
  metadata; names compared case-sensitively; no duplicate command, sort state, or Library preference
  bridge existed. Certificate validity metadata and expiration ordering are owned by the dedicated
  certificate-validity child.
- [x] (2026-08-10) Added failing coverage for case-insensitive names, duplicate identity/pin reset,
  pin ordering, certificate pin round-trip, and AppSettings Library preferences.
- [x] (2026-08-10) Implemented persistent pins for appearances, placements, presets, managed
  certificates, and certificate configurations; added typed DuplicateObject/SetPinned commands,
  normalized uniqueness, pinned-first Name A-Z/Z-A projection, and Library preference persistence.
- [x] (2026-08-10) Subsequent compliance review found configured-first ordering, orphan-certificate
  actionability, and merged-name validation gaps; the projection and AppFrame callbacks were corrected
  and the merged identity semantics are now explicit.
- [x] (2026-08-10) Ran focused, regression, offscreen GUI, static, diff, and process-cleanup
  validation; no owned FoliaSeal/PySide6/pytest process remains.
- [x] (2026-08-10) Updated architecture documentation for the Library mutation boundary; the
  current follow-up commit is the remaining handoff gate.
- [x] (2026-08-10) Reconciled the former expiration deferral with
  `ui_certificate_validity_expiration_sort_execplan.md`: this child owns row identity ordering while
  the certificate child owns public validity metadata and the expiration-specific control.
- [x] (2026-08-10) Fresh compliance review identified the remaining Library mutation-lifecycle gap;
  successful retained-certificate configuration must refresh an already-open Library, and every
  destructive Delete action must ask for explicit confirmation before invoking a mutation callback.
- [x] (2026-08-10) Added red Qt-boundary coverage for configure-to-row refresh, Delete cancellation,
  referenced-delete preservation, and expiration-sort preference propagation; the implementation and
  complete validation are recorded in the subsequent checked entries.
- [x] (2026-08-10) Added red coverage for configure-to-row refresh, Delete cancellation/acceptance
  for reusable and certificate rows, expiration preference propagation, and global pinned-versus-
  configured precedence; the new focused suite initially failed on the two missing UI behaviors.
- [x] (2026-08-10) Implemented confirmation-gated Delete and successful Configure refresh/reselect
  in `ReusableObjectLibraryDialog` without moving reference or persistence policy into Qt.
- [x] (2026-08-10) Focused mutation/catalog/session tests pass: `22 passed`; Ruff and
  `git diff --check` are clean for the changed modules.
- [x] (2026-08-10) Full regression passes: `1277 passed, 20 skipped, 1 warning in 48.66s`; the
  warning is the pre-existing Pillow `Image.getdata` deprecation in `tests/unit/test_interactive_harness.py`.
- [x] (2026-08-10) Bounded offscreen GUI launch reached the known isolated single-instance socket
  limitation (`SingleInstanceUnavailable`, exit code 1) before frame creation; process audit was
  empty and `/tmp/foliaseal-library-audit-BiU3I7` was removed.

## Surprises & Discoveries

- Observation: catalog persistence is implemented separately from the AppSettings restart state;
  this child owns the explicit bridge for last-catalog, sort, and stable pin semantics.
  Evidence: the live source paths and focused tests listed below are the audit baseline.
- Observation: `_edit_selected_object()` returned the retained-certificate configuration callback
  without refreshing the modeless Library, so the visible row could remain stale until a later
  reopen or unrelated refresh. Evidence: `src/foliaseal/presentation/qt/app_frame_profile_library.py`
  called `self._on_configure_certificate(ref)` directly at the certificate branch.
- Observation: `delete_selected()` invoked reusable-object and certificate deletion callbacks
  without a modal question, contrary to UI_SPEC WF06 and the modal destructive-decision topology.
  Evidence: the method dispatched directly to `ReusableSigningObjects.execute(DeleteObject(...))`
  or `_on_delete_certificate`.

## Decision Log

- Decision: obey SPEC.md, SCHEMAS.md, and UI_SPEC.md in that precedence order.
  Rationale: these are the repository's explicit authority boundaries.
  Date/Author: 2026-08-09 / Codex
- Decision: keep the slice limited to one user-visible catalog search, sort, pinning, naming, and deletion rules outcome.
  Rationale: narrow changes are independently testable and recoverable.
  Date/Author: 2026-08-09 / Codex
- Decision: keep destructive confirmation in the Library presentation boundary, immediately before
  a typed mutation or AppFrame certificate callback, and treat Cancel or an unavailable question
  API as a no-op.
  Rationale: the application/catalog authorities already enforce references and persistence; the
  UI boundary is the correct place to ask the user without allowing a canceled action to mutate
  state or duplicating policy in storage.
  Date/Author: 2026-08-10 / Codex
- Decision: refresh the modeless Library only after a successful retained-certificate configure
  callback and preserve the existing session/search/sort state while rebuilding its rows.
  Rationale: configuration changes the merged certificate row identity, so a refresh is necessary
  for truthful status while the session already owns safe selection/search state.
  Date/Author: 2026-08-10 / Codex

## Outcomes & Retrospective

The application/storage boundary now owns stable pin metadata and duplicate semantics for all
persisted catalog records. The Library session keeps pinned rows first, configured certificate rows
before retained unconfigured files, and applies Name A-Z or Z-A ordering while persisting last
catalog/sort choices without restoring an open window or draft.
Certificate import/create/configure UI, nested editors, and
dirty-detail prompts remain explicit follow-on work owned by certificate/editor children; the
Library now routes certificate pin, rename, and delete operations through typed AppFrame callbacks.

The mutation-lifecycle follow-up is implemented: successful retained-certificate configuration
refreshes and reselects the merged row, and Delete is confirmation-gated before any reusable or
certificate mutation. Expiration sort now has explicit Qt preference-propagation coverage, and a
session test records the global pinned-first precedence when a pinned retained file competes with an
unpinned configured row. Nested editors, dirty-detail prompts, and active-placement invalidation
remain explicit follow-on boundaries.

## Context and Orientation

The relevant code is reusable signing models/catalog store; Library list/detail widgets; schemas/profile storage. FoliaSeal is a Python/Qt Linux PDF signing application. The
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

Implement case-insensitive live search, Name A-Z/Z-A sorting, pinned-first ordering, trimmed
case-insensitive unique names, and explicit Rename/Duplicate/Delete/Pin rules. Prevent dangling
references and preserve pins across rename and merged results. Add or preserve typed application and public Qt-port boundaries rather than reaching
through private widgets. Keep schema and terminology aligned with the frozen documents. When a
legacy path is replaced, prove its callers are migrated before deleting it.

Consume the canonical AppSettings keys owned by
`docs/ExecPlans/ui_window_theme_responsive_execplan.md` for `library_last_catalog` and
`library_sort`; do not create a second settings schema. Add catalog fixtures proving those keys are
preserved while Library open state/session drafts remain non-restorable.

## Milestones

Milestone 1 adds model/store tests for normalized names, stable pins, sorting, duplicate identity,
and AppSettings keys. Milestone 2 wires the Library controls and refresh behavior through the catalog
  authority. Milestone 3 proves restart persistence and deletion safety in the GUI, then records
  evidence and cleanup. Certificate validity metadata and expiration ordering are implemented by
  the separate certificate-model child; this child owns the merged-row precedence and Qt preference
  propagation that consume that result.
Milestone 4 closes the mutation lifecycle by refreshing the open Library after successful
certificate configuration, asking for confirmation before destructive actions, and proving the
expiration preference reaches the persistent settings callback without changing the session-only
search state. The milestone is complete once the focused tests, full regression, static checks, and
bounded GUI/process cleanup are recorded below.

## Concrete Steps

Run from /home/daekar/FoliaSeal.

The commands below assume the repository virtual environment exists. If it does not, create it
before continuing with `python3 -m venv .venv && .venv/bin/python -m pip install -e '.[gui]'`. If
dependency installation is unavailable, stop and report that environment blocker; do not silently
fall back to a system Python or system Qt installation.

    rg -n -e 'pin|sort|search|duplicate|delete|display_name' src/foliaseal/application/reusable_signing_models.py src/foliaseal/application/reusable_signing_objects.py src/foliaseal/infra/config/profile_storage.py
    .venv/bin/pytest -q tests/unit/test_reusable_signing_models.py tests/unit/test_reusable_signing_objects.py tests/unit/test_signature_preset_storage.py
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
cleanup result; the bounded timeout is only a lifecycle check. The mutation follow-up must include
the exact confirmation title/text for both reusable and certificate rows, the unchanged catalog after
Cancel, the refreshed configured row after Configure, and the persisted
`library_sort=expiration_soonest` callback value.

## Validation and Acceptance

Acceptance is behavioral: Each of the four catalogs has predictable live filtering, pinned-first
ordering, and Name A-Z/Z-A sorting; configured certificate rows precede retained unconfigured files;
invalid names and referenced-object deletion are explained and
cannot corrupt persisted references. Delete must ask before either mutation authority is invoked;
Cancel leaves the catalog unchanged, while Yes reaches the existing reference checks. Successful
retained-certificate Configure must refresh and reselect the merged row as configured. Focused tests must pass, shared-code changes must
leave the full suite green, and the GUI audit must record the visible result and cleanup.

## Required Acceptance Cases

Pins persist by stable object reference across restart; last catalog and Name sort persist in AppSettings;
search exists only while the Library is open. Names are trimmed and case-insensitively unique.
Referenced deletion is blocked or resolved without dangling references, duplicate objects receive a
new stable identity and start unpinned, and pinned entries remain first after rename or merged search
results. Certificate validity metadata and expiration sorting are owned by
`ui_certificate_validity_expiration_sort_execplan.md`; certificate pin/rename/delete are routed
through the existing certificate authority. Delete confirmation is required before either authority
is invoked, and a successful retained-certificate Configure refreshes the open Library row.

## Evidence Record

Evidence recorded for the original catalog implementation: its focused catalog/session/Qt/AppSettings
command passed `58 tests`, and its baseline regression passed `1241 passed, 20 skipped, 1 warning`;
the mutation follow-up focused command passed `22 tests`; Ruff and `git diff --check` are clean; the
offscreen Library/no-document integration passed `2 tests`; process audit was empty. The GUI surface
now exposes search, Name A-Z/Z-A sort, pin, duplicate, rename, and delete controls, with configured
certificate rows before retained unconfigured files. The certificate validity child adds the
expiration choice without changing this catalog's identity ordering.
The mutation follow-up adds red/green proof for confirmation-cancel and confirmation-accept,
configure refresh/reselection, expiration preference propagation, and global pinned precedence. The
complete regression now reports `1277 passed, 20 skipped, 1 warning`; the bounded offscreen launch
was limited by the isolated single-instance socket before frame creation, with no owned process or
temporary audit root remaining.

Before completion, record the exact catalog/AppSettings test command and result, the GUI search,
sort, pin, duplicate, rename, and delete sequence with observed rows, the evidence path and restart result,
serialized fixture compatibility result, cleanup, and compatibility grep proof.

Record the contributing UI_SPEC scenario ID(s) and either the owning SVG path or an explicit
"no SVG" decision alongside the evidence row.
Also record the exact focused test node and expected result (`N passed`); when the slice adds a new
contract, record that the test was red before implementation and green afterward.

## Idempotence and Recovery

Use temporary configuration and sibling output paths. If work fails halfway, preserve user PDFs and
drafts, update Progress with completed/remaining work, clean owned processes and artifacts, and
retry from the recorded state. Do not resurrect removed compatibility paths.

## Artifacts and Notes

Record concise output, focused screenshots or JSON under ignored artifacts/when useful, and exact
changed files. Never commit private keys, passwords, generated PDFs, or machine-local absolute paths.

## Interfaces and Dependencies

Use the existing typed application workflows, schema models, persistence stores, and public Qt frame
or workspace ports. The final behavior must be exercised by the reusable-object, certificate-model,
AppSettings, Library-session, and Qt Library tests. Any temporary adapter must
name its remaining consumer and retirement condition in this plan.

Revision note: 2026-08-09 / Codex
Created as a dependency-ordered child of the approved SPEC/UI_SPEC compliance breakdown.

Revision note: 2026-08-10 / Codex
Revised during implementation to record persistent pin metadata across reusable and certificate
catalogs, typed duplicate/pin commands, case-insensitive uniqueness, pinned-first Name sorting,
AppSettings Library preferences, focused evidence, and the explicit certificate-expiration/editor
deferrals.

Revision note: 2026-08-10 / Codex
Updated after the validity-metadata audit so the catalog child owns merged-row ordering while the
certificate child owns public certificate metadata and the expiration-specific UI choice.

Revision note: 2026-08-10 / Codex
Reopened for the fresh mutation-lifecycle review: added the open-Library configure refresh,
confirmation-gated Delete, explicit expiration-preference acceptance, and their required evidence so
the plan does not overstate completion.

Revision note: 2026-08-10 / Codex
Reconciled the post-implementation architecture review: expiration sorting is now described as a
completed dependency owned by the validity child, while this child records merged-row precedence and
preference propagation; no functional blocker was found.
