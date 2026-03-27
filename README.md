# PDF Signer

Foundations for a Linux desktop PDF signing app.

## What is included
- package skeleton with architecture-aligned module boundaries (`presentation`, `application`, `domain`, `infra`)
- `DocumentOperation` domain contract and operation registry with capability enable/disable flags
- initial config schemas for trust profile, timestamp policy, and signature presets
- Phase 1 headless signing orchestration (`SignPdfUseCase`) with:
  - compatibility policy enforcement for PDF `1.4` to `2.0`
  - incremental-signing version-preservation checks
  - stable failure-code mapping and structured signing results
  - temp-file + atomic replace output writes
- unit tests for schema validation, compatibility policy, operation registry behavior, and signing orchestration

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ruff check .
pytest -q
python -m pdf_signer
```
