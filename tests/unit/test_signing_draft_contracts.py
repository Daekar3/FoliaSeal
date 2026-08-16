from __future__ import annotations

import os
import subprocess
import sys

import pytest

from foliaseal.application.coordinate_transform import PageBox
from foliaseal.application.signing_draft_contracts import (
    SignaturePlacementContext,
    SigningDraftPreview,
    SigningDraftPreviewField,
    SigningDraftValidationError,
    SigningDraftValidationIssue,
    SigningDraftValidationSeverity,
)
from foliaseal.domain.models import SignatureFieldKey, SignatureFieldSource


def test_validation_contracts_preserve_defaults_and_error_formatting() -> None:
    issue = SigningDraftValidationIssue(code="missing", message="A value is required.")

    assert issue.severity is SigningDraftValidationSeverity.ERROR
    assert issue.field_name is None
    error = SigningDraftValidationError((issue,))
    assert error.issues == (issue,)
    assert str(error) == "A value is required."
    assert str(SigningDraftValidationError(())) == "Invalid draft."


@pytest.mark.parametrize(
    ("page_index", "rotation", "message"),
    [
        (True, 0, "page_index must be zero or greater."),
        (-1, 0, "page_index must be zero or greater."),
        (0, 45, "rotation must be a multiple of 90 degrees."),
    ],
)
def test_placement_context_preserves_validation_invariants(
    page_index: int,
    rotation: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        SignaturePlacementContext(
            page_index=page_index,
            page_box=PageBox(0, 0, 612, 792),
            rotation=rotation,
        )


def test_preview_contract_preserves_empty_optional_defaults() -> None:
    preview = SigningDraftPreview(
        title="Signature preview",
        page_index=None,
        signature_rect=None,
        signer_label_prefix=None,
        layout_template=None,
        stamp_position=None,
        timezone_display_mode=None,
        show_field_names=False,
        datetime_format=None,
        text_style=None,
        box_style=None,
        image_stamp_path=None,
        fields=(),
        detail_text="",
        issues=(),
        can_submit=False,
    )

    assert preview.fields == ()
    assert preview.issues == ()
    assert preview.stamp_text is None


def test_package_exports_resolve_contracts_without_duplicate_type_identity() -> None:
    import foliaseal.application as application

    assert application.SignaturePlacementContext is SignaturePlacementContext
    assert application.SigningDraftPreview is SigningDraftPreview
    assert application.SigningDraftPreviewField is SigningDraftPreviewField
    assert application.SigningDraftValidationError is SigningDraftValidationError
    assert application.SigningDraftValidationIssue is SigningDraftValidationIssue
    assert application.SigningDraftValidationSeverity is SigningDraftValidationSeverity


def test_preview_field_domain_values_remain_typed() -> None:
    from foliaseal.application.signing_draft_contracts import SigningDraftPreviewField

    field = SigningDraftPreviewField(
        field_key=SignatureFieldKey.COMMON_NAME,
        label="Signer",
        text="Morgan Ellery",
        visible=True,
        source=SignatureFieldSource.DERIVED,
    )

    assert field.field_key is SignatureFieldKey.COMMON_NAME
    assert field.source is SignatureFieldSource.DERIVED


def _subprocess_environment() -> dict[str, str]:
    return os.environ.copy()


@pytest.mark.parametrize("order", ["contracts_first", "semantics_first"])
def test_contract_import_firewall_and_cycle_orders(order: str) -> None:
    if order == "contracts_first":
        imports = "\n".join(
            (
                "import foliaseal.application.signing_draft_contracts as contracts",
                "import foliaseal.application.visible_signature_semantics as semantics",
                "import foliaseal.application.signing_draft_workflow as workflow",
            )
        )
    else:
        imports = "\n".join(
            (
                "import foliaseal.application.visible_signature_semantics as semantics",
                "import foliaseal.application.signing_draft_workflow as workflow",
                "import foliaseal.application.signing_draft_contracts as contracts",
            )
        )
    script = f"""
import sys
{imports}
assert semantics.SigningDraftValidationIssue is contracts.SigningDraftValidationIssue
assert not hasattr(workflow, 'SigningDraftValidationIssue')
assert not hasattr(workflow, 'SigningDraftValidationSeverity')
assert not hasattr(workflow, 'SigningDraftValidationError')
assert not hasattr(workflow, 'SignaturePlacementContext')
assert not hasattr(workflow, 'SigningDraftPreview')
assert not hasattr(workflow, 'SigningDraftPreviewField')
assert 'foliaseal.application.signing_draft_workflow' in sys.modules
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=_subprocess_environment(),
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_semantics_import_firewall_has_no_workflow_or_backend() -> None:
    script = """
import sys
import foliaseal.application.visible_signature_semantics
blocked = (
    'foliaseal.application.signing_draft_workflow',
    'foliaseal.application.signing_backend',
    'PyQt',
    'PySide6',
)
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
)
if loaded:
    raise SystemExit(','.join(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=_subprocess_environment(),
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_contract_module_isolation_subprocess() -> None:
    script = """
import sys
import foliaseal.application.signing_draft_contracts
blocked = (
    'foliaseal.application.signing_draft_workflow',
    'foliaseal.application.signing_backend',
    'PIL',
    'pyhanko',
    'PyQt',
    'PySide6',
)
loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + '.') for prefix in blocked)
)
if loaded:
    raise SystemExit(','.join(loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=_subprocess_environment(),
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
