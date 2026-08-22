"""Guard the Qt presentation layer against schema vocabulary leaking into ordinary UI copy."""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]
QT_PRESENTATION_ROOT = REPOSITORY_ROOT / "src" / "foliaseal" / "presentation" / "qt"
USER_FACING_APPLICATION_MODULES = (
    REPOSITORY_ROOT / "src" / "foliaseal" / "application" / "certificate_models.py",
    REPOSITORY_ROOT / "src" / "foliaseal" / "application" / "certificate_readiness.py",
    REPOSITORY_ROOT / "src" / "foliaseal" / "application" / "signature_properties_coordinator.py",
    REPOSITORY_ROOT / "src" / "foliaseal" / "application" / "signing_material_resolver.py",
    REPOSITORY_ROOT / "src" / "foliaseal" / "application" / "signing_readiness.py",
)
FORBIDDEN_UI_TERMS = re.compile(
    r"(?:certificate\s+configuration|managed\s+certificate|pkcs#12\s+object|"
    r"appearance\s+profile|placement\s+profile)",
    re.IGNORECASE,
)
TECHNICAL_DIAGNOSTIC_ALLOWLIST = {
    "Field 'certificate_configurations' must not contain duplicate managed certificate references."
}


def _docstring_nodes(tree: ast.AST) -> set[int]:
    nodes: set[int] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body or not isinstance(body[0], ast.Expr):
            continue
        value = body[0].value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            nodes.add(id(value))
    return nodes


def _ui_string_values(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docstrings = _docstring_nodes(tree)
    values: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if id(node) not in docstrings:
                values.append((node.lineno, node.value))
        elif isinstance(node, ast.JoinedStr):
            literal = "".join(
                part.value for part in node.values if isinstance(part, ast.Constant)
            )
            if literal:
                values.append((node.lineno, literal))
    return values


def test_qt_presentation_strings_use_approved_user_vocabulary() -> None:
    violations: list[str] = []
    paths = [*sorted(QT_PRESENTATION_ROOT.glob("*.py")), *USER_FACING_APPLICATION_MODULES]
    for path in paths:
        for line_number, value in _ui_string_values(path):
            if FORBIDDEN_UI_TERMS.search(value) and value not in TECHNICAL_DIAGNOSTIC_ALLOWLIST:
                relative_path = path.relative_to(REPOSITORY_ROOT)
                violations.append(f"{relative_path}:{line_number}: {value}")
    assert not violations, "Forbidden schema terminology remains in Qt UI copy:\n" + "\n".join(
        violations
    )
