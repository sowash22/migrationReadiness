export type MigrationStage =
  | "intake"
  | "research"
  | "compatibility"
  | "gap_analysis"
  | "planning"
  | "awaiting_approval"
  | "validation"
  | "reporting"
  | "complete";

export type PaymentMethod =
  | "card"
  | "apple_pay"
  | "google_pay"
  | "shop_pay"
  | "klarna"
  | "afterpay"
  | "gift_card"
  | "boleto"
  | "sepa_debit";

export type MerchantConfig = {
  merchantId: string;
  displayName: string;
  commercePlatform: "shopify" | "woocommerce" | "custom";
  region: string;
  currencies: string[];
  oldIntegration: string;
  paymentMethods: PaymentMethod[];
  webhooks: string[];
  apiDependencies: string[];
  settings: {
    threeDsEnabled: boolean;
    webhookHmacConfigured: boolean;
    settlementCurrencies: string[];
    refundsApiVersion: string;
    payoutSchedule: string;
  };
};

export type CompatibilityFinding = {
  paymentMethod: PaymentMethod;
  status: "supported" | "unsupported" | "needs_remap";
  notes: string;
};

export type ApiDependencyFinding = {
  dependency: string;
  status: "compatible" | "upgrade_required" | "blocked";
  notes: string;
};

export type GapItem = {
  id: string;
  severity: "blocker" | "high" | "medium" | "low";
  area: string;
  description: string;
  remediation: string;
};

export type MigrationTask = {
  id: string;
  title: string;
  owner: string;
  dependsOn: string[];
  priority: "p0" | "p1" | "p2";
  status: "todo" | "in_progress" | "done";
};

export type ValidationCheck = {
  id: string;
  name: string;
  status: "pass" | "fail" | "retrying" | "skipped";
  attempts: number;
  detail: string;
};

export type ReadinessScore = {
  score: number;
  band: "not_ready" | "at_risk" | "ready";
  blockers: number;
  unsupportedMethods: number;
  failedChecks: number;
  summary: string;
};

export type MigrationState = {
  caseId: string;
  stage: MigrationStage;
  createdAt: string;
  updatedAt: string;
  intake?: {
    rawRequest: string;
    merchantHint: string;
    targetPlatform: string;
    goals: string[];
  };
  research?: {
    merchant: MerchantConfig;
    notes: string[];
  };
  compatibility?: {
    paymentMethods: CompatibilityFinding[];
    apiDependencies: ApiDependencyFinding[];
  };
  gaps?: GapItem[];
  plan?: {
    tasks: MigrationTask[];
    cutoverWindowHint: string;
  };
  approval?: {
    requested: boolean;
    approved: boolean;
    approvedAt?: string;
    note?: string;
  };
  validation?: {
    checks: ValidationCheck[];
    retriesUsed: number;
  };
  readiness?: ReadinessScore;
  reportPath?: string;
};
