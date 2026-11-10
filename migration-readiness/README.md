# migration-readiness (Python)

Python multi-agent workflow that prepares merchants for migration from a
legacy payment integration to the **new payment platform**.

## Agents

1. **IntakeAgent** – understand the merchant request  
2. **ResearchAgent** – load integration details from the catalog  
3. **CompatibilityAgent** – check payment methods and API deps  
4. **GapAnalysisAgent** – find missing configuration / blockers  
5. **MigrationPlanningAgent** – create migration tasks  
6. **ValidationAgent** – run checks with retries + readiness score  
7. **ReportingAgent** – write the final markdown report  

The `MigrationOrchestrator` sequences them, persists case state as JSON,
applies conditional cutover rules, and pauses for **human-in-the-loop**
approval before validation.

## Example

```bash
cd migration-readiness
python3 -m pip install -e ".[dev]"
migration-readiness --auto-approve --json \
  "Prepare Shopify merchant ABC for migration to the new payment integration."
```

Or:

```bash
python3 -m migration_readiness.cli --auto-approve \
  "Prepare Shopify merchant ABC for migration to the new payment integration."
```

Interactive approval (default):

```bash
migration-readiness "Prepare Shopify merchant ABC for migration to the new payment integration."
# Approve cutover validation? [y/N]:
```

## Scenarios to try

| Merchant | Expected band | What it shows |
| --- | --- | --- |
| **ABC** | `not_ready` | Unsupported boleto, missing HMAC/3DS, blockers |
| **RISK** | `at_risk` | No blockers, but remaps + API/settlement gaps |
| **ACME** | `ready` | Clean config; safe to schedule cutover |
| **andrew** | error | Unknown merchant rejected at intake |

In the web preview, click a scenario card to load and run it.

## Web preview

```bash
python3 -m migration_readiness.web --port 8765
# open http://127.0.0.1:8765/
```

Click **Run migration readiness** to execute the agent pipeline and preview
score, blockers, agent steps, and the report.

## Tests

```bash
python3 -m pip install -e ".[dev]"
pytest -q
```
