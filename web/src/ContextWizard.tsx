import { useEffect, useState } from "react";
import { ApiHttpError } from "./sandbox";
import { DAYS_FR, WEEKDAYS_EN } from "./format";
import {
  CONTEXT_SERVICES,
  emptyWellbeing,
  employeesForPatch,
  loadContext,
  newId,
  patchContext,
  type ContextEmployee,
  type ContextServiceId,
  type RestaurantContext,
  type RoleRow,
  type ServiceType,
  type TeamId,
  type TypicalWeekCell,
  type Unavailability,
  type WeekendChoice,
  type Wellbeing,
} from "./context";
import { DAYS_FR_SHORT, formatClock, weekLabelPair } from "./format";

const STEPS = ["Rôles", "Équipe", "Souhaits bien-être", "Services", "Types", "Semaine type"] as const;
const TEAMS: { id: TeamId; label: string }[] = [
  { id: "salle", label: "Salle" },
  { id: "cuisine", label: "Cuisine" },
];

function legalLabel(id: string): string {
  return id === "france" ? "France" : id;
}

function emptyWeek(services: ContextServiceId[]): TypicalWeekCell[] {
  return WEEKDAYS_EN.flatMap((weekday) =>
    services.map((service_id) => ({
      weekday,
      service_id,
      type_id: null,
      closed: true,
    })),
  );
}

function inferUnlocked(ctx: RestaurantContext, team: TeamId): number {
  if (!ctx.ladders[team]) {
    return 0;
  }
  if (!ctx.employees.some((person) => person.team === team)) {
    return 1;
  }
  if (ctx.services.length === 0) {
    return 3;
  }
  if (!ctx.types.some((item) => item.team === team)) {
    return 4;
  }
  if (ctx.typical_week[team] == null) {
    return 5;
  }
  return 6;
}

function dayLabel(weekday: string): string {
  const index = WEEKDAYS_EN.indexOf(weekday as (typeof WEEKDAYS_EN)[number]);
  return index >= 0 ? DAYS_FR[index] : weekday;
}

export function ContextWizard() {
  const [ctx, setCtx] = useState<RestaurantContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [team, setTeam] = useState<TeamId>("salle");
  const [step, setStep] = useState(0);
  const [unlocked, setUnlocked] = useState<{ salle: number; cuisine: number }>({ salle: 0, cuisine: 0 });
  const [nameDraft, setNameDraft] = useState("");

  useEffect(() => {
    let cancelled = false;
    loadContext()
      .then((next) => {
        if (cancelled) {
          return;
        }
        setCtx(next);
        setNameDraft(next.name);
        setUnlocked({
          salle: inferUnlocked(next, "salle"),
          cuisine: inferUnlocked(next, "cuisine"),
        });
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

  async function apply(body: Parameters<typeof patchContext>[0], advance = false) {
    setBusy(true);
    setError(null);
    try {
      const next = await patchContext(body);
      setCtx(next);
      setNameDraft(next.name);
      setUnlocked({
        salle: inferUnlocked(next, "salle"),
        cuisine: inferUnlocked(next, "cuisine"),
      });
      if (advance) {
        setStep((prev) => Math.min(prev + 1, STEPS.length - 1));
      }
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  if (!ctx && !error) {
    return (
      <main className="page">
        <p className="sub">Chargement du restaurant…</p>
      </main>
    );
  }
  if (!ctx) {
    return (
      <main className="page">
        <h1>Mon restaurant</h1>
        <p className="error" role="alert">
          {error}
        </p>
      </main>
    );
  }

  const ladder = ctx.ladders[team];
  const teamEmployees = ctx.employees.filter((person) => person.team === team);
  const teamTypes = ctx.types.filter((item) => item.team === team);

  return (
    <main className="page context-page">
      <h1>Mon restaurant</h1>
      <section className="context-identity">
        <label>
          Nom
          <input value={nameDraft} onChange={(event) => setNameDraft(event.target.value)} />
        </label>
        <button type="button" className="choice" disabled={busy} onClick={() => void apply({ name: nameDraft })}>
          Enregistrer le nom
        </button>
        <p className="sub">Droit du travail : {legalLabel(ctx.legal_context_id)}</p>
        <p>
          Code entreprise : <code>{ctx.company_code}</code>
        </p>
        <p className="ready-badges">
          <span className={ctx.ready.salle ? "badge-ready" : "badge-wait"}>
            Salle · {ctx.ready.salle ? "Prêt à calculer" : "Pas encore prêt"}
          </span>
          <span className={ctx.ready.cuisine ? "badge-ready" : "badge-wait"}>
            Cuisine · {ctx.ready.cuisine ? "Prêt à calculer" : "Pas encore prêt"}
          </span>
        </p>
      </section>

      <div className="auth-switch">
        {TEAMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={team === item.id ? "choice active" : "choice"}
            onClick={() => {
              setTeam(item.id);
              setStep((current) => Math.min(current, unlocked[item.id]));
            }}
          >
            {item.label}
          </button>
        ))}
      </div>

      <ol className="wizard-steps">
        {STEPS.map((label, index) => (
          <li key={label}>
            <button
              type="button"
              className={step === index ? "choice active" : "choice"}
              disabled={index > unlocked[team]}
              onClick={() => setStep(index)}
            >
              {index + 1}. {label}
            </button>
          </li>
        ))}
      </ol>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {step === 0 ? (
        <RolesStep
          key={`${team}-roles`}
          roles={ladder?.roles ?? []}
          busy={busy}
          onSave={(roles) =>
            void apply(
              {
                ladders: {
                  salle: team === "salle" ? { roles, substitution_explained: true } : ctx.ladders.salle,
                  cuisine: team === "cuisine" ? { roles, substitution_explained: true } : ctx.ladders.cuisine,
                },
              },
              true,
            )
          }
        />
      ) : null}
      {step === 1 ? (
        <EmployeesStep
          key={`${team}-equipe`}
          team={team}
          roles={ladder?.roles ?? []}
          people={teamEmployees}
          all={ctx.employees}
          services={ctx.services}
          companyCode={ctx.company_code}
          busy={busy}
          onSave={(people) =>
            void apply(
              {
                employees: employeesForPatch([
                  ...ctx.employees.filter((person) => person.team !== team),
                  ...people,
                ]),
              },
              true,
            )
          }
        />
      ) : null}
      {step === 2 ? (
        <WishesStep
          key={`${team}-souhaits`}
          team={team}
          people={teamEmployees}
          all={ctx.employees}
          busy={busy}
          onSave={(people) =>
            void apply(
              {
                employees: employeesForPatch([
                  ...ctx.employees.filter((person) => person.team !== team),
                  ...people,
                ]),
              },
              true,
            )
          }
        />
      ) : null}
      {step === 3 ? (
        <ServicesStep
          key={`${team}-services`}
          selected={ctx.services}
          busy={busy}
          onSave={(services) => void apply({ services }, true)}
        />
      ) : null}
      {step === 4 ? (
        <TypesStep
          key={`${team}-${ctx.services.join(",")}-types`}
          team={team}
          services={ctx.services}
          types={teamTypes}
          busy={busy}
          onSave={(types) =>
            void apply(
              {
                types: [...ctx.types.filter((item) => item.team !== team), ...types],
              },
              true,
            )
          }
        />
      ) : null}
      {step === 5 ? (
        <WeekStep
          key={`${team}-${ctx.services.join(",")}-week`}
          team={team}
          services={ctx.services}
          types={teamTypes}
          cells={ctx.typical_week[team] ?? emptyWeek(ctx.services)}
          other={team === "salle" ? ctx.typical_week.cuisine : ctx.typical_week.salle}
          weekLabels={ctx.week_labels}
          busy={busy}
          onSave={(cells) =>
            void apply({
              typical_week: {
                salle: team === "salle" ? cells : ctx.typical_week.salle,
                cuisine: team === "cuisine" ? cells : ctx.typical_week.cuisine,
              },
            })
          }
        />
      ) : null}
    </main>
  );
}

function RolesStep({
  roles,
  busy,
  onSave,
}: {
  roles: RoleRow[];
  busy: boolean;
  onSave: (roles: RoleRow[]) => void;
}) {
  const [rows, setRows] = useState<RoleRow[]>(roles.length ? roles : [{ name: "", level: 1 }]);
  return (
    <section>
      <h2>Rôles</h2>
      <p className="sub">Un niveau plus élevé peut tenir un poste inférieur.</p>
      {rows.map((row, index) => (
        <div key={index} className="auth-row">
          <input
            placeholder="Nom du rôle"
            value={row.name}
            onChange={(event) =>
              setRows((prev) => prev.map((item, i) => (i === index ? { ...item, name: event.target.value } : item)))
            }
          />
          <input
            type="number"
            min={1}
            value={row.level}
            onChange={(event) =>
              setRows((prev) =>
                prev.map((item, i) =>
                  i === index
                    ? { ...item, level: Math.max(1, Math.floor(Number(event.target.value) || 1)) }
                    : item,
                ),
              )
            }
          />
        </div>
      ))}
      <button type="button" className="choice" onClick={() => setRows((prev) => [...prev, { name: "", level: 1 }])}>
        Ajouter un rôle
      </button>
      <button
        type="button"
        className="choice active"
        disabled={busy || rows.some((row) => !row.name.trim())}
        onClick={() => onSave(rows.map((row) => ({ name: row.name.trim(), level: row.level })))}
      >
        Enregistrer et continuer
      </button>
    </section>
  );
}

function serviceCaption(serviceId: string): string {
  return (CONTEXT_SERVICES.find((item) => item.id === serviceId)?.label ?? serviceId).toLowerCase();
}

function formatUnavailSlot(row: Unavailability): string {
  return `${dayLabel(row.weekday)} ${serviceCaption(row.service_id)}`;
}

function EmployeesStep({
  team,
  roles,
  people,
  all,
  services,
  companyCode,
  busy,
  onSave,
}: {
  team: TeamId;
  roles: RoleRow[];
  people: ContextEmployee[];
  all: ContextEmployee[];
  services: ContextServiceId[];
  companyCode: string;
  busy: boolean;
  onSave: (people: ContextEmployee[]) => void;
}) {
  const [rows, setRows] = useState<ContextEmployee[]>(people);
  const [popupIndex, setPopupIndex] = useState<number | null>(null);
  function add() {
    const role = roles[0];
    if (!role) {
      return;
    }
    setRows((prev) => [
      ...prev,
      {
        id: newId(team),
        name: "",
        team,
        role: { name: role.name, level: role.level, team },
        contractual_hours_per_week: 35,
        min_shift_hours: 4,
        unavailabilities: [],
        wellbeing: emptyWellbeing(),
        invite_token: "",
      },
    ]);
  }
  return (
    <section>
      <h2>Équipe</h2>
      <p className="sub">
        Liste complète envoyée (l’autre équipe est conservée : {all.filter((p) => p.team !== team).length} salarié(s)).
      </p>
      {rows.map((person, index) => (
        <article key={person.id} className="fiche-card equipe-row">
          <div className="equipe-line">
            <input
              placeholder="Nom"
              value={person.name}
              onChange={(event) =>
                setRows((prev) => prev.map((item, i) => (i === index ? { ...item, name: event.target.value } : item)))
              }
            />
            <label>
              Rôle
              <select
                value={person.role.name}
                onChange={(event) => {
                  const role = roles.find((item) => item.name === event.target.value) ?? roles[0];
                  if (!role) {
                    return;
                  }
                  setRows((prev) =>
                    prev.map((item, i) =>
                      i === index ? { ...item, role: { name: role.name, level: role.level, team } } : item,
                    ),
                  );
                }}
              >
                {roles.map((role) => (
                  <option key={role.name} value={role.name}>
                    {role.name} ({role.level})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Heures contrat
              <input
                type="number"
                min={0}
                value={person.contractual_hours_per_week}
                onChange={(event) =>
                  setRows((prev) =>
                    prev.map((item, i) =>
                      i === index ? { ...item, contractual_hours_per_week: Number(event.target.value) || 0 } : item,
                    ),
                  )
                }
              />
            </label>
            <label>
              Min. créneau (h)
              <input
                type="number"
                min={1}
                step={1}
                value={person.min_shift_hours}
                onChange={(event) =>
                  setRows((prev) =>
                    prev.map((item, i) =>
                      i === index ? { ...item, min_shift_hours: Math.max(1, Number(event.target.value) || 4) } : item,
                    ),
                  )
                }
              />
            </label>
          </div>
          <p className="unavail-summary">
            {person.unavailabilities.length === 0
              ? "Aucune indispo"
              : person.unavailabilities.map((row) => formatUnavailSlot(row)).join(", ")}
          </p>
          <div className="unavail-chips">
            {person.unavailabilities.map((row, slotIndex) => (
              <button
                key={`${row.weekday}-${row.service_id}-${slotIndex}`}
                type="button"
                className="chip"
                onClick={() =>
                  setRows((prev) =>
                    prev.map((item, i) =>
                      i === index
                        ? { ...item, unavailabilities: item.unavailabilities.filter((_, j) => j !== slotIndex) }
                        : item,
                    ),
                  )
                }
              >
                {formatUnavailSlot(row)} ×
              </button>
            ))}
            <button type="button" className="choice" onClick={() => setPopupIndex(index)}>
              Ajouter une indispo
            </button>
          </div>
          {person.invite_token ? (
            <p className="sub">
              Jeton : <code>{person.invite_token}</code>
              <br />
              URL :{" "}
              <code>
                /register?company_code={companyCode}&employee_token={person.invite_token}
              </code>
            </p>
          ) : null}
        </article>
      ))}
      <button type="button" className="choice" disabled={!roles.length} onClick={add}>
        Ajouter un salarié
      </button>
      <button
        type="button"
        className="choice active"
        disabled={busy || rows.some((row) => !row.name.trim()) || rows.length === 0}
        onClick={() => onSave(rows)}
      >
        Enregistrer et continuer
      </button>
      {popupIndex !== null ? (
        <UnavailPopup
          services={services.length ? services : CONTEXT_SERVICES.map((item) => item.id)}
          onClose={() => setPopupIndex(null)}
          onConfirm={(slots) => {
            const target = popupIndex;
            setRows((prev) =>
              prev.map((item, i) => {
                if (i !== target) {
                  return item;
                }
                const seen = new Set(item.unavailabilities.map((row) => `${row.weekday}:${row.service_id}`));
                const extra = slots.filter((row) => !seen.has(`${row.weekday}:${row.service_id}`));
                return { ...item, unavailabilities: [...item.unavailabilities, ...extra] };
              }),
            );
            setPopupIndex(null);
          }}
        />
      ) : null}
    </section>
  );
}

function UnavailPopup({
  services,
  onClose,
  onConfirm,
}: {
  services: ContextServiceId[];
  onClose: () => void;
  onConfirm: (slots: Unavailability[]) => void;
}) {
  const [days, setDays] = useState<string[]>([]);
  const [serviceIds, setServiceIds] = useState<ContextServiceId[]>([]);
  function toggleDay(day: string) {
    setDays((prev) => (prev.includes(day) ? prev.filter((item) => item !== day) : [...prev, day]));
  }
  function toggleService(id: ContextServiceId) {
    setServiceIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]));
  }
  return (
    <div className="overlay-backdrop" onClick={onClose}>
      <div className="overlay unavail-popup" onClick={(event) => event.stopPropagation()} role="dialog" aria-labelledby="unavail-title">
        <h3 id="unavail-title">Ajouter une indispo</h3>
        <p className="sub">Jours × services : chaque case cochée produit un créneau.</p>
        <fieldset>
          <legend>Jours</legend>
          <div className="check-grid">
            {WEEKDAYS_EN.map((day, index) => (
              <label key={day} className="auth-fiche">
                <input type="checkbox" checked={days.includes(day)} onChange={() => toggleDay(day)} />
                {DAYS_FR_SHORT[index]}
              </label>
            ))}
          </div>
          <div className="auth-row">
            <button type="button" className="choice" onClick={() => setDays([...WEEKDAYS_EN])}>
              Tout sélectionner
            </button>
            <button type="button" className="choice" onClick={() => setDays([])}>
              Tout déselectionner
            </button>
          </div>
        </fieldset>
        <fieldset>
          <legend>Services</legend>
          <div className="check-grid">
            {CONTEXT_SERVICES.filter((item) => services.includes(item.id)).map((item) => (
              <label key={item.id} className="auth-fiche">
                <input type="checkbox" checked={serviceIds.includes(item.id)} onChange={() => toggleService(item.id)} />
                {item.label}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="auth-row">
          <button type="button" className="choice" onClick={onClose}>
            Annuler
          </button>
          <button
            type="button"
            className="choice active"
            disabled={days.length === 0 || serviceIds.length === 0}
            onClick={() =>
              onConfirm(
                days.flatMap((weekday) => serviceIds.map((service_id) => ({ weekday, service_id }))),
              )
            }
          >
            Valider
          </button>
        </div>
      </div>
    </div>
  );
}

const WEEKEND_OPTIONS: { value: WeekendChoice; label: string }[] = [
  { value: "every_two", label: "Un we sur deux" },
  { value: "even", label: "We paire" },
  { value: "odd", label: "We impaire" },
];

function digitValue(raw: string): number | undefined {
  if (raw.trim() === "") {
    return undefined;
  }
  const n = Number(raw);
  return Number.isFinite(n) ? n : undefined;
}

function WishesStep({
  team,
  people,
  all,
  busy,
  onSave,
}: {
  team: TeamId;
  people: ContextEmployee[];
  all: ContextEmployee[];
  busy: boolean;
  onSave: (people: ContextEmployee[]) => void;
}) {
  const [rows, setRows] = useState<ContextEmployee[]>(people);
  function setWellbeing(index: number, patch: Partial<Wellbeing>) {
    setRows((prev) =>
      prev.map((item, i) => (i === index ? { ...item, wellbeing: { ...item.wellbeing, ...patch } } : item)),
    );
  }
  return (
    <section>
      <h2>Souhaits bien-être</h2>
      <p className="sub">
        Pas un prérequis pour calculer. L’autre équipe est conservée ({all.filter((p) => p.team !== team).length}{" "}
        salarié(s)).
      </p>
      <div className="scroll">
        <table className="wishes-edit">
          <thead>
            <tr>
              <th>Salarié</th>
              <th>Deux repos consécutifs par semaine</th>
              <th>Week-end</th>
              <th>Max petit-déj / déj / dîner</th>
              <th>Nbre de coupures max</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((person, index) => (
              <tr key={person.id}>
                <td>{person.name || "—"}</td>
                <td>
                  <label className="auth-fiche">
                    <input
                      type="checkbox"
                      checked={person.wellbeing.consecutive_rest}
                      onChange={(event) => setWellbeing(index, { consecutive_rest: event.target.checked })}
                    />
                  </label>
                </td>
                <td>
                  {WEEKEND_OPTIONS.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      className={person.wellbeing.weekend === option.value ? "choice active" : "choice"}
                      onClick={() =>
                        setWellbeing(index, {
                          weekend: person.wellbeing.weekend === option.value ? null : option.value,
                        })
                      }
                    >
                      {option.label}
                    </button>
                  ))}
                </td>
                <td className="max-services">
                  {(["morning", "midday", "evening"] as const).map((id) => (
                    <input
                      key={id}
                      type="number"
                      min={0}
                      placeholder={id === "morning" ? "PDJ" : id === "midday" ? "Déj" : "Dîner"}
                      value={person.wellbeing.max_services[id] ?? ""}
                      onChange={(event) => {
                        const next = { ...person.wellbeing.max_services };
                        const parsed = digitValue(event.target.value);
                        if (parsed === undefined) {
                          delete next[id];
                        } else {
                          next[id] = parsed;
                        }
                        setWellbeing(index, { max_services: next });
                      }}
                    />
                  ))}
                </td>
                <td>
                  <input
                    type="number"
                    min={0}
                    value={person.wellbeing.max_coupures_per_week ?? ""}
                    onChange={(event) => {
                      const parsed = digitValue(event.target.value);
                      setWellbeing(index, { max_coupures_per_week: parsed === undefined ? null : parsed });
                    }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button type="button" className="choice active" disabled={busy || rows.length === 0} onClick={() => onSave(rows)}>
        Enregistrer et continuer
      </button>
    </section>
  );
}

function ServicesStep({
  selected,
  busy,
  onSave,
}: {
  selected: ContextServiceId[];
  busy: boolean;
  onSave: (services: ContextServiceId[]) => void;
}) {
  const [ids, setIds] = useState<ContextServiceId[]>(selected);
  return (
    <section>
      <h2>Services</h2>
      <p className="sub">Une fois pour tout le restaurant.</p>
      {CONTEXT_SERVICES.map((service) => (
        <label key={service.id} className="auth-fiche">
          <input
            type="checkbox"
            checked={ids.includes(service.id)}
            onChange={(event) =>
              setIds((prev) =>
                event.target.checked ? [...prev, service.id] : prev.filter((id) => id !== service.id),
              )
            }
          />
          {service.label}
        </label>
      ))}
      <button type="button" className="choice active" disabled={busy || ids.length === 0} onClick={() => onSave(ids)}>
        Enregistrer et continuer
      </button>
    </section>
  );
}

function TypesStep({
  team,
  services,
  types,
  busy,
  onSave,
}: {
  team: TeamId;
  services: ContextServiceId[];
  types: ServiceType[];
  busy: boolean;
  onSave: (types: ServiceType[]) => void;
}) {
  const [rows, setRows] = useState<ServiceType[]>(
    types.length
      ? types
      : services.map((service_id) => ({
          id: newId(`${team}-${service_id}`),
          name: "",
          team,
          service_id,
          arrivals: [{ time_minutes: 11 * 60, post_levels: [1] }],
          departures: [{ time_minutes: 16 * 60, remaining_post_levels: [] }],
        })),
  );
  return (
    <section>
      <h2>Types</h2>
      {rows.map((row, index) => (
        <article key={row.id} className="fiche-card">
          <input
            placeholder="Nom de la feuille"
            value={row.name}
            onChange={(event) =>
              setRows((prev) => prev.map((item, i) => (i === index ? { ...item, name: event.target.value } : item)))
            }
          />
          <p className="sub">
            {CONTEXT_SERVICES.find((item) => item.id === row.service_id)?.label ?? row.service_id}
          </p>
          <WaveEditor
            label="Arrivées"
            time={row.arrivals[0]?.time_minutes ?? 660}
            levels={row.arrivals[0]?.post_levels ?? [1]}
            onTime={(time_minutes) =>
              setRows((prev) =>
                prev.map((item, i) =>
                  i === index
                    ? { ...item, arrivals: [{ time_minutes, post_levels: item.arrivals[0]?.post_levels ?? [1] }] }
                    : item,
                ),
              )
            }
            onLevels={(post_levels) =>
              setRows((prev) =>
                prev.map((item, i) =>
                  i === index
                    ? { ...item, arrivals: [{ time_minutes: item.arrivals[0]?.time_minutes ?? 660, post_levels }] }
                    : item,
                ),
              )
            }
          />
          <WaveEditor
            label="Départs"
            time={row.departures[0]?.time_minutes ?? 960}
            levels={row.departures[0]?.remaining_post_levels ?? []}
            remaining
            onTime={(time_minutes) =>
              setRows((prev) =>
                prev.map((item, i) =>
                  i === index
                    ? {
                        ...item,
                        departures: [
                          { time_minutes, remaining_post_levels: item.departures[0]?.remaining_post_levels ?? [] },
                        ],
                      }
                    : item,
                ),
              )
            }
            onLevels={(remaining_post_levels) =>
              setRows((prev) =>
                prev.map((item, i) =>
                  i === index
                    ? {
                        ...item,
                        departures: [
                          { time_minutes: item.departures[0]?.time_minutes ?? 960, remaining_post_levels },
                        ],
                      }
                    : item,
                ),
              )
            }
          />
        </article>
      ))}
      <button
        type="button"
        className="choice active"
        disabled={busy || rows.some((row) => !row.name.trim() || !row.arrivals[0]?.post_levels.length)}
        onClick={() => onSave(rows)}
      >
        Enregistrer et continuer
      </button>
    </section>
  );
}

function WaveEditor({
  label,
  time,
  levels,
  remaining,
  onTime,
  onLevels,
}: {
  label: string;
  time: number;
  levels: number[];
  remaining?: boolean;
  onTime: (minutes: number) => void;
  onLevels: (levels: number[]) => void;
}) {
  return (
    <div>
      <p>
        {label} {formatClock(time)}
      </p>
      <button type="button" className="choice" onClick={() => onTime(time - 15)}>
        −15
      </button>
      <button type="button" className="choice" onClick={() => onTime(time + 15)}>
        +15
      </button>
      <label>
        {remaining ? "Niveaux restants" : "Niveaux de poste"}
        <input
          value={levels.join(",")}
          onChange={(event) =>
            onLevels(
              event.target.value
                .split(",")
                .map((part) => Number(part.trim()))
                .filter((value) => Number.isInteger(value)),
            )
          }
        />
      </label>
    </div>
  );
}

function WeekStep({
  team,
  services,
  types,
  cells,
  other,
  weekLabels,
  busy,
  onSave,
}: {
  team: TeamId;
  services: ContextServiceId[];
  types: ServiceType[];
  cells: TypicalWeekCell[];
  other: TypicalWeekCell[] | null;
  weekLabels: "ab" | "parity";
  busy: boolean;
  onSave: (cells: TypicalWeekCell[]) => void;
}) {
  const [rows, setRows] = useState<TypicalWeekCell[]>(cells);
  function cell(weekday: string, service_id: ContextServiceId): TypicalWeekCell {
    return (
      rows.find((item) => item.weekday === weekday && item.service_id === service_id) ?? {
        weekday,
        service_id,
        type_id: null,
        closed: true,
      }
    );
  }
  function setCell(weekday: string, service_id: ContextServiceId, value: string) {
    const next: TypicalWeekCell =
      value === ""
        ? { weekday, service_id, type_id: null, closed: true }
        : { weekday, service_id, type_id: value, closed: false };
    setRows((prev) => {
      const without = prev.filter((item) => !(item.weekday === weekday && item.service_id === service_id));
      return [...without, next];
    });
  }
  return (
    <section>
      <h2>Semaine type · {team}</h2>
      <p className="sub">Libellés de cycle : {weekLabelPair(weekLabels)}</p>
      <div className="scroll">
        <table className="matrix">
          <thead>
            <tr>
              <th>Jour</th>
              {services.map((id) => (
                <th key={id}>{CONTEXT_SERVICES.find((item) => item.id === id)?.label ?? id}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {WEEKDAYS_EN.map((day) => (
              <tr key={day}>
                <td>{dayLabel(day)}</td>
                {services.map((service_id) => {
                  const current = cell(day, service_id);
                  return (
                    <td key={service_id}>
                      <select
                        value={current.closed ? "" : (current.type_id ?? "")}
                        onChange={(event) => setCell(day, service_id, event.target.value)}
                      >
                        <option value="">Fermé</option>
                        {types
                          .filter((item) => item.service_id === service_id)
                          .map((item) => (
                            <option key={item.id} value={item.id}>
                              {item.name}
                            </option>
                          ))}
                      </select>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="sub">L’autre équipe est renvoyée telle quelle ({other ? `${other.length} cases` : "null"}).</p>
      <button type="button" className="choice active" disabled={busy} onClick={() => onSave(rows)}>
        Enregistrer la semaine
      </button>
    </section>
  );
}
