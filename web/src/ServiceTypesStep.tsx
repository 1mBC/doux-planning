import { useLayoutEffect, useMemo, useRef, useState } from "react";
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
  composeTimeMinutes,
  TimeDial,
  TIME_DIAL_ARRIVAL_PRESET,
  TIME_DIAL_DEPARTURE_PRESET,
} from "./TimeDial";
import {
  countsToLevels,
  formatBag,
  levelsToCounts,
  remainFromBag,
  simulateWaves,
  type ArrivalDraft,
  type DepartureDraft,
} from "./waves";

const REORDER_MS = 600;

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

function lineKey(line: Line): string {
  return line.kind === "arrival" ? `a-${line.index}` : `d-${line.index}`;
}

function orderSignature(arrivals: ArrivalDraft[], departures: DepartureDraft[]): string {
  return timeline(arrivals, departures)
    .map((line) => lineKey(line))
    .join("|");
}

type TypeDraft = { arrivals: ArrivalDraft[]; departures: DepartureDraft[] };

type DialState =
  | { mode: "add"; typeId: string; kind: "arrival" | "departure"; previousMinutes: number }
  | { mode: "edit"; typeId: string; kind: "arrival" | "departure"; index: number; previousMinutes: number };

function prefersReducedMotion(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function snapshotTops(nodes: Map<string, HTMLTableRowElement>): Map<string, number> {
  const out = new Map<string, number>();
  for (const [key, el] of nodes) {
    out.set(key, el.getBoundingClientRect().top);
  }
  return out;
}

function playReorder(nodes: Map<string, HTMLTableRowElement>, first: Map<string, number>): void {
  if (prefersReducedMotion()) {
    return;
  }
  for (const [key, el] of nodes) {
    const prevTop = first.get(key);
    if (prevTop === undefined) {
      continue;
    }
    const dy = prevTop - el.getBoundingClientRect().top;
    if (Math.abs(dy) < 1) {
      continue;
    }
    const cells = [...el.querySelectorAll("td")] as HTMLElement[];
    for (const cell of cells) {
      cell.style.transition = "none";
      cell.style.transform = `translateY(${dy}px)`;
    }
    void el.offsetHeight;
    for (const cell of cells) {
      cell.style.transition = `transform ${REORDER_MS}ms ease`;
      cell.style.transform = "translateY(0)";
    }
    const cleanup = (event: TransitionEvent) => {
      if (event.propertyName !== "transform") {
        return;
      }
      for (const cell of cells) {
        cell.style.transition = "";
        cell.style.transform = "";
      }
      el.removeEventListener("transitionend", cleanup);
    };
    el.addEventListener("transitionend", cleanup);
  }
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
  const offeredTabs = CONTEXT_SERVICES.filter((s) => services.includes(s.id));
  const [serviceId, setServiceId] = useState<ContextServiceId | undefined>(offeredTabs[0]?.id);
  const [rows, setRows] = useState<ServiceType[]>(types);
  const [drafts, setDrafts] = useState<Record<string, TypeDraft>>(() => {
    const out: Record<string, TypeDraft> = {};
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
  });
  const [dial, setDial] = useState<DialState | null>(null);
  const [focusKey, setFocusKey] = useState<string | null>(null);
  const rowNodes = useRef(new Map<string, HTMLTableRowElement>());
  const pendingFlip = useRef<Map<string, number> | null>(null);
  const currentService = offeredTabs.some((item) => item.id === serviceId) ? serviceId : offeredTabs[0]?.id;
  const visible = rows.filter((row) => row.service_id === currentService);

  function draftFor(id: string): TypeDraft {
    return drafts[id] ?? { arrivals: [], departures: [] };
  }

  function setDraft(id: string, next: TypeDraft) {
    setDrafts((prev) => ({ ...prev, [id]: next }));
  }

  useLayoutEffect(() => {
    const first = pendingFlip.current;
    if (!first) {
      return;
    }
    pendingFlip.current = null;
    playReorder(rowNodes.current, first);
  }, [drafts]);

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
    if (!currentService) {
      return;
    }
    const id = newId(`${team}-${currentService}`);
    const arrivals = [{ time_minutes: TIME_DIAL_ARRIVAL_PRESET, post_levels: [defaultLevel(roles)] }];
    setRows((prev) => [...prev, { id, name: "", team, service_id: currentService, arrivals: [], departures: [] }]);
    setDrafts((prev) => ({ ...prev, [id]: { arrivals, departures: [] } }));
  }

  function changeLineTime(
    typeId: string,
    kind: "arrival" | "departure",
    index: number,
    time_minutes: number,
  ) {
    const draft = draftFor(typeId);
    const next: TypeDraft =
      kind === "arrival"
        ? {
            ...draft,
            arrivals: draft.arrivals.map((item, i) => (i === index ? { ...item, time_minutes } : item)),
          }
        : {
            ...draft,
            departures: draft.departures.map((item, i) => (i === index ? { ...item, time_minutes } : item)),
          };
    if (orderSignature(draft.arrivals, draft.departures) !== orderSignature(next.arrivals, next.departures)) {
      pendingFlip.current = snapshotTops(rowNodes.current);
    }
    setDraft(typeId, next);
    setFocusKey(`${typeId}:${kind === "arrival" ? "a" : "d"}-${index}`);
  }

  function confirmDial(hour: number, minute: number) {
    if (!dial) {
      return;
    }
    const time_minutes = composeTimeMinutes(dial.previousMinutes, hour, minute);
    const draft = draftFor(dial.typeId);
    if (dial.mode === "add") {
      if (dial.kind === "arrival") {
        const index = draft.arrivals.length;
        setDraft(dial.typeId, {
          ...draft,
          arrivals: [...draft.arrivals, { time_minutes, post_levels: [defaultLevel(roles)] }],
        });
        setFocusKey(`${dial.typeId}:a-${index}`);
      } else {
        const index = draft.departures.length;
        setDraft(dial.typeId, {
          ...draft,
          departures: [...draft.departures, { time_minutes, leaveCount: 1, remainByLevel: {} }],
        });
        setFocusKey(`${dial.typeId}:d-${index}`);
      }
      setDial(null);
      return;
    }
    changeLineTime(dial.typeId, dial.kind, dial.index, time_minutes);
    setDial(null);
  }

  function save() {
    onSave(
      rows.map((row) => {
        const draft = draftFor(row.id);
        return persistType(row.team, row.service_id, row.id, row.name, draft.arrivals, draft.departures);
      }),
    );
  }

  function bindRow(domKey: string) {
    return (el: HTMLTableRowElement | null) => {
      if (el) {
        rowNodes.current.set(domKey, el);
      } else {
        rowNodes.current.delete(domKey);
      }
    };
  }

  if (!currentService) {
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
      <p className="sub">Une ligne par événement, dans l’ordre du temps.</p>
      <div className="auth-switch">
        {offeredTabs.map((item) => (
          <button
            key={item.id}
            type="button"
            className={currentService === item.id ? "choice active" : "choice"}
            onClick={() => setServiceId(item.id)}
          >
            {item.label}
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
                  <th>Niveaux minimal requis (par arrivée | après départ)</th>
                  <th>STAFF minimal resultant</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {lines.map((line) => {
                  const reactKey = lineKey(line);
                  const domKey = `${row.id}:${reactKey}`;
                  const focused = focusKey === domKey;
                  if (line.kind === "arrival") {
                    const arrival = draft.arrivals[line.index];
                    const counts = levelsToCounts(arrival.post_levels);
                    const staff = sim.afterArrival[line.index];
                    return (
                      <tr
                        key={reactKey}
                        ref={bindRow(domKey)}
                        className={focused ? "type-row-focus" : undefined}
                      >
                        <td>Arrivée</td>
                        <td>
                          <Stepper
                            value={arrival.time_minutes}
                            step={15}
                            display={formatClock(arrival.time_minutes)}
                            onChange={(time_minutes) =>
                              changeLineTime(row.id, "arrival", line.index, time_minutes)
                            }
                            onDisplayClick={() =>
                              setDial({
                                mode: "edit",
                                typeId: row.id,
                                kind: "arrival",
                                index: line.index,
                                previousMinutes: arrival.time_minutes,
                              })
                            }
                          />
                        </td>
                        <td>
                          <div className="level-steppers">
                            {levels.map((level) => (
                              <Stepper
                                key={level}
                                label={String(level)}
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
                    <tr
                      key={reactKey}
                      ref={bindRow(domKey)}
                      className={focused ? "type-row-focus" : undefined}
                    >
                      <td>Départ</td>
                      <td>
                        <Stepper
                          value={departure.time_minutes}
                          step={15}
                          display={formatClock(departure.time_minutes)}
                          onChange={(time_minutes) =>
                            changeLineTime(row.id, "departure", line.index, time_minutes)
                          }
                          onDisplayClick={() =>
                            setDial({
                              mode: "edit",
                              typeId: row.id,
                              kind: "departure",
                              index: line.index,
                              previousMinutes: departure.time_minutes,
                            })
                          }
                        />
                      </td>
                      <td>
                        <div className="level-steppers">
                          {levels.map((level) => (
                            <Stepper
                              key={level}
                              label={String(level)}
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
                  setDial({
                    mode: "add",
                    typeId: row.id,
                    kind: "arrival",
                    previousMinutes: TIME_DIAL_ARRIVAL_PRESET,
                  })
                }
              >
                Ajouter une arrivée
              </button>
              <button
                type="button"
                className="choice"
                onClick={() =>
                  setDial({
                    mode: "add",
                    typeId: row.id,
                    kind: "departure",
                    previousMinutes: TIME_DIAL_DEPARTURE_PRESET,
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
      {dial ? (
        <TimeDial
          title={
            dial.mode === "add"
              ? dial.kind === "arrival"
                ? "Heure d’arrivée"
                : "Heure de départ"
              : "Modifier l’heure"
          }
          initialMinutes={dial.previousMinutes}
          onCancel={() => setDial(null)}
          onConfirm={confirmDial}
        />
      ) : null}
    </section>
  );
}
