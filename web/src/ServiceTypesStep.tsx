import { useMemo, useState } from "react";
import {
  CONTEXT_SERVICES,
  newId,
  type ContextServiceId,
  type RoleRow,
  type ServiceType,
  type TeamId,
} from "./context";
import { formatClock } from "./format";
import { Stepper } from "./Stepper";
import {
  countsToLevels,
  formatBag,
  levelsToCounts,
  remainFromBag,
  simulateWaves,
  type ArrivalDraft,
  type DepartureDraft,
} from "./waves";

function roleLevels(roles: RoleRow[]): number[] {
  return [...new Set(roles.map((role) => role.level))].sort((a, b) => a - b);
}

function defaultLevel(roles: RoleRow[]): number {
  return roleLevels(roles)[0] ?? 1;
}

function inferLeaveCounts(row: ServiceType): DepartureDraft[] {
  let bag: number[] = [];
  const events = [
    ...row.arrivals.map((item) => ({ kind: "a" as const, time: item.time_minutes, item })),
    ...row.departures.map((item, index) => ({ kind: "d" as const, time: item.time_minutes, item, index })),
  ].sort((a, b) => (a.time !== b.time ? a.time - b.time : a.kind === "a" ? -1 : 1));
  const drafts: DepartureDraft[] = row.departures.map((item) => ({
    time_minutes: item.time_minutes,
    leaveCount: 0,
    remainByLevel: remainFromBag(item.remaining_post_levels),
  }));
  for (const event of events) {
    if (event.kind === "a") {
      bag = [...bag, ...event.item.post_levels];
      continue;
    }
    drafts[event.index].leaveCount = Math.max(0, bag.length - event.item.remaining_post_levels.length);
    bag = [...event.item.remaining_post_levels];
  }
  return drafts;
}

function persistType(
  team: TeamId,
  service_id: ContextServiceId,
  id: string,
  name: string,
  arrivals: ArrivalDraft[],
  departures: DepartureDraft[],
): ServiceType {
  const sim = simulateWaves(arrivals, departures);
  return {
    id,
    name,
    team,
    service_id,
    arrivals: arrivals.map((item) => ({ time_minutes: item.time_minutes, post_levels: [...item.post_levels] })),
    departures: departures.map((item, index) => ({
      time_minutes: item.time_minutes,
      remaining_post_levels: sim.afterDeparture[index]?.bag ?? [],
    })),
  };
}

type Line = { kind: "arrival"; index: number; time: number } | { kind: "departure"; index: number; time: number };

function timeline(arrivals: ArrivalDraft[], departures: DepartureDraft[]): Line[] {
  const lines: Line[] = [
    ...arrivals.map((item, index) => ({ kind: "arrival" as const, index, time: item.time_minutes })),
    ...departures.map((item, index) => ({ kind: "departure" as const, index, time: item.time_minutes })),
  ];
  lines.sort((a, b) => {
    if (a.time !== b.time) {
      return a.time - b.time;
    }
    if (a.kind === b.kind) {
      return a.index - b.index;
    }
    return a.kind === "arrival" ? -1 : 1;
  });
  return lines;
}

export function ServiceTypesStep({
  team,
  services,
  roles,
  types,
  busy,
  onSave,
}: {
  team: TeamId;
  services: ContextServiceId[];
  roles: RoleRow[];
  types: ServiceType[];
  busy: boolean;
  onSave: (types: ServiceType[]) => void;
}) {
  const levels = roleLevels(roles);
  const [serviceId, setServiceId] = useState<ContextServiceId>(services[0] ?? "midday");
  const [rows, setRows] = useState<ServiceType[]>(types);
  const [drafts, setDrafts] = useState<Record<string, { arrivals: ArrivalDraft[]; departures: DepartureDraft[] }>>(
    () => {
      const out: Record<string, { arrivals: ArrivalDraft[]; departures: DepartureDraft[] }> = {};
      for (const row of types) {
        out[row.id] = {
          arrivals: row.arrivals.map((item) => ({
            time_minutes: item.time_minutes,
            post_levels: [...item.post_levels],
          })),
          departures: inferLeaveCounts(row),
        };
      }
      return out;
    },
  );
  const offered = services.includes(serviceId) ? serviceId : services[0];
  const visible = rows.filter((row) => row.service_id === offered);

  function draftFor(id: string): { arrivals: ArrivalDraft[]; departures: DepartureDraft[] } {
    return drafts[id] ?? { arrivals: [], departures: [] };
  }

  function setDraft(id: string, next: { arrivals: ArrivalDraft[]; departures: DepartureDraft[] }) {
    setDrafts((prev) => ({ ...prev, [id]: next }));
  }

  const errors = useMemo(() => {
    const list: string[] = [];
    for (const row of rows) {
      const draft = drafts[row.id];
      if (!draft) {
        continue;
      }
      const sim = simulateWaves(draft.arrivals, draft.departures);
      for (const bag of [...sim.afterArrival, ...sim.afterDeparture]) {
        if (bag.error) {
          list.push(bag.error);
        }
      }
    }
    return list;
  }, [rows, drafts]);

  function addType() {
    if (!offered) {
      return;
    }
    const id = newId(`${team}-${offered}`);
    const arrivals = [{ time_minutes: 11 * 60, post_levels: [defaultLevel(roles)] }];
    setRows((prev) => [...prev, { id, name: "", team, service_id: offered, arrivals: [], departures: [] }]);
    setDrafts((prev) => ({ ...prev, [id]: { arrivals, departures: [] } }));
  }

  function save() {
    onSave(
      rows.map((row) => {
        const draft = draftFor(row.id);
        return persistType(row.team, row.service_id, row.id, row.name, draft.arrivals, draft.departures);
      }),
    );
  }

  if (!offered) {
    return (
      <section>
        <h2>Services types</h2>
        <p className="sub">Aucun service offert.</p>
      </section>
    );
  }

  return (
    <section>
      <h2>Services types</h2>
      <p className="sub">Une ligne par événement, dans l’ordre du temps. Sous-onglets = services offerts.</p>
      <div className="auth-switch">
        {services.map((id) => (
          <button
            key={id}
            type="button"
            className={offered === id ? "choice active" : "choice"}
            onClick={() => setServiceId(id)}
          >
            {CONTEXT_SERVICES.find((item) => item.id === id)?.label ?? id}
          </button>
        ))}
      </div>
      {visible.map((row) => {
        const draft = draftFor(row.id);
        const sim = simulateWaves(draft.arrivals, draft.departures);
        const lines = timeline(draft.arrivals, draft.departures);
        return (
          <article key={row.id} className="fiche-card">
            <input
              placeholder="Nom de la feuille"
              value={row.name}
              onChange={(event) =>
                setRows((prev) =>
                  prev.map((item) => (item.id === row.id ? { ...item, name: event.target.value } : item)),
                )
              }
            />
            <table className="type-sheet">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Heure</th>
                  <th>N</th>
                  <th>Niveaux</th>
                  <th>STAFF minimal resultant</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {lines.map((line) => {
                  if (line.kind === "arrival") {
                    const arrival = draft.arrivals[line.index];
                    const counts = levelsToCounts(arrival.post_levels);
                    const staff = sim.afterArrival[line.index];
                    return (
                      <tr key={`a-${line.index}`}>
                        <td>Arrivée</td>
                        <td>
                          <Stepper
                            value={arrival.time_minutes}
                            step={15}
                            display={formatClock(arrival.time_minutes)}
                            onChange={(time_minutes) =>
                              setDraft(row.id, {
                                ...draft,
                                arrivals: draft.arrivals.map((item, i) =>
                                  i === line.index ? { ...item, time_minutes } : item,
                                ),
                              })
                            }
                          />
                        </td>
                        <td>
                          <span className="count-field">
                            <span className="count-label">N</span>
                            <Stepper
                              value={arrival.post_levels.length}
                              min={1}
                              onChange={(n) => {
                                const post_levels = arrival.post_levels.slice(0, n);
                                while (post_levels.length < n) {
                                  post_levels.push(defaultLevel(roles));
                                }
                                setDraft(row.id, {
                                  ...draft,
                                  arrivals: draft.arrivals.map((item, i) =>
                                    i === line.index ? { ...item, post_levels } : item,
                                  ),
                                });
                              }}
                            />
                          </span>
                        </td>
                        <td>
                          <div className="level-steppers">
                            {levels.map((level) => (
                              <label key={level}>
                                {level}
                                <Stepper
                                  value={counts[level] ?? 0}
                                  min={0}
                                  onChange={(next) => {
                                    const updated = { ...counts, [level]: next };
                                    setDraft(row.id, {
                                      ...draft,
                                      arrivals: draft.arrivals.map((item, i) =>
                                        i === line.index ? { ...item, post_levels: countsToLevels(updated) } : item,
                                      ),
                                    });
                                  }}
                                />
                              </label>
                            ))}
                          </div>
                        </td>
                        <td className={staff?.error ? "error" : "staff-after"}>
                          {staff?.error ?? formatBag(staff?.bag ?? [])}
                        </td>
                        <td>
                          <button
                            type="button"
                            className="choice trash"
                            aria-label="Supprimer la ligne"
                            onClick={() =>
                              setDraft(row.id, {
                                ...draft,
                                arrivals: draft.arrivals.filter((_, i) => i !== line.index),
                              })
                            }
                          >
                            🗑
                          </button>
                        </td>
                      </tr>
                    );
                  }
                  const departure = draft.departures[line.index];
                  const staff = sim.afterDeparture[line.index];
                  return (
                    <tr key={`d-${line.index}`}>
                      <td>Sortie</td>
                      <td>
                        <Stepper
                          value={departure.time_minutes}
                          step={15}
                          display={formatClock(departure.time_minutes)}
                          onChange={(time_minutes) =>
                            setDraft(row.id, {
                              ...draft,
                              departures: draft.departures.map((item, i) =>
                                i === line.index ? { ...item, time_minutes } : item,
                              ),
                            })
                          }
                        />
                      </td>
                      <td>
                        <span className="count-field">
                          <span className="count-label">N</span>
                          <Stepper
                            value={departure.leaveCount}
                            min={0}
                            onChange={(leaveCount) =>
                              setDraft(row.id, {
                                ...draft,
                                departures: draft.departures.map((item, i) =>
                                  i === line.index ? { ...item, leaveCount } : item,
                                ),
                              })
                            }
                          />
                        </span>
                      </td>
                      <td>
                        <div className="level-steppers">
                          {levels.map((level) => (
                            <label key={level}>
                              {level}
                              <Stepper
                                value={departure.remainByLevel[level] ?? 0}
                                min={0}
                                onChange={(next) =>
                                  setDraft(row.id, {
                                    ...draft,
                                    departures: draft.departures.map((item, i) =>
                                      i === line.index
                                        ? { ...item, remainByLevel: { ...item.remainByLevel, [level]: next } }
                                        : item,
                                    ),
                                  })
                                }
                              />
                            </label>
                          ))}
                        </div>
                      </td>
                      <td className={staff?.error ? "error" : "staff-after"}>
                        {staff?.error ?? formatBag(staff?.bag ?? [])}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="choice trash"
                          aria-label="Supprimer la ligne"
                          onClick={() =>
                            setDraft(row.id, {
                              ...draft,
                              departures: draft.departures.filter((_, i) => i !== line.index),
                            })
                          }
                        >
                          🗑
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="auth-row">
              <button
                type="button"
                className="choice"
                onClick={() =>
                  setDraft(row.id, {
                    ...draft,
                    arrivals: [...draft.arrivals, { time_minutes: 11 * 60, post_levels: [defaultLevel(roles)] }],
                  })
                }
              >
                Ajouter une arrivée
              </button>
              <button
                type="button"
                className="choice"
                onClick={() =>
                  setDraft(row.id, {
                    ...draft,
                    departures: [...draft.departures, { time_minutes: 16 * 60, leaveCount: 1, remainByLevel: {} }],
                  })
                }
              >
                Ajouter un départ
              </button>
              <button
                type="button"
                className="choice"
                onClick={() => {
                  setRows((prev) => prev.filter((item) => item.id !== row.id));
                  setDrafts((prev) => {
                    const next = { ...prev };
                    delete next[row.id];
                    return next;
                  });
                }}
              >
                Retirer ce type
              </button>
            </div>
          </article>
        );
      })}
      <button type="button" className="choice" onClick={addType}>
        Ajouter un type
      </button>
      <button
        type="button"
        className="choice active"
        disabled={
          busy ||
          errors.length > 0 ||
          rows.some((row) => !row.name.trim() || (drafts[row.id]?.arrivals.length ?? 0) === 0)
        }
        onClick={save}
      >
        Enregistrer et continuer
      </button>
    </section>
  );
}
