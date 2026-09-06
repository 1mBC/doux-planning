import type {
  Assignment,
  Employee,
  Gesture,
  LegalContext,
  LegalRow,
  LegalRule,
  WarningItem,
} from "./types";

export const DAYS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"];
export const DAYS_FR_SHORT = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"];

export type WeekLabelScheme = "ab" | "parity";

export function weekSheetTitle(scheme: WeekLabelScheme, weekOffset: 0 | 7): string {
  if (scheme === "parity") {
    return weekOffset === 0 ? "Semaine paire" : "Semaine impaire";
  }
  return weekOffset === 0 ? "Semaine A" : "Semaine B";
}

export function weekLabelPair(scheme: WeekLabelScheme): string {
  return scheme === "parity" ? "Paire / Impaire" : "A / B";
}

export function formatGeneratedAt(iso: string | undefined): string {
  if (!iso) {
    return "—";
  }
  const at = new Date(iso);
  if (Number.isNaN(at.getTime())) {
    return "—";
  }
  return at.toLocaleString("fr-FR", {
    timeZone: "Europe/Paris",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export const WEEKDAYS_EN = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const;

export function weekdayFromDayIndex(dayIndex: number): string {
  return WEEKDAYS_EN[((dayIndex % 7) + 7) % 7];
}

export const SERVICE_ROWS: { id: "midday" | "evening"; label: string }[] = [
  { id: "midday", label: "Matin" },
  { id: "evening", label: "Soir" },
];

const PERSON_INKS = [
  "#2b6ea8",
  "#2f8a52",
  "#c49a2a",
  "#1f8a8a",
  "#c45a7a",
  "#4a62b8",
  "#d4782c",
  "#c45a52",
];

export function personInk(employees: Employee[], employeeId: string): string {
  const index = employees.findIndex((person) => person.id === employeeId);
  return PERSON_INKS[(index < 0 ? 0 : index) % PERSON_INKS.length];
}

export function formatClock(minutes: number): string {
  const total = ((minutes % 1440) + 1440) % 1440;
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  const hourLabel = hours === 0 ? "00h" : `${hours}h`;
  if (mins === 0) {
    return hourLabel;
  }
  return `${hours}h${String(mins).padStart(2, "0")}`;
}

export function formatDuration(hours: number): string {
  const totalMinutes = Math.round(hours * 60);
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  if (m === 0) {
    return `${h}h`;
  }
  return `${h}h${String(m).padStart(2, "0")}`;
}

export function formatHoursTotal(value: number): string {
  if (Math.abs(value - Math.round(value)) < 1e-9) {
    return `${Math.round(value)} h`;
  }
  const rounded = Math.round(value * 10) / 10;
  return `${String(rounded).replace(".", ",")} h`;
}

export function formatSeconds(seconds: number): string {
  return `${String(seconds).replace(".", ",")} s`;
}

const EFFORT_FR: Record<string, string> = {
  minimal: "minimal",
  optimized: "optimisé",
  maximal: "maximal",
};

export function effortLabel(effort: string): string {
  return EFFORT_FR[effort] ?? effort;
}

export const SEVERITY_FR: Record<WarningItem["severity"], string> = {
  interdit: "Interdit",
  couverture: "Couverture",
  souhait: "Souhait",
};

const CODE_TITLE_FR: Record<string, string> = {
  empty_post: "Poste vide",
  contract_hours: "Heures de contrat",
};

export const GESTURE_CHOICE_FR: { id: Gesture; label: string }[] = [
  { id: "retune", label: "Changer les heures" },
  { id: "replace", label: "Attribuer une autre personne" },
  { id: "swap", label: "Échanger" },
];

export const GESTURE_HISTORY_FR: Record<Gesture, string> = {
  retune: "Ajustement d’heures",
  replace: "Remplacement",
  swap: "Échange",
  fill: "Créneau posé",
};

export function formatScoreValue(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }
  return String(value).replace(".", ",");
}

export function dayThenClock(dayIndex: number, startMinutes: number, endMinutes: number): string {
  const day = DAYS_FR[((dayIndex % 7) + 7) % 7];
  const week = dayIndex >= 7 ? " · sem. B" : "";
  return `${day}${week} · ${formatClock(startMinutes)} – ${formatClock(endMinutes)}`;
}

export function hoursDeltaMinutes(currentHours: number, trialHours: number): number {
  return Math.round((trialHours - currentHours) * 60);
}

export function formatContractPercents(
  currentHours: number,
  trialHours: number,
  contracted: number,
): string | null {
  if (contracted === 0) {
    return null;
  }
  const before = Math.round((currentHours / contracted) * 1000) / 10;
  const after = Math.round((trialHours / contracted) * 1000) / 10;
  return `(${formatScoreValue(before)} % → ${formatScoreValue(after)} %)`;
}

export function warningTitle(code: string): string | undefined {
  return CODE_TITLE_FR[code];
}

export function warningSeverityLabel(warning: { code: string; severity: WarningItem["severity"] }): string {
  if (warning.code === "contract_hours") {
    return "Contrat";
  }
  return SEVERITY_FR[warning.severity];
}

export function assignmentKey(employeeId: string, dayIndex: number, serviceId: string): string {
  return `${employeeId}:${dayIndex}:${serviceId}`;
}

export function indexAssignments(assignments: Assignment[]): Map<string, Assignment> {
  const map = new Map<string, Assignment>();
  for (const shift of assignments) {
    const key = assignmentKey(shift.employee_id, shift.day_index, shift.service_id);
    if (!map.has(key)) {
      map.set(key, shift);
    }
  }
  return map;
}

export function weekHours(
  assignments: Assignment[],
  employeeId: string,
  weekOffset: 0 | 7,
): number {
  let total = 0;
  for (const shift of assignments) {
    if (shift.employee_id !== employeeId) {
      continue;
    }
    if (shift.day_index < weekOffset || shift.day_index > weekOffset + 6) {
      continue;
    }
    total += shift.duration_hours;
  }
  return total;
}

export function groupedEmployees(employees: Employee[]): { role: string; members: Employee[] }[] {
  const order: string[] = [];
  const members = new Map<string, Employee[]>();
  for (const person of employees) {
    const role = person.role.name;
    if (!members.has(role)) {
      order.push(role);
      members.set(role, []);
    }
    members.get(role)!.push(person);
  }
  return order.map((role) => ({ role, members: members.get(role)! }));
}

export function legalColumns(legal: LegalContext, rows: LegalRow[]): LegalRule[] {
  const used = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row.cells)) {
      used.add(key);
    }
  }
  return legal.rules.filter((rule) => used.has(rule.id));
}
