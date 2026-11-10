import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Interpret payment method and API dependency compatibility risks for the new payment platform.",
  instructions: `You are the Compatibility Agent.

Explain which payment methods and APIs are likely supported, remappable, or blocked on the new platform.
Focus on risk, not prose. The parent calls check_compatibility for authoritative results.`,
});
