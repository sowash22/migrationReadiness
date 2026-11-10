import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Generate and persist the final migration readiness report for the case.
    Writes a markdown artifact via host.files and marks the case complete.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    caseId: z.string(),
    executiveSummary: z
      .string()
      .describe("2-4 sentence executive summary for stakeholders."),
  }),
  async execute({ caseId, executiveSummary }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "reporting");
    if (!state.readiness) {
      throw new Error("Missing readiness score. Call validate_readiness first.");
    }

    const reportPath = `reports/${state.caseId}-migration-readiness.md`;
    const body = renderReport(state, executiveSummary);
    await ctx.host.files.write(reportPath, body, {
      scope: { kind: "deployment", partition: `migration-${state.caseId}` },
    });

    state.reportPath = reportPath;
    state.stage = "complete";
    const saved = await saveState(ctx, state);

    return {
      caseId: saved.caseId,
      stage: saved.stage,
      reportPath,
      readiness: saved.readiness,
      reportPreview: body.slice(0, 1200),
      nextStep: "Reply to the user with the readiness score, blockers, and report path.",
    };
  },
});

function renderReport(
  state: Awaited<ReturnType<typeof requireState>>,
  executiveSummary: string,
): string {
  const merchant = state.research?.merchant;
  const gaps = state.gaps ?? [];
  const tasks = state.plan?.tasks ?? [];
  const checks = state.validation?.checks ?? [];
  const readiness = state.readiness!;

  return `# Migration readiness report — ${state.caseId}

## Executive summary

${executiveSummary}

## Merchant

- **Id:** ${merchant?.merchantId ?? "unknown"}
- **Name:** ${merchant?.displayName ?? "unknown"}
- **Commerce platform:** ${merchant?.commercePlatform ?? "unknown"}
- **Old integration:** ${merchant?.oldIntegration ?? "unknown"}
- **Target:** ${state.intake?.targetPlatform ?? "new-payment-platform"}

## Readiness

- **Score:** ${readiness.score}/100
- **Band:** ${readiness.band}
- **Blockers:** ${readiness.blockers}
- **Unsupported methods:** ${readiness.unsupportedMethods}
- **Failed checks:** ${readiness.failedChecks}
- **Summary:** ${readiness.summary}

## Compatibility

### Payment methods
${(state.compatibility?.paymentMethods ?? [])
  .map((p) => `- ${p.paymentMethod}: **${p.status}** — ${p.notes}`)
  .join("\n") || "- none"}

### API dependencies
${(state.compatibility?.apiDependencies ?? [])
  .map((d) => `- ${d.dependency}: **${d.status}** — ${d.notes}`)
  .join("\n") || "- none"}

## Gaps
${gaps
  .map(
    (g) =>
      `- **[${g.severity}]** ${g.id} (${g.area}): ${g.description} → ${g.remediation}`,
  )
  .join("\n") || "- none"}

## Migration plan
${tasks
  .map(
    (t) =>
      `- ${t.id} [${t.priority}] ${t.title} (owner: ${t.owner}; depends: ${t.dependsOn.join(", ") || "—"})`,
  )
  .join("\n") || "- none"}

Cutover hint: ${state.plan?.cutoverWindowHint ?? "n/a"}

## Validation
${checks
  .map(
    (c) =>
      `- ${c.id}: **${c.status}** (attempts=${c.attempts}) — ${c.detail}`,
  )
  .join("\n") || "- none"}

Retries used: ${state.validation?.retriesUsed ?? 0}

## Approval

- Approved: ${state.approval?.approved ? "yes" : "no"}
- At: ${state.approval?.approvedAt ?? "n/a"}
- Note: ${state.approval?.note ?? "n/a"}

---
Generated at ${new Date().toISOString()}
`;
}
