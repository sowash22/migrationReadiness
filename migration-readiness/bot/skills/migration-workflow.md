# Migration workflow

Use this skill when a user asks to prepare, assess, or migrate a merchant to the new payment platform.

## Stage machine

`intake → research → compatibility → gap_analysis → planning → awaiting_approval → validation → reporting → complete`

Each stage has a durable tool. Call tools in order. Persistence is automatic in `ctx.host.kv` via those tools.

## Tool checklist

1. `intake_merchant` with the raw user request
2. `research_merchant`
3. `check_compatibility`
4. `analyze_gaps`
5. `plan_migration`
6. `request_cutover_approval` — waits for a human
7. `validate_readiness`
8. `publish_report` with an executive summary from the `reporting` subagent

## Conditionals

- Blockers present → plan still runs, but cutover hint forbids scheduling until blockers clear.
- Approval denied or missing → do not call `validate_readiness`.
- Validation `fail` checks → readiness band will not be `ready`; report must say so.
- Unknown merchant hint → tell the user known demos are ABC and ACME.

## Retries

`validate_readiness` retries transient webhook challenge failures up to `maxRetries` (default 3). Mention retries used when non-zero.
