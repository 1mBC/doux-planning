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

export type WeekLabels = "ab" | "parity";
export type WeekendChoice = "every_two" | "even" | "odd";

export type Unavailability = {
  weekday: string;
  service_id: string;
};

export type MaxServices = {
  morning?: number;
  midday?: number;
  evening?: number;
};

export type Wellbeing = {
  consecutive_rest: boolean;
  weekend: WeekendChoice | null;
  max_services: MaxServices;
  max_coupures_per_week: number | null;
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
  wellbeing: Wellbeing;
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
  week_labels: WeekLabels;
};

export type ContextPatch = {
  name?: string;
  services?: ContextServiceId[];
  ladders?: RestaurantContext["ladders"];
  employees?: Omit<ContextEmployee, "invite_token">[];
  types?: ServiceType[];
  typical_week?: RestaurantContext["typical_week"];
};

export function emptyWellbeing(): Wellbeing {
  return {
    consecutive_rest: false,
    weekend: null,
    max_services: {},
    max_coupures_per_week: null,
  };
}

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

export function parseUnavailability(value: unknown, path: string): Unavailability {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if ("every_morning" in value || "every_evening" in value) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return {
    weekday: requireString(value, "weekday", path),
    service_id: requireString(value, "service_id", path),
  };
}

function parseWeekend(value: unknown, path: string): WeekendChoice | null {
  if (value === null) {
    return null;
  }
  if (value === "every_two" || value === "even" || value === "odd") {
    return value;
  }
  throw new PayloadError(`clé invalide : ${path}`);
}

function parseMaxServices(value: unknown, path: string): MaxServices {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const out: MaxServices = {};
  for (const id of ["morning", "midday", "evening"] as const) {
    if (!(id in value) || value[id] === undefined) {
      continue;
    }
    const raw = value[id];
    if (typeof raw !== "number" || Number.isNaN(raw)) {
      throw new PayloadError(`clé invalide : ${path}.${id}`);
    }
    out[id] = raw;
  }
  return out;
}

export function parseWellbeing(value: unknown, path: string): Wellbeing {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (typeof value.consecutive_rest !== "boolean") {
    throw new PayloadError(`clé absente ou invalide : ${path}.consecutive_rest`);
  }
  if (!("weekend" in value)) {
    throw new PayloadError(`clé absente : ${path}.weekend`);
  }
  if (!("max_coupures_per_week" in value)) {
    throw new PayloadError(`clé absente : ${path}.max_coupures_per_week`);
  }
  const coupures = value.max_coupures_per_week;
  if (coupures !== null && (typeof coupures !== "number" || Number.isNaN(coupures))) {
    throw new PayloadError(`clé invalide : ${path}.max_coupures_per_week`);
  }
  return {
    consecutive_rest: value.consecutive_rest,
    weekend: parseWeekend(value.weekend, `${path}.weekend`),
    max_services: parseMaxServices(requireRecord(value, "max_services", path), `${path}.max_services`),
    max_coupures_per_week: coupures,
  };
}

function parseWeekLabels(value: unknown, path: string): WeekLabels {
  if (value === "ab" || value === "parity") {
    return value;
  }
  throw new PayloadError(`week_labels inattendu : ${path}`);
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
    wellbeing: parseWellbeing(requireRecord(value, "wellbeing", path), `${path}.wellbeing`),
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
    week_labels: parseWeekLabels(value.week_labels, "context.week_labels"),
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

export async function seedExampleContext(): Promise<RestaurantContext> {
  return parseRestaurantContext(await sendAuth("/v1/context/seed-example", { method: "POST" }, true));
}

export function employeesForPatch(employees: ContextEmployee[]): ContextPatch["employees"] {
  return employees.map(({ invite_token: _token, ...rest }) => rest);
}

export function newId(prefix: string): string {
  const rand = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  return `${prefix}-${rand.slice(0, 8)}`;
}
