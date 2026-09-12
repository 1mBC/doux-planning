import {
  isRecord,
  parseCycleScore,
  parseEmployee,
  PayloadError,
  requireArray,
  requireNumber,
  requireRecord,
  requireString,
} from "./api";
import { sendAuth } from "./auth";
import { parseCycleSlice, type CycleSlice, type SearchEffort } from "./generate";
import type { CycleScore, Employee } from "./types";

export type BenchScope = "all" | "category" | "dataset";

export type BenchDataset = {
  category: string;
  id: string;
  name: string;
  challenge_fr: string;
};

export type BenchDeltas = {
  couverture: number | null;
  legal: number | null;
  contrat: number | null;
  wellbeing: number | null;
  roles: number | null;
  global: number | null;
};

export type BenchRunSummary = {
  id: string;
  created_at: string;
  engine_ref: string;
  app_version: string;
  category: string;
  dataset_id: string;
  search_effort: SearchEffort;
  duration_seconds: number;
  score: CycleScore;
  expected_score: CycleScore;
  deltas: BenchDeltas;
};

export type BenchVersionCell = {
  run_id: string;
  global: number | null;
  deltas: BenchDeltas;
  duration_seconds: number;
};

export type BenchVersionEfforts = {
  minimal: BenchVersionCell | null;
  optimized: BenchVersionCell | null;
  maximal: BenchVersionCell | null;
};

export type BenchVersionDataset = {
  category: string;
  id: string;
  name: string;
  challenge_fr: string;
  manual: { global: number | null } | null;
  by_ref: Record<string, BenchVersionEfforts>;
};

export type BenchVersions = {
  engine_ref: string;
  engine_refs: string[];
  datasets: BenchVersionDataset[];
};

export type BenchJobStatus = "queued" | "running" | "done" | "failed";

export type BenchJob = {
  job_id: string;
  category: string;
  dataset_id: string;
  search_effort: SearchEffort;
  status: BenchJobStatus;
  error?: string;
  run_id?: string;
};

export type BenchCompare = BenchRunSummary & {
  employees: Employee[];
  model: CycleSlice;
  manual: CycleSlice;
};

export type BenchExportScope = "dataset" | "below_manuel";

const DELTA_KEYS = ["couverture", "legal", "contrat", "wellbeing", "roles", "global"] as const;
export const BENCH_EFFORTS: SearchEffort[] = ["minimal", "optimized", "maximal"];

function parseEffort(value: unknown, path: string): SearchEffort {
  if (value === "minimal" || value === "optimized" || value === "maximal") {
    return value;
  }
  throw new PayloadError(`search_effort inattendu : ${path}`);
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

function parseEngineRef(obj: Record<string, unknown>, path: string): string {
  if (typeof obj.engine_ref === "string" && obj.engine_ref) {
    return obj.engine_ref;
  }
  if (typeof obj.app_version === "string" && obj.app_version) {
    return obj.app_version;
  }
  throw new PayloadError(`clé absente : ${path}.engine_ref`);
}

function parseDeltas(obj: Record<string, unknown>, path: string): BenchDeltas {
  const raw = requireRecord(obj, "deltas", path);
  const deltas = {} as BenchDeltas;
  for (const key of DELTA_KEYS) {
    if (!(key in raw)) {
      throw new PayloadError(`clé absente : ${path}.deltas.${key}`);
    }
    deltas[key] = parseNullableNumber(raw[key], `${path}.deltas.${key}`);
  }
  return deltas;
}

export function parseBenchDatasets(value: unknown): { engine_ref: string; app_version: string; datasets: BenchDataset[] } {
  if (!isRecord(value)) {
    throw new PayloadError("réponse bench datasets invalide");
  }
  const ref = parseEngineRef(value, "bench");
  return {
    engine_ref: ref,
    app_version: ref,
    datasets: requireArray(value, "datasets", "bench").map((item, i) => {
      const path = `bench.datasets[${i}]`;
      if (!isRecord(item)) {
        throw new PayloadError(`objet attendu : ${path}`);
      }
      return {
        category: requireString(item, "category", path),
        id: requireString(item, "id", path),
        name: requireString(item, "name", path),
        challenge_fr: requireString(item, "challenge_fr", path),
      };
    }),
  };
}

export function parseBenchRunSummary(value: unknown, path: string): BenchRunSummary {
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    id: requireString(value, "id", path),
    created_at: requireString(value, "created_at", path),
    engine_ref: parseEngineRef(value, path),
    app_version: parseEngineRef(value, path),
    category: requireString(value, "category", path),
    dataset_id: requireString(value, "dataset_id", path),
    search_effort: parseEffort(value.search_effort, `${path}.search_effort`),
    duration_seconds: requireNumber(value, "duration_seconds", path),
    score: parseCycleScore(value.score, `${path}.score`),
    expected_score: parseCycleScore(value.expected_score, `${path}.expected_score`),
    deltas: parseDeltas(value, path),
  };
}

export function parseBenchRuns(value: unknown): { runs: BenchRunSummary[] } {
  if (!isRecord(value)) {
    throw new PayloadError("réponse bench runs invalide");
  }
  return {
    runs: requireArray(value, "runs", "bench").map((item, i) => parseBenchRunSummary(item, `bench.runs[${i}]`)),
  };
}

function parseJobStatus(value: unknown, path: string): BenchJobStatus {
  if (value === "queued" || value === "running" || value === "done" || value === "failed") {
    return value;
  }
  throw new PayloadError(`status inattendu : ${path}`);
}

export function parseBenchJob(value: unknown): BenchJob {
  if (!isRecord(value)) {
    throw new PayloadError("réponse bench job invalide");
  }
  const job: BenchJob = {
    job_id: requireString(value, "job_id", "job"),
    category: requireString(value, "category", "job"),
    dataset_id: requireString(value, "dataset_id", "job"),
    search_effort: parseEffort(value.search_effort, "job.search_effort"),
    status: parseJobStatus(value.status, "job.status"),
  };
  if (typeof value.error === "string") {
    job.error = value.error;
  }
  if (typeof value.run_id === "string") {
    job.run_id = value.run_id;
  }
  return job;
}

export function parseBenchRunResponse(
  value: unknown,
): { kind: "runs"; runs: BenchRunSummary[] } | { kind: "queued"; job_ids: string[] } {
  if (!isRecord(value)) {
    throw new PayloadError("réponse bench run invalide");
  }
  if ("job_ids" in value) {
    const ids = requireArray(value, "job_ids", "bench").map((item, i) => {
      if (typeof item !== "string") {
        throw new PayloadError(`clé invalide : bench.job_ids[${i}]`);
      }
      return item;
    });
    return { kind: "queued", job_ids: ids };
  }
  return { kind: "runs", runs: parseBenchRuns(value).runs };
}

export function parseBenchCompare(value: unknown): BenchCompare {
  const summary = parseBenchRunSummary(value, "compare");
  if (!isRecord(value)) {
    throw new PayloadError("objet attendu : compare");
  }
  return {
    ...summary,
    employees: requireArray(value, "employees", "compare").map((item, i) =>
      parseEmployee(item, `compare.employees[${i}]`),
    ),
    model: parseCycleSlice(value.model, "compare.model"),
    manual: parseCycleSlice(value.manual, "compare.manual"),
  };
}

export function benchDatasetExportFilename(category: string, datasetId: string): string {
  return `bench-${category}-${datasetId}.json`;
}

export function benchBelowManuelExportFilename(): string {
  return "bench-below-manuel.json";
}

export function downloadJsonFile(payload: unknown, filename: string): void {
  const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function loadBenchExport(params: {
  scope: "dataset";
  category: string;
  dataset_id: string;
}): Promise<unknown>;
export async function loadBenchExport(params: { scope: "below_manuel" }): Promise<unknown>;
export async function loadBenchExport(params: {
  scope: BenchExportScope;
  category?: string;
  dataset_id?: string;
}): Promise<unknown> {
  const query = new URLSearchParams();
  query.set("scope", params.scope);
  if (params.scope === "dataset") {
    if (!params.category || !params.dataset_id) {
      throw new PayloadError("export dataset : category et dataset_id requis");
    }
    query.set("category", params.category);
    query.set("dataset_id", params.dataset_id);
  }
  return sendAuth(`/v1/admin/bench/export?${query.toString()}`, { method: "GET" }, true);
}

export function parseBenchVersionCell(value: unknown, path: string): BenchVersionCell | null {
  if (value === null) {
    return null;
  }
  if (!isRecord(value)) {
    throw new PayloadError(`objet attendu : ${path}`);
  }
  return {
    run_id: requireString(value, "run_id", path),
    global: parseNullableNumber(value.global, `${path}.global`),
    deltas: parseDeltas(value, path),
    duration_seconds: requireNumber(value, "duration_seconds", path),
  };
}

export function parseBenchVersions(value: unknown): BenchVersions {
  if (!isRecord(value)) {
    throw new PayloadError("réponse bench versions invalide");
  }
  const engineRefs = requireArray(value, "engine_refs", "versions").map((item, i) => {
    if (typeof item !== "string" || !item) {
      throw new PayloadError(`clé invalide : versions.engine_refs[${i}]`);
    }
    return item;
  });
  return {
    engine_ref: parseEngineRef(value, "versions"),
    engine_refs: engineRefs,
    datasets: requireArray(value, "datasets", "versions").map((item, i) => {
      const path = `versions.datasets[${i}]`;
      if (!isRecord(item)) {
        throw new PayloadError(`objet attendu : ${path}`);
      }
      const byRefRaw = requireRecord(item, "by_ref", path);
      const by_ref: Record<string, BenchVersionEfforts> = {};
      for (const ref of engineRefs) {
        const bucket = requireRecord(byRefRaw, ref, `${path}.by_ref`);
        by_ref[ref] = {
          minimal: parseBenchVersionCell(bucket.minimal ?? null, `${path}.by_ref.${ref}.minimal`),
          optimized: parseBenchVersionCell(bucket.optimized ?? null, `${path}.by_ref.${ref}.optimized`),
          maximal: parseBenchVersionCell(bucket.maximal ?? null, `${path}.by_ref.${ref}.maximal`),
        };
      }
      let manual: { global: number | null } | null = null;
      if (item.manual !== null && item.manual !== undefined) {
        const raw = requireRecord(item, "manual", path);
        manual = { global: parseNullableNumber(raw.global, `${path}.manual.global`) };
      }
      return {
        category: requireString(item, "category", path),
        id: requireString(item, "id", path),
        name: requireString(item, "name", path),
        challenge_fr: requireString(item, "challenge_fr", path),
        manual,
        by_ref,
      };
    }),
  };
}

export async function loadBenchDatasets(): Promise<{ engine_ref: string; app_version: string; datasets: BenchDataset[] }> {
  return parseBenchDatasets(await sendAuth("/v1/admin/bench/datasets", { method: "GET" }, true));
}

export async function loadBenchRuns(): Promise<{ runs: BenchRunSummary[] }> {
  return parseBenchRuns(await sendAuth("/v1/admin/bench/runs", { method: "GET" }, true));
}

export async function loadBenchJob(jobId: string): Promise<BenchJob> {
  return parseBenchJob(await sendAuth(`/v1/admin/bench/jobs/${encodeURIComponent(jobId)}`, { method: "GET" }, true));
}

export async function loadBenchCompare(category: string, datasetId: string, effort: SearchEffort): Promise<BenchCompare> {
  return parseBenchCompare(
    await sendAuth(
      `/v1/admin/bench/compare/${encodeURIComponent(category)}/${encodeURIComponent(datasetId)}/${encodeURIComponent(effort)}`,
      { method: "GET" },
      true,
    ),
  );
}

export async function loadBenchRun(runId: string): Promise<BenchCompare> {
  return parseBenchCompare(await sendAuth(`/v1/admin/bench/runs/${encodeURIComponent(runId)}`, { method: "GET" }, true));
}

export async function loadBenchVersions(): Promise<BenchVersions> {
  return parseBenchVersions(await sendAuth("/v1/admin/bench/versions", { method: "GET" }, true));
}

export async function postBenchRun(body: {
  scope: BenchScope;
  category?: string;
  dataset_id?: string;
  search_effort: SearchEffort;
}): Promise<{ kind: "runs"; runs: BenchRunSummary[] } | { kind: "queued"; job_ids: string[] }> {
  const raw = await sendAuth(
    "/v1/admin/bench/run",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    true,
  );
  const parsed = parseBenchRunResponse(raw);
  return parsed;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export async function pollBenchJob(jobId: string, cancelled: () => boolean): Promise<BenchJob> {
  for (;;) {
    if (cancelled()) {
      throw new Error("annulé");
    }
    await sleep(1000);
    const job = await loadBenchJob(jobId);
    if (job.status === "done" || job.status === "failed") {
      return job;
    }
  }
}

export function latestRun(
  runs: BenchRunSummary[],
  category: string,
  datasetId: string,
  effort: SearchEffort,
  engineRef?: string,
): BenchRunSummary | undefined {
  return runs.find(
    (run) =>
      run.category === category &&
      run.dataset_id === datasetId &&
      run.search_effort === effort &&
      (!engineRef || run.engine_ref === engineRef),
  );
}

export function formatDelta(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const abs = Math.abs(value).toFixed(1).replace(".", ",");
  if (value > 0) {
    return `+${abs}`;
  }
  if (value < 0) {
    return `−${abs}`;
  }
  return "0,0";
}

/** Green at 0. Red crescendo when negative, blue when positive. Intensity clamped at |delta| = 1. */
export function deltaBackground(value: number | null | undefined): string | undefined {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return undefined;
  }
  if (value === 0) {
    return "#c6e8c9";
  }
  const intensity = Math.min(1, Math.abs(value));
  const alpha = 0.18 + 0.67 * intensity;
  if (value < 0) {
    return `rgba(196, 48, 48, ${alpha})`;
  }
  return `rgba(36, 86, 196, ${alpha})`;
}

export type BenchRecapEffort = {
  effort: SearchEffort;
  mean: number | null;
  percent: number | null;
  max: number | null;
  min: number | null;
};

export type BenchModelRecap = {
  ref: string;
  prev: string;
  efforts: BenchRecapEffort[];
};

function cellGlobal(dataset: BenchVersionDataset, ref: string, effort: SearchEffort): number | null {
  const value = dataset.by_ref[ref]?.[effort]?.global;
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }
  return value;
}

function recapForEffort(
  datasets: BenchVersionDataset[],
  ref: string,
  prev: string,
  effort: SearchEffort,
): BenchRecapEffort {
  const diffs: number[] = [];
  for (const dataset of datasets) {
    const current = cellGlobal(dataset, ref, effort);
    const before = cellGlobal(dataset, prev, effort);
    if (current !== null && before !== null) {
      diffs.push(current - before);
    }
  }
  if (diffs.length === 0) {
    return { effort, mean: null, percent: null, max: null, min: null };
  }
  const mean = diffs.reduce((sum, item) => sum + item, 0) / diffs.length;
  return {
    effort,
    mean,
    percent: (100 * mean) / 10,
    max: Math.max(...diffs),
    min: Math.min(...diffs),
  };
}

export function buildBenchRecaps(versions: BenchVersions): BenchModelRecap[] {
  const recaps: BenchModelRecap[] = [];
  for (let index = 1; index < versions.engine_refs.length; index += 1) {
    const ref = versions.engine_refs[index];
    const prev = versions.engine_refs[index - 1];
    recaps.push({
      ref,
      prev,
      efforts: BENCH_EFFORTS.map((effort) => recapForEffort(versions.datasets, ref, prev, effort)),
    });
  }
  return recaps;
}

export function formatRecapPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const abs = Math.abs(value).toFixed(1).replace(".", ",");
  if (value > 0) {
    return `+${abs} %`;
  }
  if (value < 0) {
    return `−${abs} %`;
  }
  return "0,0 %";
}
