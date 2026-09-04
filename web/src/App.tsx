import { useEffect, useMemo, useState } from "react";
import { loadSaintCloudExample, PayloadError } from "./api";
import { Overlay, FillOverlay } from "./Overlay";
import { ApiHttpError, commitBody, commitFillBody, commitSandbox, discardSandbox, enterSandbox, historyEntryFromCran, undoSandbox } from "./sandbox";
import {
  DAYS_FR,
  SERVICE_ROWS,
  effortLabel,
  formatClock,
  formatDuration,
  formatHoursTotal,
  formatSeconds,
  GESTURE_HISTORY_FR,
  groupedEmployees,
  indexAssignments,
  legalColumns,
  personInk,
  SEVERITY_FR,
  warningTitle,
  weekdayFromDayIndex,
  weekHours,
} from "./format";
import type {
  Assignment,
  Employee,
  ExamplePayload,
  FillSlot,
  Gesture,
  HistoryEntry,
  PreviewProposal,
  SandboxState,
  ShiftIdentity,
  WarningItem,
} from "./types";
import { toShiftIdentity } from "./types";
import { cranHow, fillHow, fillSlotSummary, GestureImpact, slotSummary } from "./impact";
import { UI_RELEASE } from "./release";
import "./App.css";

function PlanningSheet({
  title,
  weekOffset,
  employees,
  assignments,
  byKey,
  onOccupiedClick,
  onEmptyClick,
}: {
  title: string;
  weekOffset: 0 | 7;
  employees: Employee[];
  assignments: Assignment[];
  byKey: Map<string, Assignment>;
  onOccupiedClick?: (shift: Assignment) => void;
  onEmptyClick?: (slot: FillSlot) => void;
}) {
  const groups = groupedEmployees(employees);
  const colCount = 2 + DAYS_FR.length * 3 + 1;

  return (
    <section className="sheet">
      <h3>{title}</h3>
      <div className="scroll">
        <table className="plan">
          <thead>
            <tr>
              <th rowSpan={2} className="name">
                Personne
              </th>
              <th rowSpan={2}>Service</th>
              {DAYS_FR.map((day) => (
                <th key={day} colSpan={3} className="day">
                  {day}
                </th>
              ))}
              <th rowSpan={2}>Total</th>
            </tr>
            <tr>
              {DAYS_FR.flatMap((day) =>
                ["Début", "Fin", "H"].map((label) => (
                  <th key={`${day}-${label}`} className={label === "Début" ? "day" : undefined}>
                    {label}
                  </th>
                )),
              )}
            </tr>
          </thead>
          <tbody>
            {groups.flatMap((group) => [
              <tr key={`role-${group.role}`} className="role">
                <td colSpan={colCount}>{group.role}</td>
              </tr>,
              ...group.members.flatMap((person) => {
                const ink = personInk(employees, person.id);
                const total = weekHours(assignments, person.id, weekOffset);
                return SERVICE_ROWS.map((service, rowIndex) => (
                  <tr
                    key={`${person.id}-${service.id}`}
                    className={service.id === "evening" ? "soir" : undefined}
                    style={{ ["--ink" as string]: ink }}
                  >
                    {rowIndex === 0 ? (
                      <th className="name" rowSpan={2}>
                        {person.name} <span className="lvl">{person.role.level}</span>
                      </th>
                    ) : null}
                    <th className="svc">{service.label}</th>
                    {DAYS_FR.map((_, day) => {
                      const shift = byKey.get(`${person.id}:${weekOffset + day}:${service.id}`);
                      const worked = Boolean(shift);
                      const below =
                        shift !== undefined && shift.post_level < person.role.level;
                      return (["start", "end", "hours"] as const).map((field, fieldIndex) => (
                        <td
                          key={`${person.id}-${service.id}-${day}-${field}`}
                          className={[
                            fieldIndex === 0 ? "d" : "",
                            worked ? "work" : "rest",
                            worked && onOccupiedClick ? "slot" : "",
                            !worked && onEmptyClick ? "empty-slot" : "",
                          ]
                            .filter(Boolean)
                            .join(" ")}
                          onClick={
                            shift && onOccupiedClick
                              ? () => onOccupiedClick(shift)
                              : !shift && onEmptyClick
                                ? () =>
                                    onEmptyClick({
                                      employee_id: person.id,
                                      day_index: weekOffset + day,
                                      weekday: weekdayFromDayIndex(weekOffset + day),
                                      service_id: service.id,
                                      team: person.team,
                                    })
                                : undefined
                          }
                        >
                          {shift
                            ? field === "start"
                              ? formatClock(shift.start_minutes)
                              : field === "end"
                                ? formatClock(shift.end_minutes)
                                : below
                                  ? `${formatDuration(shift.duration_hours)} (${shift.post_level})`
                                  : formatDuration(shift.duration_hours)
                            : ""}
                        </td>
                      ));
                    })}
                    {rowIndex === 0 ? (
                      <td className="total" rowSpan={2}>
                        {formatHoursTotal(total)}
                      </td>
                    ) : null}
                  </tr>
                ));
              }),
            ])}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Stats({ stats }: { stats: ExamplePayload["planning"]["stats"] }) {
  const items: { value: string; label: string; tone?: "ok" | "warn" }[] = [
    { value: String(stats.assignments), label: "Shifts posés" },
    { value: String(stats.empty), label: "Postes vides", tone: stats.empty === 0 ? "ok" : "warn" },
    {
      value: String(stats.interdit),
      label: "Alertes légales",
      tone: stats.interdit === 0 ? "ok" : "warn",
    },
    {
      value: `${stats.below_role} / ${stats.assignments}`,
      label: "Shifts sous le rôle",
      tone: stats.below_role === 0 ? "ok" : "warn",
    },
    {
      value: `${stats.hours.percent} %`,
      label: "Heures vs contrat",
      tone: stats.hours.percent === 100 ? "ok" : "warn",
    },
    {
      value: `${stats.wellbeing.held} / ${stats.wellbeing.total}`,
      label: "Souhaits bien-être",
      tone: stats.wellbeing.held === stats.wellbeing.total ? "ok" : "warn",
    },
  ];
  return (
    <div className="stats">
      {items.map((item) => (
        <div key={item.label} className={`stat ${item.tone ?? ""}`}>
          <b>{item.value}</b>
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}

function WarningsList({ warnings }: { warnings: WarningItem[] }) {
  return (
    <section>
      <h2>Alertes</h2>
      <p className="sub">{warnings.length} warning{warnings.length > 1 ? "s" : ""} du moteur — affichés tels quels.</p>
      <ol className="warnings">
        {warnings.map((warning, index) => {
          const title = warningTitle(warning.code);
          return (
            <li key={`${warning.severity}-${warning.code}-${warning.employee_id}-${warning.day_index}-${index}`} className={`warn-${warning.severity}`}>
              <span className="sev">{SEVERITY_FR[warning.severity]}</span>
              {title ? <span className="code">{title}</span> : null}
              <span className="msg">{warning.message}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function HistoryList({
  entries,
  employees,
}: {
  entries: HistoryEntry[];
  employees: Employee[];
}) {
  if (entries.length === 0) {
    return <p className="sub">Aucun cran.</p>;
  }
  return (
    <ol className="history">
      {entries.map((entry) => (
        <li key={entry.index} className="history-item">
          <strong>
            {entry.index}. {GESTURE_HISTORY_FR[entry.gesture]}
          </strong>
          {entry.shift ? <p className="history-who">{slotSummary(entry.shift, employees)}</p> : null}
          {entry.slot && entry.proposal ? (
            <p className="history-who">{fillSlotSummary(entry.slot, entry.proposal, employees)}</p>
          ) : null}
          {entry.shift && entry.proposal ? (
            <p className="history-how">{cranHow(entry.gesture, entry.shift, entry.proposal, employees)}</p>
          ) : null}
          {entry.slot && entry.proposal ? (
            <p className="history-how">{fillHow(entry.slot, entry.proposal, employees)}</p>
          ) : null}
          {entry.proposal ? (
            <GestureImpact gesture={entry.gesture} impact={entry.proposal.impact} employees={employees} />
          ) : null}
        </li>
      ))}
    </ol>
  );
}

type OverlayTarget = { kind: "occupied"; shift: ShiftIdentity } | { kind: "fill"; slot: FillSlot };

export default function App({ canEdit = true }: { canEdit?: boolean }) {
  const [payload, setPayload] = useState<ExamplePayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sandbox, setSandbox] = useState<SandboxState | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const [overlay, setOverlay] = useState<OverlayTarget | null>(null);
  const [entering, setEntering] = useState(false);
  const editing = sandbox !== null;

  useEffect(() => {
    if (!canEdit) {
      setSandbox(null);
      setOverlay(null);
    }
  }, [canEdit]);

  useEffect(() => {
    let cancelled = false;
    loadSaintCloudExample()
      .then((data) => {
        if (!cancelled) {
          setPayload(data);
        }
      })
      .catch((err: unknown) => {
        if (cancelled) {
          return;
        }
        const detail = err instanceof PayloadError ? err.message : "erreur inattendue";
        setError(detail);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const employees = editing ? sandbox.restaurant.employees : payload?.restaurant.employees ?? [];
  const assignments = editing ? sandbox.planning.assignments : payload?.planning.assignments ?? [];
  const warnings = editing ? sandbox.planning.warnings : payload?.planning.warnings ?? [];
  const byKey = useMemo(() => indexAssignments(assignments), [assignments]);

  async function startEdit() {
    setEntering(true);
    setBanner(null);
    try {
      const next = await enterSandbox();
      setSandbox(next);
    } catch (err) {
      setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setEntering(false);
    }
  }

  async function applyCommit(gesture: Gesture, proposal: PreviewProposal) {
    if (!overlay || overlay.kind !== "occupied") {
      return;
    }
    try {
      const next = await commitSandbox(commitBody(gesture, overlay.shift, proposal));
      setSandbox(next);
      setOverlay(null);
      setBanner(null);
    } catch (err) {
      setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function applyFill(proposal: PreviewProposal) {
    if (!overlay || overlay.kind !== "fill") {
      return;
    }
    try {
      const next = await commitSandbox(commitFillBody(overlay.slot, proposal));
      setSandbox(next);
      setOverlay(null);
      setBanner(null);
    } catch (err) {
      setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function undoLast() {
    try {
      const next = await undoSandbox();
      setSandbox(next);
      setBanner(null);
    } catch (err) {
      if (err instanceof ApiHttpError && err.status === 409) {
        setBanner(err.detail);
        return;
      }
      setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function discardAll() {
    try {
      const next = await discardSandbox();
      setSandbox(next);
      setOverlay(null);
      setBanner(null);
    } catch (err) {
      if (err instanceof ApiHttpError && err.status === 404) {
        setBanner(err.detail);
        return;
      }
      setBanner(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  if (error) {
    return (
      <main className="page">
        <h1>Planning</h1>
        <p className="error" role="alert">
          Impossible de charger le planning. L’API doit tourner :{" "}
          <code>uvicorn doux_planning.api.app:app --reload</code>
          {error ? ` (${error})` : ""}.
        </p>
      </main>
    );
  }

  if (!payload) {
    return (
      <main className="page">
        <h1>Planning</h1>
        <p className="sub">Chargement du planning…</p>
      </main>
    );
  }

  const { restaurant, legal, planning } = payload;
  const legalCols = legalColumns(legal, planning.legal_rows);

  return (
    <main className="page">
      <header>
        <h1>Planning {editing ? "— édition" : `${restaurant.team} — 14 jours`}</h1>
        <p className="sub">
          {editing ? sandbox.restaurant.name : restaurant.name}
          {editing
            ? " · brouillon sandbox (cycle) · les tableaux légal / souhaits de l’exemple sont masqués"
            : ` · recherche ${effortLabel(planning.search_effort)} (${planning.calendars} calendriers, ${formatSeconds(planning.seconds)}) · lecture seule`}
        </p>
        <div className="toolbar">
          {canEdit ? (
            editing ? (
              <button
                type="button"
                className="choice"
                onClick={() => {
                  setSandbox(null);
                  setOverlay(null);
                }}
              >
                Lecture
              </button>
            ) : (
              <button type="button" className="choice active" disabled={entering} onClick={() => void startEdit()}>
                {entering ? "Ouverture…" : "Mode édition"}
              </button>
            )
          ) : null}
        </div>
        <p className="release">
          v{UI_RELEASE.version} · {UI_RELEASE.note}
        </p>
      </header>

      {banner ? (
        <p className="error" role="alert">
          {banner}
        </p>
      ) : null}

      {!editing ? <Stats stats={planning.stats} /> : null}

      <PlanningSheet
        title="Semaine A"
        weekOffset={0}
        employees={employees}
        assignments={assignments}
        byKey={byKey}
        onOccupiedClick={editing ? (shift) => setOverlay({ kind: "occupied", shift: toShiftIdentity(shift) }) : undefined}
        onEmptyClick={editing ? (slot) => setOverlay({ kind: "fill", slot }) : undefined}
      />
      <PlanningSheet
        title="Semaine B"
        weekOffset={7}
        employees={employees}
        assignments={assignments}
        byKey={byKey}
        onOccupiedClick={editing ? (shift) => setOverlay({ kind: "occupied", shift: toShiftIdentity(shift) }) : undefined}
        onEmptyClick={editing ? (slot) => setOverlay({ kind: "fill", slot }) : undefined}
      />

      {!editing ? <WarningsList warnings={warnings} /> : null}

      {editing ? (
        <section>
          <h2>Historique</h2>
          <p className="sub">Annuler enlève uniquement le dernier cran. Tout annuler revient au brouillon initial.</p>
          <HistoryList entries={sandbox.history.map(historyEntryFromCran)} employees={employees} />
          <div className="history-actions">
            <button type="button" className="choice" onClick={() => void undoLast()}>
              Annuler
            </button>
            {sandbox.history.length > 0 ? (
              <button type="button" className="choice" onClick={() => void discardAll()}>
                Tout annuler
              </button>
            ) : null}
          </div>
        </section>
      ) : null}

      {!editing ? (
        <>
          <section>
            <h2>Règles légales</h2>
            <p className="sub">Plafonds interdits, mesurés sur le cycle. Colonnes présentes dans le snapshot uniquement.</p>
            <table className="matrix">
              <thead>
                <tr>
                  <th>Personne</th>
                  {legalCols.map((col) => (
                    <th key={col.id}>{col.label_fr}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {planning.legal_rows.map((row) => {
                  const bad = legalCols.some((col) => row.cells[col.id] && !row.cells[col.id]!.ok);
                  return (
                    <tr key={row.employee_id} className={bad ? "warn" : "ok"}>
                      <td>{row.name}</td>
                      {legalCols.map((col) => (
                        <td key={col.id}>{row.cells[col.id]?.text ?? ""}</td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>

          <section>
            <h2>Souhaits</h2>
            <p className="sub">Colonnes = types de souhait. Case vide = non émis.</p>
            <table className="matrix">
              <thead>
                <tr>
                  <th>Personne</th>
                  {planning.wish_cols.map((col) => (
                    <th key={col.key}>{col.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {planning.wish_rows.map((row) => {
                  const bad = planning.wish_cols.some((col) => {
                    const cell = row.cells[col.key];
                    return cell && !cell.ok && col.key !== "contrat";
                  });
                  return (
                    <tr key={row.employee_id} className={bad ? "warn" : "ok"}>
                      <td>{row.name}</td>
                      {planning.wish_cols.map((col) => {
                        const cell = row.cells[col.key];
                        return <td key={col.key}>{cell ? cell.text : ""}</td>;
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </section>
        </>
      ) : null}

      {overlay?.kind === "occupied" && sandbox ? (
        <Overlay
          shift={overlay.shift}
          employees={employees}
          onClose={() => setOverlay(null)}
          onCommit={applyCommit}
          onError={setBanner}
        />
      ) : null}
      {overlay?.kind === "fill" && sandbox ? (
        <FillOverlay
          slot={overlay.slot}
          employees={employees}
          onClose={() => setOverlay(null)}
          onCommit={applyFill}
          onError={setBanner}
        />
      ) : null}
    </main>
  );
}
