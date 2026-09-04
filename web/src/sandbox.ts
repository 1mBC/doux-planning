import {
  isRecord,
  parseAssignment,
  parseEmployee,
  parseWarning,
  PayloadError,
  requireArray,
  requireNumber,
  requireRecord,
  requireString,
} from "./api";
import type {
  Assignment,
  ContractImpact,
  ContractKind,
  FillSlot,
  Gesture,
  HistoryCran,
  HistoryEntry,
  Impact,
  PreviewProposal,
  RoleFit,
  RoleFitKind,
  SandboxState,
  Score,
  ShiftIdentity,
} from "./types";
import { SCORE_FIELDS, toShiftIdentity } from "./types";

export class ApiHttpError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = "ApiHttpError";
  }
}

async function parseDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    /* ignore */
  }
  return `HTTP ${response.status}`;
}

async function sendJson(url: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new ApiHttpError(response.status, await parseDetail(response));
  }
  return response.json();
}

function parseGesture(value: unknown, path: string): Gesture {
  if (value === "retune" || value === "replace" || value === "swap" || value === "fill") {
    return value;
  }
  throw new PayloadError(`geste inattendu : ${path}`);
}

function parseNullableNumber(value: unknown, path: string): number | null {
  if (value === null) {
    return null;
  }
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

function parseNullableString(value: unknown, path: string): string | null {
  if (value === null) {
    return null;
  }
  if (typeof value !== "string") {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

function parseScore(value: unknown, path: string): Score {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const score = {} as Score;
  for (const field of SCORE_FIELDS) {
    score[field] = requireNumber(value, field, path);
  }
  return score;
}

function parseContractKind(value: unknown, path: string): ContractKind {
  if (value === "closer" || value === "farther" || value === "excess") {
    return value;
  }
  throw new PayloadError(`kind inattendu : ${path}`);
}

function parseRoleFitKind(value: unknown, path: string): RoleFitKind {
  if (value === "better" || value === "worse") {
    return value;
  }
  throw new PayloadError(`kind inattendu : ${path}`);
}

function parseWeekStart(value: unknown, path: string): 0 | 7 {
  if (value === 0 || value === 7) {
    return value;
  }
  throw new PayloadError(`week_start inattendu : ${path}`);
}

function parseContractImpact(value: unknown, path: string): ContractImpact {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    employee_id: requireString(value, "employee_id", path),
    week_start: parseWeekStart(value.week_start, `${path}.week_start`),
    current_hours: requireNumber(value, "current_hours", path),
    trial_hours: requireNumber(value, "trial_hours", path),
    contracted: requireNumber(value, "contracted", path),
    kind: parseContractKind(value.kind, `${path}.kind`),
  };
}

function parseRoleFit(value: unknown, path: string): RoleFit {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    current_gap: requireNumber(value, "current_gap", path),
    trial_gap: requireNumber(value, "trial_gap", path),
    kind: parseRoleFitKind(value.kind, `${path}.kind`),
  };
}

function parseImpact(value: unknown, path: string): Impact {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    new_interdits: requireArray(value, "new_interdits", path).map((item, i) =>
      parseWarning(item, `${path}.new_interdits[${i}]`),
    ),
    broken_wishes: requireArray(value, "broken_wishes", path).map((item, i) =>
      parseWarning(item, `${path}.broken_wishes[${i}]`),
    ),
    contract: requireArray(value, "contract", path).map((item, i) =>
      parseContractImpact(item, `${path}.contract[${i}]`),
    ),
    coverage_added: requireArray(value, "coverage_added", path).map((item, i) =>
      parseWarning(item, `${path}.coverage_added[${i}]`),
    ),
    coverage_removed: requireArray(value, "coverage_removed", path).map((item, i) =>
      parseWarning(item, `${path}.coverage_removed[${i}]`),
    ),
    role_fit: requireArray(value, "role_fit", path).map((item, i) => parseRoleFit(item, `${path}.role_fit[${i}]`)),
  };
}

function parseProposal(value: unknown, path: string): PreviewProposal {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (!("start_minutes" in value) || !("end_minutes" in value) || !("employee_id" in value) || !("partner" in value)) {
    throw new PayloadError(`clé absente : ${path}`);
  }
  const partner = value.partner;
  if (partner !== null && !isRecord(partner)) {
    throw new PayloadError(`clé invalide : ${path}.partner`);
  }
  return {
    rank: requireNumber(value, "rank", path),
    gesture: parseGesture(value.gesture, `${path}.gesture`),
    start_minutes: parseNullableNumber(value.start_minutes, `${path}.start_minutes`),
    end_minutes: parseNullableNumber(value.end_minutes, `${path}.end_minutes`),
    employee_id: parseNullableString(value.employee_id, `${path}.employee_id`),
    partner: partner === null ? null : parseAssignment(partner, `${path}.partner`),
    impact: parseImpact(value.impact, `${path}.impact`),
    current_score: parseScore(value.current_score, `${path}.current_score`),
    trial_score: parseScore(value.trial_score, `${path}.trial_score`),
  };
}

function parseServiceId(value: unknown, path: string): "midday" | "evening" {
  if (value === "midday" || value === "evening") {
    return value;
  }
  throw new PayloadError(`service_id inattendu : ${path}`);
}

function parseFillSlot(value: unknown, path: string): FillSlot {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    employee_id: requireString(value, "employee_id", path),
    day_index: requireNumber(value, "day_index", path),
    weekday: requireString(value, "weekday", path),
    service_id: parseServiceId(value.service_id, `${path}.service_id`),
    team: requireString(value, "team", path),
  };
}

function parseNullableAssignment(value: unknown, path: string): Assignment | null {
  if (value === null) {
    return null;
  }
  return parseAssignment(value, path);
}

function parseNullableFillSlot(value: unknown, path: string): FillSlot | null {
  if (value === null) {
    return null;
  }
  return parseFillSlot(value, path);
}

function parseHistoryCran(value: unknown, path: string): HistoryCran {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (
    !("shift" in value) ||
    !("slot" in value) ||
    !("employee_id" in value) ||
    !("start_minutes" in value) ||
    !("end_minutes" in value) ||
    !("partner" in value)
  ) {
    throw new PayloadError(`clé absente : ${path}`);
  }
  return {
    index: requireNumber(value, "index", path),
    gesture: parseGesture(value.gesture, `${path}.gesture`),
    shift: parseNullableAssignment(value.shift, `${path}.shift`),
    slot: parseNullableFillSlot(value.slot, `${path}.slot`),
    employee_id: parseNullableString(value.employee_id, `${path}.employee_id`),
    start_minutes: parseNullableNumber(value.start_minutes, `${path}.start_minutes`),
    end_minutes: parseNullableNumber(value.end_minutes, `${path}.end_minutes`),
    partner: parseNullableAssignment(value.partner, `${path}.partner`),
    impact: parseImpact(value.impact, `${path}.impact`),
  };
}

const SILENT_SCORE: Score = {
  empty: 0,
  interdit: 0,
  hours_miss: 0,
  souhait: 0,
  below_role: 0,
  overqualification: 0,
};

export function historyEntryFromCran(cran: HistoryCran): HistoryEntry {
  return {
    index: cran.index,
    gesture: cran.gesture,
    shift: cran.shift ? toShiftIdentity(cran.shift) : null,
    slot: cran.slot,
    proposal: {
      rank: 1,
      gesture: cran.gesture,
      start_minutes: cran.start_minutes,
      end_minutes: cran.end_minutes,
      employee_id: cran.employee_id,
      partner: cran.partner,
      impact: cran.impact,
      current_score: SILENT_SCORE,
      trial_score: SILENT_SCORE,
    },
  };
}

export function parseSandboxState(value: unknown): SandboxState {
  if (!isRecord(value)) {
    throw new PayloadError("réponse sandbox invalide");
  }
  const sandbox = requireRecord(value, "sandbox", "root");
  const restaurant = requireRecord(value, "restaurant", "root");
  const planning = requireRecord(value, "planning", "root");
  return {
    sandbox: {
      target: requireString(sandbox, "target", "sandbox"),
      history_length: requireNumber(sandbox, "history_length", "sandbox"),
    },
    restaurant: {
      id: requireString(restaurant, "id", "restaurant"),
      name: requireString(restaurant, "name", "restaurant"),
      employees: requireArray(restaurant, "employees", "restaurant").map((item, i) =>
        parseEmployee(item, `restaurant.employees[${i}]`),
      ),
    },
    planning: {
      assignments: requireArray(planning, "assignments", "planning").map((item, i) =>
        parseAssignment(item, `planning.assignments[${i}]`),
      ),
      warnings: requireArray(planning, "warnings", "planning").map((item, i) =>
        parseWarning(item, `planning.warnings[${i}]`),
      ),
    },
    score: parseScore(value.score, "score"),
    history: requireArray(value, "history", "root").map((item, i) => parseHistoryCran(item, `history[${i}]`)),
  };
}

export function parsePreviewBody(value: unknown): { proposals: PreviewProposal[] } {
  if (!isRecord(value)) {
    throw new PayloadError("réponse preview invalide");
  }
  return {
    proposals: requireArray(value, "proposals", "root").map((item, i) => parseProposal(item, `proposals[${i}]`)),
  };
}

export async function enterSandbox(): Promise<SandboxState> {
  return parseSandboxState(await sendJson("/v1/sandbox/enter", { method: "POST" }));
}

export async function getSandbox(): Promise<SandboxState> {
  return parseSandboxState(await sendJson("/v1/sandbox"));
}

export async function previewSandbox(
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
    await sendJson("/v1/sandbox/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  );
  return body.proposals;
}

export async function previewFill(
  slot: FillSlot,
  hours: { start_minutes: number | null; end_minutes: number | null },
): Promise<PreviewProposal[]> {
  const body = parsePreviewBody(
    await sendJson("/v1/sandbox/preview", {
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

export async function commitSandbox(body: Record<string, unknown>): Promise<SandboxState> {
  return parseSandboxState(
    await sendJson("/v1/sandbox/commit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  );
}

export async function undoSandbox(): Promise<SandboxState> {
  return parseSandboxState(await sendJson("/v1/sandbox/undo", { method: "POST" }));
}

export async function discardSandbox(): Promise<SandboxState> {
  return parseSandboxState(await sendJson("/v1/sandbox/discard", { method: "POST" }));
}

export function commitFillBody(
  slot: FillSlot,
  proposal: PreviewProposal,
): Record<string, unknown> {
  return {
    gesture: "fill",
    slot,
    employee_id: proposal.employee_id,
    start_minutes: proposal.start_minutes,
    end_minutes: proposal.end_minutes,
  };
}

export function commitBody(gesture: Gesture, shift: ShiftIdentity, proposal: PreviewProposal): Record<string, unknown> {
  const payload: Record<string, unknown> = { gesture, shift };
  if (gesture === "retune") {
    payload.start_minutes = proposal.start_minutes;
    payload.end_minutes = proposal.end_minutes;
  } else if (gesture === "replace") {
    payload.employee_id = proposal.employee_id;
  } else if (gesture === "swap") {
    payload.partner = proposal.partner
      ? {
          employee_id: proposal.partner.employee_id,
          day_index: proposal.partner.day_index,
          weekday: proposal.partner.weekday,
          service_id: proposal.partner.service_id,
          team: proposal.partner.team,
          start_minutes: proposal.partner.start_minutes,
          end_minutes: proposal.partner.end_minutes,
          post_level: proposal.partner.post_level,
        }
      : null;
  }
  return payload;
}
