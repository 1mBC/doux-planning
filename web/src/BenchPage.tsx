import { useEffect, useMemo, useRef, useState } from "react";
import { effortLabel } from "./admin";
import { AdminNav } from "./AdminPage";
import { go } from "./AuthScreens";
import {
  BENCH_EFFORTS,
  benchBelowManuelExportFilename,
  benchDatasetExportFilename,
  buildBenchRecaps,
  downloadJsonFile,
  deltaBackground,
  formatDelta,
  formatRecapPercent,
  loadBenchExport,
  loadBenchVersions,
  pollBenchJob,
  postBenchRun,
  type BenchScope,
  type BenchVersionCell,
  type BenchVersionDataset,
  type BenchVersions,
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

function RecapStat({ label, value, text }: { label: string; value: number | null; text: string }) {
  const colored = value !== null && Number.isFinite(value);
  return (
    <span className="bench-recap-stat-wrap">
      <span className="bench-recap-stat-label">{label}</span>
      <span
        className={colored ? "bench-recap-stat" : "bench-recap-stat bench-cell-empty"}
        style={colored ? { backgroundColor: deltaBackground(value) } : undefined}
      >
        {text}
      </span>
    </span>
  );
}

function CategoryLaunch({
  categories,
  disabled,
  onLaunch,
}: {
  categories: string[];
  disabled: boolean;
  onLaunch: (effort: SearchEffort, category: string) => void;
}) {
  return (
    <div className="bench-toolbar-row">
      {BENCH_EFFORTS.map((effort) => (
        <details key={effort} className="bench-effort-menu">
          <summary className="choice">{effortLabel(effort)}</summary>
          <ul className="bench-category-list">
            {categories.map((category) => (
              <li key={category}>
                <button
                  type="button"
                  className="choice"
                  disabled={disabled}
                  onClick={(event) => {
                    const menu = event.currentTarget.closest("details");
                    if (menu) {
                      menu.open = false;
                    }
                    onLaunch(effort, category);
                  }}
                >
                  {category}
                </button>
              </li>
            ))}
          </ul>
        </details>
      ))}
    </div>
  );
}

function EngineCell({ cell }: { cell: BenchVersionCell | null }) {
  const delta = cell?.deltas.global;
  if (!cell || delta === null || delta === undefined || !Number.isFinite(delta)) {
    return <span className="bench-cell-empty">—</span>;
  }
  const label = formatDelta(delta);
  return (
    <button
      type="button"
      className="bench-cell bench-delta-cell"
      title={label}
      style={{ backgroundColor: deltaBackground(delta) }}
      onClick={() => go(`/admin/bench/run/${encodeURIComponent(cell.run_id)}`)}
    >
      {label}
    </button>
  );
}

export function BenchPage() {
  const [versions, setVersions] = useState<BenchVersions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    loadBenchVersions()
      .then((next) => {
        if (!cancelled.current) {
          setVersions(next);
        }
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
    for (const item of versions?.datasets ?? []) {
      if (!seen.includes(item.category)) {
        seen.push(item.category);
      }
    }
    return seen;
  }, [versions]);

  async function refreshVersions() {
    const next = await loadBenchVersions();
    if (!cancelled.current) {
      setVersions(next);
    }
  }

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
      await refreshVersions();
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

  async function exportDataset(dataset: BenchVersionDataset) {
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

  if (error && !versions) {
    return (
      <main className="page">
        <AdminNav current="bench" />
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!versions) {
    return (
      <main className="page">
        <AdminNav current="bench" />
        <p className="sub">Chargement du banc…</p>
      </main>
    );
  }

  const locked = busy || exporting;
  const recaps = buildBenchRecaps(versions);

  return (
    <main className="page admin-page">
      <AdminNav current="bench" />
      <p className="sub">
        Jeux salle · moteur {versions.engine_ref || "—"}. Quitter la page pendant un Maximal / lot est sans danger.
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
          <CategoryLaunch
            categories={categories}
            disabled={locked}
            onLaunch={(effort, category) => void launch({ scope: "category", category, search_effort: effort })}
          />
        </div>
      </section>

      {recaps.length > 0 ? (
        <section className="bench-recap">
          <h2>Recap</h2>
          {recaps.map((recap) => (
            <article key={`${recap.prev}->${recap.ref}`} className="bench-recap-block">
              <h3>
                {recap.ref} vs {recap.prev}
              </h3>
              <div className="bench-recap-efforts">
                {recap.efforts.map((item) => (
                  <div key={item.effort} className="bench-recap-row">
                    <span className="bench-recap-effort">{effortLabel(item.effort)}</span>
                    <RecapStat label="%" value={item.mean} text={formatRecapPercent(item.percent)} />
                    <RecapStat label="max" value={item.max} text={formatDelta(item.max)} />
                    <RecapStat label="min" value={item.min} text={formatDelta(item.min)} />
                  </div>
                ))}
              </div>
            </article>
          ))}
        </section>
      ) : null}

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
              <th rowSpan={2}>Manuel</th>
              {versions.engine_refs.map((ref) => (
                <th key={ref} colSpan={3}>
                  {ref}
                </th>
              ))}
            </tr>
            <tr>
              {versions.engine_refs.flatMap((ref) =>
                BENCH_EFFORTS.map((effort) => (
                  <th key={`${ref}-${effort}`}>{effortLabel(effort)}</th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {versions.datasets.map((dataset) => (
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
                <td>
                  <button
                    type="button"
                    className="bench-cell"
                    onClick={() => go(`/admin/bench/${dataset.category}/${dataset.id}/optimized`)}
                  >
                    {formatCycleNote(dataset.manual?.global)}
                  </button>
                </td>
                {versions.engine_refs.flatMap((ref) =>
                  BENCH_EFFORTS.map((effort) => (
                    <td key={`${ref}-${effort}`}>
                      <EngineCell cell={dataset.by_ref[ref]?.[effort] ?? null} />
                    </td>
                  )),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
