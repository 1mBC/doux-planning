import { isRecord, PayloadError, requireArray, requireNumber, requireRecord, requireString } from "./api";
import { sendAuth } from "./auth";
import {
  CONTEXT_SERVICES,
  parseUnavailability,
  type ContextServiceId,
  type TeamId,
  type Unavailability,
  type WeekendChoice,
  type WeekLabels,
} from "./context";
import { parseCycleAssignment, type CycleAssignment } from "./generate";
import type { Employee } from "./types";

export type EmployeeContract = {
  weekly: number;
  assigned: number;
  ok: boolean;
};

export type EmployeeWish =
  | { kind: "consecutive_rest"; held: boolean }
  | { kind: "weekend"; value: WeekendChoice; held: boolean }
  | { kind: "max_services"; service_id: ContextServiceId; limit: number; held: boolean }
  | { kind: "max_coupures"; limit: number; held: boolean };

export type EmployeePlanning = {
  employee_id: string;
  team: TeamId;
  week_labels: WeekLabels;
  employees: Employee[];
  assignments: CycleAssignment[];
  contract: EmployeeContract;
  wishes: EmployeeWish[];
  unavailabilities: Unavailability[];
};

function parseTeam(value: unknown, path: string): TeamId {
  if (value === "salle" || value === "cuisine") {
    return value;
  }
  throw new PayloadError(`team inattendue : ${path}`);
}

function parseWeekLabels(value: unknown, path: string): WeekLabels {
  if (value === "ab" || value === "parity") {
    return value;
  }
  throw new PayloadError(`week_labels inattendu : ${path}`);
}

function parseRole(value: unknown, path: string): Employee["role"] {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    name: requireString(value, "name", path),
    level: requireNumber(value, "level", path),
    team: requireString(value, "team", path),
  };
}

function parseBoardEmployee(value: unknown, path: string): Employee {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    name: requireString(value, "name", path),
    role: parseRole(requireRecord(value, "role", path), `${path}.role`),
    team: requireString(value, "team", path),
  };
}

function parseContract(value: unknown, path: string): EmployeeContract {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (typeof value.ok !== "boolean") {
    throw new PayloadError(`clé absente ou invalide : ${path}.ok`);
  }
  return {
    weekly: requireNumber(value, "weekly", path),
    assigned: requireNumber(value, "assigned", path),
    ok: value.ok,
  };
}

function parseServiceId(value: unknown, path: string): ContextServiceId {
  if (value === "morning" || value === "midday" || value === "evening") {
    return value;
  }
  throw new PayloadError(`service_id inattendu : ${path}`);
}

function parseWeekendValue(value: unknown, path: string): WeekendChoice {
  if (value === "every_two" || value === "even" || value === "odd") {
    return value;
  }
  throw new PayloadError(`clé invalide : ${path}`);
}

function parseWish(value: unknown, path: string): EmployeeWish {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (typeof value.held !== "boolean") {
    throw new PayloadError(`clé absente ou invalide : ${path}.held`);
  }
  const kind = requireString(value, "kind", path);
  if (kind === "consecutive_rest") {
    return { kind, held: value.held };
  }
  if (kind === "weekend") {
    return { kind, value: parseWeekendValue(value.value, `${path}.value`), held: value.held };
  }
  if (kind === "max_services") {
    return {
      kind,
      service_id: parseServiceId(value.service_id, `${path}.service_id`),
      limit: requireNumber(value, "limit", path),
      held: value.held,
    };
  }
  if (kind === "max_coupures") {
    return { kind, limit: requireNumber(value, "limit", path), held: value.held };
  }
  throw new PayloadError(`kind inattendu : ${path}.kind`);
}

export function parseEmployeePlanning(value: unknown): EmployeePlanning {
  if (!isRecord(value)) {
    throw new PayloadError("réponse me/planning invalide");
  }
  return {
    employee_id: requireString(value, "employee_id", "me.planning"),
    team: parseTeam(value.team, "me.planning.team"),
    week_labels: parseWeekLabels(value.week_labels, "me.planning.week_labels"),
    employees: requireArray(value, "employees", "me.planning").map((item, i) =>
      parseBoardEmployee(item, `me.planning.employees[${i}]`),
    ),
    assignments: requireArray(value, "assignments", "me.planning").map((item, i) =>
      parseCycleAssignment(item, `me.planning.assignments[${i}]`),
    ),
    contract: parseContract(requireRecord(value, "contract", "me.planning"), "me.planning.contract"),
    wishes: requireArray(value, "wishes", "me.planning").map((item, i) => parseWish(item, `me.planning.wishes[${i}]`)),
    unavailabilities: requireArray(value, "unavailabilities", "me.planning").map((item, i) =>
      parseUnavailability(item, `me.planning.unavailabilities[${i}]`),
    ),
  };
}

export async function loadEmployeePlanning(): Promise<EmployeePlanning> {
  return parseEmployeePlanning(await sendAuth("/v1/me/planning", { method: "GET" }, true));
}

export function wishLabel(wish: EmployeeWish): string {
  if (wish.kind === "consecutive_rest") {
    return "Deux repos consécutifs par semaine";
  }
  if (wish.kind === "weekend") {
    if (wish.value === "every_two") {
      return "Un we sur deux";
    }
    return wish.value === "even" ? "We paire" : "We impaire";
  }
  if (wish.kind === "max_services") {
    const service = CONTEXT_SERVICES.find((item) => item.id === wish.service_id)?.label ?? wish.service_id;
    return `Max ${service.toLowerCase()} : ${wish.limit}`;
  }
  return `Nbre de coupures max : ${wish.limit}`;
}

export function serviceLabel(serviceId: string): string {
  return CONTEXT_SERVICES.find((item) => item.id === serviceId)?.label ?? serviceId;
}
