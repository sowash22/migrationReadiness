import type {
  GapItem,
  ReadinessScore,
  ValidationCheck,
  CompatibilityFinding,
} from "./types.js";

export function computeReadiness(args: {
  gaps: GapItem[];
  paymentMethods: CompatibilityFinding[];
  checks: ValidationCheck[];
  approved: boolean;
}): ReadinessScore {
  const blockers = args.gaps.filter((g) => g.severity === "blocker").length;
  const highs = args.gaps.filter((g) => g.severity === "high").length;
  const unsupportedMethods = args.paymentMethods.filter(
    (p) => p.status === "unsupported",
  ).length;
  const failedChecks = args.checks.filter((c) => c.status === "fail").length;
  const passedChecks = args.checks.filter((c) => c.status === "pass").length;

  let score = 100;
  score -= blockers * 20;
  score -= highs * 8;
  score -= unsupportedMethods * 10;
  score -= failedChecks * 12;
  score += Math.min(10, passedChecks * 2);
  if (!args.approved) {
    score -= 15;
  }
  score = Math.max(0, Math.min(100, score));

  const band =
    score >= 80 && blockers === 0 && failedChecks === 0
      ? "ready"
      : score >= 55
        ? "at_risk"
        : "not_ready";

  const summary =
    band === "ready"
      ? "Merchant is ready for cutover after final monitoring setup."
      : band === "at_risk"
        ? "Merchant can proceed only after closing remaining high-risk gaps."
        : "Merchant is not ready; resolve blockers before validation sign-off.";

  return {
    score,
    band,
    blockers,
    unsupportedMethods,
    failedChecks,
    summary,
  };
}
