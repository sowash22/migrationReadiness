import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Sequence migration tasks, owners, and dependencies into a cutover plan.",
  instructions: `You are the Migration Planning Agent.

Propose an ordered task list with owners (payments-platform, merchant-engineering, merchant-ops, qa, migration-pm).
Mark p0 work that closes blockers before sandbox validation.
The parent calls plan_migration to persist the plan.`,
});
