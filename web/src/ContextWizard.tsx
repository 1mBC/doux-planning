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
  purgeRemovedServices,
  seedExampleContext,
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
import { DAYS_FR_SHORT, weekLabelPair } from "./format";
import { ServiceTypesStep } from "./ServiceTypesStep";
import { Stepper } from "./Stepper";
import { inviteQrDataUrl, inviteRegisterPath } from "./inviteQr";

const STEPS = ["Services", "Rôles", "Équipe", "Souhaits bien-être", "Services types", "Semaine type"] as const;
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
  if (ctx.services.length === 0) {
    return 0;
  }
  if (!ctx.ladders[team]) {
    return 1;
  }
  if (!ctx.employees.some((person) => person.team === team)) {
    return 2;
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
  const [wizardEpoch, setWizardEpoch] = useState(0);
  const [inviteOpen, setInviteOpen] = useState(false);

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

  function adopt(next: RestaurantContext) {
    setCtx(next);
    setNameDraft(next.name);
    setUnlocked({
      salle: inferUnlocked(next, "salle"),
      cuisine: inferUnlocked(next, "cuisine"),
    });
  }

  async function seedExample() {
    const ok = window.confirm(
      "Ça remplace rôles, équipe, souhaits, types et semaine, garde le nom, casse les comptes salariés liés, et ne colle pas le planning exemple.",
    );
    if (!ok) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const next = await seedExampleContext();
      adopt(next);
      setWizardEpoch((value) => value + 1);
    } catch (err) {
      setError(err instanceof ApiHttpError ? err.detail : err instanceof Error ? err.message : "erreur inattendue");
    } finally {
      setBusy(false);
    }
  }

  async function apply(body: Parameters<typeof patchContext>[0], advance = false) {
    setBusy(true);
    setError(null);
    try {
      const next = await patchContext(body);
      adopt(next);
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
        <p className="seed-row">
          Code entreprise : <code>{ctx.company_code}</code>{" "}
          <button type="button" className="choice" onClick={() => setInviteOpen(true)}>
            Inviter mes employés
          </button>{" "}
          <button type="button" className="choice" disabled={busy} onClick={() => void seedExample()}>
            {busy ? "Intégration…" : "Intégrer l’exemple Saint-Cloud"}
          </button>
        </p>
        {inviteOpen ? <InvitePopup companyCode={ctx.company_code} onClose={() => setInviteOpen(false)} /> : null}
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
        <ServicesStep
          key={`${wizardEpoch}-services`}
          selected={ctx.services}
          busy={busy}
          onSave={(services) => {
            const removed = ctx.services.filter((id) => !services.includes(id));
            if (removed.length > 0) {
              const ok = window.confirm(
                "Ça efface types, cases de semaine, indispos et plafonds de ce service.",
              );
              if (!ok) {
                return;
              }
              const cleaned = purgeRemovedServices(ctx, services);
              setWizardEpoch((value) => value + 1);
              void apply(
                {
                  services,
                  employees: employeesForPatch(cleaned.employees),
                  types: cleaned.types,
                  typical_week: cleaned.typical_week,
                },
                true,
              );
              return;
            }
            void apply({ services }, true);
          }}
        />
      ) : null}
      {step === 1 ? (
        <RolesStep
          key={`${wizardEpoch}-${team}-roles`}
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
      {step === 2 ? (
        <EmployeesStep
          key={`${wizardEpoch}-${team}-equipe`}
          team={team}
          roles={ladder?.roles ?? []}
          people={teamEmployees}
          all={ctx.employees}
          services={ctx.services}
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
        <WishesStep
          key={`${wizardEpoch}-${team}-souhaits`}
          team={team}
          people={teamEmployees}
          all={ctx.employees}
          services={ctx.services}
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
      {step === 4 ? (
        <ServiceTypesStep
          key={`${wizardEpoch}-${team}-${ctx.services.join(",")}-types`}
          team={team}
          services={ctx.services}
          roles={ladder?.roles ?? []}
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
          key={`${wizardEpoch}-${team}-${ctx.services.join(",")}-week`}
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

function InvitePopup({ companyCode, onClose }: { companyCode: string; onClose: () => void }) {
  const path = inviteRegisterPath(companyCode);
  const [qr, setQr] = useState("");
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    let cancelled = false;
    void inviteQrDataUrl(companyCode).then((dataUrl) => {
      if (!cancelled) {
        setQr(dataUrl);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [companyCode]);

  async function copy() {
    await navigator.clipboard.writeText(path);
    setCopied(true);
  }

  return (
    <div className="overlay-backdrop" onClick={onClose}>
      <div
        className="overlay invite-popup"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-labelledby="invite-title"
      >
        <h3 id="invite-title">Inviter mes employés</h3>
        <p className="sub">Ils s’inscrivent avec le code entreprise. Le jeton de chaque fiche reste masqué.</p>
        <p>
          <code>{path}</code>
        </p>
        <div className="auth-row">
          <button type="button" className="choice active" onClick={() => void copy()}>
            {copied ? "URL copiée" : "Copier l’URL"}
          </button>
          <button type="button" className="choice" onClick={onClose}>
            Fermer
          </button>
        </div>
        {qr ? <img className="invite-qr" src={qr} alt="QR d’inscription" /> : <p className="sub">QR…</p>}
      </div>
    </div>
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
        <article key={index} className="fiche-card equipe-row">
          <div className="equipe-line">
            <label>
              Nom
              <input
                placeholder="Nom"
                value={row.name}
                onChange={(event) =>
                  setRows((prev) => prev.map((item, i) => (i === index ? { ...item, name: event.target.value } : item)))
                }
              />
            </label>
            <label>
              Niveau
              <Stepper
                value={row.level}
                min={1}
                onChange={(level) =>
                  setRows((prev) => prev.map((item, i) => (i === index ? { ...item, level } : item)))
                }
              />
            </label>
          </div>
        </article>
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
  busy,
  onSave,
}: {
  team: TeamId;
  roles: RoleRow[];
  people: ContextEmployee[];
  all: ContextEmployee[];
  services: ContextServiceId[];
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
  services,
  busy,
  onSave,
}: {
  team: TeamId;
  people: ContextEmployee[];
  all: ContextEmployee[];
  services: ContextServiceId[];
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
              <th>
                Max{" "}
                {CONTEXT_SERVICES.filter((item) => services.includes(item.id))
                  .map((item) => item.label.toLowerCase())
                  .join(" / ") || "services"}
              </th>
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
                  <div className="weekend-cell">
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
                    <label className="auth-fiche weekend-rest-day">
                      <input
                        type="checkbox"
                        checked={person.wellbeing.weekend_rest_day}
                        onChange={(event) =>
                          setWellbeing(index, { weekend_rest_day: event.target.checked })
                        }
                      />
                      Au moins un repos samedi ou dimanche
                    </label>
                  </div>
                </td>
                <td className="max-services">
                  {CONTEXT_SERVICES.filter((item) => services.includes(item.id)).map((item) => (
                    <input
                      key={item.id}
                      type="number"
                      min={0}
                      placeholder={item.id === "morning" ? "PDJ" : item.id === "midday" ? "Déj" : "Dîner"}
                      value={person.wellbeing.max_services[item.id] ?? ""}
                      onChange={(event) => {
                        const next = { ...person.wellbeing.max_services };
                        const parsed = digitValue(event.target.value);
                        if (parsed === undefined) {
                          delete next[item.id];
                        } else {
                          next[item.id] = parsed;
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
