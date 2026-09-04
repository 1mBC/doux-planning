import { useEffect, useMemo, useState } from "react";
import { ApiHttpError } from "./sandbox";
import { CONTEXT_SERVICES, type ContextServiceId } from "./context";
import { DAYS_FR, WEEKDAYS_EN, formatClock, formatDuration, formatHoursTotal, groupedEmployees, personInk } from "./format";
import {
  loadEmployeePlanning,
  serviceLabel,
  wishLabel,
  type EmployeePlanning as EmployeePlanningPayload,
  type EmployeeWish,
} from "./mePlanning";
import type { Employee } from "./types";
import type { CycleAssignment } from "./generate";
import type { Unavailability } from "./context";

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

function serviceRows(assignments: CycleAssignment[]): { id: ContextServiceId; label: string }[] {
  const ids = [...new Set(assignments.map((item) => item.service_id))] as ContextServiceId[];
  const known = CONTEXT_SERVICES.filter((item) => ids.includes(item.id));
  return known.length ? known : CONTEXT_SERVICES.filter((item) => item.id === "midday" || item.id === "evening");
}

function dayLabel(weekday: string): string {
  const index = WEEKDAYS_EN.indexOf(weekday as (typeof WEEKDAYS_EN)[number]);
  return index >= 0 ? DAYS_FR[index] : weekday;
}

function describeUnavail(row: Unavailability): string {
  const parts: string[] = [];
  parts.push(row.weekday ? dayLabel(row.weekday) : "Tous les jours");
  if (row.every_morning) {
    parts.push("tous les matins");
  }
  if (row.every_evening) {
    parts.push("tous les soirs");
  }
  if (row.service_id) {
    parts.push(serviceLabel(row.service_id));
  }
  return parts.join(" · ");
}

function EmployeeSheet({
  title,
  weekOffset,
  employees,
  meId,
  assignments,
  services,
  byKey,
}: {
  title: string;
  weekOffset: 0 | 7;
  employees: Employee[];
  meId: string;
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
                const mine = person.id === meId;
                const ink = mine ? personInk(employees, person.id) : "#9aa0a6";
                const total = weekHours(assignments, person.id, weekOffset);
                return services.map((service, rowIndex) => (
                  <tr
                    key={`${person.id}-${service.id}`}
                    className={[service.id === "evening" ? "soir" : "", mine ? "me" : "colleague"]
                      .filter(Boolean)
                      .join(" ")}
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

function WishesList({ wishes }: { wishes: EmployeeWish[] }) {
  if (wishes.length === 0) {
    return <p className="sub">Aucun souhait.</p>;
  }
  return (
    <ul className="employee-list">
      {wishes.map((wish) => (
        <li key={wish.key} className={wish.held ? "wish-held" : "wish-missed"}>
          <span>{wishLabel(wish.key)}</span>
          <strong>{wish.held ? "tenu" : "non tenu"}</strong>
        </li>
      ))}
    </ul>
  );
}

function UnavailList({ rows }: { rows: Unavailability[] }) {
  if (rows.length === 0) {
    return <p className="sub">Aucune indisponibilité.</p>;
  }
  return (
    <ul className="employee-list">
      {rows.map((row, index) => (
        <li key={`${row.weekday ?? "any"}-${row.service_id ?? "any"}-${index}`}>{describeUnavail(row)}</li>
      ))}
    </ul>
  );
}

export function EmployeePlanning() {
  const [board, setBoard] = useState<EmployeePlanningPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadEmployeePlanning()
      .then((next) => {
        if (!cancelled) {
          setBoard(next);
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

  const byKey = useMemo(() => indexCycle(board?.assignments ?? []), [board]);
  const services = board ? serviceRows(board.assignments) : [];
  const published = (board?.assignments.length ?? 0) > 0;

  if (!board && !error) {
    return (
      <main className="page">
        <p className="sub">Chargement du planning…</p>
      </main>
    );
  }

  return (
    <main className="page planning-page employee-planning">
      <h1>Planning {board ? (board.team === "salle" ? "salle" : "cuisine") : "salarié"}</h1>
      <p className="sub">Grille de votre équipe. Lecture seule.</p>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
      {board && published ? (
        <>
          <EmployeeSheet
            title="Semaine A"
            weekOffset={0}
            employees={board.employees}
            meId={board.employee_id}
            assignments={board.assignments}
            services={services}
            byKey={byKey}
          />
          <EmployeeSheet
            title="Semaine B"
            weekOffset={7}
            employees={board.employees}
            meId={board.employee_id}
            assignments={board.assignments}
            services={services}
            byKey={byKey}
          />
        </>
      ) : board ? (
        <p className="sub">Pas encore publié</p>
      ) : null}
      {board ? (
        <section className="employee-panel">
          <h2>Contrat</h2>
          <p className={board.contract.ok ? "contract-ok" : "contract-off"}>
            {formatHoursTotal(board.contract.weekly)} / semaine · {formatHoursTotal(board.contract.assigned)} affectées ·{" "}
            {board.contract.ok ? "dans les heures" : "hors contrat"}
          </p>
          <h2>Indisponibilités</h2>
          <UnavailList rows={board.unavailabilities} />
          <h2>Souhaits</h2>
          <WishesList wishes={board.wishes} />
        </section>
      ) : null}
    </main>
  );
}
