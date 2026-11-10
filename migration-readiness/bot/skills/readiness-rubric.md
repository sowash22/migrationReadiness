# Readiness rubric

Use when explaining or drafting the readiness score.

## Score bands

| Band | Score | Meaning |
| --- | --- | --- |
| `ready` | ≥ 80, no blockers, no failed checks | Safe to schedule cutover |
| `at_risk` | 55–79 | Proceed only with an explicit remediation plan |
| `not_ready` | < 55 or open blockers/failed checks | Do not cut over |

## Penalties (implemented in tools)

- Blocker gap: −20
- High gap: −8
- Unsupported payment method: −10
- Failed validation check: −12
- Missing human approval: −15
- Passing checks add small credit (capped)

## What to tell stakeholders

- Name the blockers first.
- Separate unsupported methods from remappable methods.
- Tie each p0 task to a gap id when possible.
- End with a single next action for the human owner.
