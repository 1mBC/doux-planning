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
import {
  formatBag,
  remainFromBag,
  simulateWaves,
  type ArrivalDraft,
  type DepartureDraft,
} from "./waves";

function defaultLevel(roles: RoleRow[]): number {
  const levels = roleLevels(roles);
  return levels[0] ?? 1;
}

function roleLevels(roles: RoleRow[]): number[] {
  return [...new Set(roles.map((role) => role.level))].sort((a, b) => a - b);
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
    const departures: DepartureDraft[] = [];
    setRows((prev) => [
      ...prev,
      { id, name: "", team, service_id: offered, arrivals: [], departures: [] },
    ]);
    setDrafts((prev) => ({ ...prev, [id]: { arrivals, departures } }));
  }

  function save() {
    const next = rows.map((row) => {
      const draft = draftFor(row.id);
      return persistType(row.team, row.service_id, row.id, row.name, draft.arrivals, draft.departures);
    });
    onSave(next);
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
      <p className="sub">Sous-onglets = services offerts. Plusieurs types par service.</p>
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
            <div className="wave-block">
              <h3>Arrivées</h3>
              {draft.arrivals.map((arrival, index) => (
                <div key={`a-${index}`} className="wave-line">
                  <p>
                    {formatClock(arrival.time_minutes)}{" "}
                    <button
                      type="button"
                      className="choice"
                      onClick={() =>
                        setDraft(row.id, {
                          ...draft,
                          arrivals: draft.arrivals.map((item, i) =>
                            i === index ? { ...item, time_minutes: item.time_minutes - 15 } : item,
                          ),
                        })
                      }
                    >
                      −15
                    </button>
                    <button
                      type="button"
                      className="choice"
                      onClick={() =>
                        setDraft(row.id, {
                          ...draft,
                          arrivals: draft.arrivals.map((item, i) =>
                            i === index ? { ...item, time_minutes: item.time_minutes + 15 } : item,
                          ),
                        })
                      }
                    >
                      +15
                    </button>
                  </p>
                  <label>
                    Personnes
                    <input
                      type="number"
                      min={1}
                      value={arrival.post_levels.length}
                      onChange={(event) => {
                        const n = Math.max(1, Number(event.target.value) || 1);
                        const post_levels = arrival.post_levels.slice(0, n);
                        while (post_levels.length < n) {
                          post_levels.push(defaultLevel(roles));
                        }
                        setDraft(row.id, {
                          ...draft,
                          arrivals: draft.arrivals.map((item, i) => (i === index ? { ...item, post_levels } : item)),
                        });
                      }}
                    />
                  </label>
                  <div className="level-pickers">
                    {arrival.post_levels.map((level, person) => (
                      <label key={person}>
                        Niveau {person + 1}
                        <select
                          value={level}
                          onChange={(event) => {
                            const post_levels = arrival.post_levels.map((item, i) =>
                              i === person ? Number(event.target.value) : item,
                            );
                            setDraft(row.id, {
                              ...draft,
                              arrivals: draft.arrivals.map((item, i) => (i === index ? { ...item, post_levels } : item)),
                            });
                          }}
                        >
                          {levels.map((option) => (
                            <option key={option} value={option}>
                              {option}
                            </option>
                          ))}
                        </select>
                      </label>
                    ))}
                  </div>
                  <p className="sub">Sac après : {formatBag(sim.afterArrival[index]?.bag ?? [])}</p>
                  <button
                    type="button"
                    className="choice"
                    onClick={() =>
                      setDraft(row.id, {
                        ...draft,
                        arrivals: draft.arrivals.filter((_, i) => i !== index),
                      })
                    }
                  >
                    Retirer l’arrivée
                  </button>
                </div>
              ))}
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
            </div>
            <div className="wave-block">
              <h3>Départs</h3>
              {draft.departures.map((departure, index) => (
                <div key={`d-${index}`} className="wave-line">
                  <p>
                    {formatClock(departure.time_minutes)}{" "}
                    <button
                      type="button"
                      className="choice"
                      onClick={() =>
                        setDraft(row.id, {
                          ...draft,
                          departures: draft.departures.map((item, i) =>
                            i === index ? { ...item, time_minutes: item.time_minutes - 15 } : item,
                          ),
                        })
                      }
                    >
                      −15
                    </button>
                    <button
                      type="button"
                      className="choice"
                      onClick={() =>
                        setDraft(row.id, {
                          ...draft,
                          departures: draft.departures.map((item, i) =>
                            i === index ? { ...item, time_minutes: item.time_minutes + 15 } : item,
                          ),
                        })
                      }
                    >
                      +15
                    </button>
                  </p>
                  <label>
                    Qui partent
                    <input
                      type="number"
                      min={0}
                      value={departure.leaveCount}
                      onChange={(event) => {
                        const leaveCount = Math.max(0, Number(event.target.value) || 0);
                        setDraft(row.id, {
                          ...draft,
                          departures: draft.departures.map((item, i) =>
                            i === index ? { ...item, leaveCount } : item,
                          ),
                        });
                      }}
                    />
                  </label>
                  <div className="level-pickers">
                    {levels.map((level) => (
                      <label key={level}>
                        Reste niv. {level}
                        <input
                          type="number"
                          min={0}
                          value={departure.remainByLevel[level] ?? 0}
                          onChange={(event) => {
                            const remainByLevel = {
                              ...departure.remainByLevel,
                              [level]: Math.max(0, Number(event.target.value) || 0),
                            };
                            setDraft(row.id, {
                              ...draft,
                              departures: draft.departures.map((item, i) =>
                                i === index ? { ...item, remainByLevel } : item,
                              ),
                            });
                          }}
                        />
                      </label>
                    ))}
                  </div>
                  {sim.afterDeparture[index]?.error ? (
                    <p className="error" role="alert">
                      {sim.afterDeparture[index].error}
                    </p>
                  ) : (
                    <p className="sub">Sac après : {formatBag(sim.afterDeparture[index]?.bag ?? [])}</p>
                  )}
                  <button
                    type="button"
                    className="choice"
                    onClick={() =>
                      setDraft(row.id, {
                        ...draft,
                        departures: draft.departures.filter((_, i) => i !== index),
                      })
                    }
                  >
                    Retirer le départ
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="choice"
                onClick={() =>
                  setDraft(row.id, {
                    ...draft,
                    departures: [
                      ...draft.departures,
                      { time_minutes: 16 * 60, leaveCount: 1, remainByLevel: {} },
                    ],
                  })
                }
              >
                Ajouter un départ
              </button>
            </div>
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
