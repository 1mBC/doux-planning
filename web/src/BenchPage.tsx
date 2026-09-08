import { useEffect, useMemo, useRef, useState } from "react";
import { effortLabel } from "./admin";
import { go } from "./AuthScreens";
import {
  BENCH_EFFORTS,
  formatDelta,
  latestRun,
  loadBenchDatasets,
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

function cellText(run: BenchRunSummary | undefined): string {
  if (!run) {
    return "—";
  }
  return `${formatCycleNote(run.score.global)} · ${formatCycleNote(run.expected_score.global)} · ${formatDelta(run.deltas.global)}`;
}

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

  if (error && !datasets) {
    return (
      <main className="page">
        <h1>Banc</h1>
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!datasets) {
    return (
      <main className="page">
        <p className="sub">Chargement du banc…</p>
      </main>
    );
  }

  return (
    <main className="page admin-page">
      <h1>Banc</h1>
      <p className="sub">
        Jeux salle · moteur {appVersion || "—"}. Quitter la page pendant un Maximal / lot est sans danger.
      </p>
      <p>
        <button type="button" className="choice" onClick={() => go("/admin")}>
          ← Admin
        </button>
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
            <LaunchButtons disabled={busy} onLaunch={(effort) => void launch({ scope: "all", search_effort: effort })} />
          </div>
          {categories.map((category) => (
            <div key={category} className="bench-toolbar-row">
              <span>{category}</span>
              <LaunchButtons
                disabled={busy}
                onLaunch={(effort) => void launch({ scope: "category", category, search_effort: effort })}
              />
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2>Derniers runs</h2>
        <table className="admin-table bench-table">
          <thead>
            <tr>
              <th>Catégorie</th>
              <th>Jeu</th>
              <th>Défi</th>
              <th>Lancer</th>
              {BENCH_EFFORTS.map((effort) => (
                <th key={effort}>{effortLabel(effort)}</th>
              ))}
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
                  <LaunchButtons
                    disabled={busy}
                    onLaunch={(effort) =>
                      void launch({
                        scope: "dataset",
                        category: dataset.category,
                        dataset_id: dataset.id,
                        search_effort: effort,
                      })
                    }
                  />
                </td>
                {BENCH_EFFORTS.map((effort) => {
                  const run = latestRun(runs, dataset.category, dataset.id, effort);
                  return (
                    <td key={effort}>
                      <button
                        type="button"
                        className="bench-cell"
                        onClick={() => go(`/admin/bench/${dataset.category}/${dataset.id}/${effort}`)}
                      >
                        {cellText(run)}
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
