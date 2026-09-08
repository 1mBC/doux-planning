import { useEffect, useMemo, useState } from "react";
import { go } from "./AuthScreens";
import { loadBenchCompare, type BenchCompare } from "./bench";
import { CycleScoreNotes } from "./cycleRecaps";
import { CONTEXT_SERVICES, type ContextServiceId } from "./context";
import { weekSheetTitle } from "./format";
import { PublishedSheet } from "./PublishedPlanning";
import { ApiHttpError } from "./sandbox";
import type { CycleAssignment, SearchEffort } from "./generate";
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

function peopleFromAssignments(assignments: CycleAssignment[]): Employee[] {
  const ids: string[] = [];
  for (const shift of assignments) {
    if (!ids.includes(shift.employee_id)) {
      ids.push(shift.employee_id);
    }
  }
  return ids.map((id) => ({
    id,
    name: id,
    role: { name: "Salle", level: 1, team: "salle" },
    team: "salle",
  }));
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

function BenchGrids({ assignments }: { assignments: CycleAssignment[] }) {
  const people = useMemo(() => peopleFromAssignments(assignments), [assignments]);
  const services = useMemo(() => servicesFromAssignments(assignments), [assignments]);
  const byKey = useMemo(() => indexCycle(assignments), [assignments]);
  return (
    <div className="export-sheets">
      <PublishedSheet
        title={weekSheetTitle("ab", 0)}
        weekOffset={0}
        employees={people}
        assignments={assignments}
        services={services}
        byKey={byKey}
      />
      <PublishedSheet
        title={weekSheetTitle("ab", 7)}
        weekOffset={7}
        employees={people}
        assignments={assignments}
        services={services}
        byKey={byKey}
      />
    </div>
  );
}

export function BenchComparePage({ params }: { params: BenchCompareParams | null }) {
  const [payload, setPayload] = useState<BenchCompare | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params) {
      setError("Page introuvable.");
      setPayload(null);
      return;
    }
    let cancelled = false;
    setError(null);
    setPayload(null);
    loadBenchCompare(params.category, params.datasetId, params.effort)
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
  }, [params?.category, params?.datasetId, params?.effort]);

  const title = params ? `${params.category} · ${params.datasetId} · ${params.effort}` : "Banc";

  return (
    <main className="page admin-page">
      <h1>{title}</h1>
      <p>
        <button type="button" className="choice" onClick={() => go("/admin/bench")}>
          ← Banc
        </button>
      </p>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {!error && !payload ? <p className="sub">Chargement de la comparaison…</p> : null}
      {payload ? (
        <>
          <section>
            <h2>Planning généré</h2>
            <CycleScoreNotes score={payload.score} />
            <BenchGrids assignments={payload.assignments} />
          </section>
          <section>
            <h2>Planning oracle</h2>
            <CycleScoreNotes score={payload.expected.score} />
            <BenchGrids assignments={payload.expected.assignments} />
          </section>
        </>
      ) : null}
    </main>
  );
}
