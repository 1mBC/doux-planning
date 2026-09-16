import { useEffect, useMemo, useRef, useState } from "react";
import { effortLabel } from "./admin";
import { AdminNav } from "./AdminPage";
import { go } from "./AuthScreens";
import {
  BENCH_EFFORTS,
  benchBankExportFilename,
  benchBelowManuelExportFilename,
  benchDatasetExportFilename,
  downloadJsonFile,
  deltaBackground,
  loadActiveBenchBatch,
  loadBenchExport,
  loadBenchVersions,
  pollBenchBatch,
  postBenchRun,
  type BenchBatch,
  type BenchScope,
  type BenchVersionCell,
  type BenchVersionDataset,
  type BenchVersions,
} from "./bench";
import { formatCycleNote, formatSolveDuration } from "./format";
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

function formatDeltaX10(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "—";
  }
  const x10 = Math.round(value * 10);
  if (x10 > 0) {
    return `+${x10}`;
  }
  if (x10 < 0) {
    return `−${Math.abs(x10)}`;
  }
  return "0";
}

function DeltaIndicator({ current, previous }: { current: number | null; previous: number | null }) {
  if (current === null || previous === null || !Number.isFinite(current) || !Number.isFinite(previous)) {
    return null;
  }
  const diff = current - previous;
  const diffX10 = Math.round(diff * 10);
  if (diffX10 === 0) {
    return <span className="bench-indicator bench-indicator-equal" aria-label="égal" />;
  }
  const absDiff = Math.abs(diffX10);
  const intensity = Math.min(1, absDiff / 10);
  if (diffX10 > 0) {
    return (
      <span
        className="bench-indicator bench-indicator-up"
        style={{ "--indicator-intensity": intensity } as React.CSSProperties}
        aria-label={`+${absDiff}`}
      >
        <span className="bench-indicator-arrow">↑</span>
        <span className="bench-indicator-value">{absDiff}</span>
      </span>
    );
  }
  return (
    <span
      className="bench-indicator bench-indicator-down"
      style={{ "--indicator-intensity": intensity } as React.CSSProperties}
      aria-label={`−${absDiff}`}
    >
      <span className="bench-indicator-arrow">↓</span>
      <span className="bench-indicator-value">{absDiff}</span>
    </span>
  );
}

function EngineCell({
  cell,
  prevCell,
  isFirst,
}: {
  cell: BenchVersionCell | null;
  prevCell: BenchVersionCell | null;
  isFirst: boolean;
}) {
  const delta = cell?.deltas.global;
  if (!cell || delta === null || delta === undefined || !Number.isFinite(delta)) {
    return <span className="bench-cell-empty">—</span>;
  }
  const label = formatDeltaX10(delta);
  return (
    <button
      type="button"
      className="bench-cell bench-delta-cell-wrap"
      title={`${label} (×10)`}
      onClick={() => go(`/admin/bench/run/${encodeURIComponent(cell.run_id)}`)}
    >
      <span className="bench-delta-bubble" style={{ backgroundColor: deltaBackground(delta) }}>
        {label}
      </span>
      {!isFirst && <DeltaIndicator current={cell.global} previous={prevCell?.global ?? null} />}
    </button>
  );
}

function EngineStack({
  dataset,
  engineRef,
  prevRef,
  isFirst,
}: {
  dataset: BenchVersionDataset;
  engineRef: string;
  prevRef: string | null;
  isFirst: boolean;
}) {
  return (
    <div className="bench-engine-stack">
      {BENCH_EFFORTS.map((effort) => (
        <EngineCell
          key={effort}
          cell={dataset.by_ref[engineRef]?.[effort] ?? null}
          prevCell={prevRef ? dataset.by_ref[prevRef]?.[effort] ?? null : null}
          isFirst={isFirst}
        />
      ))}
    </div>
  );
}

export function BenchPage() {
  const [versions, setVersions] = useState<BenchVersions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [batch, setBatch] = useState<BenchBatch | null>(null);
  const cancelled = useRef(false);

  async function refreshVersions() {
    const next = await loadBenchVersions();
    if (!cancelled.current) {
      setVersions(next);
    }
  }

  async function watchBatch(batchId: string) {
    setBusy(true);
    try {
      await pollBenchBatch(batchId, () => cancelled.current, (progress) => {
        if (!cancelled.current) {
          setBatch(progress);
        }
      });
      if (cancelled.current) {
        return;
      }
      setBatch(null);
      await refreshVersions();
    } catch (err: unknown) {
      if (err instanceof Error && err.message === "annulé") {
        return;
      }
      throw err;
    } finally {
      if (!cancelled.current) {
        setBusy(false);
      }
    }
  }

  useEffect(() => {
    cancelled.current = false;
    loadBenchVersions()
      .then(async (next) => {
        if (cancelled.current) {
          return;
        }
        setVersions(next);
        const active = await loadActiveBenchBatch();
        if (cancelled.current || !active || active.pct >= 100) {
          return;
        }
        setBatch(active);
        await watchBatch(active.batch_id);
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

  async function launch(body: { scope: BenchScope; category?: string; dataset_id?: string; search_effort?: SearchEffort }) {
    setBusy(true);
    setError(null);
    try {
      const result = await postBenchRun(body);
      if (result.kind === "queued") {
        setBatch({
          batch_id: result.batch_id,
          total: result.total,
          queued: result.total,
          running: 0,
          done: 0,
          failed: 0,
          pct: 0,
          eta_max_seconds: 0,
        });
        await watchBatch(result.batch_id);
        return;
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

  async function exportBank() {
    setExporting(true);
    setError(null);
    try {
      const pack = await loadBenchExport({ scope: "bank" });
      if (cancelled.current) {
        return;
      }
      downloadJsonFile(pack, benchBankExportFilename());
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

      <section>
        <h2>Lancer</h2>
        {batch ? (
          <div className="bench-batch-status" role="status" aria-live="polite">
            <p>{`${Math.round(batch.pct)} %`}</p>
            <p>{`~ ${formatSolveDuration(batch.eta_max_seconds)}`}</p>
          </div>
        ) : null}
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
          <div className="bench-toolbar-row">
            <button type="button" className="choice" disabled={locked} onClick={() => void launch({ scope: "gaps" })}>
              Compléter les trous
            </button>
          </div>
        </div>
      </section>

      <section>
        <h2>Derniers runs</h2>
        <div className="bench-toolbar-row">
          <button type="button" className="choice" disabled={exporting} onClick={() => void exportBelowManuel()}>
            Exporter sous le Manuel
          </button>
          <button type="button" className="choice" disabled={exporting} onClick={() => void exportBank()}>
            Exporter tout le banc
          </button>
        </div>
        <table className="admin-table bench-table">
          <thead>
            <tr>
              <th>Catégorie</th>
              <th>Jeu</th>
              <th>Défi</th>
              <th>Lancer</th>
              <th>Manuel</th>
              {versions.engine_refs.map((ref) => (
                <th key={ref}>{ref}</th>
              ))}
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
                    <button type="button" className="choice" disabled={exporting} onClick={() => void exportDataset(dataset)}>
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
                {versions.engine_refs.map((ref, refIndex) => (
                  <td key={ref}>
                    <EngineStack
                      dataset={dataset}
                      engineRef={ref}
                      prevRef={refIndex > 0 ? versions.engine_refs[refIndex - 1] : null}
                      isFirst={refIndex === 0}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
