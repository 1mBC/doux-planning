import { useEffect, useState } from "react";
import {
  groupEntriesByParisDay,
  loadAdminGenerates,
  parisClock,
  teamLabel,
  type AdminGenerateEntry,
} from "./admin";
import { ApiHttpError } from "./sandbox";

function warningTip(entry: AdminGenerateEntry): string {
  if (entry.warnings.length === 0) {
    return "aucun warning";
  }
  return entry.warnings.map((item) => item.message).join("\n");
}

export function AdminDenied() {
  return (
    <main className="page">
      <h1>Admin</h1>
      <p className="error" role="alert">
        Action réservée à l’admin.
      </p>
    </main>
  );
}

export function AdminPage() {
  const [entries, setEntries] = useState<AdminGenerateEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadAdminGenerates()
      .then((next) => {
        if (!cancelled) {
          setEntries(next.entries);
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

  if (error) {
    return (
      <main className="page">
        <h1>Admin</h1>
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }
  if (!entries) {
    return (
      <main className="page">
        <p className="sub">Chargement des generates…</p>
      </main>
    );
  }
  if (entries.length === 0) {
    return (
      <main className="page">
        <h1>Admin</h1>
        <p className="sub">Aucun generate pour l’instant.</p>
      </main>
    );
  }

  return (
    <main className="page admin-page">
      <h1>Admin</h1>
      <p className="sub">Generates réussis, plus récent d’abord.</p>
      {groupEntriesByParisDay(entries).map((group) => (
        <section key={group.key}>
          <h2>{group.label}</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Heure</th>
                <th>Email</th>
                <th>Restaurant</th>
                <th>Équipe</th>
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
                  <td>
                    <span className="admin-pill">{entry.warnings.length}</span>
                    <div className="admin-tip" role="tooltip">
                      {warningTip(entry)
                        .split("\n")
                        .map((line, index) => (
                          <p key={`${entry.id}-w-${index}`}>{line}</p>
                        ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </main>
  );
}
