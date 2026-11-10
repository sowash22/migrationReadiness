import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { buildMigrationPlan } from "../lib/platform.js";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Create migration tasks from gap analysis and move the case into awaiting_approval.
  `,
  effect: "idempotent",
  inputSchema: z.object({
    caseId: z.string(),
  }),
  async execute({ caseId }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "gap_analysis");
    const merchant = state.research?.merchant;
    const gaps = state.gaps;
    if (!merchant || !gaps) {
      throw new Error("Need merchant research and gaps before planning.");
    }

    const plan = buildMigrationPlan({ merchant, gaps });
    state.plan = plan;
    state.approval = {
      requested: true,
      approved: false,
      note: "Human approval required before validation and cutover.",
    };
    state.stage = "awaiting_approval";
    const saved = await saveState(ctx, state);

    return {
      caseId: saved.caseId,
      stage: saved.stage,
      plan: saved.plan,
      approvalRequired: true,
      nextStep:
        "Call request_cutover_approval. It parks for human-in-the-loop approval before validation.",
    };
  },
});
