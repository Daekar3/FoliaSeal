#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYINSTALLER_BIN="${PYINSTALLER_BIN:-$ROOT_DIR/.venv/bin/pyinstaller}"
SPEC_FILE="${SPEC_FILE:-$ROOT_DIR/pdf-signer.spec}"

if [[ ! -x "$PYINSTALLER_BIN" ]]; then
  echo "PyInstaller executable not found at: $PYINSTALLER_BIN" >&2
  echo "Install dev dependencies first, for example: .venv/bin/pip install -e .[dev]" >&2
  exit 1
fi

if [[ ! -f "$SPEC_FILE" ]]; then
  echo "Spec file not found at: $SPEC_FILE" >&2
  exit 1
fi

rm -rf "$ROOT_DIR/build/pdf-signer" "$ROOT_DIR/dist/pdf-signer"

"$PYINSTALLER_BIN" --noconfirm --clean "$SPEC_FILE"

echo
echo "PyInstaller build complete."
echo "Bundle directory: $ROOT_DIR/dist/pdf-signer"
echo "Executable: $ROOT_DIR/dist/pdf-signer/pdf-signer"
