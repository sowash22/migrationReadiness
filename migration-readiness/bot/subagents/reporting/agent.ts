import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Draft the executive summary and stakeholder-facing readiness narrative for the final report.",
  instructions: `You are the Reporting Agent.

Draft a 2-4 sentence executive summary covering readiness band, top blockers, and the single next action.
Do not invent scores. Use the parent's tool results.
The parent passes your summary into publish_report.`,
});
