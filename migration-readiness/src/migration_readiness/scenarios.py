from __future__ import annotations

from typing import TypedDict


class Scenario(TypedDict):
    id: str
    title: str
    request: str
    expected_band: str
    expected_stage: str
    summary: str


SCENARIOS: list[Scenario] = [
    {
        "id": "ABC",
        "title": "Not ready — blockers",
        "request": "Prepare Shopify merchant ABC for migration to the new payment integration.",
        "expected_band": "not_ready",
        "expected_stage": "complete",
        "summary": "Unsupported boleto, missing HMAC, missing 3DS.",
    },
    {
        "id": "RISK",
        "title": "At risk — remediations needed",
        "request": "Prepare merchant RISK for migration to the new payment integration.",
        "expected_band": "at_risk",
        "expected_stage": "complete",
        "summary": "No blockers, but gift-card/afterpay remap, API upgrade, settlement gaps.",
    },
    {
        "id": "ACME",
        "title": "Ready — clean cutover",
        "request": "Prepare WooCommerce merchant ACME for migration to the new payment integration.",
        "expected_band": "ready",
        "expected_stage": "complete",
        "summary": "Supported methods, HMAC + 3DS configured, validation passes.",
    },
    {
        "id": "UNKNOWN",
        "title": "Fails early — unknown merchant",
        "request": "andrew",
        "expected_band": "n/a",
        "expected_stage": "error",
        "summary": "Rejected at intake; demo catalog only has ABC, RISK, ACME.",
    },
]


def scenarios_for_api() -> list[dict[str, str]]:
    return [dict(s) for s in SCENARIOS]
