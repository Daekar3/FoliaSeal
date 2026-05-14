"""Generate local signed acceptance assets under artifacts/."""

from __future__ import annotations

from foliaseal.application.qa_signed_acceptance_generation import (
    generate_signed_acceptance_assets,
)


def main() -> None:
    assets = generate_signed_acceptance_assets()
    for label, path in assets.as_dict().items():
        print(f"{label}: {path}")


if __name__ == "__main__":
    main()
