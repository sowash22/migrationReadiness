import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { resolveMerchant } from "../lib/catalog.js";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Collect merchant integration details from the catalog for an intake case.
    Returns payment methods, webhooks, API dependencies, and settings.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    caseId: z.string().describe("Migration case id from intake_merchant."),
  }),
  async execute({ caseId }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "intake");
    const hint = state.intake?.merchantHint ?? caseId;
    const merchant = resolveMerchant(hint);
    if (!merchant) {
      throw new Error(
        `No merchant catalog entry for "${hint}". Known demos: ABC, ACME.`,
      );
    }

    state.research = {
      merchant,
      notes: [
        `Old integration: ${merchant.oldIntegration}`,
        `Commerce platform: ${merchant.commercePlatform}`,
        `Region: ${merchant.region}`,
      ],
    };
    state.stage = "research";
    const saved = await saveState(ctx, state);
    return {
      caseId: saved.caseId,
      stage: saved.stage,
      merchant: saved.research?.merchant,
      notes: saved.research?.notes,
      nextStep: "Call check_compatibility (optionally after compatibility subagent).",
    };
  },
});
