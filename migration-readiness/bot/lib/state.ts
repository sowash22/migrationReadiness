import type { ToolContext } from "@grok/agent-sdk/tools";
import type { MigrationStage, MigrationState } from "./types.js";

const STAGE_ORDER: MigrationStage[] = [
  "intake",
  "research",
  "compatibility",
  "gap_analysis",
  "planning",
  "awaiting_approval",
  "validation",
  "reporting",
  "complete",
];

export function stageIndex(stage: MigrationStage): number {
  return STAGE_ORDER.indexOf(stage);
}

export function canEnter(current: MigrationStage, next: MigrationStage): boolean {
  return stageIndex(next) <= stageIndex(current) + 1;
}

function keyFor(_ctx: ToolContext, caseId: string): string {
  // Case state is merchant-scoped and shared across sessions of this agent so
  // operators can resume a migration from a later turn or direct tool call.
  return `migration:case:${caseId}`;
}

export async function loadState(
  ctx: ToolContext,
  caseId: string,
): Promise<MigrationState | null> {
  const value = await ctx.host.kv.get(keyFor(ctx, caseId));
  if (!value || typeof value !== "object") {
    return null;
  }
  return value as MigrationState;
}

export async function saveState(
  ctx: ToolContext,
  state: MigrationState,
): Promise<MigrationState> {
  const next: MigrationState = {
    ...state,
    updatedAt: new Date().toISOString(),
  };
  await ctx.host.kv.put(keyFor(ctx, next.caseId), next);
  return next;
}

export async function createState(
  ctx: ToolContext,
  caseId: string,
): Promise<MigrationState> {
  const now = new Date().toISOString();
  const state: MigrationState = {
    caseId,
    stage: "intake",
    createdAt: now,
    updatedAt: now,
  };
  await ctx.host.kv.put(keyFor(ctx, caseId), state);
  return state;
}

export async function requireState(
  ctx: ToolContext,
  caseId: string,
): Promise<MigrationState> {
  const state = await loadState(ctx, caseId);
  if (!state) {
    throw new Error(
      `Unknown migration case "${caseId}". Call intake_merchant first.`,
    );
  }
  return state;
}

export function assertStageAtLeast(
  state: MigrationState,
  required: MigrationStage,
): void {
  if (stageIndex(state.stage) < stageIndex(required)) {
    throw new Error(
      `Case ${state.caseId} is in stage "${state.stage}"; need "${required}" or later.`,
    );
  }
}

export { STAGE_ORDER };
