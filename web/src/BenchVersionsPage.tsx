import { useEffect, useState } from "react";
import { AdminNav } from "./AdminPage";
import { go } from "./AuthScreens";
import { formatDelta, loadBenchVersions, type BenchVersions } from "./bench";
import { formatCycleNote } from "./format";
import { ApiHttpError } from "./sandbox";

export function BenchVersionsPage() {
  const [payload, setPayload] = useState<BenchVersions | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadBenchVersions()
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
  }, []);

  if (error && !payload) {
    return (
      <main className="page">
        <AdminNav current="versions" />
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!payload) {
    return (
      <main className="page">
        <AdminNav current="versions" />
        <p className="sub">Chargement des versions…</p>
      </main>
    );
  }

  return (
    <main className="page admin-page">
      <AdminNav current="versions" />
      <p className="sub">Maximal par moteur · courant {payload.engine_ref || "—"}.</p>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      <section>
        <h2>Versions</h2>
        <table className="admin-table bench-table">
          <thead>
            <tr>
              <th>Catégorie</th>
              <th>Jeu</th>
              <th>Défi</th>
              {payload.engine_refs.map((ref) => (
                <th key={ref}>{ref}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {payload.datasets.map((dataset) => (
              <tr key={`${dataset.category}/${dataset.id}`}>
                <td>{dataset.category}</td>
                <td>
                  {dataset.id}
                  <div className="bench-name">{dataset.name}</div>
                </td>
                <td className="bench-challenge">{dataset.challenge_fr}</td>
                {payload.engine_refs.map((ref) => {
                  const cell = dataset.by_ref[ref]?.maximal ?? null;
                  if (!cell) {
                    return (
                      <td key={ref}>
                        <span className="bench-cell-empty">—</span>
                      </td>
                    );
                  }
                  const label = `${formatCycleNote(cell.global)} ${formatDelta(cell.deltas.global)}`;
                  return (
                    <td key={ref}>
                      <button
                        type="button"
                        className="bench-cell bench-version-cell"
                        title={label}
                        onClick={() => go(`/admin/bench/run/${encodeURIComponent(cell.run_id)}`)}
                      >
                        <span>{formatCycleNote(cell.global)}</span>
                        <span className="bench-version-delta">{formatDelta(cell.deltas.global)}</span>
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
