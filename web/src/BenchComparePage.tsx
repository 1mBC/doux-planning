import { useEffect, useMemo, useState } from "react";
import { AdminNav } from "./AdminPage";
import {
  benchDatasetExportFilename,
  downloadJsonFile,
  loadBenchCompare,
  loadBenchExport,
  loadBenchRun,
  type BenchCompare,
} from "./bench";
import { CycleScoreNotes } from "./cycleRecaps";
import { CONTEXT_SERVICES, type ContextServiceId } from "./context";
import { weekSheetTitle } from "./format";
import { PublishedSheet } from "./PublishedPlanning";
import { ApiHttpError } from "./sandbox";
import type { CycleAssignment, CycleSlice, SearchEffort } from "./generate";
import type { Employee } from "./types";

export type BenchCompareParams = {
  category: string;
  datasetId: string;
  effort: SearchEffort;
};

function parseEffort(value: string): SearchEffort | null {
  if (value === "minimal" || value === "optimized" || value === "maximal") {
    return value;
  }
  return null;
}

export function parseBenchComparePath(path: string): BenchCompareParams | null {
  const match = /^\/admin\/bench\/([^/]+)\/([^/]+)\/([^/]+)$/.exec(path);
  if (!match) {
    return null;
  }
  const effort = parseEffort(match[3]);
  if (!effort) {
    return null;
  }
  return { category: decodeURIComponent(match[1]), datasetId: decodeURIComponent(match[2]), effort };
}

export function parseBenchRunPath(path: string): string | null {
  const match = /^\/admin\/bench\/run\/([^/]+)$/.exec(path);
  return match ? decodeURIComponent(match[1]) : null;
}

function servicesFromAssignments(assignments: CycleAssignment[]): { id: ContextServiceId; label: string }[] {
  const ids = [...new Set(assignments.map((item) => item.service_id))];
  const known = CONTEXT_SERVICES.filter((item) => ids.includes(item.id));
  return known.length ? known : CONTEXT_SERVICES.filter((item) => item.id === "midday" || item.id === "evening");
}

function indexCycle(assignments: CycleAssignment[]): Map<string, CycleAssignment> {
  const map = new Map<string, CycleAssignment>();
  for (const shift of assignments) {
    map.set(`${shift.employee_id}:${shift.day_index}:${shift.service_id}`, shift);
  }
  return map;
}

function BenchGrids({ assignments, employees }: { assignments: CycleAssignment[]; employees: Employee[] }) {
  const services = useMemo(() => servicesFromAssignments(assignments), [assignments]);
  const byKey = useMemo(() => indexCycle(assignments), [assignments]);
  return (
    <div className="export-sheets">
      <PublishedSheet
        title={weekSheetTitle("ab", 0)}
        weekOffset={0}
        employees={employees}
        assignments={assignments}
        services={services}
        byKey={byKey}
      />
      <PublishedSheet
        title={weekSheetTitle("ab", 7)}
        weekOffset={7}
        employees={employees}
        assignments={assignments}
        services={services}
        byKey={byKey}
      />
    </div>
  );
}

function SliceNotes({ slice, employees }: { slice: CycleSlice; employees: Employee[] }) {
  return (
    <CycleScoreNotes
      score={slice.score}
      facts={slice.facts}
      stats={slice.stats}
      legalRows={slice.legal_rows}
      wishRows={slice.wish_rows}
      employees={employees}
    />
  );
}

export function BenchComparePage({
  params,
  runId,
}: {
  params: BenchCompareParams | null;
  runId?: string | null;
}) {
  const [payload, setPayload] = useState<BenchCompare | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!runId && !params) {
      setError("Page introuvable.");
      setPayload(null);
      return;
    }
    let cancelled = false;
    setError(null);
    setPayload(null);
    const request = runId
      ? loadBenchRun(runId)
      : loadBenchCompare(params!.category, params!.datasetId, params!.effort);
    request
      .then((next) => {
        if (!cancelled) {
          setPayload(next);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [runId, params?.category, params?.datasetId, params?.effort]);

  const title = payload
    ? `${payload.category} · ${payload.dataset_id} · ${payload.search_effort}`
    : params
      ? `${params.category} · ${params.datasetId} · ${params.effort}`
      : "Banc";

  async function exportDataset() {
    const category = payload?.category ?? params?.category;
    const datasetId = payload?.dataset_id ?? params?.datasetId;
    if (!category || !datasetId) {
      return;
    }
    setExporting(true);
    setError(null);
    try {
      const pack = await loadBenchExport({
        scope: "dataset",
        category,
        dataset_id: datasetId,
      });
      downloadJsonFile(pack, benchDatasetExportFilename(category, datasetId));
    } catch (err: unknown) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setExporting(false);
    }
  }

  return (
    <main className="page admin-page">
      <AdminNav current="bench" />
      <h1>{title}</h1>
      <div className="bench-toolbar-row">
        <button
          type="button"
          className="choice"
          disabled={exporting || !(payload || params)}
          onClick={() => void exportDataset()}
        >
          Exporter ce jeu
        </button>
      </div>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {!error && !payload ? <p className="sub">Chargement de la comparaison…</p> : null}
      {payload ? (
        <>
          <section>
            <h2>Modèle</h2>
            <SliceNotes slice={payload.model} employees={payload.employees} />
            <BenchGrids assignments={payload.model.assignments} employees={payload.employees} />
          </section>
          <section>
            <h2>Manuel</h2>
            <SliceNotes slice={payload.manual} employees={payload.employees} />
            <BenchGrids assignments={payload.manual.assignments} employees={payload.employees} />
          </section>
        </>
      ) : null}
    </main>
  );
}
