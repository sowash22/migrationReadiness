from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

MigrationStage = Literal[
    "intake",
    "research",
    "compatibility",
    "gap_analysis",
    "planning",
    "awaiting_approval",
    "validation",
    "reporting",
    "complete",
]

PaymentMethod = Literal[
    "card",
    "apple_pay",
    "google_pay",
    "shop_pay",
    "klarna",
    "afterpay",
    "gift_card",
    "boleto",
    "sepa_debit",
]

STAGE_ORDER: list[MigrationStage] = [
    "intake",
    "research",
    "compatibility",
    "gap_analysis",
    "planning",
    "awaiting_approval",
    "validation",
    "reporting",
    "complete",
]


@dataclass
class MerchantSettings:
    three_ds_enabled: bool
    webhook_hmac_configured: bool
    settlement_currencies: list[str]
    refunds_api_version: str
    payout_schedule: str


@dataclass
class MerchantConfig:
    merchant_id: str
    display_name: str
    commerce_platform: Literal["shopify", "woocommerce", "custom"]
    region: str
    currencies: list[str]
    old_integration: str
    payment_methods: list[PaymentMethod]
    webhooks: list[str]
    api_dependencies: list[str]
    settings: MerchantSettings


@dataclass
class CompatibilityFinding:
    payment_method: PaymentMethod
    status: Literal["supported", "unsupported", "needs_remap"]
    notes: str


@dataclass
class ApiDependencyFinding:
    dependency: str
    status: Literal["compatible", "upgrade_required", "blocked"]
    notes: str


@dataclass
class GapItem:
    id: str
    severity: Literal["blocker", "high", "medium", "low"]
    area: str
    description: str
    remediation: str


@dataclass
class MigrationTask:
    id: str
    title: str
    owner: str
    depends_on: list[str]
    priority: Literal["p0", "p1", "p2"]
    status: Literal["todo", "in_progress", "done"] = "todo"


@dataclass
class ValidationCheck:
    id: str
    name: str
    status: Literal["pass", "fail", "retrying", "skipped"]
    attempts: int
    detail: str


@dataclass
class ReadinessScore:
    score: int
    band: Literal["not_ready", "at_risk", "ready"]
    blockers: int
    unsupported_methods: int
    failed_checks: int
    summary: str


@dataclass
class IntakeData:
    raw_request: str
    merchant_hint: str
    target_platform: str
    goals: list[str]


@dataclass
class ResearchData:
    merchant: MerchantConfig
    notes: list[str]


@dataclass
class CompatibilityData:
    payment_methods: list[CompatibilityFinding]
    api_dependencies: list[ApiDependencyFinding]


@dataclass
class PlanData:
    tasks: list[MigrationTask]
    cutover_window_hint: str


@dataclass
class ApprovalData:
    requested: bool
    approved: bool
    approved_at: str | None = None
    note: str | None = None


@dataclass
class ValidationData:
    checks: list[ValidationCheck]
    retries_used: int


@dataclass
class MigrationState:
    case_id: str
    stage: MigrationStage
    created_at: str
    updated_at: str
    intake: IntakeData | None = None
    research: ResearchData | None = None
    compatibility: CompatibilityData | None = None
    gaps: list[GapItem] = field(default_factory=list)
    plan: PlanData | None = None
    approval: ApprovalData | None = None
    validation: ValidationData | None = None
    readiness: ReadinessScore | None = None
    report_path: str | None = None
    agent_log: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MigrationState:
        intake = data.get("intake")
        research = data.get("research")
        compatibility = data.get("compatibility")
        plan = data.get("plan")
        approval = data.get("approval")
        validation = data.get("validation")
        readiness = data.get("readiness")

        merchant = None
        if research and research.get("merchant"):
            m = research["merchant"]
            settings = MerchantSettings(**m["settings"])
            merchant = MerchantConfig(
                merchant_id=m["merchant_id"],
                display_name=m["display_name"],
                commerce_platform=m["commerce_platform"],
                region=m["region"],
                currencies=list(m["currencies"]),
                old_integration=m["old_integration"],
                payment_methods=list(m["payment_methods"]),
                webhooks=list(m["webhooks"]),
                api_dependencies=list(m["api_dependencies"]),
                settings=settings,
            )

        return cls(
            case_id=data["case_id"],
            stage=data["stage"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            intake=IntakeData(**intake) if intake else None,
            research=(
                ResearchData(merchant=merchant, notes=list(research["notes"]))
                if research and merchant
                else None
            ),
            compatibility=(
                CompatibilityData(
                    payment_methods=[
                        CompatibilityFinding(**p)
                        for p in compatibility["payment_methods"]
                    ],
                    api_dependencies=[
                        ApiDependencyFinding(**d)
                        for d in compatibility["api_dependencies"]
                    ],
                )
                if compatibility
                else None
            ),
            gaps=[GapItem(**g) for g in data.get("gaps", [])],
            plan=(
                PlanData(
                    tasks=[MigrationTask(**t) for t in plan["tasks"]],
                    cutover_window_hint=plan["cutover_window_hint"],
                )
                if plan
                else None
            ),
            approval=ApprovalData(**approval) if approval else None,
            validation=(
                ValidationData(
                    checks=[ValidationCheck(**c) for c in validation["checks"]],
                    retries_used=validation["retries_used"],
                )
                if validation
                else None
            ),
            readiness=ReadinessScore(**readiness) if readiness else None,
            report_path=data.get("report_path"),
            agent_log=list(data.get("agent_log", [])),
        )
