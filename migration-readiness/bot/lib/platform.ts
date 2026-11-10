import type {
  ApiDependencyFinding,
  CompatibilityFinding,
  GapItem,
  MerchantConfig,
  MigrationTask,
  PaymentMethod,
  ValidationCheck,
} from "./types.js";

const NEW_PLATFORM = {
  name: "new-payment-platform",
  supportedMethods: new Set<PaymentMethod>([
    "card",
    "apple_pay",
    "google_pay",
    "shop_pay",
    "klarna",
    "afterpay",
    "sepa_debit",
  ]),
  remap: {
    gift_card: {
      status: "needs_remap" as const,
      notes: "Map Shopify gift cards to platform stored-value wallets before cutover.",
    },
    boleto: {
      status: "unsupported" as const,
      notes: "Boleto is not available on the new platform. Offer Pix or remove LATAM boleto checkout.",
    },
  } as Partial<
    Record<PaymentMethod, { status: "needs_remap" | "unsupported"; notes: string }>
  >,
  requiredSettings: {
    threeDsForEea: true,
    webhookHmac: true,
    minRefundsApi: "2024-10",
  },
};

export function platformName(): string {
  return NEW_PLATFORM.name;
}

export function checkPaymentCompatibility(
  merchant: MerchantConfig,
): CompatibilityFinding[] {
  return merchant.paymentMethods.map((paymentMethod) => {
    const remap = NEW_PLATFORM.remap[paymentMethod];
    if (remap) {
      return { paymentMethod, status: remap.status, notes: remap.notes };
    }
    if (NEW_PLATFORM.supportedMethods.has(paymentMethod)) {
      return {
        paymentMethod,
        status: "supported",
        notes: "Available on the new payment platform.",
      };
    }
    return {
      paymentMethod,
      status: "unsupported",
      notes: "Not listed in the new platform catalog.",
    };
  });
}

export function checkApiDependencies(
  merchant: MerchantConfig,
): ApiDependencyFinding[] {
  return merchant.apiDependencies.map((dependency) => {
    if (/2023-01/i.test(dependency)) {
      return {
        dependency,
        status: "upgrade_required",
        notes: "Upgrade to Admin API 2024-10 or later before enabling the new payments app.",
      };
    }
    if (/Order Editing/i.test(dependency)) {
      return {
        dependency,
        status: "compatible",
        notes: "Order editing continues to work through the new capture/refund APIs.",
      };
    }
    if (/Payments Apps API|Checkout Extensibility|WooCommerce REST|Payment Gateway API/i.test(dependency)) {
      return {
        dependency,
        status: "compatible",
        notes: "Compatible with the new integration adapters.",
      };
    }
    return {
      dependency,
      status: "compatible",
      notes: "No known blocker.",
    };
  });
}

export function analyzeGaps(args: {
  merchant: MerchantConfig;
  paymentMethods: CompatibilityFinding[];
  apiDependencies: ApiDependencyFinding[];
}): GapItem[] {
  const gaps: GapItem[] = [];

  for (const finding of args.paymentMethods) {
    if (finding.status === "unsupported") {
      gaps.push({
        id: `pay-${finding.paymentMethod}`,
        severity: "blocker",
        area: "payment_methods",
        description: `${finding.paymentMethod} is unsupported on the new platform.`,
        remediation: finding.notes,
      });
    } else if (finding.status === "needs_remap") {
      gaps.push({
        id: `pay-${finding.paymentMethod}`,
        severity: "high",
        area: "payment_methods",
        description: `${finding.paymentMethod} needs remapping.`,
        remediation: finding.notes,
      });
    }
  }

  for (const dep of args.apiDependencies) {
    if (dep.status === "upgrade_required") {
      gaps.push({
        id: `api-${dep.dependency.replace(/\s+/g, "-").toLowerCase()}`,
        severity: "high",
        area: "api_dependencies",
        description: `${dep.dependency} must be upgraded.`,
        remediation: dep.notes,
      });
    } else if (dep.status === "blocked") {
      gaps.push({
        id: `api-${dep.dependency.replace(/\s+/g, "-").toLowerCase()}`,
        severity: "blocker",
        area: "api_dependencies",
        description: `${dep.dependency} blocks migration.`,
        remediation: dep.notes,
      });
    }
  }

  if (!args.merchant.settings.webhookHmacConfigured) {
    gaps.push({
      id: "cfg-webhook-hmac",
      severity: "blocker",
      area: "configuration",
      description: "Webhook HMAC signing secret is not configured.",
      remediation: "Generate and store a platform webhook signing secret before go-live.",
    });
  }

  if (
    !args.merchant.settings.threeDsEnabled &&
    /EU|EEA|UK|GBP|EUR/i.test(
      `${args.merchant.region} ${args.merchant.currencies.join(" ")}`,
    )
  ) {
    gaps.push({
      id: "cfg-3ds",
      severity: "blocker",
      area: "configuration",
      description: "3-D Secure is disabled for an EEA-facing merchant.",
      remediation: "Enable 3DS / SCA for card payments in EU/UK markets.",
    });
  }

  const missingSettlement = args.merchant.currencies.filter(
    (c) => !args.merchant.settings.settlementCurrencies.includes(c),
  );
  if (missingSettlement.length > 0) {
    gaps.push({
      id: "cfg-settlement",
      severity: "high",
      area: "configuration",
      description: `Settlement currencies missing: ${missingSettlement.join(", ")}.`,
      remediation: "Add settlement accounts for every storefront currency.",
    });
  }

  if (args.merchant.settings.refundsApiVersion < "2024-10") {
    gaps.push({
      id: "cfg-refunds-api",
      severity: "medium",
      area: "configuration",
      description: `Refunds API version ${args.merchant.settings.refundsApiVersion} is below the required 2024-10 baseline.`,
      remediation: "Bump refunds API version and retest partial refunds.",
    });
  }

  return gaps;
}

export function buildMigrationPlan(args: {
  merchant: MerchantConfig;
  gaps: GapItem[];
}): { tasks: MigrationTask[]; cutoverWindowHint: string } {
  const tasks: MigrationTask[] = [
    {
      id: "T1",
      title: "Provision new-platform merchant account and API keys",
      owner: "payments-platform",
      dependsOn: [],
      priority: "p0",
      status: "todo",
    },
    {
      id: "T2",
      title: "Connect commerce store and install payments app",
      owner: "merchant-engineering",
      dependsOn: ["T1"],
      priority: "p0",
      status: "todo",
    },
  ];

  for (const gap of args.gaps) {
    tasks.push({
      id: `G-${gap.id}`,
      title: gap.remediation,
      owner: gap.area === "configuration" ? "merchant-ops" : "merchant-engineering",
      dependsOn: ["T2"],
      priority: gap.severity === "blocker" || gap.severity === "high" ? "p0" : "p1",
      status: "todo",
    });
  }

  tasks.push(
    {
      id: "T3",
      title: "Run sandbox authorization, capture, and refund suite",
      owner: "qa",
      dependsOn: tasks.filter((t) => t.id.startsWith("G-")).map((t) => t.id),
      priority: "p0",
      status: "todo",
    },
    {
      id: "T4",
      title: "Schedule dual-run cutover and monitoring window",
      owner: "migration-pm",
      dependsOn: ["T3"],
      priority: "p1",
      status: "todo",
    },
  );

  const hasBlockers = args.gaps.some((g) => g.severity === "blocker");
  return {
    tasks,
    cutoverWindowHint: hasBlockers
      ? "Do not schedule cutover until every blocker gap is closed and approval is granted."
      : `Propose a low-traffic cutover window for ${args.merchant.displayName} after sandbox validation passes.`,
  };
}

export async function runValidationSuite(args: {
  merchant: MerchantConfig;
  gaps: GapItem[];
  maxRetries?: number;
}): Promise<{ checks: ValidationCheck[]; retriesUsed: number }> {
  const maxRetries = args.maxRetries ?? 3;
  const openBlockers = args.gaps.filter((g) => g.severity === "blocker");
  const checks: ValidationCheck[] = [];
  let retriesUsed = 0;

  checks.push({
    id: "cfg-hmac",
    name: "Webhook HMAC configured",
    status: args.merchant.settings.webhookHmacConfigured ||
        !openBlockers.some((g) => g.id === "cfg-webhook-hmac")
      ? "pass"
      : "fail",
    attempts: 1,
    detail: args.merchant.settings.webhookHmacConfigured
      ? "HMAC secret present."
      : "HMAC secret still missing.",
  });

  // Simulate a flaky webhook probe that recovers with retries.
  let webhookAttempts = 0;
  let webhookStatus: ValidationCheck["status"] = "fail";
  let webhookDetail = "Webhook endpoint unreachable.";
  while (webhookAttempts < maxRetries) {
    webhookAttempts += 1;
    retriesUsed += webhookAttempts > 1 ? 1 : 0;
    const flakyFail = webhookAttempts < 2;
    if (flakyFail) {
      webhookStatus = "retrying";
      webhookDetail = `Transient timeout on attempt ${webhookAttempts}.`;
      await delay(5);
      continue;
    }
    webhookStatus = "pass";
    webhookDetail = `Webhook challenge succeeded on attempt ${webhookAttempts}.`;
    break;
  }
  checks.push({
    id: "webhook-challenge",
    name: "Webhook challenge/response",
    status: webhookStatus === "retrying" ? "fail" : webhookStatus,
    attempts: webhookAttempts,
    detail: webhookDetail,
  });

  const unsupportedOpen = openBlockers.some((g) => g.area === "payment_methods");
  checks.push({
    id: "methods",
    name: "Unsupported payment methods cleared",
    status: unsupportedOpen ? "fail" : "pass",
    attempts: 1,
    detail: unsupportedOpen
      ? "Blocker payment methods remain enabled on the storefront."
      : "No unsupported methods remain as blockers.",
  });

  checks.push({
    id: "auth-capture",
    name: "Sandbox auth + capture",
    status: openBlockers.length > 0 ? "skipped" : "pass",
    attempts: 1,
    detail:
      openBlockers.length > 0
        ? "Skipped while blockers remain."
        : "Sandbox card auth and capture succeeded.",
  });

  return { checks, retriesUsed };
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
