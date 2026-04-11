"""Stress fixture data for preview-matrix and harness validation.

These values intentionally mimic the length and punctuation pressure of
real-world signing identities without embedding any user-specific strings in
the repository.
"""

from __future__ import annotations

from dataclasses import replace

from foliaseal.domain.models import (
    SignatureAppearance,
    SignatureFieldBinding,
    SignatureFieldKey,
    SignatureFieldSource,
)

STRESS_VISIBLE_APPEARANCE_PROFILE = "stress_visible_appearance_v1"

STRESS_VISIBLE_APPEARANCE_VALUES: dict[SignatureFieldKey, str] = {
    SignatureFieldKey.COMMON_NAME: "Morgan Ellery",
    SignatureFieldKey.EMAIL: "records.operations@northwindledger.org",
    SignatureFieldKey.TITLE: "Corporate Records Secretary",
    SignatureFieldKey.COMPANY: "Northwind Ledger Holdings",
    SignatureFieldKey.LOCATION: "Charlottesville, Virginia, United States",
    SignatureFieldKey.REASON: "Approved for board circulation",
}


def apply_preview_stress_fixture_profile(
    *,
    appearance: SignatureAppearance,
    profile_name: str,
) -> SignatureAppearance:
    """Apply a checked-in stress fixture profile to a signature appearance."""

    if profile_name != STRESS_VISIBLE_APPEARANCE_PROFILE:
        raise ValueError(f"Unknown preview stress fixture profile: {profile_name}")

    updates: dict[str, SignatureFieldBinding] = {}
    for field_key, value in STRESS_VISIBLE_APPEARANCE_VALUES.items():
        binding = appearance.binding_for(field_key)
        updates[field_key.value] = replace(
            binding,
            source=SignatureFieldSource.OVERRIDE,
            show_in_visible_appearance=True,
            override_text=value,
        )
    return replace(appearance, **updates)
