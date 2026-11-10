import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Prioritize missing configurations and migration blockers from compatibility findings.",
  instructions: `You are the Gap Analysis Agent.

Prioritize gaps as blocker / high / medium / low.
Call out missing HMAC, 3DS, settlement currencies, and unsupported methods first.
The parent calls analyze_gaps for the durable gap list.`,
});
