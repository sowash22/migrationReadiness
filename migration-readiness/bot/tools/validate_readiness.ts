import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { runValidationSuite } from "../lib/platform.js";
import { computeReadiness } from "../lib/readiness.js";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Run migration validation checks with automatic retries for transient failures.
    Computes a readiness score. Requires an approved plan.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    caseId: z.string(),
    maxRetries: z
      .number()
      .int()
      .min(1)
      .max(5)
      .optional()
      .describe("Max attempts for flaky checks. Default 3."),
  }),
  async execute({ caseId, maxRetries }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "validation");
    if (!state.approval?.approved) {
      throw new Error(
        "Cutover is not approved. Call request_cutover_approval and wait for human approval.",
      );
    }
    const merchant = state.research?.merchant;
    const gaps = state.gaps ?? [];
    const paymentMethods = state.compatibility?.paymentMethods ?? [];
    if (!merchant) {
      throw new Error("Missing merchant research.");
    }

    const { checks, retriesUsed } = await runValidationSuite({
      merchant,
      gaps,
      maxRetries,
    });
    const readiness = computeReadiness({
      gaps,
      paymentMethods,
      checks,
      approved: true,
    });

    state.validation = { checks, retriesUsed };
    state.readiness = readiness;
    state.stage = "reporting";
    const saved = await saveState(ctx, state);

    return {
      caseId: saved.caseId,
      stage: saved.stage,
      checks,
      retriesUsed,
      readiness,
      nextStep: "Call publish_report to write the final migration report.",
    };
  },
});
