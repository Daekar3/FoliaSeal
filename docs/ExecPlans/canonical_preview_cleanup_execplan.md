# Close exception-safe canonical preview cleanup

This ExecPlan is a living document and must be maintained in accordance with
`/home/daekar/.codex/skills/write-execplan/PLANS.md`. It is a behavior-plus-test
cleanup child of `docs/ExecPlans/ui_product_support_and_release_execplan.md`.

## Purpose / Big Picture

FoliaSeal renders canonical signature previews into temporary directories named
`foliaseal-canonical-preview-*`. The active UI and fit adapters normally own and
clean these directories, but evidence adapters only cleaned on their happy path,
and direct renderer tests left many roots after a full suite. After this slice,
an evidence-adapter exception cannot leak its temporary snapshot, and direct
renderer tests clean only the roots they create. Under the test-scoped cleanup
fixture, a full test run leaves no FoliaSeal-owned preview roots in `/tmp`, while
durable evidence images copied to
the requested artifacts directory remain available.

## Child ExecPlan Dependencies

- [x] `src/foliaseal/presentation/qt/preview_render_evidence_adapters.py`
  owns headless and Qt evidence snapshot cleanup.
- [x] Existing lifecycle and rendered-fit adapters establish explicit snapshot
  ownership and must not be regressed.
- [x] A full-suite run demonstrated the leak: many idle
  `foliaseal-canonical-preview-*` roots remained after pytest exited.

## Progress

- [x] (2026-08-16) Explorer review identified exception paths in both evidence
  adapters and direct renderer test consumers; eager renderer deletion was
  rejected because active consumers need the image path during capture.
- [x] (2026-08-16) Added wrapper-owned `try/finally` cleanup around Qt analysis
  snapshots and headless canonical snapshots, registering each snapshot as soon
  as it is created.
- [x] (2026-08-16) Added focused exception-regression tests for both adapters
  and an autouse `tests/conftest.py` fixture that removes only new
  canonical-preview roots from any direct renderer test.
- [x] (2026-08-16) Focused preview/evidence/parity validation passed (`67 passed`);
  the full suite passed (`1584 passed, 20 skipped, 1 warning`), Ruff and
  compileall passed, and `git diff --check` was clean. The final owned-root
  check printed nothing. The result is zero roots after test-scoped cleanup,
  backed by explicit renderer failure and adapter success/exception tests.
- [ ] Reconcile the release plans, commit the bounded cleanup slice, and verify
  the post-commit checkout.

## Surprises & Discoveries

- Observation: deleting the renderer directory immediately after return would
  break Qt lifecycle and raster-analysis consumers that still read `image_path`.
  Evidence: `QtCanonicalPreviewLifecycle`, rendered-fit adapters, and signed
  preview parity all consume the returned snapshot after rendering.
- Observation: the evidence adapters returned copied durable images but only
  called cleanup after successful analysis/projection assembly.
  Evidence: exceptions before the old cleanup line left the temporary root.
- Observation: direct unit tests intentionally inspect snapshots without a
  common ownership fixture, producing one root per render.
  Evidence: `tests/unit/test_signing_preview_renderer.py` calls the renderer
  dozens of times and the post-suite root count matched those calls.

## Decision Log

- Decision: clean evidence snapshots in public adapter wrappers with
  `try/finally`, registering the snapshot immediately after rendering.
  Rationale: this covers copy, analysis, projection, and payload exceptions
  without changing the snapshot lifetime for successful callers.
  Date/Author: 2026-08-16 / Codex.
- Decision: use a test-local fixture for direct renderer tests rather than a
  nondeterministic snapshot destructor or eager renderer deletion.
  Rationale: tests can prove exact root cleanup while production consumers keep
  explicit ownership and durable artifact paths remain valid.
  Date/Author: 2026-08-16 / Codex.

## Outcomes & Retrospective

Validation achieved exception-safe evidence capture, deterministic direct-test
cleanup, unchanged preview image behavior, and zero owned canonical-preview
roots after the full suite. Independent review required two follow-ups: scope
the renderer-failure assertion to roots created by that test, and prove that a
real copied artifact remains readable after adapter cleanup; both are now
covered by tests. The full-suite zero-root result is explicitly interpreted as
test-scoped cleanup plus the direct ownership tests, not as proof that every
consumer is intrinsically leak-free.

## Context and Orientation

`render_canonical_signature_preview()` in
`src/foliaseal/application/signing_preview_renderer.py` returns a snapshot whose
`image_path` points into a temporary directory. The snapshot must remain alive
until its consumer has copied or analyzed the image. The Qt and headless evidence
functions in `src/foliaseal/presentation/qt/preview_render_evidence_adapters.py`
are the correct boundaries for exception-safe cleanup. Their dependency bundle
already supplies `cleanup_canonical_preview_tempdir`, which deletes only the
known canonical-preview directory.

## Change Slice

The primary change class is cleanup behavior plus focused tests and plan
status. Allowed files are the evidence adapter, its existing unit test module,
`tests/unit/test_signing_preview_renderer.py`, this plan, and owning release
plan status entries. Do not alter signing output, preview geometry, schemas,
Qt product behavior, or Wayland support. Generated images and temporary roots
must not be committed.

## Plan of Work

Keep the public adapter functions as the ownership boundary. Have each wrapper
hold the snapshot in a small mutable holder, register it immediately after the
private capture body renders it, and call the dependency cleanup function in a
`finally` block. The private body must not delete the active UI snapshot or the
copied durable artifact. Add tests that force payload/analysis exceptions and
assert that the registered snapshot is cleaned. Add a test-local fixture around
direct renderer tests that records pre-existing roots and removes only new
roots after each test.

## Concrete Steps

Run from `/home/daekar/FoliaSeal`:

    .venv/bin/pytest -q tests/unit/test_preview_render_evidence_adapters.py tests/unit/test_signing_preview_renderer.py tests/integration/test_preview_signed_output_parity.py
    .venv/bin/ruff check src/foliaseal/presentation/qt/preview_render_evidence_adapters.py tests/unit/test_preview_render_evidence_adapters.py tests/unit/test_signing_preview_renderer.py
    .venv/bin/pytest -q
    find /tmp -maxdepth 1 -mindepth 1 -type d -name 'foliaseal-canonical-preview-*' -print
    git diff --check

The final `find` command must print nothing. If it finds roots, inspect that no
process owns them, remove only the verified FoliaSeal canonical-preview roots,
record the contradiction in `Progress`, and continue debugging rather than
claiming cleanup success.

## Validation and Acceptance

Focused adapter tests must prove cleanup on both success and exception paths,
preview parity must remain green, and the full suite must pass with no owned
canonical-preview root afterward. Ruff, compile checks, and diff checks must be
clean. A copied evidence image under a test artifact directory must remain
readable after the temporary snapshot root is removed.

## Idempotence and Recovery

The fixture is scoped to each renderer test and preserves roots that existed
before that test. Adapter cleanup is idempotent and ignores an already-removed
root. Never delete arbitrary `/tmp` entries; only remove paths whose basename
starts with `foliaseal-canonical-preview-` after verifying no process uses them.

## Artifacts and Notes

Commit only source/test/plan text. Do not commit generated images, PDFs,
credentials, packages, or temporary JSON. Record focused/full counts, the final
zero-root check, and the commit hash in `Progress` and `Outcomes`.

## Interfaces and Dependencies

Use the existing `PreviewRenderEvidenceDependencies.cleanup_canonical_preview_tempdir`
callback and Python `try/finally`; add no dependency. Preserve
`PreviewRenderEvidenceFrame` paths and the public adapter signatures. The
cleanup callback must receive the snapshot object, not a copied artifact path,
so it can enforce the existing canonical-prefix safety check.

Revision note: 2026-08-16 / Codex: created after the X11 audit-hardening loop's
full-suite closeout found repeated idle canonical-preview roots. The plan
separates evidence-adapter exception cleanup from direct renderer test cleanup
without changing preview/signing behavior.
