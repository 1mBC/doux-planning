import { isRecord, PayloadError, requireArray, requireString } from "./api";
import { sendAuth } from "./auth";
import { parseWarning } from "./generate";
import type { WarningItem } from "./types";

export type AdminTeam = "salle" | "cuisine";

export type AdminGenerateEntry = {
  id: string;
  created_at: string;
  email: string;
  restaurant_name: string;
  team: AdminTeam;
  warnings: WarningItem[];
};

export type AdminGenerates = {
  entries: AdminGenerateEntry[];
};

export type AdminDayGroup = {
  key: string;
  label: string;
  entries: AdminGenerateEntry[];
};

function parseTeam(value: unknown, path: string): AdminTeam {
  if (value === "salle" || value === "cuisine") {
    return value;
  }
  throw new PayloadError(`team inattendue : ${path}`);
}

function parseEntry(value: unknown, path: string): AdminGenerateEntry {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    created_at: requireString(value, "created_at", path),
    email: requireString(value, "email", path),
    restaurant_name: requireString(value, "restaurant_name", path),
    team: parseTeam(value.team, `${path}.team`),
    warnings: requireArray(value, "warnings", path).map((item, i) => parseWarning(item, `${path}.warnings[${i}]`)),
  };
}

export function parseAdminGenerates(value: unknown): AdminGenerates {
  if (!isRecord(value)) {
    throw new PayloadError("réponse admin invalide");
  }
  return {
    entries: requireArray(value, "entries", "admin").map((item, i) => parseEntry(item, `admin.entries[${i}]`)),
  };
}

export async function loadAdminGenerates(): Promise<AdminGenerates> {
  return parseAdminGenerates(await sendAuth("/v1/admin/generates", { method: "GET" }, true));
}

export function parisDayKey(iso: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Paris",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(iso));
}

export function parisDayLabel(iso: string): string {
  const raw = new Intl.DateTimeFormat("fr-FR", {
    timeZone: "Europe/Paris",
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date(iso));
  return raw.charAt(0).toUpperCase() + raw.slice(1);
}

export function parisClock(iso: string): string {
  const parts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Europe/Paris",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(new Date(iso));
  const hour = parts.find((part) => part.type === "hour")?.value ?? "00";
  const minute = parts.find((part) => part.type === "minute")?.value ?? "00";
  return `${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`;
}

export function groupEntriesByParisDay(entries: AdminGenerateEntry[]): AdminDayGroup[] {
  const groups: AdminDayGroup[] = [];
  for (const entry of entries) {
    const key = parisDayKey(entry.created_at);
    const last = groups[groups.length - 1];
    if (last && last.key === key) {
      last.entries.push(entry);
      continue;
    }
    groups.push({ key, label: parisDayLabel(entry.created_at), entries: [entry] });
  }
  return groups;
}

export function teamLabel(team: AdminTeam): string {
  return team === "salle" ? "Salle" : "Cuisine";
}
