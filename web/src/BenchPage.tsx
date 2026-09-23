import { useEffect, useMemo, useRef, useState, type ChangeEvent } from "react";
import { effortLabel } from "./admin";
import { AdminNav } from "./AdminPage";
import { go } from "./AuthScreens";
import {
  BENCH_EFFORTS,
  benchBankExportFilename,
  benchBelowManuelExportFilename,
  benchDatasetExportFilename,
  cancelBenchBatch,
  deleteBenchDataset,
  downloadJsonFile,
  deltaBackground,
  loadActiveBenchBatch,
  loadBenchExport,
  loadBenchVersions,
  pollBenchBatch,
  postBenchRun,
  putBenchEngine,
  type BenchBatch,
  type BenchOrigin,
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

function datasetHoverTitle(dataset: BenchVersionDataset): string {
  if (dataset.comment != null) {
    return `${dataset.challenge_fr}\n${dataset.comment}`;
  }
  return dataset.challenge_fr;
}

function DatasetRowMenu({
  open,
  disabled,
  onToggle,
  onClose,
  onLaunch,
  onExport,
  onDelete,
}: {
  open: boolean;
  disabled: boolean;
  onToggle: () => void;
  onClose: () => void;
  onLaunch: (effort: SearchEffort) => void;
  onExport: () => void;
  onDelete: () => void;
}) {
  const rootRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!open) {
      return;
    }
    function onPointerDown(event: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(event.target as Node)) {
        onCloseRef.current();
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCloseRef.current();
      }
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div className="bench-dataset-menu" ref={rootRef}>
      <button
        type="button"
        className="choice bench-dataset-menu-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label="Actions du jeu"
        onClick={onToggle}
      >
        …
      </button>
      {open ? (
        <div className="bench-dataset-menu-list" role="menu">
          {BENCH_EFFORTS.map((effort) => (
            <button
              key={effort}
              type="button"
              role="menuitem"
              className="choice"
              disabled={disabled}
              onClick={() => {
                onClose();
                onLaunch(effort);
              }}
            >
              {`Lancer ${effortLabel(effort)}`}
            </button>
          ))}
          <button
            type="button"
            role="menuitem"
            className="choice"
            disabled={disabled}
            onClick={() => {
              onClose();
              onExport();
            }}
          >
            Exporter ce jeu
          </button>
          <button
            type="button"
            role="menuitem"
            className="choice"
            disabled={disabled}
            onClick={() => {
              onClose();
              onDelete();
            }}
          >
            Supprimer…
          </button>
        </div>
      ) : null}
    </div>
  );
}

function formatDeltaX10(value: number): string {
  const x10 = Math.round(value * 10);
  if (x10 > 0) {
    return `+${x10}`;
  }
  if (x10 < 0) {
    return `−${Math.abs(x10)}`;
  }
  return "0";
}

function formatGapX10(gap: number): string {
  const x10 = Math.round(gap * 10);
  if (x10 >= 0) {
    return "0";
  }
  return `−${Math.abs(x10)}`;
}

function gapTextColor(gap: number): string {
  const absGap = Math.abs(Math.round(gap * 10));
  const intensity = Math.min(1, absGap / 10);
  const lightness = 50 - 20 * intensity;
  return `hsl(0, 70%, ${lightness}%)`;
}

function EngineCellBest({
  cell,
  manualGlobal,
}: {
  cell: BenchVersionCell;
  manualGlobal: number | null;
}) {
  const delta = manualGlobal !== null ? cell.global! - manualGlobal : 0;
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
    </button>
  );
}

function EngineCellGap({
  cell,
  gap,
}: {
  cell: BenchVersionCell;
  gap: number;
}) {
  const label = formatGapX10(gap);
  return (
    <button
      type="button"
      className="bench-cell bench-gap-cell"
      title={`${label} vs meilleur`}
      style={{ color: gapTextColor(gap) }}
      onClick={() => go(`/admin/bench/run/${encodeURIComponent(cell.run_id)}`)}
    >
      {label}
    </button>
  );
}

function EngineRowCell({
  cell,
  bestGlobal,
  manualGlobal,
}: {
  cell: BenchVersionCell | null;
  bestGlobal: number | null;
  manualGlobal: number | null;
}) {
  if (!cell || cell.global === null || cell.global === undefined || !Number.isFinite(cell.global)) {
    return <span className="bench-cell-empty">—</span>;
  }
  if (bestGlobal === null || cell.global === bestGlobal) {
    return <EngineCellBest cell={cell} manualGlobal={manualGlobal} />;
  }
  const gap = cell.global - bestGlobal;
  return <EngineCellGap cell={cell} gap={gap} />;
}

function EngineStack({
  dataset,
  engineRef,
  engineRefs,
}: {
  dataset: BenchVersionDataset;
  engineRef: string;
  engineRefs: string[];
}) {
  const manualGlobal = dataset.manual?.global ?? null;

  return (
    <div className="bench-engine-stack">
      {BENCH_EFFORTS.map((effort) => {
        const allCells = engineRefs.map((ref) => dataset.by_ref[ref]?.[effort] ?? null);
        const validGlobals = allCells
          .filter((c): c is BenchVersionCell => c !== null && c.global !== null && Number.isFinite(c.global))
          .map((c) => c.global!);
        const bestGlobal = validGlobals.length > 0 ? Math.max(...validGlobals) : null;
        const cell = dataset.by_ref[engineRef]?.[effort] ?? null;
        return (
          <EngineRowCell
            key={effort}
            cell={cell}
            bestGlobal={bestGlobal}
            manualGlobal={manualGlobal}
          />
        );
      })}
    </div>
  );
}

export function BenchPage({ origin }: { origin: BenchOrigin }) {
  const [versions, setVersions] = useState<BenchVersions | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [batch, setBatch] = useState<BenchBatch | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [savingEngine, setSavingEngine] = useState(false);
  const [openMenuKey, setOpenMenuKey] = useState<string | null>(null);
  const cancelled = useRef(false);
  const navCurrent = origin === "imported" ? "bench-manuels" : "bench";
  const title = origin === "imported" ? "Banc Manuels" : "Banc IA";

  async function refreshVersions() {
    const next = await loadBenchVersions(origin);
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

  async function handleCancelBatch() {
    if (!batch) return;
    setCancelling(true);
    try {
      await cancelBenchBatch(batch.batch_id);
      cancelled.current = true;
      setBatch(null);
      await refreshVersions();
    } catch (err: unknown) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setCancelling(false);
      setBusy(false);
    }
  }

  useEffect(() => {
    cancelled.current = false;
    loadBenchVersions(origin)
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
  }, [origin]);

  const pageDatasets = useMemo(() => {
    return (versions?.datasets ?? []).filter((item) => item.origin === origin);
  }, [versions, origin]);

  const categories = useMemo(() => {
    const seen: string[] = [];
    for (const item of pageDatasets) {
      if (!seen.includes(item.category)) {
        seen.push(item.category);
      }
    }
    return seen;
  }, [pageDatasets]);

  function closeMenu() {
    setOpenMenuKey(null);
  }

  async function launch(body: {
    scope: BenchScope;
    category?: string;
    dataset_id?: string;
    search_effort?: SearchEffort;
    engine_ref?: string;
  }) {
    setBusy(true);
    setError(null);
    try {
      const payload = body.scope === "dataset" ? { ...body } : { ...body, origin };
      if (payload.scope === "gaps") {
        delete payload.engine_ref;
      }
      const result = await postBenchRun(payload);
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
      const pack = await loadBenchExport({ scope: "bank", origin });
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
      const pack = await loadBenchExport({ scope: "below_manuel", origin });
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

  async function removeDataset(dataset: BenchVersionDataset) {
    if (!window.confirm("Supprimer ce jeu et tous ses résultats ?")) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await deleteBenchDataset(dataset.category, dataset.id);
      if (cancelled.current) {
        return;
      }
      await refreshVersions();
    } catch (err: unknown) {
      if (!cancelled.current) {
        setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
      }
    } finally {
      if (!cancelled.current) {
        setBusy(false);
      }
    }
  }

  async function changeBenchEngine(event: ChangeEvent<HTMLSelectElement>) {
    const previous = versions?.engine_ref ?? "";
    const next = event.target.value;
    if (!previous || next === previous || savingEngine) {
      event.target.value = previous;
      return;
    }
    setSavingEngine(true);
    try {
      const saved = await putBenchEngine(next);
      if (cancelled.current) {
        return;
      }
      setVersions((current) => (current ? { ...current, engine_ref: saved.engine_ref } : current));
      setError(null);
    } catch (err: unknown) {
      event.target.value = previous;
      if (!cancelled.current) {
        setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
      }
    } finally {
      if (!cancelled.current) {
        setSavingEngine(false);
      }
    }
  }

  if (error && !versions) {
    return (
      <main className="page">
        <AdminNav current={navCurrent} />
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!versions) {
    return (
      <main className="page">
        <AdminNav current={navCurrent} />
        <p className="sub">Chargement du banc…</p>
      </main>
    );
  }

  const locked = busy || exporting;
  const benchEngine = versions.engine_ref;

  return (
    <main className="page admin-page">
      <AdminNav current={navCurrent} />
      <h1>{title}</h1>
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
            <button
              type="button"
              className="bench-cancel-btn"
              disabled={cancelling}
              onClick={() => void handleCancelBatch()}
            >
              {cancelling ? "Annulation..." : "Annuler"}
            </button>
          </div>
        ) : null}
        <div className="bench-toolbar">
          <div className="bench-toolbar-row">
            <select
              className="bench-engine-select"
              value={benchEngine}
              onChange={(event) => void changeBenchEngine(event)}
              disabled={locked || savingEngine}
            >
              {versions.engine_refs.map((ref) => (
                <option key={ref} value={ref}>
                  {ref}
                </option>
              ))}
            </select>
            <span>Toutes les catégories</span>
            <LaunchButtons disabled={locked} onLaunch={(effort) => void launch({ scope: "all", search_effort: effort, engine_ref: benchEngine })} />
          </div>
          {origin === "catalogue" ? (
            <CategoryLaunch
              categories={categories}
              disabled={locked}
              onLaunch={(effort, category) => void launch({ scope: "category", category, search_effort: effort, engine_ref: benchEngine })}
            />
          ) : null}
          <div className="bench-toolbar-row">
            <button type="button" className="choice" disabled={locked} onClick={() => void launch({ scope: "gaps" })}>
              Compléter les trous
            </button>
          </div>
          <div className="bench-toolbar-row">
            <button type="button" className="choice" disabled={exporting} onClick={() => void exportBelowManuel()}>
              Exporter sous le Manuel
            </button>
            <button type="button" className="choice" disabled={exporting} onClick={() => void exportBank()}>
              Exporter tout le banc
            </button>
          </div>
        </div>
      </section>

      <section>
        <h2>Derniers runs</h2>
        {pageDatasets.length === 0 ? (
          <p className="sub">Aucun jeu.</p>
        ) : (
          <table className="admin-table bench-table">
            <thead>
              <tr>
                <th>Catégorie</th>
                <th>Jeu</th>
                <th>Manuel</th>
                {versions.engine_refs.map((ref) => (
                  <th key={ref}>{ref}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageDatasets.map((dataset) => {
                const menuKey = `${dataset.category}/${dataset.id}`;
                return (
                  <tr key={menuKey}>
                    <td>{dataset.category}</td>
                    <td>
                      <div className="bench-game-text" title={datasetHoverTitle(dataset)}>
                        {dataset.id}
                        <div className="bench-name">{dataset.name}</div>
                      </div>
                      <DatasetRowMenu
                        open={openMenuKey === menuKey}
                        disabled={locked}
                        onToggle={() => setOpenMenuKey(openMenuKey === menuKey ? null : menuKey)}
                        onClose={closeMenu}
                        onLaunch={(effort) =>
                          void launch({
                            scope: "dataset",
                            category: dataset.category,
                            dataset_id: dataset.id,
                            search_effort: effort,
                            engine_ref: benchEngine,
                          })
                        }
                        onExport={() => void exportDataset(dataset)}
                        onDelete={() => void removeDataset(dataset)}
                      />
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
                    {versions.engine_refs.map((ref) => (
                      <td key={ref}>
                        <EngineStack
                          dataset={dataset}
                          engineRef={ref}
                          engineRefs={versions.engine_refs}
                        />
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </main>
  );
}
