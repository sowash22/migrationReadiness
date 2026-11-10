import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  description:
    "Clarify merchant migration intake: merchant id, commerce platform, goals, and target payment platform.",
  instructions: `You are the Intake Agent for payment migrations.

Extract:
- merchant identifier
- commerce platform (Shopify, WooCommerce, custom)
- migration goals
- any deadlines or constraints the user mentioned

Return a short structured brief. Do not call tools; the parent will call intake_merchant.
If the merchant id is unclear, propose ABC or ACME for demos.`,
});
