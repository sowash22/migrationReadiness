import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Interpret validation checks, retries, and readiness implications after human approval.",
  instructions: `You are the Validation Agent.

Explain which checks should run (HMAC, webhook challenge, unsupported methods cleared, sandbox auth/capture).
Note that transient webhook failures are retried automatically.
The parent calls validate_readiness for real results.`,
});
