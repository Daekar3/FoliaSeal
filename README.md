# PDF Signer

Phase 0 foundations for a Linux desktop PDF signing app.

## What is included
- package skeleton with architecture-aligned module boundaries (`presentation`, `application`, `domain`, `infra`)
- `DocumentOperation` domain contract and operation registry with capability enable/disable flags
- initial config schemas for trust profile, timestamp policy, and signature presets
- unit tests for schema round-trip serialization and operation registry behavior
- baseline CI workflow with lint, tests, and packaging smoke stub

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
ruff check .
pytest -q
python -m pdf_signer
```
