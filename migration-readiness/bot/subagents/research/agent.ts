import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Research brief for a merchant's current payment integration surface before catalog lookup.",
  instructions: `You are the Research Agent.

Given intake context, list what to verify:
- payment methods in use
- webhooks
- API dependencies
- settlement and 3DS settings

Return a concise research checklist. The parent calls research_merchant for ground truth.`,
});
