# Beginner Setup Guide: Linux Mint 22.3 Development Environment

This guide walks you through setting up a **working local development environment** for the PDF signer project (Python 3.11+, PySide6, pyHanko, PyInstaller one-dir) on Linux Mint 22.3.

It assumes you have basic familiarity with VS Code only.

---

## 0) What you will install
You will install:
- system build tools and Python support packages,
- VS Code extensions for Python,
- a project-local virtual environment,
- project dependencies (`pyHanko`, `PySide6`, `PyInstaller`),
- optional quality tools (`pytest`, `ruff`, `mypy`),
- a basic run/build workflow.

---

## 1) Update your system first
Open Terminal (`Ctrl` + `Alt` + `T`) and run:

```bash
sudo apt update
sudo apt upgrade -y
```

Reboot if Mint asks you to.

---

## 2) Install required system packages
Run:

```bash
sudo apt install -y \
  python3 python3-venv python3-pip python3-dev \
  build-essential libssl-dev libffi-dev \
  git curl
```

What these are for:
- `python3`, `python3-venv`, `python3-pip`: Python + isolated env management.
- `python3-dev`, `build-essential`: compiling dependencies if needed.
- `libssl-dev`, `libffi-dev`: common crypto build deps.
- `git`: version control.

---

## 3) Verify Python version
Run:

```bash
python3 --version
```

You want Python 3.11+.

If it reports lower than 3.11, stop and install a 3.11+ interpreter before continuing.

---

## 4) Create a project folder
Choose a location (example `~/projects`):

```bash
mkdir -p ~/projects
cd ~/projects
mkdir foliaseal
cd foliaseal
```

---

## 5) Initialize Git (optional but recommended)
```bash
git init
```

---

## 6) Create and activate a virtual environment
From inside `~/projects/foliaseal`:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

When activated, your terminal prompt should show `(.venv)`.

> Every time you open a new terminal for this project, run:
> `source .venv/bin/activate`

---

## 7) Upgrade pip tools inside venv
```bash
python -m pip install --upgrade pip setuptools wheel
```

---

## 8) Install core project dependencies
```bash
pip install pyhanko pyside6 pyinstaller
```

Optional dev tooling (recommended):
```bash
pip install pytest ruff mypy
```

---

## 9) Verify the installed tools
```bash
python --version
pip --version
pyhanko --version
pyinstaller --version
```

If any command fails, check whether your virtual environment is activated.

---

## 10) Open project in VS Code
From project root:

```bash
code .
```

If `code` command is missing:
1. Open VS Code normally.
2. Press `Ctrl+Shift+P`.
3. Run: **Shell Command: Install 'code' command in PATH**.

---

## 11) Install VS Code extensions
In VS Code Extensions panel, install:
- **Python** (Microsoft)
- **Pylance** (Microsoft)
- **Ruff** (optional but recommended)

Then select interpreter:
1. `Ctrl+Shift+P`
2. **Python: Select Interpreter**
3. Choose: `.../foliaseal/.venv/bin/python`

---

## 12) Create starter project files
In project root, create this structure:

```text
foliaseal/
  .venv/
  src/foliaseal/
    __init__.py
    __main__.py
  tests/
```

Commands:

```bash
mkdir -p src/foliaseal tests
touch src/foliaseal/__init__.py
cat > src/foliaseal/__main__.py <<'PY'
print("FoliaSeal dev environment is working")
PY
```

Run it:

```bash
PYTHONPATH=src python -m foliaseal
# After `pip install -e .[dev]`, the same entry point is also available as:
foliaseal
```

(If module path errors occur, use the next section's editable install setup.)

---

## 13) Add minimal `pyproject.toml`
Create `pyproject.toml`:

```toml
[project]
name = "foliaseal"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "pyhanko",
  "pyside6",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy", "pyinstaller"]

[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"
```

Install project in editable mode:

```bash
pip install -e .[dev]
```

Now run:

```bash
foliaseal
```

(Replace your `__main__.py` content with package-based code as needed.)

---

## 14) Quick health checks
Run these in project root (with venv active):

```bash
python -c "import pyhanko, PySide6; print('Imports OK')"
pytest -q
ruff check .
```

`pytest` may report “no tests collected” initially—that is fine.

---

## 15) Create a basic `.gitignore`
```gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
build/
*.spec
```

---

## 16) First PyInstaller one-dir test
From project root:

```bash
pyinstaller --onedir --name foliaseal src/foliaseal/__main__.py
```

Expected output folder:
- `dist/foliaseal/`

Run the built executable:

```bash
./dist/foliaseal/foliaseal
```

If it prints your test message, packaging basics work.

---

## 17) Common beginner issues and fixes

## Problem: `pyhanko: command not found`
Fix:
- activate venv (`source .venv/bin/activate`) and retry.

## Problem: VS Code uses wrong Python
Fix:
- run **Python: Select Interpreter** and pick `.venv/bin/python`.

## Problem: Qt app fails with plugin errors
Fix:
- ensure PySide6 installed inside venv,
- verify PyInstaller spec collects Qt plugins,
- test on clean Mint VM after packaging.

## Problem: `pip install` build failures
Fix:
- ensure system deps from step 2 are installed,
- re-run `pip install --upgrade pip setuptools wheel`.

---

## 18) Daily workflow (simple)
Every coding session:

```bash
cd ~/projects/foliaseal
source .venv/bin/activate
code .
```

Before commits:

```bash
ruff check .
pytest -q
```

---

## 19) Next step after environment setup
Once the environment is working, implement in this order:
1. headless signing service (pyHanko integration),
2. PDF preview + mouse rectangle interaction in PySide6,
3. TSA and verification reporting,
4. PyInstaller one-dir release hardening.
