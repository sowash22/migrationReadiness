import { prompt } from "@grok/agent-sdk";
import { defineTool } from "@grok/agent-sdk/tools";
import { z } from "zod";
import { loadState, STAGE_ORDER } from "../lib/state.js";

export default defineTool({
  description: prompt`
    Read the durable migration case state for this session.
    Use to resume a workflow or show progress.
  `,
  effect: "read",
  inputSchema: z.object({
    caseId: z.string(),
  }),
  async execute({ caseId }, ctx) {
    const state = await loadState(ctx, caseId.toUpperCase());
    if (!state) {
      return {
        found: false,
        caseId: caseId.toUpperCase(),
        stages: STAGE_ORDER,
      };
    }
    return {
      found: true,
      caseId: state.caseId,
      stage: state.stage,
      stages: STAGE_ORDER,
      intake: state.intake ?? null,
      merchantId: state.research?.merchant.merchantId ?? null,
      gapCount: state.gaps?.length ?? 0,
      blockerCount: state.gaps?.filter((g) => g.severity === "blocker").length ?? 0,
      taskCount: state.plan?.tasks.length ?? 0,
      approved: state.approval?.approved ?? false,
      readiness: state.readiness ?? null,
      reportPath: state.reportPath ?? null,
      updatedAt: state.updatedAt,
    };
  },
});
