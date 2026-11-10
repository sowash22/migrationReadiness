import type { MerchantConfig } from "./types.js";

const merchants: Record<string, MerchantConfig> = {
  ABC: {
    merchantId: "ABC",
    displayName: "Shopify Merchant ABC",
    commercePlatform: "shopify",
    region: "US+EU",
    currencies: ["USD", "EUR", "GBP"],
    oldIntegration: "legacy-shopify-payments-bridge",
    paymentMethods: [
      "card",
      "apple_pay",
      "shop_pay",
      "klarna",
      "gift_card",
      "boleto",
    ],
    webhooks: [
      "orders/paid",
      "refunds/create",
      "checkouts/create",
      "app/uninstalled",
    ],
    apiDependencies: [
      "Shopify Admin REST 2023-01",
      "Shopify Payments Apps API",
      "Checkout Extensibility",
      "Order Editing API",
    ],
    settings: {
      threeDsEnabled: false,
      webhookHmacConfigured: false,
      settlementCurrencies: ["USD"],
      refundsApiVersion: "2023-01",
      payoutSchedule: "weekly",
    },
  },
  ACME: {
    merchantId: "ACME",
    displayName: "WooCommerce Merchant ACME",
    commercePlatform: "woocommerce",
    region: "US",
    currencies: ["USD"],
    oldIntegration: "legacy-wc-gateway",
    paymentMethods: ["card", "apple_pay", "sepa_debit"],
    webhooks: ["order.completed", "refund.created"],
    apiDependencies: ["WooCommerce REST v3", "Payment Gateway API"],
    settings: {
      threeDsEnabled: true,
      webhookHmacConfigured: true,
      settlementCurrencies: ["USD"],
      refundsApiVersion: "v3",
      payoutSchedule: "daily",
    },
  },
};

export function listMerchants(): Array<{ merchantId: string; displayName: string }> {
  return Object.values(merchants).map((m) => ({
    merchantId: m.merchantId,
    displayName: m.displayName,
  }));
}

export function resolveMerchant(hint: string): MerchantConfig | null {
  const normalized = hint.trim().toUpperCase();
  if (merchants[normalized]) {
    return structuredClone(merchants[normalized]);
  }

  const byName = Object.values(merchants).find((m) =>
    m.displayName.toUpperCase().includes(normalized) ||
    m.merchantId.toUpperCase() === normalized ||
    hint.toUpperCase().includes(m.merchantId.toUpperCase()),
  );
  return byName ? structuredClone(byName) : null;
}

export function extractMerchantHint(text: string): string {
  const idMatch = text.match(/\bmerchant\s+([A-Za-z0-9_-]+)\b/i);
  if (idMatch?.[1]) {
    return idMatch[1];
  }
  const shopifyMatch = text.match(/\bShopify\s+merchant\s+([A-Za-z0-9_-]+)\b/i);
  if (shopifyMatch?.[1]) {
    return shopifyMatch[1];
  }
  for (const id of Object.keys(merchants)) {
    if (text.toUpperCase().includes(id)) {
      return id;
    }
  }
  return text.trim().slice(0, 64) || "UNKNOWN";
}
