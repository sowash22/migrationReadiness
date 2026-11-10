import { defineEval } from "@grok/agent-sdk/evals";

export default defineEval({
  tags: ["smoke"],
  description:
    "Shopify merchant ABC intake reaches compatibility tooling with durable case state.",
  async test(t) {
    await t.send(
      "Prepare Shopify merchant ABC for migration to the new payment integration.",
    );
    t.succeeded();
    t.calledTool("intake_merchant");
    t.calledTool("research_merchant");
    t.calledTool("check_compatibility");
  },
});
