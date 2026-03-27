from pdf_signer.infra.config.schemas import SignaturePreset, TimestampPolicy, TrustProfile


def test_trust_profile_round_trip() -> None:
    original = TrustProfile(
        schema_version=1,
        use_system_store=True,
        extra_ca_bundle_path="/tmp/custom-ca.pem",
        revocation_mode="online",
    )

    payload = original.to_dict()
    reconstructed = TrustProfile.from_dict(payload)

    assert reconstructed == original


def test_timestamp_policy_round_trip() -> None:
    original = TimestampPolicy(
        schema_version=1,
        required=True,
        tsa_url="https://tsa.example.com",
        timeout_seconds=10,
    )

    payload = original.to_dict()
    reconstructed = TimestampPolicy.from_dict(payload)

    assert reconstructed == original


def test_signature_preset_round_trip() -> None:
    original = SignaturePreset(
        schema_version=1,
        name="default",
        show_common_name=True,
        show_email=False,
        show_signing_time=True,
        reason="Approved",
        location="Austin",
        datetime_format="%Y-%m-%d %H:%M:%S %Z",
    )

    payload = original.to_dict()
    reconstructed = SignaturePreset.from_dict(payload)

    assert reconstructed == original
