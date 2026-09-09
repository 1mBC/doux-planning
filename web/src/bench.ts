import {
  isRecord,
  parseCycleScore,
  parseFactsPrefer,
  PayloadError,
  requireArray,
  requireNumber,
  requireRecord,
  requireString,
} from "./api";
import { sendAuth } from "./auth";
import { parseCycleAssignment, type CycleAssignment, type SearchEffort } from "./generate";
import type { CycleScore, ScoreFact } from "./types";

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
  app_version: string;
  category: string;
  dataset_id: string;
  search_effort: SearchEffort;
  duration_seconds: number;
  score: CycleScore;
  expected_score: CycleScore;
  deltas: BenchDeltas;
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
  assignments: CycleAssignment[];
  facts: ScoreFact[];
  expected: {
    assignments: CycleAssignment[];
    score: CycleScore;
  };
};

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

export function parseBenchDatasets(value: unknown): { app_version: string; datasets: BenchDataset[] } {
  if (!isRecord(value)) {
    throw new PayloadError("réponse bench datasets invalide");
  }
  return {
    app_version: requireString(value, "app_version", "bench"),
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
    app_version: requireString(value, "app_version", path),
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
  const expectedRaw = requireRecord(value, "expected", "compare");
  const expectedScore = "score" in expectedRaw ? parseCycleScore(expectedRaw.score, "compare.expected.score") : summary.expected_score;
  return {
    ...summary,
    assignments: requireArray(value, "assignments", "compare").map((item, i) =>
      parseCycleAssignment(item, `compare.assignments[${i}]`),
    ),
    facts: parseFactsPrefer(value, "compare"),
    expected: {
      assignments: requireArray(expectedRaw, "assignments", "compare.expected").map((item, i) =>
        parseCycleAssignment(item, `compare.expected.assignments[${i}]`),
      ),
      score: expectedScore,
    },
  };
}

export async function loadBenchDatasets(): Promise<{ app_version: string; datasets: BenchDataset[] }> {
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
): BenchRunSummary | undefined {
  return runs.find((run) => run.category === category && run.dataset_id === datasetId && run.search_effort === effort);
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
