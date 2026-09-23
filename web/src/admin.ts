import { isRecord, parseFactsPrefer, PayloadError, requireArray, requireNumber, requireString } from "./api";
import { sendAuth } from "./auth";
import { parseRestaurantContext, type RestaurantContext } from "./context";
import { parseCyclesPayload, type CyclesPayload, type SearchEffort } from "./generate";
import type { ScoreFact } from "./types";

export type AdminTeam = "salle" | "cuisine";

export type AdminGenerateEntry = {
  id: string;
  created_at: string;
  email: string;
  restaurant_name: string;
  restaurant_id: string | null;
  team: AdminTeam;
  search_effort: SearchEffort | null;
  duration_seconds: number | null;
  engine_ref: string | null;
  score_global: number | null;
  facts: ScoreFact[];
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

function parseOptionalEffort(value: unknown, path: string): SearchEffort | null {
  if (value === null) {
    return null;
  }
  if (value === "minimal" || value === "optimized" || value === "maximal") {
    return value;
  }
  throw new PayloadError(`search_effort inattendu : ${path}`);
}

function parseOptionalDuration(value: unknown, path: string): number | null {
  if (value === null) {
    return null;
  }
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

function parseOptionalString(value: unknown, path: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== "string") {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value === "" ? null : value;
}

function parseOptionalScore(value: unknown, path: string): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new PayloadError(`clé invalide : ${path}`);
  }
  return value;
}

function parseEntry(value: unknown, path: string): AdminGenerateEntry {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (!("search_effort" in value) || !("duration_seconds" in value)) {
    throw new PayloadError(`clé absente : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    created_at: requireString(value, "created_at", path),
    email: requireString(value, "email", path),
    restaurant_name: requireString(value, "restaurant_name", path),
    restaurant_id: parseOptionalString(value.restaurant_id, `${path}.restaurant_id`),
    team: parseTeam(value.team, `${path}.team`),
    search_effort: parseOptionalEffort(value.search_effort, `${path}.search_effort`),
    duration_seconds: parseOptionalDuration(value.duration_seconds, `${path}.duration_seconds`),
    engine_ref: parseOptionalString(value.engine_ref, `${path}.engine_ref`),
    score_global: parseOptionalScore(value.score_global, `${path}.score_global`),
    facts: parseFactsPrefer(value, path),
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

export async function loadAdminRestaurantCycles(restaurantId: string): Promise<CyclesPayload> {
  return parseCyclesPayload(
    await sendAuth(`/v1/admin/restaurants/${encodeURIComponent(restaurantId)}/cycles`, { method: "GET" }, true),
  );
}

export async function loadAdminRestaurantContext(restaurantId: string): Promise<RestaurantContext> {
  return parseRestaurantContext(
    await sendAuth(`/v1/admin/restaurants/${encodeURIComponent(restaurantId)}/context`, { method: "GET" }, true),
  );
}

export type ImportPreviewComputes = {
  minimal: boolean;
  optimized: boolean;
  maximal: boolean;
};

export type ImportPreviewTeam = {
  ready: boolean;
  manuel_published: boolean;
  computes_published: ImportPreviewComputes;
};

export type ImportPreview = {
  restaurant_id: string;
  restaurant_name: string;
  email: string;
  salle: ImportPreviewTeam;
  cuisine: ImportPreviewTeam;
  generate_count: number;
};

export type BenchImportBody = {
  restaurant_id: string;
  include_salle: boolean;
  include_cuisine: boolean;
  include_manuel: boolean;
  include_runs: boolean;
  manual_score: number | null;
  comment: string | null;
};

function requireBoolean(obj: Record<string, unknown>, key: string, path: string): boolean {
  const value = obj[key];
  if (typeof value !== "boolean") {
    throw new PayloadError(`clé invalide : ${path}.${key}`);
  }
  return value;
}

function parseImportPreviewComputes(value: unknown, path: string): ImportPreviewComputes {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    minimal: requireBoolean(value, "minimal", path),
    optimized: requireBoolean(value, "optimized", path),
    maximal: requireBoolean(value, "maximal", path),
  };
}

function parseImportPreviewTeam(value: unknown, path: string): ImportPreviewTeam {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    ready: requireBoolean(value, "ready", path),
    manuel_published: requireBoolean(value, "manuel_published", path),
    computes_published: parseImportPreviewComputes(value.computes_published, `${path}.computes_published`),
  };
}

export function parseImportPreview(value: unknown): ImportPreview {
  if (!isRecord(value)) {
    throw new PayloadError("réponse import-preview invalide");
  }
  return {
    restaurant_id: requireString(value, "restaurant_id", "import-preview"),
    restaurant_name: requireString(value, "restaurant_name", "import-preview"),
    email: requireString(value, "email", "import-preview"),
    salle: parseImportPreviewTeam(value.salle, "import-preview.salle"),
    cuisine: parseImportPreviewTeam(value.cuisine, "import-preview.cuisine"),
    generate_count: requireNumber(value, "generate_count", "import-preview"),
  };
}

export async function loadImportPreview(restaurantId: string): Promise<ImportPreview> {
  return parseImportPreview(
    await sendAuth(
      `/v1/admin/restaurants/${encodeURIComponent(restaurantId)}/import-preview`,
      { method: "GET" },
      true,
    ),
  );
}

export async function postBenchImport(body: BenchImportBody): Promise<void> {
  await sendAuth(
    "/v1/admin/bench/import",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    true,
  );
}

export async function mintImpersonateLink(restaurantId: string): Promise<string> {
  const value = await sendAuth(
    "/v1/admin/impersonate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ restaurant_id: restaurantId }),
    },
    true,
  );
  if (!isRecord(value) || typeof value.url !== "string" || !value.url) {
    throw new PayloadError("réponse impersonate invalide");
  }
  return value.url;
}

export async function copyToClipboard(value: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    const area = document.createElement("textarea");
    area.value = value;
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
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

export function effortLabel(effort: SearchEffort | null): string {
  if (effort === "minimal") {
    return "Minimal";
  }
  if (effort === "optimized") {
    return "Optimisé";
  }
  if (effort === "maximal") {
    return "Maximal";
  }
  return "—";
}

export type LiveEngine = {
  engine_ref: string;
  engine_refs: string[];
};

function parseLiveEngine(value: unknown): LiveEngine {
  if (!isRecord(value)) {
    throw new PayloadError("réponse live-engine invalide");
  }
  return {
    engine_ref: requireString(value, "engine_ref", "live-engine"),
    engine_refs: requireArray(value, "engine_refs", "live-engine").map((item, i) => {
      if (typeof item !== "string" || !item) {
        throw new PayloadError(`clé invalide : live-engine.engine_refs[${i}]`);
      }
      return item;
    }),
  };
}

export async function loadLiveEngine(): Promise<LiveEngine> {
  return parseLiveEngine(await sendAuth("/v1/admin/live-engine", { method: "GET" }, true));
}

export async function putLiveEngine(engineRef: string): Promise<LiveEngine> {
  return parseLiveEngine(
    await sendAuth(
      "/v1/admin/live-engine",
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ engine_ref: engineRef }),
      },
      true,
    ),
  );
}
