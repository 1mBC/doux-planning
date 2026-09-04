import { useEffect, useMemo, useState } from "react";
import { ApiHttpError } from "./sandbox";
import { loadContext, CONTEXT_SERVICES, type ContextServiceId, type RestaurantContext, type TeamId } from "./context";
import { loadCycles, postGenerate, type CycleAssignment, type PublishedCycles } from "./generate";
import {
  DAYS_FR,
  formatClock,
  formatDuration,
  formatHoursTotal,
  groupedEmployees,
  personInk,
  SEVERITY_FR,
  warningTitle,
} from "./format";
import type { Employee, WarningItem } from "./types";

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

function PublishedSheet({
  title,
  weekOffset,
  employees,
  assignments,
  services,
  byKey,
}: {
  title: string;
  weekOffset: 0 | 7;
  employees: Employee[];
  assignments: CycleAssignment[];
  services: { id: ContextServiceId; label: string }[];
  byKey: Map<string, CycleAssignment>;
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
                          className={[fieldIndex === 0 ? "d" : "", worked ? "work" : "rest"].filter(Boolean).join(" ")}
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

export function PublishedPlanning() {
  const [ctx, setCtx] = useState<RestaurantContext | null>(null);
  const [published, setPublished] = useState<PublishedCycles | null>(null);
  const [team, setTeam] = useState<TeamId>("salle");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
    () => (ctx ? ctx.employees.filter((person) => person.team === team).map(toGridEmployee) : []),
    [ctx, team],
  );
  const assignments = cycle?.assignments ?? [];
  const byKey = useMemo(() => indexCycle(assignments), [assignments]);
  const services = ctx ? serviceRows(ctx, assignments) : [];
  const canCalculate = ctx?.ready[team] === true;

  async function calculate() {
    if (!canCalculate) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await postGenerate(team);
      setPublished(result.published);
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
      <h1>Planning publié</h1>
      <p className="sub">Cycle persisté par équipe. Pas d’édition sandbox ici.</p>
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
            onClick={() => setTeam(item.id)}
          >
            {item.label}
          </button>
        ))}
        <button type="button" className="choice active" disabled={!canCalculate || busy} onClick={() => void calculate()}>
          {busy ? "Calcul…" : "Calculer"}
        </button>
      </div>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {cycle ? (
        <>
          <PublishedSheet
            title="Semaine A"
            weekOffset={0}
            employees={people}
            assignments={assignments}
            services={services}
            byKey={byKey}
          />
          <PublishedSheet
            title="Semaine B"
            weekOffset={7}
            employees={people}
            assignments={assignments}
            services={services}
            byKey={byKey}
          />
          <WarningsList warnings={cycle.warnings} />
        </>
      ) : (
        <p className="sub">Pas encore calculé</p>
      )}
    </main>
  );
}
