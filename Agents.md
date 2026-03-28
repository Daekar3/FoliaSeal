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
