import {
  isRecord,
  parseLegalRow,
  parseStats,
  parseWishCol,
  parseWishRow,
  PayloadError,
  requireArray,
  requireNumber,
  requireRecord,
  requireString,
} from "./api";
import { sendAuth } from "./auth";
import { ApiHttpError } from "./sandbox";
import type { LegalRow, PlanningStats, WarningItem, WishCol, WishRow } from "./types";

export type LegalCol = {
  id: string;
  label_fr: string;
};

export type CycleTeam = "salle" | "cuisine";
export type CycleServiceId = "morning" | "midday" | "evening";
export type SearchEffort = "minimal" | "optimized" | "maximal";

export type CycleAssignment = {
  employee_id: string;
  day_index: number;
  weekday: string;
  service_id: CycleServiceId;
  team: string;
  start_minutes: number;
  end_minutes: number;
  post_level: number;
  duration_hours: number;
};

export type PublishedCycle = {
  assignments: CycleAssignment[];
  warnings: WarningItem[];
  stats: PlanningStats;
  legal_cols: LegalCol[];
  legal_rows: LegalRow[];
  wish_cols: WishCol[];
  wish_rows: WishRow[];
};

export type PublishedCycles = {
  salle: PublishedCycle | null;
  cuisine: PublishedCycle | null;
};

export type CyclesPayload = {
  published: PublishedCycles;
};

export type GenerateResult = {
  team: CycleTeam;
  search_effort: SearchEffort;
  published: PublishedCycles;
};

export type GenerateJobStatus = "queued" | "running" | "done" | "failed";

export type GenerateJob = {
  job_id: string;
  team: CycleTeam;
  search_effort: SearchEffort;
  status: GenerateJobStatus;
  estimated_seconds: number;
  error?: string;
  published?: PublishedCycles;
};

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function parseTeam(value: unknown, path: string): CycleTeam {
  if (value === "salle" || value === "cuisine") {
    return value;
  }
  throw new PayloadError(`team inattendue : ${path}`);
}

function parseEffort(value: unknown, path: string): SearchEffort {
  if (value === "minimal" || value === "optimized" || value === "maximal") {
    return value;
  }
  throw new PayloadError(`search_effort inattendu : ${path}`);
}

function parseJobStatus(value: unknown, path: string): GenerateJobStatus {
  if (value === "queued" || value === "running" || value === "done" || value === "failed") {
    return value;
  }
  throw new PayloadError(`status inattendu : ${path}`);
}

function parseServiceId(value: unknown, path: string): CycleServiceId {
  if (value === "morning" || value === "midday" || value === "evening") {
    return value;
  }
  throw new PayloadError(`service_id inattendu : ${path}`);
}

function parseSeverity(value: unknown, path: string): WarningItem["severity"] {
  if (value === "interdit" || value === "couverture" || value === "souhait") {
    return value;
  }
  throw new PayloadError(`severity inattendue : ${path}`);
}

export function parseWarning(value: unknown, path: string): WarningItem {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  if (!("employee_id" in value) || !("day_index" in value)) {
    throw new PayloadError(`clé absente : ${path}`);
  }
  const employeeId = value.employee_id;
  const dayIndex = value.day_index;
  if (employeeId !== null && typeof employeeId !== "string") {
    throw new PayloadError(`clé invalide : ${path}.employee_id`);
  }
  if (dayIndex !== null && typeof dayIndex !== "number") {
    throw new PayloadError(`clé invalide : ${path}.day_index`);
  }
  return {
    severity: parseSeverity(value.severity, `${path}.severity`),
    code: requireString(value, "code", path),
    message: requireString(value, "message", path),
    employee_id: employeeId,
    day_index: dayIndex,
  };
}

export function parseCycleAssignment(value: unknown, path: string): CycleAssignment {
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

function parseLegalCol(value: unknown, path: string): LegalCol {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    label_fr: requireString(value, "label_fr", path),
  };
}

function parseCycle(value: unknown, path: string): PublishedCycle | null {
  if (value === null) {
    return null;
  }
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    assignments: requireArray(value, "assignments", path).map((item, i) =>
      parseCycleAssignment(item, `${path}.assignments[${i}]`),
    ),
    warnings: requireArray(value, "warnings", path).map((item, i) => parseWarning(item, `${path}.warnings[${i}]`)),
    stats: parseStats(value.stats, `${path}.stats`),
    legal_cols: requireArray(value, "legal_cols", path).map((item, i) => parseLegalCol(item, `${path}.legal_cols[${i}]`)),
    legal_rows: requireArray(value, "legal_rows", path).map((item, i) => parseLegalRow(item, `${path}.legal_rows[${i}]`)),
    wish_cols: requireArray(value, "wish_cols", path).map((item, i) => parseWishCol(item, `${path}.wish_cols[${i}]`)),
    wish_rows: requireArray(value, "wish_rows", path).map((item, i) => parseWishRow(item, `${path}.wish_rows[${i}]`)),
  };
}

function parsePublished(value: unknown, path: string): PublishedCycles {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  const published = requireRecord(value, "published", path);
  if (!("salle" in published) || !("cuisine" in published)) {
    throw new PayloadError(`clé absente : ${path}.published`);
  }
  return {
    salle: parseCycle(published.salle, `${path}.published.salle`),
    cuisine: parseCycle(published.cuisine, `${path}.published.cuisine`),
  };
}

export function parseCyclesPayload(value: unknown): CyclesPayload {
  if (!isRecord(value)) {
    throw new PayloadError("réponse cycles invalide");
  }
  return { published: parsePublished(value, "cycles") };
}

export function parseGenerateResult(value: unknown): GenerateResult {
  if (!isRecord(value)) {
    throw new PayloadError("réponse generate invalide");
  }
  return {
    team: parseTeam(value.team, "generate.team"),
    search_effort: parseEffort(value.search_effort, "generate.search_effort"),
    published: parsePublished(value, "generate"),
  };
}

export function parseGenerateJob(value: unknown): GenerateJob {
  if (!isRecord(value)) {
    throw new PayloadError("réponse job invalide");
  }
  const job: GenerateJob = {
    job_id: requireString(value, "job_id", "job"),
    team: parseTeam(value.team, "job.team"),
    search_effort: parseEffort(value.search_effort, "job.search_effort"),
    status: parseJobStatus(value.status, "job.status"),
    estimated_seconds: requireNumber(value, "estimated_seconds", "job"),
  };
  if ("error" in value && value.error !== undefined && value.error !== null) {
    if (typeof value.error !== "string") {
      throw new PayloadError("clé invalide : job.error");
    }
    job.error = value.error;
  }
  if ("published" in value && value.published !== undefined) {
    job.published = parsePublished(value, "job");
  }
  return job;
}

export async function loadCycles(): Promise<CyclesPayload> {
  return parseCyclesPayload(await sendAuth("/v1/cycles", { method: "GET" }, true));
}

export async function getGenerateJob(jobId: string): Promise<GenerateJob> {
  return parseGenerateJob(await sendAuth(`/v1/generate/jobs/${encodeURIComponent(jobId)}`, { method: "GET" }, true));
}

export async function pollGenerateJob(jobId: string): Promise<GenerateResult> {
  for (;;) {
    await sleep(1000);
    const job = await getGenerateJob(jobId);
    if (job.status === "done") {
      if (!job.published) {
        throw new PayloadError("published absent : job done");
      }
      return {
        team: job.team,
        search_effort: job.search_effort,
        published: job.published,
      };
    }
    if (job.status === "failed") {
      throw new ApiHttpError(400, job.error ?? "Le calcul maximal a échoué.");
    }
  }
}

export async function postGenerate(team: CycleTeam, effort: SearchEffort): Promise<GenerateResult> {
  const raw = await sendAuth(
    "/v1/generate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team, search_effort: effort }),
    },
    true,
  );
  if (effort === "maximal") {
    const queued = parseGenerateJob(raw);
    return pollGenerateJob(queued.job_id);
  }
  return parseGenerateResult(raw);
}
