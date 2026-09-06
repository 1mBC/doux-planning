import { useEffect, useMemo, useRef, useState } from "react";
import { Overlay, FillOverlay } from "./Overlay";
import {
  ApiHttpError,
  commitBody,
  commitFillBody,
  historyEntryFromCran,
} from "./sandbox";
import {
  commitLiveSandbox,
  discardLiveSandbox,
  enterLiveSandbox,
  previewLiveFill,
  previewLiveOccupied,
  publishLiveSandbox,
  undoLiveSandbox,
  type LiveState,
} from "./liveSandbox";
import { loadContext, CONTEXT_SERVICES, type ContextServiceId, type RestaurantContext, type TeamId } from "./context";
import { CycleStats, LegalRecap, WishRecap } from "./cycleRecaps";
import {
  buildPlanningExport,
  exportPublishedPlanning,
  type PlanningExportFormat,
} from "./exportPlanning";
import { loadCycles, postGenerate, type CycleAssignment, type PublishedCycles, type SearchEffort } from "./generate";
import {
  DAYS_FR,
  GESTURE_HISTORY_FR,
  formatClock,
  formatDuration,
  formatHoursTotal,
  groupedEmployees,
  personInk,
  warningSeverityLabel,
  warningTitle,
  weekdayFromDayIndex,
  weekSheetTitle,
} from "./format";
import { cranHow, fillHow, fillSlotSummary, GestureImpact, slotSummary } from "./impact";
import type {
  Assignment,
  Employee,
  FillSlot,
  Gesture,
  HistoryEntry,
  PreviewProposal,
  ShiftIdentity,
  WarningItem,
} from "./types";
import { toShiftIdentity } from "./types";

type OverlayTarget = { kind: "occupied"; shift: ShiftIdentity } | { kind: "fill"; slot: FillSlot };

const TEAMS: { id: TeamId; label: string }[] = [
  { id: "salle", label: "Salle" },
  { id: "cuisine", label: "Cuisine" },
];

function toGridEmployee(person: RestaurantContext["employees"][number]): Employee {
  return {
    id: person.id,
    name: person.name,
    team: person.team,
    role: person.role,
  };
}

function indexCycle(assignments: CycleAssignment[]): Map<string, CycleAssignment> {
  const map = new Map<string, CycleAssignment>();
  for (const shift of assignments) {
    const key = `${shift.employee_id}:${shift.day_index}:${shift.service_id}`;
    if (!map.has(key)) {
      map.set(key, shift);
    }
  }
  return map;
}

function weekHours(assignments: CycleAssignment[], employeeId: string, weekOffset: 0 | 7): number {
  let total = 0;
  for (const shift of assignments) {
    if (shift.employee_id !== employeeId) {
      continue;
    }
    if (shift.day_index < weekOffset || shift.day_index > weekOffset + 6) {
      continue;
    }
    total += shift.duration_hours;
  }
  return total;
}

function serviceRows(ctx: RestaurantContext, assignments: CycleAssignment[]): { id: ContextServiceId; label: string }[] {
  const ids = ctx.services.length
    ? ctx.services
    : ([...new Set(assignments.map((item) => item.service_id))] as ContextServiceId[]);
  const known = CONTEXT_SERVICES.filter((item) => ids.includes(item.id));
  return known.length ? known : CONTEXT_SERVICES.filter((item) => item.id === "midday" || item.id === "evening");
}

function asAssignment(shift: CycleAssignment): Assignment {
  return shift as Assignment;
}

function PublishedSheet({
  title,
  weekOffset,
  employees,
  assignments,
  services,
  byKey,
  onOccupiedClick,
  onEmptyClick,
}: {
  title: string;
  weekOffset: 0 | 7;
  employees: Employee[];
  assignments: CycleAssignment[];
  services: { id: ContextServiceId; label: string }[];
  byKey: Map<string, CycleAssignment>;
  onOccupiedClick?: (shift: CycleAssignment) => void;
  onEmptyClick?: (slot: FillSlot) => void;
}) {
  const groups = groupedEmployees(employees);
  const span = Math.max(services.length, 1);
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
                return services.map((service, rowIndex) => (
                  <tr
                    key={`${person.id}-${service.id}`}
                    className={service.id === "evening" ? "soir" : undefined}
                    style={{ ["--ink" as string]: ink }}
                  >
                    {rowIndex === 0 ? (
                      <th className="name" rowSpan={span}>
                        {person.name} <span className="lvl">{person.role.level}</span>
                      </th>
                    ) : null}
                    <th className="svc">{service.label}</th>
                    {DAYS_FR.map((_, day) => {
                      const shift = byKey.get(`${person.id}:${weekOffset + day}:${service.id}`);
                      const worked = Boolean(shift);
                      const below = shift !== undefined && shift.post_level < person.role.level;
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
                                      service_id: service.id as FillSlot["service_id"],
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
                      <td className="total" rowSpan={span}>
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

function WarningsList({ warnings }: { warnings: WarningItem[] }) {
  return (
    <section>
      <h2>Alertes</h2>
      <p className="sub">
        {warnings.length} warning{warnings.length > 1 ? "s" : ""} du moteur — affichés tels quels.
      </p>
      <ol className="warnings">
        {warnings.map((warning, index) => {
          const title = warningTitle(warning.code);
          return (
            <li
              key={`${warning.severity}-${warning.code}-${warning.employee_id}-${warning.day_index}-${index}`}
              className={`warn-${warning.severity}`}
            >
              <span className="sev">{warningSeverityLabel(warning)}</span>
              {title ? <span className="code">{title}</span> : null}
              <span className="msg">{warning.message}</span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

export function PublishedPlanning() {
  const [ctx, setCtx] = useState<RestaurantContext | null>(null);
  const [published, setPublished] = useState<PublishedCycles | null>(null);
  const [team, setTeam] = useState<TeamId>("salle");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [calculating, setCalculating] = useState<SearchEffort | null>(null);
  const [live, setLive] = useState<LiveState | null>(null);
  const [overlay, setOverlay] = useState<OverlayTarget | null>(null);
  const [exportOpen, setExportOpen] = useState(false);
  const sheetsRef = useRef<HTMLDivElement>(null);
  const editing = live !== null;

  useEffect(() => {
    let cancelled = false;
    Promise.all([loadContext(), loadCycles()])
      .then(([nextCtx, cycles]) => {
        if (cancelled) {
          return;
        }
        setCtx(nextCtx);
        setPublished(cycles.published);
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

  const cycle = published?.[team] ?? null;
  const people = useMemo(
    () =>
      editing
        ? live.restaurant.employees
        : ctx
          ? ctx.employees.filter((person) => person.team === team).map(toGridEmployee)
          : [],
    [ctx, team, editing, live],
  );
  const assignments = editing ? (live.planning.assignments as CycleAssignment[]) : (cycle?.assignments ?? []);
  const warnings = editing ? live.planning.warnings : (cycle?.warnings ?? []);
  const byKey = useMemo(() => indexCycle(assignments), [assignments]);
  const services = ctx ? serviceRows(ctx, assignments) : [];
  const canCalculate = ctx?.ready[team] === true && !editing && calculating === null;
  const canEdit = cycle !== null && !editing && calculating === null;
  const canExport = cycle !== null && !editing && calculating === null;

  async function calculate(effort: SearchEffort) {
    if (!canCalculate) {
      return;
    }
    const started = Date.now();
    setCalculating(effort);
    setError(null);
    try {
      const result = await postGenerate(team, effort);
      setPublished(result.published);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      const wait = Math.max(0, 1000 - (Date.now() - started));
      if (wait > 0) {
        await new Promise<void>((resolve) => {
          window.setTimeout(resolve, wait);
        });
      }
      setCalculating(null);
    }
  }

  async function startEdit() {
    if (!cycle) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      setLive(await enterLiveSandbox(team));
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  function leaveEdit() {
    setLive(null);
    setOverlay(null);
  }

  async function applyCommit(gesture: Gesture, proposal: PreviewProposal) {
    if (!overlay || overlay.kind !== "occupied") {
      return;
    }
    try {
      setLive(await commitLiveSandbox(team, commitBody(gesture, overlay.shift, proposal)));
      setOverlay(null);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function applyFill(proposal: PreviewProposal) {
    if (!overlay || overlay.kind !== "fill") {
      return;
    }
    try {
      setLive(await commitLiveSandbox(team, commitFillBody(overlay.slot, proposal)));
      setOverlay(null);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function undoLast() {
    try {
      setLive(await undoLiveSandbox(team));
      setError(null);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function discardAll() {
    try {
      setLive(await discardLiveSandbox(team));
      setOverlay(null);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    }
  }

  async function exportFormat(format: PlanningExportFormat) {
    if (!ctx || !cycle || !canExport) {
      return;
    }
    setExportOpen(false);
    setBusy(true);
    setError(null);
    try {
      const sheets = sheetsRef.current ? [...sheetsRef.current.querySelectorAll<HTMLElement>(":scope > .sheet")] : [];
      await exportPublishedPlanning(buildPlanningExport(ctx, team, cycle), format, sheets, ctx.services);
    } catch (err) {
      setError(err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    setBusy(true);
    setError(null);
    try {
      const next = await publishLiveSandbox(team);
      setPublished(next.published);
      setLive(null);
      setOverlay(null);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  if (!ctx && !error) {
    return (
      <main className="page">
        <p className="sub">Chargement du planning…</p>
      </main>
    );
  }

  return (
    <main className="page planning-page">
      <h1>Planning {editing ? "— édition" : "publié"}</h1>
      <p className="sub">
        {editing
          ? "Brouillon live persisté. Lecture quitte sans jeter. Publier écrit le cycle."
          : "Cycle persisté par équipe."}
      </p>
      {ctx ? (
        <p className="ready-badges">
          <span className={ctx.ready.salle ? "badge-ready" : "badge-wait"}>
            Salle · {ctx.ready.salle ? "Prêt à calculer" : "Pas encore prêt"}
          </span>
          <span className={ctx.ready.cuisine ? "badge-ready" : "badge-wait"}>
            Cuisine · {ctx.ready.cuisine ? "Prêt à calculer" : "Pas encore prêt"}
          </span>
        </p>
      ) : null}

      <div className="auth-switch">
        {TEAMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={team === item.id ? "choice active" : "choice"}
            onClick={() => {
              setTeam(item.id);
              setLive(null);
              setOverlay(null);
              setExportOpen(false);
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="auth-switch planning-actions">
        {!editing
          ? (
            [
              { id: "minimal" as const, label: "Minimal" },
              { id: "optimized" as const, label: "Optimisé" },
              { id: "maximal" as const, label: "Maximal" },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                className="choice active"
                disabled={!canCalculate || busy}
                onClick={() => void calculate(item.id)}
              >
                {item.label}
              </button>
            ))
          )
          : null}
        {canEdit ? (
          <button type="button" className="choice active" disabled={busy} onClick={() => void startEdit()}>
            {busy ? "Ouverture…" : "Mode édition"}
          </button>
        ) : null}
        {editing ? (
          <>
            <button type="button" className="choice" onClick={leaveEdit}>
              Lecture
            </button>
            <button type="button" className="choice active" disabled={busy} onClick={() => void publish()}>
              {busy ? "Publication…" : "Publier"}
            </button>
          </>
        ) : null}
        <div className="export-menu">
          <button
            type="button"
            className="choice"
            disabled={!canExport || busy}
            aria-haspopup="menu"
            aria-expanded={exportOpen && canExport}
            onClick={() => setExportOpen((open) => !open)}
          >
            Exporter
          </button>
          {exportOpen && canExport ? (
            <div className="export-menu-list" role="menu">
              {(["json", "csv", "xlsx", "jpeg"] as const).map((format) => (
                <button
                  key={format}
                  type="button"
                  role="menuitem"
                  className="choice"
                  onClick={() => void exportFormat(format)}
                >
                  {format === "jpeg" ? "JPEG" : format.toUpperCase()}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {calculating ? (
        <div className="calc-overlay" role="status" aria-live="polite">
          <p>Calcul en cours…</p>
        </div>
      ) : null}

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {cycle || editing ? (
        <>
          {cycle && !editing ? <CycleStats stats={cycle.stats} /> : null}
          <div ref={sheetsRef} className="export-sheets">
            <PublishedSheet
              title={weekSheetTitle(ctx?.week_labels ?? "ab", 0)}
              weekOffset={0}
              employees={people}
              assignments={assignments}
              services={services}
              byKey={byKey}
              onOccupiedClick={
                editing ? (shift) => setOverlay({ kind: "occupied", shift: toShiftIdentity(asAssignment(shift)) }) : undefined
              }
              onEmptyClick={editing ? (slot) => setOverlay({ kind: "fill", slot }) : undefined}
            />
            <PublishedSheet
              title={weekSheetTitle(ctx?.week_labels ?? "ab", 7)}
              weekOffset={7}
              employees={people}
              assignments={assignments}
              services={services}
              byKey={byKey}
              onOccupiedClick={
                editing ? (shift) => setOverlay({ kind: "occupied", shift: toShiftIdentity(asAssignment(shift)) }) : undefined
              }
              onEmptyClick={editing ? (slot) => setOverlay({ kind: "fill", slot }) : undefined}
            />
          </div>
          <WarningsList warnings={warnings} />
          {cycle && !editing ? (
            <>
              <LegalRecap cols={cycle.legal_cols} rows={cycle.legal_rows} />
              <WishRecap cycle={cycle} />
            </>
          ) : null}
          {editing ? (
            <section>
              <h2>Historique</h2>
              <p className="sub">Annuler enlève uniquement le dernier cran. Tout annuler revient au cycle publié.</p>
              <HistoryList entries={live.history.map(historyEntryFromCran)} employees={people} />
              <div className="history-actions">
                <button type="button" className="choice" onClick={() => void undoLast()}>
                  Annuler
                </button>
                {live.history.length > 0 ? (
                  <button type="button" className="choice" onClick={() => void discardAll()}>
                    Tout annuler
                  </button>
                ) : null}
              </div>
            </section>
          ) : null}
        </>
      ) : (
        <p className="sub">Pas encore calculé</p>
      )}

      {overlay?.kind === "occupied" && live ? (
        <Overlay
          shift={overlay.shift}
          employees={people}
          onClose={() => setOverlay(null)}
          onCommit={applyCommit}
          onError={setError}
          preview={(gesture, shift, hours) => previewLiveOccupied(team, gesture, shift, hours)}
        />
      ) : null}
      {overlay?.kind === "fill" && live ? (
        <FillOverlay
          slot={overlay.slot}
          employees={people}
          onClose={() => setOverlay(null)}
          onCommit={applyFill}
          onError={setError}
          preview={(slot, hours) => previewLiveFill(team, slot, hours)}
        />
      ) : null}
    </main>
  );
}
