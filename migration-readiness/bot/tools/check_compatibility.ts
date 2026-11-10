import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import {
  checkApiDependencies,
  checkPaymentCompatibility,
} from "../lib/platform.js";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Check payment methods and API dependencies against the new payment platform.
    Requires research_merchant to have completed.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    caseId: z.string(),
  }),
  async execute({ caseId }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "research");
    const merchant = state.research?.merchant;
    if (!merchant) {
      throw new Error("Missing research.merchant. Call research_merchant first.");
    }

    const paymentMethods = checkPaymentCompatibility(merchant);
    const apiDependencies = checkApiDependencies(merchant);
    state.compatibility = { paymentMethods, apiDependencies };
    state.stage = "compatibility";
    const saved = await saveState(ctx, state);

    return {
      caseId: saved.caseId,
      stage: saved.stage,
      paymentMethods,
      apiDependencies,
      unsupported: paymentMethods.filter((p) => p.status === "unsupported"),
      upgradeRequired: apiDependencies.filter((d) => d.status === "upgrade_required"),
      nextStep: "Call analyze_gaps after the gap-analysis subagent reviews findings.",
    };
  },
});
