from __future__ import annotations

import copy
import re

from migration_readiness.types import MerchantConfig, MerchantSettings

_MERCHANTS: dict[str, MerchantConfig] = {
    "ABC": MerchantConfig(
        merchant_id="ABC",
        display_name="Shopify Merchant ABC",
        commerce_platform="shopify",
        region="US+EU",
        currencies=["USD", "EUR", "GBP"],
        old_integration="legacy-shopify-payments-bridge",
        payment_methods=[
            "card",
            "apple_pay",
            "shop_pay",
            "klarna",
            "gift_card",
            "boleto",
        ],
        webhooks=[
            "orders/paid",
            "refunds/create",
            "checkouts/create",
            "app/uninstalled",
        ],
        api_dependencies=[
            "Shopify Admin REST 2023-01",
            "Shopify Payments Apps API",
            "Checkout Extensibility",
            "Order Editing API",
        ],
        settings=MerchantSettings(
            three_ds_enabled=False,
            webhook_hmac_configured=False,
            settlement_currencies=["USD"],
            refunds_api_version="2023-01",
            payout_schedule="weekly",
        ),
    ),
    "ACME": MerchantConfig(
        merchant_id="ACME",
        display_name="WooCommerce Merchant ACME",
        commerce_platform="woocommerce",
        region="US",
        currencies=["USD"],
        old_integration="legacy-wc-gateway",
        payment_methods=["card", "apple_pay", "sepa_debit"],
        webhooks=["order.completed", "refund.created"],
        api_dependencies=["WooCommerce REST v3", "Payment Gateway API"],
        settings=MerchantSettings(
            three_ds_enabled=True,
            webhook_hmac_configured=True,
            settlement_currencies=["USD"],
            refunds_api_version="v3",
            payout_schedule="daily",
        ),
    ),
}


def list_merchants() -> list[dict[str, str]]:
    return [
        {"merchant_id": m.merchant_id, "display_name": m.display_name}
        for m in _MERCHANTS.values()
    ]


def resolve_merchant(hint: str) -> MerchantConfig | None:
    normalized = hint.strip().upper()
    if normalized in _MERCHANTS:
        return copy.deepcopy(_MERCHANTS[normalized])

    upper = hint.upper()
    for merchant in _MERCHANTS.values():
        if (
            merchant.merchant_id in upper
            or merchant.display_name.upper() in upper
            or upper in merchant.display_name.upper()
        ):
            return copy.deepcopy(merchant)
    return None


def extract_merchant_hint(text: str) -> str:
    match = re.search(r"\bmerchant\s+([A-Za-z0-9_-]+)\b", text, flags=re.I)
    if match:
        return match.group(1)
    shopify = re.search(
        r"\bShopify\s+merchant\s+([A-Za-z0-9_-]+)\b", text, flags=re.I
    )
    if shopify:
        return shopify.group(1)
    upper = text.upper()
    for merchant_id in _MERCHANTS:
        if merchant_id in upper:
            return merchant_id
    return (text.strip()[:64] or "UNKNOWN")
