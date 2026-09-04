import { isRecord, PayloadError, requireArray, requireNumber, requireRecord, requireString } from "./api";
import { sendAuth } from "./auth";
import { CONTEXT_SERVICES, WELLBEING_FR, type TeamId, type Unavailability } from "./context";
import { parseCycleAssignment, type CycleAssignment } from "./generate";
import type { Employee } from "./types";

export type EmployeeContract = {
  weekly: number;
  assigned: number;
  ok: boolean;
};

export type EmployeeWish = {
  key: string;
  held: boolean;
};

export type EmployeePlanning = {
  employee_id: string;
  team: TeamId;
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

function parseWish(value: unknown, path: string): EmployeeWish {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (typeof value.held !== "boolean") {
    throw new PayloadError(`clé absente ou invalide : ${path}.held`);
  }
  return {
    key: requireString(value, "key", path),
    held: value.held,
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

export function parseEmployeePlanning(value: unknown): EmployeePlanning {
  if (!isRecord(value)) {
    throw new PayloadError("réponse me/planning invalide");
  }
  return {
    employee_id: requireString(value, "employee_id", "me.planning"),
    team: parseTeam(value.team, "me.planning.team"),
    employees: requireArray(value, "employees", "me.planning").map((item, i) =>
      parseBoardEmployee(item, `me.planning.employees[${i}]`),
    ),
    assignments: requireArray(value, "assignments", "me.planning").map((item, i) =>
      parseCycleAssignment(item, `me.planning.assignments[${i}]`),
    ),
    contract: parseContract(requireRecord(value, "contract", "me.planning"), "me.planning.contract"),
    wishes: requireArray(value, "wishes", "me.planning").map((item, i) =>
      parseWish(item, `me.planning.wishes[${i}]`),
    ),
    unavailabilities: requireArray(value, "unavailabilities", "me.planning").map((item, i) =>
      parseUnavailability(item, `me.planning.unavailabilities[${i}]`),
    ),
  };
}

export async function loadEmployeePlanning(): Promise<EmployeePlanning> {
  return parseEmployeePlanning(await sendAuth("/v1/me/planning", { method: "GET" }, true));
}

export function wishLabel(key: string): string {
  return key in WELLBEING_FR ? WELLBEING_FR[key as keyof typeof WELLBEING_FR] : key;
}

export function serviceLabel(serviceId: string): string {
  return CONTEXT_SERVICES.find((item) => item.id === serviceId)?.label ?? serviceId;
}
