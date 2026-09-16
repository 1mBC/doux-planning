import { useEffect, useState, type ReactNode } from "react";
import {
  effortLabel,
  groupEntriesByParisDay,
  loadAdminGenerates,
  loadLiveEngine,
  parisClock,
  putLiveEngine,
  teamLabel,
  type AdminGenerateEntry,
  type LiveEngine,
} from "./admin";
import { formatSolveDuration, warningWhen } from "./format";
import { factSeverityLabel, factTitle, formatFactLine } from "./scoreFacts";
import { ApiHttpError } from "./sandbox";
import { go } from "./AuthScreens";
import type { ScoreFact } from "./types";

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
                  <th>Durée</th>
                  <th>Moteur</th>
                  <th>Warnings</th>
                </tr>
              </thead>
              <tbody>
                {group.entries.map((entry) => (
                  <tr key={entry.id}>
                    <td>{parisClock(entry.created_at)}</td>
                    <td>{entry.email}</td>
                    <td>{entry.restaurant_name || "—"}</td>
                    <td>{teamLabel(entry.team)}</td>
                    <td>{effortLabel(entry.search_effort)}</td>
                    <td>{formatSolveDuration(entry.duration_seconds)}</td>
                    <td>{entry.engine_ref || "—"}</td>
                    <td>
                      <span className="admin-pill">{entry.facts.length}</span>
                      <div className="admin-tip" role="tooltip">
                        <FactTip entry={entry} />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))
      )}
    </main>
  );
}
