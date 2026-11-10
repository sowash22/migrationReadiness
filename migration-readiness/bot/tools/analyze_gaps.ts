import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { analyzeGaps } from "../lib/platform.js";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Identify missing configurations and migration blockers from compatibility findings.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    caseId: z.string(),
  }),
  async execute({ caseId }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "compatibility");
    const merchant = state.research?.merchant;
    const compatibility = state.compatibility;
    if (!merchant || !compatibility) {
      throw new Error("Need research and compatibility before gap analysis.");
    }

    const gaps = analyzeGaps({
      merchant,
      paymentMethods: compatibility.paymentMethods,
      apiDependencies: compatibility.apiDependencies,
    });
    state.gaps = gaps;
    state.stage = "gap_analysis";
    const saved = await saveState(ctx, state);

    return {
      caseId: saved.caseId,
      stage: saved.stage,
      gaps,
      blockers: gaps.filter((g) => g.severity === "blocker"),
      nextStep: "Call plan_migration to create the task plan.",
    };
  },
});
