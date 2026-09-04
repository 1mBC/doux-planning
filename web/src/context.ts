import { isRecord, PayloadError, requireArray, requireNumber, requireRecord, requireString } from "./api";
import { sendAuth } from "./auth";

export type TeamId = "salle" | "cuisine";
export type ContextServiceId = "morning" | "midday" | "evening";

export type RoleRow = {
  name: string;
  level: number;
};

export type RoleLadder = {
  roles: RoleRow[];
  substitution_explained: true;
};

export type Unavailability = {
  weekday?: string;
  every_morning: boolean;
  every_evening: boolean;
  service_id?: string;
};

export type ContextRole = {
  name: string;
  level: number;
  team: TeamId;
};

export type ContextEmployee = {
  id: string;
  name: string;
  team: TeamId;
  role: ContextRole;
  contractual_hours_per_week: number;
  min_shift_hours: number;
  unavailabilities: Unavailability[];
  wellbeing: string[];
  invite_token: string;
};

export type ArrivalWave = {
  time_minutes: number;
  post_levels: number[];
};

export type DepartureWave = {
  time_minutes: number;
  remaining_post_levels: number[];
};

export type ServiceType = {
  id: string;
  name: string;
  team: TeamId;
  service_id: ContextServiceId;
  arrivals: ArrivalWave[];
  departures: DepartureWave[];
};

export type TypicalWeekCell = {
  weekday: string;
  service_id: ContextServiceId;
  type_id: string | null;
  closed: boolean;
};

export type RestaurantContext = {
  name: string;
  legal_context_id: string;
  company_code: string;
  services: ContextServiceId[];
  ladders: { salle: RoleLadder | null; cuisine: RoleLadder | null };
  employees: ContextEmployee[];
  types: ServiceType[];
  typical_week: { salle: TypicalWeekCell[] | null; cuisine: TypicalWeekCell[] | null };
  ready: { salle: boolean; cuisine: boolean };
};

export type ContextPatch = {
  name?: string;
  services?: ContextServiceId[];
  ladders?: RestaurantContext["ladders"];
  employees?: Omit<ContextEmployee, "invite_token">[];
  types?: ServiceType[];
  typical_week?: RestaurantContext["typical_week"];
};

export const WELLBEING_KEYS = [
  "two_consecutive_rest_days",
  "weekend_off_every_two_weeks",
  "at_least_one_weekend_rest_day",
  "no_evening_service",
  "no_morning_service",
  "max_two_coupures_per_week",
  "max_three_coupures_per_week",
] as const;

export const WELLBEING_FR: Record<(typeof WELLBEING_KEYS)[number], string> = {
  two_consecutive_rest_days: "Deux repos consécutifs en semaine",
  weekend_off_every_two_weeks: "Un week-end sur deux",
  at_least_one_weekend_rest_day: "Au moins un jour de repos le week-end",
  no_evening_service: "Pas de service du soir",
  no_morning_service: "Pas de service du matin",
  max_two_coupures_per_week: "Au plus deux coupures / semaine",
  max_three_coupures_per_week: "Au plus trois coupures / semaine",
};

export const CONTEXT_SERVICES: { id: ContextServiceId; label: string }[] = [
  { id: "morning", label: "Petit-déjeuner" },
  { id: "midday", label: "Déjeuner" },
  { id: "evening", label: "Dîner" },
];

function parseTeam(value: unknown, path: string): TeamId {
  if (value === "salle" || value === "cuisine") {
    return value;
  }
  throw new PayloadError(`team inattendue : ${path}`);
}

function parseServiceId(value: unknown, path: string): ContextServiceId {
  if (value === "morning" || value === "midday" || value === "evening") {
    return value;
  }
  throw new PayloadError(`service_id inattendu : ${path}`);
}

function parseRoleRow(value: unknown, path: string): RoleRow {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const level = requireNumber(value, "level", path);
  if (level < 1 || !Number.isInteger(level)) {
    throw new PayloadError(`level invalide : ${path}.level`);
  }
  return { name: requireString(value, "name", path), level };
}

function parseLadder(value: unknown, path: string): RoleLadder | null {
  if (value === null) {
    return null;
  }
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (value.substitution_explained !== true) {
    throw new PayloadError(`substitution_explained invalide : ${path}`);
  }
  return {
    roles: requireArray(value, "roles", path).map((item, i) => parseRoleRow(item, `${path}.roles[${i}]`)),
    substitution_explained: true,
  };
}

function parseUnavailability(value: unknown, path: string): Unavailability {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (typeof value.every_morning !== "boolean" || typeof value.every_evening !== "boolean") {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  const row: Unavailability = {
    every_morning: value.every_morning,
    every_evening: value.every_evening,
  };
  if ("weekday" in value && value.weekday !== undefined && value.weekday !== null) {
    if (typeof value.weekday !== "string") {
      throw new PayloadError(`clé invalide : ${path}.weekday`);
    }
    row.weekday = value.weekday;
  }
  if ("service_id" in value && value.service_id !== undefined && value.service_id !== null) {
    if (typeof value.service_id !== "string") {
      throw new PayloadError(`clé invalide : ${path}.service_id`);
    }
    row.service_id = value.service_id;
  }
  return row;
}

function parseContextRole(value: unknown, path: string): ContextRole {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    name: requireString(value, "name", path),
    level: requireNumber(value, "level", path),
    team: parseTeam(value.team, `${path}.team`),
  };
}

function parseEmployee(value: unknown, path: string): ContextEmployee {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    name: requireString(value, "name", path),
    team: parseTeam(value.team, `${path}.team`),
    role: parseContextRole(requireRecord(value, "role", path), `${path}.role`),
    contractual_hours_per_week: requireNumber(value, "contractual_hours_per_week", path),
    min_shift_hours: requireNumber(value, "min_shift_hours", path),
    unavailabilities: requireArray(value, "unavailabilities", path).map((item, i) =>
      parseUnavailability(item, `${path}.unavailabilities[${i}]`),
    ),
    wellbeing: requireArray(value, "wellbeing", path).map((item, i) => {
      if (typeof item !== "string") {
        throw new PayloadError(`clé invalide : ${path}.wellbeing[${i}]`);
      }
      return item;
    }),
    invite_token: requireString(value, "invite_token", path),
  };
}

function parseArrival(value: unknown, path: string): ArrivalWave {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    time_minutes: requireNumber(value, "time_minutes", path),
    post_levels: requireArray(value, "post_levels", path).map((item, i) => {
      if (typeof item !== "number") {
        throw new PayloadError(`clé invalide : ${path}.post_levels[${i}]`);
      }
      return item;
    }),
  };
}

function parseDeparture(value: unknown, path: string): DepartureWave {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    time_minutes: requireNumber(value, "time_minutes", path),
    remaining_post_levels: requireArray(value, "remaining_post_levels", path).map((item, i) => {
      if (typeof item !== "number") {
        throw new PayloadError(`clé invalide : ${path}.remaining_post_levels[${i}]`);
      }
      return item;
    }),
  };
}

function parseType(value: unknown, path: string): ServiceType {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    name: requireString(value, "name", path),
    team: parseTeam(value.team, `${path}.team`),
    service_id: parseServiceId(value.service_id, `${path}.service_id`),
    arrivals: requireArray(value, "arrivals", path).map((item, i) => parseArrival(item, `${path}.arrivals[${i}]`)),
    departures: requireArray(value, "departures", path).map((item, i) =>
      parseDeparture(item, `${path}.departures[${i}]`),
    ),
  };
}

function parseCell(value: unknown, path: string): TypicalWeekCell {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (!("type_id" in value) || typeof value.closed !== "boolean") {
    throw new PayloadError(`clé absente : ${path}`);
  }
  if (value.type_id !== null && typeof value.type_id !== "string") {
    throw new PayloadError(`clé invalide : ${path}.type_id`);
  }
  return {
    weekday: requireString(value, "weekday", path),
    service_id: parseServiceId(value.service_id, `${path}.service_id`),
    type_id: value.type_id,
    closed: value.closed,
  };
}

function parseWeek(value: unknown, path: string): TypicalWeekCell[] | null {
  if (value === null) {
    return null;
  }
  if (!Array.isArray(value)) {
    throw new PayloadError(`tableau attendu : ${path}`);
  }
  return value.map((item, i) => parseCell(item, `${path}[${i}]`));
}

export function parseRestaurantContext(value: unknown): RestaurantContext {
  if (!isRecord(value)) {
    throw new PayloadError("réponse contexte invalide");
  }
  const ladders = requireRecord(value, "ladders", "context");
  const typical = requireRecord(value, "typical_week", "context");
  const ready = requireRecord(value, "ready", "context");
  if (typeof ready.salle !== "boolean" || typeof ready.cuisine !== "boolean") {
    throw new PayloadError("clé invalide : context.ready");
  }
  if (!("salle" in typical) || !("cuisine" in typical)) {
    throw new PayloadError("clé absente : context.typical_week");
  }
  return {
    name: requireString(value, "name", "context"),
    legal_context_id: requireString(value, "legal_context_id", "context"),
    company_code: requireString(value, "company_code", "context"),
    services: requireArray(value, "services", "context").map((item, i) => parseServiceId(item, `context.services[${i}]`)),
    ladders: {
      salle: parseLadder(ladders.salle, "context.ladders.salle"),
      cuisine: parseLadder(ladders.cuisine, "context.ladders.cuisine"),
    },
    employees: requireArray(value, "employees", "context").map((item, i) => parseEmployee(item, `context.employees[${i}]`)),
    types: requireArray(value, "types", "context").map((item, i) => parseType(item, `context.types[${i}]`)),
    typical_week: {
      salle: parseWeek(typical.salle, "context.typical_week.salle"),
      cuisine: parseWeek(typical.cuisine, "context.typical_week.cuisine"),
    },
    ready: { salle: ready.salle, cuisine: ready.cuisine },
  };
}

export async function loadContext(): Promise<RestaurantContext> {
  return parseRestaurantContext(await sendAuth("/v1/context", { method: "GET" }, true));
}

export async function patchContext(body: ContextPatch): Promise<RestaurantContext> {
  return parseRestaurantContext(
    await sendAuth("/v1/context", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }, true),
  );
}

export function employeesForPatch(employees: ContextEmployee[]): ContextPatch["employees"] {
  return employees.map(({ invite_token: _token, ...rest }) => rest);
}

export function newId(prefix: string): string {
  const rand = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  return `${prefix}-${rand.slice(0, 8)}`;
}
