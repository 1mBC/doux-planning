import type {
  Assignment,
  Employee,
  ExamplePayload,
  LegalContext,
  LegalRow,
  LegalRule,
  Planning,
  PlanningHoursStats,
  PlanningStats,
  PlanningWellbeingStats,
  Restaurant,
  StatusCell,
  ScoreFact,
  ScoreFactPolarity,
  ScoreFactSeverity,
  WishCol,
  WishRow,
  CycleScore,
  CycleScoreNotes,
  CycleScoreWeights,
} from "./types";
import { factAxis } from "./scoreFacts";

export class PayloadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PayloadError";
  }
}

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function requireString(obj: Record<string, unknown>, key: string, path: string): string {
  const value = obj[key];
  if (typeof value !== "string") {
    throw new PayloadError(`clé absente ou invalide : ${path}.${key}`);
  }
  return value;
}

export function requireNumber(obj: Record<string, unknown>, key: string, path: string): number {
  const value = obj[key];
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new PayloadError(`clé absente ou invalide : ${path}.${key}`);
  }
  return value;
}

export function requireArray(obj: Record<string, unknown>, key: string, path: string): unknown[] {
  const value = obj[key];
  if (!Array.isArray(value)) {
    throw new PayloadError(`clé absente ou invalide : ${path}.${key}`);
  }
  return value;
}

export function requireRecord(obj: Record<string, unknown>, key: string, path: string): Record<string, unknown> {
  const value = obj[key];
  if (!isRecord(value)) {
    throw new PayloadError(`clé absente ou invalide : ${path}.${key}`);
  }
  return value;
}

function parseRule(value: unknown, path: string): LegalRule {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    label_fr: requireString(value, "label_fr", path),
    severity: requireString(value, "severity", path),
  };
}

export function parseEmployee(value: unknown, path: string): Employee {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const role = requireRecord(value, "role", path);
  return {
    id: requireString(value, "id", path),
    name: requireString(value, "name", path),
    team: requireString(value, "team", path),
    role: {
      name: requireString(role, "name", `${path}.role`),
      level: requireNumber(role, "level", `${path}.role`),
      team: requireString(role, "team", `${path}.role`),
    },
  };
}

function parseLegal(value: unknown): LegalContext {
  if (!isRecord(value)) {
    throw new PayloadError("clé absente ou invalide : legal");
  }
  return {
    id: requireString(value, "id", "legal"),
    kind: requireString(value, "kind", "legal"),
    label: requireString(value, "label", "legal"),
    rules: requireArray(value, "rules", "legal").map((rule, i) => parseRule(rule, `legal.rules[${i}]`)),
  };
}

function parseRestaurant(value: unknown): Restaurant {
  if (!isRecord(value)) {
    throw new PayloadError("clé absente ou invalide : restaurant");
  }
  const hours = value.hours;
  if (!isRecord(hours)) {
    throw new PayloadError("clé absente ou invalide : restaurant.hours");
  }
  return {
    id: requireString(value, "id", "restaurant"),
    name: requireString(value, "name", "restaurant"),
    team: requireString(value, "team", "restaurant"),
    hours,
    employees: requireArray(value, "employees", "restaurant").map((emp, i) =>
      parseEmployee(emp, `restaurant.employees[${i}]`),
    ),
  };
}

function parseServiceId(value: unknown, path: string): "midday" | "evening" {
  if (value === "midday" || value === "evening") {
    return value;
  }
  throw new PayloadError(`service_id inattendu : ${path}`);
}

export function parseAssignment(value: unknown, path: string): Assignment {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    employee_id: requireString(value, "employee_id", path),
    day_index: requireNumber(value, "day_index", path),
    weekday: requireString(value, "weekday", path),
    service_id: parseServiceId(value.service_id, `${path}.service_id`),
    team: requireString(value, "team", path),
    start_minutes: requireNumber(value, "start_minutes", path),
    end_minutes: requireNumber(value, "end_minutes", path),
    post_level: requireNumber(value, "post_level", path),
    duration_hours: requireNumber(value, "duration_hours", path),
  };
}

function parsePolarity(value: unknown, path: string): ScoreFactPolarity {
  if (value === "miss" || value === "hit") {
    return value;
  }
  throw new PayloadError(`polarity inattendue : ${path}`);
}

function parseOptionalSeverity(value: unknown, path: string): ScoreFactSeverity | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (value === "interdit" || value === "couverture" || value === "souhait") {
    return value;
  }
  throw new PayloadError(`severity inattendue : ${path}`);
}

function parseOptionalId(value: unknown, path: string): string | null {
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "string") {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

function parseOptionalDayIndex(value: unknown, path: string): number | null {
  if (value === undefined || value === null) {
    return null;
  }
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

function parsePayload(value: unknown, path: string): Record<string, unknown> {
  if (value === undefined || value === null) {
    return {};
  }
  if (!isRecord(value)) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

export function parseScoreFact(value: unknown, path: string): ScoreFact {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const kind =
    typeof value.kind === "string"
      ? value.kind
      : typeof value.code === "string"
        ? value.code
        : "";
  if (!kind) {
    throw new PayloadError(`clé absente : ${path}.kind`);
  }
  const polarity = "polarity" in value && value.polarity !== undefined ? parsePolarity(value.polarity, `${path}.polarity`) : "miss";
  const fact: ScoreFact = {
    axis: typeof value.axis === "string" && value.axis ? value.axis : factAxis(kind),
    kind,
    polarity,
    severity: parseOptionalSeverity(value.severity, `${path}.severity`),
    employee_id: parseOptionalId(value.employee_id, `${path}.employee_id`),
    day_index: parseOptionalDayIndex(value.day_index, `${path}.day_index`),
    payload: parsePayload(value.payload, `${path}.payload`),
  };
  if ("employee_name" in value && value.employee_name !== undefined) {
    if (value.employee_name !== null && typeof value.employee_name !== "string") {
      throw new PayloadError(`clé invalide : ${path}.employee_name`);
    }
    fact.employee_name = value.employee_name;
  }
  if (typeof value.message === "string") {
    fact.message = value.message;
  }
  return fact;
}

export function parseFactsArray(value: unknown, path: string): ScoreFact[] {
  if (!Array.isArray(value)) {
    throw new PayloadError(`clé absente ou invalide : ${path}`);
  }
  return value.map((item, i) => parseScoreFact(item, `${path}[${i}]`));
}

export function parseFactsPrefer(obj: Record<string, unknown>, path: string): ScoreFact[] {
  if (Array.isArray(obj.facts)) {
    return parseFactsArray(obj.facts, `${path}.facts`);
  }
  if (Array.isArray(obj.warnings)) {
    return parseFactsArray(obj.warnings, `${path}.warnings`);
  }
  return [];
}

function parseHoursStats(value: unknown): PlanningHoursStats {
  if (!isRecord(value)) {
    throw new PayloadError("clé absente ou invalide : planning.stats.hours");
  }
  return {
    assigned: requireNumber(value, "assigned", "planning.stats.hours"),
    contracted: requireNumber(value, "contracted", "planning.stats.hours"),
    percent: requireNumber(value, "percent", "planning.stats.hours"),
  };
}

function parseWellbeingStats(value: unknown): PlanningWellbeingStats {
  if (!isRecord(value)) {
    throw new PayloadError("clé absente ou invalide : planning.stats.wellbeing");
  }
  return {
    held: requireNumber(value, "held", "planning.stats.wellbeing"),
    total: requireNumber(value, "total", "planning.stats.wellbeing"),
  };
}

export function parseStats(value: unknown, path = "planning.stats"): PlanningStats {
  if (!isRecord(value)) {
    throw new PayloadError(`clé absente ou invalide : ${path}`);
  }
  return {
    assignments: requireNumber(value, "assignments", path),
    empty: requireNumber(value, "empty", path),
    interdit: requireNumber(value, "interdit", path),
    below_role: requireNumber(value, "below_role", path),
    hours: parseHoursStats(value.hours),
    wellbeing: parseWellbeingStats(value.wellbeing),
  };
}

function parseNullableNote(value: unknown, path: string): number | null {
  if (value === null) {
    return null;
  }
  if (typeof value !== "number" || Number.isNaN(value)) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

const NOTE_KEYS = ["couverture", "legal", "contrat", "wellbeing", "roles"] as const;

export function parseCycleScore(value: unknown, path: string): CycleScore {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const notesRaw = requireRecord(value, "notes", path);
  const weightsRaw = requireRecord(value, "weights", path);
  if (!("global" in value)) {
    throw new PayloadError(`clé absente : ${path}.global`);
  }
  const notes = {} as CycleScoreNotes;
  const weights = {} as CycleScoreWeights;
  for (const key of NOTE_KEYS) {
    if (!(key in notesRaw)) {
      throw new PayloadError(`clé absente : ${path}.notes.${key}`);
    }
    notes[key] = parseNullableNote(notesRaw[key], `${path}.notes.${key}`);
    weights[key] = requireNumber(weightsRaw, key, `${path}.weights`);
  }
  return {
    notes,
    global: parseNullableNote(value.global, `${path}.global`),
    weights,
  };
}

export function parseOptionalCycleScore(obj: Record<string, unknown>, path: string): CycleScore | undefined {
  if (!("score" in obj) || obj.score === undefined || obj.score === null) {
    return undefined;
  }
  if (!isRecord(obj.score)) {
    return undefined;
  }
  return parseCycleScore(obj.score, `${path}.score`);
}

function parseStatusCell(value: unknown, path: string): StatusCell {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const ok = value.ok;
  if (typeof ok !== "boolean") {
    throw new PayloadError(`clé absente ou invalide : ${path}.ok`);
  }
  const kind = requireString(value, "kind", path);
  return {
    ok,
    kind,
    payload: parsePayload(value.payload, `${path}.payload`),
  };
}

export function parseLegalRow(value: unknown, path: string): LegalRow {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const cellsRaw = requireRecord(value, "cells", path);
  const cells: LegalRow["cells"] = {};
  for (const [key, cell] of Object.entries(cellsRaw)) {
    if (cell === undefined) {
      continue;
    }
    cells[key] = parseStatusCell(cell, `${path}.cells.${key}`);
  }
  return {
    name: requireString(value, "name", path),
    employee_id: requireString(value, "employee_id", path),
    cells,
  };
}

export function parseWishCol(value: unknown, path: string): WishCol {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    key: requireString(value, "key", path),
    label: requireString(value, "label", path),
  };
}

export function parseWishRow(value: unknown, path: string): WishRow {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const cellsRaw = requireRecord(value, "cells", path);
  const cells: WishRow["cells"] = {};
  for (const [key, cell] of Object.entries(cellsRaw)) {
    if (cell === null) {
      cells[key] = null;
      continue;
    }
    cells[key] = parseStatusCell(cell, `${path}.cells.${key}`);
  }
  return {
    name: requireString(value, "name", path),
    employee_id: requireString(value, "employee_id", path),
    cells,
  };
}

function parsePlanning(value: unknown): Planning {
  if (!isRecord(value)) {
    throw new PayloadError("clé absente ou invalide : planning");
  }
  return {
    search_effort: requireString(value, "search_effort", "planning"),
    calendars: requireNumber(value, "calendars", "planning"),
    seconds: requireNumber(value, "seconds", "planning"),
    assignments: requireArray(value, "assignments", "planning").map((item, i) =>
      parseAssignment(item, `planning.assignments[${i}]`),
    ),
    facts: parseFactsArray(value.facts, "planning.facts"),
    stats: parseStats(value.stats),
    legal_rows: requireArray(value, "legal_rows", "planning").map((item, i) =>
      parseLegalRow(item, `planning.legal_rows[${i}]`),
    ),
    wish_cols: requireArray(value, "wish_cols", "planning").map((item, i) =>
      parseWishCol(item, `planning.wish_cols[${i}]`),
    ),
    wish_rows: requireArray(value, "wish_rows", "planning").map((item, i) =>
      parseWishRow(item, `planning.wish_rows[${i}]`),
    ),
    score: parseOptionalCycleScore(value, "planning"),
  };
}

export function parseExamplePayload(value: unknown): ExamplePayload {
  if (!isRecord(value)) {
    throw new PayloadError("réponse JSON invalide");
  }
  return {
    example: requireString(value, "example", "root"),
    legal: parseLegal(value.legal),
    restaurant: parseRestaurant(value.restaurant),
    planning: parsePlanning(value.planning),
  };
}

export async function loadSaintCloudExample(): Promise<ExamplePayload> {
  const response = await fetch("/v1/examples/saint-cloud");
  if (!response.ok) {
    throw new PayloadError(`HTTP ${response.status}`);
  }
  return parseExamplePayload(await response.json());
}
