import { defineAgent } from "@grok/agent-sdk";

export default defineAgent({
  model: {
    id: "grok-4.7",
    params: [
      { id: "reasoning_effort", value: "high" },
      { id: "fast", value: "true" },
    ],
  },
  // Keep task so the parent can delegate to stage subagents.
  tools: ["task", "read", "grep"],
  local: {
    sandbox: true,
  },
});
