import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { extractMerchantHint } from "../lib/catalog.js";
import { platformName } from "../lib/platform.js";
import { createState, loadState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Start a payment migration case from the user's request.
    Extracts the merchant hint, records goals, and creates durable case state.
    Call this first for every new migration.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    request: z
      .string()
      .min(3)
      .describe("Full user request, e.g. Prepare Shopify merchant ABC for migration..."),
    caseId: z
      .string()
      .optional()
      .describe("Optional stable case id. Defaults to the resolved merchant id."),
    goals: z
      .array(z.string())
      .optional()
      .describe("Optional explicit migration goals."),
  }),
  async execute({ request, caseId, goals }, ctx) {
    const merchantHint = extractMerchantHint(request);
    const id = (caseId ?? merchantHint).toUpperCase();
    const existing = await loadState(ctx, id);
    const state = existing ?? (await createState(ctx, id));
    state.intake = {
      rawRequest: request,
      merchantHint,
      targetPlatform: platformName(),
      goals:
        goals && goals.length > 0
          ? goals
          : [
              "Inventory current payment integration",
              "Identify unsupported methods and missing config",
              "Produce a migration plan with readiness score",
            ],
    };
    state.stage = "intake";
    const saved = await saveState(ctx, state);
    return {
      caseId: saved.caseId,
      stage: saved.stage,
      merchantHint: saved.intake?.merchantHint,
      targetPlatform: saved.intake?.targetPlatform,
      goals: saved.intake?.goals,
      nextStep: "Delegate to intake subagent if needed, then call research_merchant.",
    };
  },
});
