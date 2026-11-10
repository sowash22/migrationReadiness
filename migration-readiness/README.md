# migration-readiness

Agent SDK multi-agent workflow that prepares merchants for migration from a
legacy payment integration to the **new payment platform**.

## What it demonstrates

- **Orchestration** — parent agent runs a strict stage machine
- **Subagents** — intake, research, compatibility, gap-analysis, migration-planning, validation, reporting
- **Tool calling** — catalog inspection, compatibility, gaps, plan, validation, report
- **State** — durable per-session case state in `ctx.host.kv`
- **Conditionals** — blockers change cutover guidance and readiness band
- **Retries** — flaky webhook challenge retries inside `validate_readiness`
- **Human-in-the-loop** — `request_cutover_approval` uses `needsApproval: true`

## Example

```text
Prepare Shopify merchant ABC for migration to the new payment integration.
```

Expected path:

1. Intake + research merchant ABC
2. Flag unsupported **boleto**, gift-card remap, Admin API upgrade
3. Gap analysis for missing HMAC / 3DS / settlement currencies
4. Migration task plan
5. Human approval gate
6. Validation with retries + readiness score
7. Final markdown report under `reports/ABC-migration-readiness.md`

## Run locally

```bash
cd migration-readiness
npx @grok/agent-sdk@0.6.0 login   # once
npx @grok/agent-sdk@0.6.0 validate --dir .
npx @grok/agent-sdk@0.6.0 info --dir . --json
npx @grok/agent-sdk@0.6.0 tool call intake_merchant --dir . --json \
  --input '{"request":"Prepare Shopify merchant ABC for migration to the new payment integration."}'
npx @grok/agent-sdk@0.6.0 run --dir . --message "Prepare Shopify merchant ABC for migration to the new payment integration."
npx @grok/agent-sdk@0.6.0 dev --dir .
npx @grok/agent-sdk@0.6.0 eval --dir .
npm run check
```

In the playground, approve the parked `request_cutover_approval` call to continue past planning.

## Defaults used for this scaffold

- **Purpose:** domain assistant over payment-migration tools
- **Name / location:** `migration-readiness/`
- **Model:** `grok-4.7` (`reasoning_effort=high`, `fast=true`)
- **Channels:** playground + HTTP
- **MCP:** none (in-process merchant catalog)
- **Capabilities:** server tools, skills, subagents, memory hook, smoke eval
