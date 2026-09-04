import { sendAuth } from "./auth";
import { parseCyclesPayload, type CyclesPayload } from "./generate";
import { parsePreviewBody, parseSandboxState } from "./sandbox";
import { isRecord, PayloadError } from "./api";
import type { FillSlot, Gesture, PreviewProposal, SandboxState, ShiftIdentity } from "./types";
import type { TeamId } from "./context";

export type LiveState = SandboxState & { team: TeamId };

function livePath(team: TeamId, suffix = ""): string {
  return `/v1/live/sandbox/${team}${suffix}`;
}

function parseTeam(value: unknown): TeamId {
  if (value === "salle" || value === "cuisine") {
    return value;
  }
  throw new PayloadError("clé invalide : live.team");
}

export function parseLiveState(value: unknown): LiveState {
  if (!isRecord(value) || !("team" in value)) {
    throw new PayloadError("clé absente : live.team");
  }
  const state = parseSandboxState(value);
  return { ...state, team: parseTeam(value.team) };
}

async function sendLive(team: TeamId, suffix: string, init: RequestInit): Promise<unknown> {
  return sendAuth(livePath(team, suffix), init, true);
}

export async function enterLiveSandbox(team: TeamId): Promise<LiveState> {
  return parseLiveState(await sendLive(team, "/enter", { method: "POST" }));
}

export async function getLiveSandbox(team: TeamId): Promise<LiveState> {
  return parseLiveState(await sendLive(team, "", { method: "GET" }));
}

export async function previewLiveOccupied(
  team: TeamId,
  gesture: Gesture,
  shift: ShiftIdentity,
  hours?: { start_minutes: number; end_minutes: number },
): Promise<PreviewProposal[]> {
  const payload: Record<string, unknown> = { gesture, shift };
  if (gesture === "retune") {
    if (!hours) {
      throw new PayloadError("start_minutes et end_minutes requis pour retune");
    }
    payload.start_minutes = hours.start_minutes;
    payload.end_minutes = hours.end_minutes;
  }
  const body = parsePreviewBody(
    await sendLive(team, "/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
  return body.proposals;
}

export async function previewLiveFill(
  team: TeamId,
  slot: FillSlot,
  hours: { start_minutes: number | null; end_minutes: number | null },
): Promise<PreviewProposal[]> {
  const body = parsePreviewBody(
    await sendLive(team, "/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        gesture: "fill",
        slot,
        start_minutes: hours.start_minutes,
        end_minutes: hours.end_minutes,
      }),
    }),
  );
  return body.proposals;
}

export async function commitLiveSandbox(team: TeamId, body: Record<string, unknown>): Promise<LiveState> {
  return parseLiveState(
    await sendLive(team, "/commit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
}

export async function undoLiveSandbox(team: TeamId): Promise<LiveState> {
  return parseLiveState(await sendLive(team, "/undo", { method: "POST" }));
}

export async function discardLiveSandbox(team: TeamId): Promise<LiveState> {
  return parseLiveState(await sendLive(team, "/discard", { method: "POST" }));
}

export async function publishLiveSandbox(team: TeamId): Promise<CyclesPayload> {
  return parseCyclesPayload(await sendLive(team, "/publish", { method: "POST" }));
}
