import pytest

from foliaseal.application.fidelity_contract import (
    RELEASE_FIDELITY_CONTRACT_VERSION,
    RELEASE_FIDELITY_CRITICAL_ZERO_COUNTERS,
    validate_release_fidelity_contract,
)


def _payload() -> dict[str, object]:
    return {
        "manifest_version": 1,
        "comparison_contract": {
            "version": RELEASE_FIDELITY_CONTRACT_VERSION,
            "critical_zero_counters": list(RELEASE_FIDELITY_CRITICAL_ZERO_COUNTERS),
            "tolerances": {"preview_vs_output": 0},
        },
        "scenarios": [
            {
                "name": "one",
                "expected_outcome": "success",
                "expected_diagnostics": {"outcome": "signable"},
            }
        ],
    }


def test_release_fidelity_contract_accepts_versioned_manifest() -> None:
    validate_release_fidelity_contract(_payload())


@pytest.mark.parametrize(
    "mutator",
    [
        lambda payload: payload.update({"manifest_version": 2}),
        lambda payload: payload["comparison_contract"].update({"version": "old"}),
        lambda payload: payload["comparison_contract"].update(
            {"tolerances": {"preview_vs_output": 1}}
        ),
        lambda payload: payload["scenarios"][0].pop("expected_outcome"),
        lambda payload: payload["scenarios"][0].pop("expected_diagnostics"),
    ],
)
def test_release_fidelity_contract_rejects_unversioned_or_incomplete_payload(mutator) -> None:
    payload = _payload()
    mutator(payload)

    with pytest.raises(ValueError):
        validate_release_fidelity_contract(payload)
