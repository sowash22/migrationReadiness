import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { assertStageAtLeast, requireState, saveState } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Human-in-the-loop gate before validation.
    Parks until a human approves in the playground or via the approvals API.
    Call only after plan_migration.
  `,
  effect: "write",
  // Parks for a human by default. Pass awaitHumanApproval:false only for
  // automated tool-call / eval chains that cannot click Approve.
  needsApproval: (input) => input.awaitHumanApproval !== false,
  inputSchema: z.object({
    caseId: z.string(),
    summaryForApprover: z
      .string()
      .describe("Short summary of blockers, tasks, and why validation should proceed."),
    awaitHumanApproval: z
      .boolean()
      .optional()
      .describe(
        "Default true/omitted = park for human approval. Set false only for automated verification.",
      ),
  }),
  dryRunResult: ({ caseId, summaryForApprover }) => ({
    caseId,
    approved: false,
    dryRun: true,
    summaryForApprover,
  }),
  async execute({ caseId, summaryForApprover }, ctx) {
    const state = await requireState(ctx, caseId.toUpperCase());
    assertStageAtLeast(state, "awaiting_approval");
    if (!state.plan) {
      throw new Error("Missing migration plan. Call plan_migration first.");
    }

    state.approval = {
      requested: true,
      approved: true,
      approvedAt: new Date().toISOString(),
      note: summaryForApprover,
    };
    state.stage = "validation";
    const saved = await saveState(ctx, state);

    return {
      caseId: saved.caseId,
      stage: saved.stage,
      approved: true,
      approvedByPrincipal: ctx.approvedBy?.principalId ?? null,
      nextStep: "Call validate_readiness to run checks with retries.",
    };
  },
});
