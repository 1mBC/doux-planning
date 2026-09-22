import { useCallback, useEffect, useState, type FormEvent, type MouseEvent, type ReactNode } from "react";
import {
  copyToClipboard,
  effortLabel,
  groupEntriesByParisDay,
  loadAdminGenerates,
  loadAdminRestaurantContext,
  loadAdminRestaurantCycles,
  loadImportPreview,
  loadLiveEngine,
  mintImpersonateLink,
  parisClock,
  postBenchImport,
  putLiveEngine,
  teamLabel,
  type AdminGenerateEntry,
  type ImportPreview,
  type ImportPreviewTeam,
  type LiveEngine,
} from "./admin";
import { PayloadError } from "./api";
import { formatCycleNote, formatSolveDuration, warningWhen } from "./format";
import { factSeverityLabel, factTitle, formatFactLine } from "./scoreFacts";
import { ApiHttpError } from "./sandbox";
import { go } from "./AuthScreens";
import { PublishedPlanning } from "./PublishedPlanning";
import type { ScoreFact } from "./types";

type AdminToast = {
  text: string;
  action?: { label: string; path: string };
};

type BenchImportTarget = {
  restaurant_id: string;
  restaurant_name: string;
  email: string;
};

function yesNo(value: boolean): string {
  return value ? "oui" : "non";
}

function TeamImportPreview({ team, label }: { team: ImportPreviewTeam; label: string }) {
  return (
    <div className="bench-import-team">
      <strong>{label}</strong>
      <ul>
        <li>Prêt : {yesNo(team.ready)}</li>
        <li>Manuel publié : {yesNo(team.manuel_published)}</li>
        <li>
          Computes : Minimal {yesNo(team.computes_published.minimal)} · Optimisé{" "}
          {yesNo(team.computes_published.optimized)} · Maximal {yesNo(team.computes_published.maximal)}
        </li>
      </ul>
    </div>
  );
}

function BenchImportPopup({
  target,
  onClose,
  onImported,
}: {
  target: BenchImportTarget;
  onClose: () => void;
  onImported: () => void;
}) {
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [includeSalle, setIncludeSalle] = useState(true);
  const [includeCuisine, setIncludeCuisine] = useState(true);
  const [includeManuel, setIncludeManuel] = useState(true);
  const [includeRuns, setIncludeRuns] = useState(true);
  const [manualScore, setManualScore] = useState("");
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setPreview(null);
    setPreviewError(null);
    loadImportPreview(target.restaurant_id)
      .then((next) => {
        if (!cancelled) {
          setPreview(next);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setPreviewError(
            err instanceof ApiHttpError || err instanceof PayloadError
              ? err.message
              : err instanceof Error
                ? err.message
                : "erreur inattendue",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [target.restaurant_id]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const trimmedScore = manualScore.trim();
    let score: number | null = null;
    if (trimmedScore !== "") {
      const parsed = Number(trimmedScore);
      score = Number.isFinite(parsed) ? parsed : null;
    }
    const trimmedComment = comment.trim();
    setBusy(true);
    setSubmitError(null);
    try {
      await postBenchImport({
        restaurant_id: target.restaurant_id,
        include_salle: includeSalle,
        include_cuisine: includeCuisine,
        include_manuel: includeManuel,
        include_runs: includeRuns,
        manual_score: score,
        comment: trimmedComment === "" ? null : trimmedComment,
      });
      onImported();
    } catch (err: unknown) {
      setSubmitError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
      setBusy(false);
    }
  }

  return (
    <div className="overlay-backdrop" role="presentation" onClick={onClose}>
      <div
        className="overlay bench-import-popup"
        role="dialog"
        aria-labelledby="bench-import-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h3 id="bench-import-title">{target.restaurant_name || "Sans nom"}</h3>
        <p className="sub">{target.email}</p>
        <section className="bench-import-preview" aria-label="complet ?">
          <h4>complet ?</h4>
          {previewError ? (
            <p className="error" role="alert">
              {previewError}
            </p>
          ) : preview ? (
            <>
              <TeamImportPreview team={preview.salle} label="Salle" />
              <TeamImportPreview team={preview.cuisine} label="Cuisine" />
              <p>Generates : {preview.generate_count}</p>
            </>
          ) : (
            <p className="sub">Chargement du résumé…</p>
          )}
        </section>
        <form onSubmit={(event) => void onSubmit(event)}>
          <fieldset className="bench-import-checks">
            <legend>Inclure</legend>
            <label>
              <input
                type="checkbox"
                checked={includeSalle}
                onChange={(event) => setIncludeSalle(event.target.checked)}
              />
              Salle
            </label>
            <label>
              <input
                type="checkbox"
                checked={includeCuisine}
                onChange={(event) => setIncludeCuisine(event.target.checked)}
              />
              Cuisine
            </label>
            <label>
              <input
                type="checkbox"
                checked={includeManuel}
                onChange={(event) => setIncludeManuel(event.target.checked)}
              />
              Dernier planning manuel publié
            </label>
            <label>
              <input
                type="checkbox"
                checked={includeRuns}
                onChange={(event) => setIncludeRuns(event.target.checked)}
              />
              Computes déjà publiés
            </label>
          </fieldset>
          <label className="bench-import-field">
            Note manuel /10
            <input
              type="number"
              min={0}
              max={10}
              step="any"
              inputMode="decimal"
              value={manualScore}
              onChange={(event) => setManualScore(event.target.value)}
            />
          </label>
          <p className="sub">Si le planning à la main n'est pas complet.</p>
          <label className="bench-import-field">
            Commentaire
            <textarea rows={3} value={comment} onChange={(event) => setComment(event.target.value)} />
          </label>
          {submitError ? (
            <p className="error" role="alert">
              {submitError}
            </p>
          ) : null}
          <div className="auth-row">
            <button type="button" className="choice" onClick={onClose}>
              Annuler
            </button>
            <button type="submit" className="choice active" disabled={busy}>
              {busy ? "Import…" : "Importer"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function FactCard({ fact }: { fact: ScoreFact }) {
  return (
    <article className="admin-warn-card">
      <p className="admin-warn-meta">
        <span className="sev">{factSeverityLabel(fact)}</span>
        <span className="code">{factTitle(fact.kind)}</span>
      </p>
      <p>{warningWhen(fact.day_index)}</p>
      <p>{fact.employee_name?.trim() ? fact.employee_name : "—"}</p>
      <p className="msg">{formatFactLine(fact)}</p>
    </article>
  );
}

function FactTip({ entry }: { entry: AdminGenerateEntry }) {
  if (entry.facts.length === 0) {
    return <p>aucun warning</p>;
  }
  return (
    <>
      {entry.facts.map((fact, index) => (
        <FactCard key={`${entry.id}-w-${index}`} fact={fact} />
      ))}
    </>
  );
}

function AdminChrome({ children }: { children?: ReactNode }) {
  return (
    <>
      <AdminNav current="history" />
      {children}
    </>
  );
}

export type AdminNavCurrent = "history" | "bench" | "bench-stats";

export function AdminNav({ current }: { current: AdminNavCurrent }) {
  return (
    <nav className="admin-nav" aria-label="Admin">
      <button
        type="button"
        className={current === "history" ? "choice active" : "choice"}
        disabled={current === "history"}
        onClick={() => go("/admin")}
      >
        Historique des computes
      </button>
      <button
        type="button"
        className={current === "bench" ? "choice active" : "choice"}
        disabled={current === "bench"}
        onClick={() => go("/admin/bench")}
      >
        Banc
      </button>
      <button
        type="button"
        className={current === "bench-stats" ? "choice active" : "choice"}
        disabled={current === "bench-stats"}
        onClick={() => go("/admin/bench/stats")}
      >
        Stats banc
      </button>
    </nav>
  );
}

export function AdminDenied() {
  return (
    <main className="page">
      <h1>Admin</h1>
      <p className="error" role="alert">
        Action réservée à l'admin.
      </p>
    </main>
  );
}

function EngineSelector({
  liveEngine,
  onUpdate,
  disabled,
}: {
  liveEngine: LiveEngine;
  onUpdate: (next: LiveEngine) => void;
  disabled: boolean;
}) {
  async function handleChange(event: React.ChangeEvent<HTMLSelectElement>) {
    const next = event.target.value;
    if (next === liveEngine.engine_ref) {
      return;
    }
    try {
      const updated = await putLiveEngine(next);
      onUpdate(updated);
    } catch {
      event.target.value = liveEngine.engine_ref;
    }
  }

  return (
    <section className="admin-engine-section">
      <h2>Moteur du planning client</h2>
      <p className="sub">
        C'est ce modèle qui tourne quand un restaurateur calcule son planning. Le banc n'est pas affecté.
      </p>
      <select
        className="admin-engine-select"
        value={liveEngine.engine_ref}
        onChange={(e) => void handleChange(e)}
        disabled={disabled}
      >
        {liveEngine.engine_refs.map((ref) => (
          <option key={ref} value={ref}>
            {ref}
          </option>
        ))}
      </select>
    </section>
  );
}

export function AdminPage() {
  const [entries, setEntries] = useState<AdminGenerateEntry[] | null>(null);
  const [liveEngine, setLiveEngine] = useState<LiveEngine | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [engineError, setEngineError] = useState<string | null>(null);
  const [toast, setToast] = useState<AdminToast | null>(null);
  const [importTarget, setImportTarget] = useState<BenchImportTarget | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([loadAdminGenerates(), loadLiveEngine()])
      .then(([generates, engine]) => {
        if (cancelled) {
          return;
        }
        setEntries(generates.entries);
        setLiveEngine(engine);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          if (err instanceof ApiHttpError && err.status === 403) {
            setEngineError(err.detail);
            loadAdminGenerates()
              .then((generates) => {
                if (!cancelled) {
                  setEntries(generates.entries);
                }
              })
              .catch((genErr: unknown) => {
                if (!cancelled) {
                  setError(genErr instanceof ApiHttpError ? genErr.detail : genErr instanceof Error ? genErr.message : "erreur inattendue");
                }
              });
          } else {
            setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
          }
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!toast) {
      return;
    }
    const timer = window.setTimeout(() => setToast(null), toast.action ? 10000 : 4000);
    return () => window.clearTimeout(timer);
  }, [toast]);

  function showToast(text: string) {
    setToast({ text });
  }

  function openBenchImport(entry: AdminGenerateEntry) {
    if (entry.restaurant_id == null) {
      showToast("Restaurant introuvable.");
      return;
    }
    setImportTarget({
      restaurant_id: entry.restaurant_id,
      restaurant_name: entry.restaurant_name,
      email: entry.email,
    });
  }

  async function onEmailContextMenu(event: MouseEvent<HTMLTableCellElement>, entry: AdminGenerateEntry) {
    event.preventDefault();
    if (entry.restaurant_id == null) {
      showToast("Restaurant introuvable.");
      return;
    }
    try {
      const url = await mintImpersonateLink(entry.restaurant_id);
      await copyToClipboard(url);
      showToast("Lien copié — ouvre-le en navigation privée.");
    } catch (err: unknown) {
      showToast(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  function onRestaurantContextMenu(event: MouseEvent<HTMLTableCellElement>, entry: AdminGenerateEntry) {
    event.preventDefault();
    openBenchImport(entry);
  }

  if (error) {
    return (
      <main className="page">
        <AdminChrome />
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!entries) {
    return (
      <main className="page">
        <AdminChrome />
        <p className="sub">Chargement des generates…</p>
      </main>
    );
  }

  return (
    <main className="page admin-page">
      <AdminChrome>
        <p className="sub">Generates réussis, plus récent d'abord.</p>
      </AdminChrome>

      {liveEngine ? (
        <EngineSelector liveEngine={liveEngine} onUpdate={setLiveEngine} disabled={false} />
      ) : engineError ? (
        <section className="admin-engine-section">
          <h2>Moteur du planning client</h2>
          <p className="error" role="alert">{engineError}</p>
        </section>
      ) : null}

      {entries.length === 0 ? (
        <p className="sub">Aucun generate pour l'instant.</p>
      ) : (
        groupEntriesByParisDay(entries).map((group) => (
          <section key={group.key}>
            <h2>{group.label}</h2>
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Heure</th>
                  <th>Email</th>
                  <th>Restaurant</th>
                  <th>Équipe</th>
                  <th>Effort</th>
                  <th>Note</th>
                  <th>Durée</th>
                  <th>Moteur</th>
                  <th>Warnings</th>
                  <th>Planning</th>
                </tr>
              </thead>
              <tbody>
                {group.entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{parisClock(entry.created_at)}</td>
                    <td className="admin-email" onContextMenu={(event) => void onEmailContextMenu(event, entry)}>
                      {entry.email}
                    </td>
                    <td
                      className="admin-restaurant"
                      onContextMenu={(event) => onRestaurantContextMenu(event, entry)}
                    >
                      {entry.restaurant_name || "—"}
                    </td>
                    <td>{teamLabel(entry.team)}</td>
                    <td>{effortLabel(entry.search_effort)}</td>
                    <td>{formatCycleNote(entry.score_global)}</td>
                    <td>{formatSolveDuration(entry.duration_seconds)}</td>
                    <td>{entry.engine_ref || "—"}</td>
                    <td>
                      <span className="admin-pill">{entry.facts.length}</span>
                      <div className="admin-tip" role="tooltip">
                        <FactTip entry={entry} />
                      </div>
                    </td>
                    <td>
                      <div className="admin-planning-actions">
                        <button
                          type="button"
                          className="choice"
                          disabled={entry.restaurant_id == null}
                          onClick={() => {
                            if (entry.restaurant_id) {
                              go("/admin/planning/" + entry.restaurant_id);
                            }
                          }}
                        >
                          Voir
                        </button>
                        <button type="button" className="choice" onClick={() => openBenchImport(entry)}>
                          Au banc
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))
      )}
      {importTarget ? (
        <BenchImportPopup
          target={importTarget}
          onClose={() => setImportTarget(null)}
          onImported={() => {
            setImportTarget(null);
            setToast({
              text: "Jeu importé.",
              action: { label: "Ouvrir le banc", path: "/admin/bench" },
            });
          }}
        />
      ) : null}
      {toast ? (
        <div className="admin-toast" role="status">
          {toast.text}
          {toast.action ? (
            <button
              type="button"
              className="admin-toast-action"
              onClick={() => {
                const path = toast.action?.path;
                setToast(null);
                if (path) {
                  go(path);
                }
              }}
            >
              {toast.action.label}
            </button>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}

export function parseAdminPlanningPath(path: string): string | null {
  const match = /^\/admin\/planning\/([^/]+)$/.exec(path);
  return match ? decodeURIComponent(match[1]) : null;
}

export function AdminPlanningPage({ restaurantId }: { restaurantId: string }) {
  const loadContextFn = useCallback(() => loadAdminRestaurantContext(restaurantId), [restaurantId]);
  const loadCyclesFn = useCallback(() => loadAdminRestaurantCycles(restaurantId), [restaurantId]);
  return (
    <PublishedPlanning
      mode="readonly"
      header={<AdminNav current="history" />}
      loadContextFn={loadContextFn}
      loadCyclesFn={loadCyclesFn}
    />
  );
}
