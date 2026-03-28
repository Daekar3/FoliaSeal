## Platform Scope (Hard Constraint)
This project is Linux-only for current scope (target: Linux Mint 22.3 / Ubuntu-compatible runtime).

### Out of scope by default
- macOS compatibility work
- Windows compatibility work
- Cross-platform packaging/CI expansion
- Platform-abstraction refactors motivated by non-Linux support

If a request implies non-Linux support, stop and request explicit approval before proposing or implementing changes.

## Scope Gate for Proposed Work
Only propose work that directly improves the Linux PDF viewing/signing flow defined in `pdf_signing_app_feasibility.md`.

Before suggesting changes, verify:
1. Linux user value is immediate and clear.
2. No new non-Linux conditionals/dependencies are introduced.
3. Packaging/testing remains Linux-targeted.

If not, mark as “Out of current scope (defer).”

## Legacy Non-Linux References
Existing non-Linux comments/code paths are not roadmap commitments.
Do not expand them. When touching adjacent code, prefer Linux-only simplification.  
When practical, refactor to remove existing non-Linux comments/code paths.

## Scope & Delivery Guardrails (v1)

### 1) v1 Capability Allowlist (hard scope)
Only capabilities directly in support of requirements in `pdf_signing_app_feasibility.md` are in scope for v1.

Any capability not in direct support of the goal in `pdf_signing_app_feasibility.md` is out of scope unless explicitly approved by the project owner.

---

### 2) Non-Goals (defer by default)
The following are deferred and must not be proposed/implemented without explicit owner approval:
- macOS support
- Windows support
- Cross-platform packaging/CI expansion
- Non-signing PDF editing features (reorder/crop/delete/merge/etc.)
- Plugin architecture or extensibility frameworks
- Auto PDF/A or PDF/UA conversion/remediation
- New “nice-to-have” UX customization not required for v1 functional goals
- New remote/cloud/account integrations

---

### 3) Complexity Budget (simplicity-first)
- Prefer the simplest direct implementation that satisfies current requirements.
- Do not add abstraction layers unless there are at least two real, current use cases.
- Do not refactor for speculative future needs.
- Every non-trivial PR must include a brief note: “Why this is the simplest viable approach.”

---

### 4) Dependency & Stack Control
- Treat the current stack as locked unless a blocker requires change.
- No new runtime dependency without explicit justification tied to an in-scope requirement.
- Pin dependency versions.
- Dependency upgrades are allowed only for security, correctness, or blocker fixes.
- Avoid bundling/tooling churn unless required to keep Linux release stability.

---

### 5) Reliability-First Rule
When tradeoffs exist, choose in this order:
1. Correct signing output
2. Data safety / non-destructive behavior
3. Deterministic failure with explicit diagnostics
4. Operational stability
5. UX polish

Additional reliability constraints:
- Signing flow remains incremental-update oriented.
- Never silently “repair” or rewrite in ways that risk signature integrity.
- Prefer explicit, user-visible errors over hidden fallback behavior.

---

### 6) PR Acceptance Gate (minimum required)
A PR is not ready unless all are true:
- Change is within v1 allowlist scope.
- Unit/integration coverage exists for changed behavior.
- No unintended behavior change in signing flow.
- Error handling is explicit and testable.
- Linux runtime/packaging impact is documented (if any).
- No new deferred-scope features are introduced.

---

### 7) No Silent Behavior Changes
- Any change to signing, compatibility, security, or file-write behavior must be documented in PR notes.
- If user-visible flow changes, update docs/checklists in the same PR.
- Hidden behavior changes are not allowed.

---

### 8) Phase Discipline (focus protection)
- Work must map to current-phase goals and exit criteria.
- If a proposal belongs to a later phase, label it “Deferred backlog” and do not implement now.
- Do not mix stabilization/fix work with feature expansion in a single PR unless explicitly approved.

---

## Fast Triage Rule for New Requests
Before implementing any request, answer:
1. Is it in the v1 capability allowlist?
2. Does it keep Linux-only scope intact?
3. Does it preserve simplicity and reliability?
4. Does it avoid deferred non-goals?

If any answer is “No”, stop and request owner approval or mark as deferred.
