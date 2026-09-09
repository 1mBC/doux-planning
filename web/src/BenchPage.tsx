import { useEffect, useMemo, useRef, useState } from "react";
import { effortLabel } from "./admin";
import { AdminNav } from "./AdminPage";
import { go } from "./AuthScreens";
import {
  BENCH_EFFORTS,
  benchBelowManuelExportFilename,
  benchDatasetExportFilename,
  downloadJsonFile,
  formatDelta,
  latestRun,
  loadBenchDatasets,
  loadBenchExport,
  loadBenchRuns,
  pollBenchJob,
  postBenchRun,
  type BenchDataset,
  type BenchRunSummary,
  type BenchScope,
} from "./bench";
import { formatCycleNote } from "./format";
import { ApiHttpError } from "./sandbox";
import type { SearchEffort } from "./generate";

function LaunchButtons({
  disabled,
  onLaunch,
}: {
  disabled: boolean;
  onLaunch: (effort: SearchEffort) => void;
}) {
  return (
    <div className="bench-launch">
      {BENCH_EFFORTS.map((effort) => (
        <button key={effort} type="button" className="choice" disabled={disabled} onClick={() => onLaunch(effort)}>
          {effortLabel(effort)}
        </button>
      ))}
    </div>
  );
}

export function BenchPage() {
  const [datasets, setDatasets] = useState<BenchDataset[] | null>(null);
  const [appVersion, setAppVersion] = useState("");
  const [runs, setRuns] = useState<BenchRunSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    Promise.all([loadBenchDatasets(), loadBenchRuns()])
      .then(([catalog, listed]) => {
        if (cancelled.current) {
          return;
        }
        setAppVersion(catalog.app_version);
        setDatasets(catalog.datasets);
        setRuns(listed.runs);
      })
      .catch((err: unknown) => {
        if (!cancelled.current) {
          setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
        }
      });
    return () => {
      cancelled.current = true;
    };
  }, []);

  const categories = useMemo(() => {
    const seen: string[] = [];
    for (const item of datasets ?? []) {
      if (!seen.includes(item.category)) {
        seen.push(item.category);
      }
    }
    return seen;
  }, [datasets]);

  async function launch(body: { scope: BenchScope; category?: string; dataset_id?: string; search_effort: SearchEffort }) {
    setBusy(true);
    setError(null);
    try {
      const result = await postBenchRun(body);
      if (result.kind === "queued") {
        await Promise.all(result.job_ids.map((id) => pollBenchJob(id, () => cancelled.current)));
      }
      if (cancelled.current) {
        return;
      }
      const listed = await loadBenchRuns();
      if (!cancelled.current) {
        setRuns(listed.runs);
      }
    } catch (err: unknown) {
      if (cancelled.current) {
        return;
      }
      if (err instanceof Error && err.message === "annulé") {
        return;
      }
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      if (!cancelled.current) {
        setBusy(false);
      }
    }
  }

  async function exportDataset(dataset: BenchDataset) {
    setExporting(true);
    setError(null);
    try {
      const pack = await loadBenchExport({
        scope: "dataset",
        category: dataset.category,
        dataset_id: dataset.id,
      });
      if (cancelled.current) {
        return;
      }
      downloadJsonFile(pack, benchDatasetExportFilename(dataset.category, dataset.id));
    } catch (err: unknown) {
      if (!cancelled.current) {
        setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
      }
    } finally {
      if (!cancelled.current) {
        setExporting(false);
      }
    }
  }

  async function exportBelowManuel() {
    setExporting(true);
    setError(null);
    try {
      const pack = await loadBenchExport({ scope: "below_manuel" });
      if (cancelled.current) {
        return;
      }
      downloadJsonFile(pack, benchBelowManuelExportFilename());
    } catch (err: unknown) {
      if (!cancelled.current) {
        setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
      }
    } finally {
      if (!cancelled.current) {
        setExporting(false);
      }
    }
  }

  if (error && !datasets) {
    return (
      <main className="page">
        <AdminNav current="bench" />
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!datasets) {
    return (
      <main className="page">
        <AdminNav current="bench" />
        <p className="sub">Chargement du banc…</p>
      </main>
    );
  }

  const locked = busy || exporting;

  return (
    <main className="page admin-page">
      <AdminNav current="bench" />
      <p className="sub">
        Jeux salle · moteur {appVersion || "—"}. Quitter la page pendant un Maximal / lot est sans danger.
      </p>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {busy ? (
        <div className="calc-overlay" role="status" aria-live="polite">
          <p>Calcul en cours…</p>
        </div>
      ) : null}

      <section>
        <h2>Lancer</h2>
        <div className="bench-toolbar">
          <div className="bench-toolbar-row">
            <span>Toutes les catégories</span>
            <LaunchButtons disabled={locked} onLaunch={(effort) => void launch({ scope: "all", search_effort: effort })} />
          </div>
          {categories.map((category) => (
            <div key={category} className="bench-toolbar-row">
              <span>{category}</span>
              <LaunchButtons
                disabled={locked}
                onLaunch={(effort) => void launch({ scope: "category", category, search_effort: effort })}
              />
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Derniers runs</h2>
        <div className="bench-toolbar-row">
          <button type="button" className="choice" disabled={locked} onClick={() => void exportBelowManuel()}>
            Exporter sous le Manuel
          </button>
        </div>
        <table className="admin-table bench-table">
          <thead>
            <tr>
              <th rowSpan={2}>Catégorie</th>
              <th rowSpan={2}>Jeu</th>
              <th rowSpan={2}>Défi</th>
              <th rowSpan={2}>Lancer</th>
              {BENCH_EFFORTS.map((effort) => (
                <th key={effort} colSpan={3}>
                  {effortLabel(effort)}
                </th>
              ))}
            </tr>
            <tr>
              {BENCH_EFFORTS.flatMap((effort) =>
                (["Modèle", "Manuel", "Delta"] as const).map((label) => (
                  <th key={`${effort}-${label}`}>{label}</th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {datasets.map((dataset) => (
              <tr key={`${dataset.category}/${dataset.id}`}>
                <td>{dataset.category}</td>
                <td>
                  {dataset.id}
                  <div className="bench-name">{dataset.name}</div>
                </td>
                <td className="bench-challenge">{dataset.challenge_fr}</td>
                <td>
                  <div className="bench-row-actions">
                    <LaunchButtons
                      disabled={locked}
                      onLaunch={(effort) =>
                        void launch({
                          scope: "dataset",
                          category: dataset.category,
                          dataset_id: dataset.id,
                          search_effort: effort,
                        })
                      }
                    />
                    <button type="button" className="choice" disabled={locked} onClick={() => void exportDataset(dataset)}>
                      Exporter ce jeu
                    </button>
                  </div>
                </td>
                {BENCH_EFFORTS.flatMap((effort) => {
                  const run = latestRun(runs, dataset.category, dataset.id, effort);
                  const open = () => go(`/admin/bench/${dataset.category}/${dataset.id}/${effort}`);
                  return [
                    <td key={`${effort}-modele`}>
                      <button type="button" className="bench-cell" onClick={open}>
                        {formatCycleNote(run?.score.global)}
                      </button>
                    </td>,
                    <td key={`${effort}-manuel`}>
                      <button type="button" className="bench-cell" onClick={open}>
                        {formatCycleNote(run?.expected_score.global)}
                      </button>
                    </td>,
                    <td key={`${effort}-delta`}>
                      <button type="button" className="bench-cell" onClick={open}>
                        {formatDelta(run?.deltas.global)}
                      </button>
                    </td>,
                  ];
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
