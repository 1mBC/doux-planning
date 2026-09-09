import type { LegalRow, PlanningStats, ScoreFact, StatusCell, WishRow } from "./types";

export type WeekLabelScheme = "ab" | "parity";

function formatClock(minutes: number): string {
  const total = ((minutes % 1440) + 1440) % 1440;
  const hours = Math.floor(total / 60);
  const mins = total % 60;
  const hourLabel = hours === 0 ? "00h" : `${hours}h`;
  if (mins === 0) {
    return hourLabel;
  }
  return `${hours}h${String(mins).padStart(2, "0")}`;
}

function weekdayFromIndex(dayIndex: number): string {
  return ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"][(((dayIndex % 7) + 7) % 7)];
}

export const KIND_TITLE_FR: Record<string, string> = {
  empty_post: "Poste vide",
  post_held: "Poste tenu",
  assigned_on_closure: "Shift sur fermeture",
  rest_between_days: "Repos 11 h",
  weekly_rest_days: "Repos hebdo",
  max_coupure: "Coupure",
  max_daily_hours: "Amplitude journalière",
  max_weekly_hours: "Heures hebdo",
  unavailability: "Indispo",
  contract_hours: "Heures de contrat",
  consecutive_rest_days: "Repos consécutifs",
  weekend_rest_day: "Repos week-end",
  weekend_every_two_weeks: "Un week-end / 14 j.",
  weekend_even_weeks: "Week-end pair",
  weekend_odd_weeks: "Week-end impair",
  max_mornings: "Max petit-déj",
  max_middays: "Max déjeuner",
  max_evenings: "Max dîner",
  max_coupures: "Max coupures",
  role_gap: "Adéquation rôle",
};

const WEEKDAY_FR: Record<string, string> = {
  monday: "lundi",
  tuesday: "mardi",
  wednesday: "mercredi",
  thursday: "jeudi",
  friday: "vendredi",
  saturday: "samedi",
  sunday: "dimanche",
};

const SERVICE_FR: Record<string, string> = {
  morning: "petit-déjeuner",
  midday: "déjeuner",
  evening: "dîner",
};

const WEEKEND_FR: Record<string, string> = {
  every_two: "un week-end sur deux",
  even: "paire",
  odd: "impaire",
};

const AXIS_FROM_KIND: Record<string, string> = {
  empty_post: "couverture",
  post_held: "couverture",
  assigned_on_closure: "couverture",
  rest_between_days: "legal",
  weekly_rest_days: "legal",
  max_coupure: "legal",
  max_daily_hours: "legal",
  max_weekly_hours: "legal",
  unavailability: "contrat",
  contract_hours: "contrat",
  consecutive_rest_days: "wellbeing",
  weekend_rest_day: "wellbeing",
  weekend_every_two_weeks: "wellbeing",
  weekend_even_weeks: "wellbeing",
  weekend_odd_weeks: "wellbeing",
  max_mornings: "wellbeing",
  max_middays: "wellbeing",
  max_evenings: "wellbeing",
  max_coupures: "wellbeing",
  role_gap: "roles",
};

export type FactFormatCtx = {
  names?: Map<string, string>;
  weekScheme?: WeekLabelScheme;
};

export function factTitle(kind: string): string {
  return KIND_TITLE_FR[kind] ?? kind;
}

export function factAxis(kind: string): string {
  return AXIS_FROM_KIND[kind] ?? "couverture";
}

export function hoursLabel(value: number): string {
  const minutes = Math.round(value * 60);
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (mins === 0) {
    return `${hours}h`;
  }
  if (mins === 30) {
    return `${hours}h30`;
  }
  return `${hours}h${String(mins).padStart(2, "0")}`;
}

export function evaluateMisses(facts: ScoreFact[]): ScoreFact[] {
  return facts.filter((fact) => fact.polarity === "miss" && fact.kind !== "role_gap");
}

export const AXIS_ORDER = ["couverture", "legal", "contrat", "wellbeing", "roles"] as const;

export const AXIS_LABEL_FR: Record<(typeof AXIS_ORDER)[number], string> = {
  couverture: "Couverture",
  legal: "Légal",
  contrat: "Contrat",
  wellbeing: "Bien-être",
  roles: "Rôles",
};

export function factCategory(axis: string): string {
  if (axis in AXIS_LABEL_FR) {
    return AXIS_LABEL_FR[axis as keyof typeof AXIS_LABEL_FR];
  }
  return axis;
}

export function factSubcategory(kind: string): string {
  if (kind === "contract_hours") {
    return "Occupation";
  }
  if (kind === "unavailability") {
    return "Indispo";
  }
  if (kind === "empty_post" || kind === "post_held") {
    return "Poste";
  }
  if (kind === "assigned_on_closure") {
    return "Fermeture";
  }
  return factTitle(kind);
}

export function sortFactsForTable(facts: ScoreFact[]): ScoreFact[] {
  const rank = (axis: string): number => {
    const index = AXIS_ORDER.indexOf(axis as (typeof AXIS_ORDER)[number]);
    return index === -1 ? AXIS_ORDER.length : index;
  };
  const stable = (items: ScoreFact[]): ScoreFact[] =>
    items
      .map((fact, index) => ({ fact, index }))
      .sort((a, b) => rank(a.fact.axis) - rank(b.fact.axis) || a.index - b.index)
      .map((item) => item.fact);
  return [...stable(facts.filter((fact) => fact.polarity === "miss")), ...stable(facts.filter((fact) => fact.polarity !== "miss"))];
}

export function factsForAxis(facts: ScoreFact[], axis: string | "global"): ScoreFact[] {
  const filtered = axis === "global" ? facts : facts.filter((fact) => fact.axis === axis);
  return sortFactsForTable(filtered);
}

export function factSeverityLabel(fact: Pick<ScoreFact, "kind" | "severity" | "polarity">): string {
  if (fact.kind === "contract_hours") {
    return "Contrat";
  }
  if (fact.severity === "interdit") {
    return "Interdit";
  }
  if (fact.severity === "couverture") {
    return "Couverture";
  }
  if (fact.severity === "souhait") {
    return "Souhait";
  }
  if (fact.polarity === "hit") {
    return "Tenu";
  }
  return "—";
}

function payloadEmpty(payload: Record<string, unknown>): boolean {
  return Object.keys(payload).length === 0;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function asInt(value: unknown): number | null {
  const n = asNumber(value);
  return n === null ? null : Math.trunc(n);
}

function weekdayFr(value: unknown, dayIndex?: number | null): string {
  const key = asString(value);
  if (key && WEEKDAY_FR[key]) {
    return WEEKDAY_FR[key];
  }
  if (dayIndex !== null && dayIndex !== undefined && Number.isFinite(dayIndex)) {
    return weekdayFromIndex(dayIndex);
  }
  return key ?? "—";
}

function serviceFr(value: unknown): string {
  const key = asString(value);
  if (!key) {
    return "—";
  }
  return SERVICE_FR[key] ?? key;
}

function weekLabel(dayIndex: number | null | undefined, scheme: WeekLabelScheme): string {
  if (dayIndex === null || dayIndex === undefined || !Number.isFinite(dayIndex)) {
    return scheme === "parity" ? "Paire" : "A";
  }
  if (scheme === "parity") {
    return dayIndex < 7 ? "Paire" : "Impaire";
  }
  return dayIndex < 7 ? "A" : "B";
}

function weekFromPayload(payload: Record<string, unknown>, dayIndex: number | null, scheme: WeekLabelScheme): string {
  const start = asInt(payload.week_start);
  if (start !== null) {
    return weekLabel(start, scheme);
  }
  return weekLabel(dayIndex, scheme);
}

function personName(fact: ScoreFact, ctx: FactFormatCtx): string {
  const named = fact.employee_name?.trim();
  if (named) {
    return named;
  }
  if (fact.employee_id) {
    return ctx.names?.get(fact.employee_id) ?? fact.employee_id;
  }
  return "";
}

function clock(value: unknown): string {
  const n = asNumber(value);
  return n === null ? "—" : formatClock(n);
}

function rawPayload(payload: Record<string, unknown>): string {
  try {
    return JSON.stringify(payload);
  } catch {
    return String(payload);
  }
}

function knownKind(kind: string): boolean {
  return kind in KIND_TITLE_FR;
}

function dayList(payload: Record<string, unknown>): string | null {
  const indexes = payload.day_indexes;
  if (!Array.isArray(indexes) || indexes.length === 0) {
    return null;
  }
  return indexes
    .map((item) => weekdayFr(undefined, asInt(item)))
    .join(", ");
}

function slotLine(payload: Record<string, unknown>, dayIndex: number | null, scheme: WeekLabelScheme): string {
  const jour = weekdayFr(payload.weekday, dayIndex);
  const week = weekFromPayload(payload, dayIndex, scheme);
  const service = serviceFr(payload.service_id);
  const start = clock(payload.start_minutes);
  const end = clock(payload.end_minutes);
  const level = asNumber(payload.post_level);
  const niveau = level === null ? "" : ` · niveau ${level}`;
  return `${jour} · sem. ${week} · ${service} · ${start}–${end}${niveau}`;
}

function formatKnownLine(fact: ScoreFact, ctx: FactFormatCtx): string | null {
  const payload = fact.payload;
  const scheme = ctx.weekScheme ?? "ab";
  const name = personName(fact, ctx);
  const who = name || "—";
  const week = weekFromPayload(payload, fact.day_index, scheme);

  switch (fact.kind) {
    case "empty_post":
    case "post_held":
      return slotLine(payload, fact.day_index, scheme);
    case "assigned_on_closure":
      return `${weekdayFr(payload.weekday, fact.day_index)} · ${serviceFr(payload.service_id)} : shift sur fermeture`;
    case "rest_between_days": {
      if (fact.polarity === "hit" && asNumber(payload.required_minutes) !== null && asNumber(payload.end_minutes) === null) {
        return `${who} : min 11 h`;
      }
      const jourA = weekdayFr(undefined, fact.day_index);
      const jourB = weekdayFr(undefined, asInt(payload.day_index_b));
      return `${who} : moins de 11 h (${jourA} ${clock(payload.end_minutes)} → ${jourB} ${clock(payload.start_minutes_b)})`;
    }
    case "weekly_rest_days": {
      const rest = asNumber(payload.rest_days);
      if (rest !== null) {
        return `${who} : ${rest} / 2 j. de repos (sem. ${week})`;
      }
      const tightest = asNumber(payload.tightest);
      const a = asNumber(payload.rest_days_week_0);
      const b = asNumber(payload.rest_days_week_7);
      if (tightest !== null) {
        return `${who} : ${tightest} / 2 j. de repos`;
      }
      if (a !== null && b !== null) {
        return `${who} : ${a} / ${b} j. de repos`;
      }
      return `${who} : repos hebdo`;
    }
    case "max_coupure": {
      const day = weekdayFr(payload.weekday, fact.day_index);
      if (asNumber(payload.gap_minutes) !== null) {
        return `${who} : coupure > 5h (${day})`;
      }
      const gapHours = asNumber(payload.max_gap_hours);
      if (gapHours !== null) {
        return `${who} : max ${hoursLabel(gapHours)}`;
      }
      return `${who} : coupure`;
    }
    case "max_daily_hours": {
      const hours = asNumber(payload.hours) ?? asNumber(payload.max_hours);
      const limit = asNumber(payload.limit_hours);
      const day = weekdayFr(payload.weekday, fact.day_index);
      if (hours !== null && limit !== null) {
        return `${who} : ${hoursLabel(hours)} / max ${hoursLabel(limit)} (${day})`;
      }
      if (hours !== null) {
        return `${who} : max ${hoursLabel(hours)}`;
      }
      return `${who} : amplitude journalière`;
    }
    case "max_weekly_hours": {
      const hours = asNumber(payload.hours);
      if (hours !== null) {
        return `${who} : ${hoursLabel(hours)} / max 48h (sem. ${week})`;
      }
      const a = asNumber(payload.hours_week_0);
      const b = asNumber(payload.hours_week_7);
      if (a !== null && b !== null) {
        return `${who} : ${hoursLabel(a)} / ${hoursLabel(b)}`;
      }
      return `${who} : heures hebdo`;
    }
    case "unavailability": {
      if (asNumber(payload.slot_count) !== null && fact.polarity === "hit") {
        return `${who} : ${asNumber(payload.slot_count)} créneaux`;
      }
      return `${who} : posé sur indispo (${weekdayFr(payload.weekday, fact.day_index)} ${serviceFr(payload.service_id)})`;
    }
    case "contract_hours": {
      const hours = asNumber(payload.hours);
      const contracted = asNumber(payload.contracted);
      if (hours !== null && contracted !== null) {
        return `${who} : ${hoursLabel(hours)} / ${hoursLabel(contracted)} contrat (sem. ${week})`;
      }
      const a = asNumber(payload.hours_week_0);
      const b = asNumber(payload.hours_week_7);
      if (a !== null && b !== null && contracted !== null) {
        return `${who} : ${hoursLabel(a)} · ${hoursLabel(b)} / ${hoursLabel(contracted)}`;
      }
      return `${who} : heures de contrat`;
    }
    case "consecutive_rest_days": {
      if (fact.polarity === "hit") {
        const left = asString(payload.left_weekday);
        const right = asString(payload.right_weekday);
        if (left && right) {
          return `${who} : tenu · ${WEEKDAY_FR[left] ?? left}–${WEEKDAY_FR[right] ?? right}`;
        }
        return `${who} : tenu`;
      }
      return `${who} : pas deux repos consécutifs (sem. ${week})`;
    }
    case "weekend_rest_day": {
      if (fact.polarity === "hit") {
        const off = asString(payload.off);
        const short = off === "sunday" ? "dim" : off === "saturday" ? "sam" : off;
        return short ? `${who} : ${short}` : `${who} : tenu`;
      }
      return `${who} : pas de repos samedi ou dimanche (sem. ${week})`;
    }
    case "weekend_every_two_weeks":
      return `${who} : pas exactement un week-end off / 14 j.`;
    case "weekend_even_weeks":
      return `${who} : week-end pair non tenu`;
    case "weekend_odd_weeks":
      return `${who} : week-end impair non tenu`;
    case "max_mornings":
    case "max_middays":
    case "max_evenings": {
      const count = asNumber(payload.count);
      const limit = asNumber(payload.limit);
      const service = serviceFr(payload.service_id ?? (fact.kind === "max_mornings" ? "morning" : fact.kind === "max_middays" ? "midday" : "evening"));
      const jours = dayList(payload);
      if (count !== null && limit !== null) {
        const days = jours ? `${jours} · sem. ${week}` : `sem. ${week}`;
        return `${who} : ${count} ${service} / max ${limit} (${days})`;
      }
      const a = asNumber(payload.count_week_0);
      const b = asNumber(payload.count_week_7);
      if (limit !== null && a !== null && b !== null) {
        return `${who} : max ${limit} · ${a} / ${b} posés`;
      }
      return `${who} : ${factTitle(fact.kind)}`;
    }
    case "max_coupures": {
      const count = asNumber(payload.count);
      const limit = asNumber(payload.limit);
      if (count !== null && limit !== null) {
        return `${who} : ${count} coupures / max ${limit} (sem. ${week})`;
      }
      const a = asNumber(payload.count_week_0);
      const b = asNumber(payload.count_week_7);
      if (limit !== null && a !== null && b !== null) {
        return `${who} : max ${limit} · ${a} / ${b} posés`;
      }
      return `${who} : max coupures`;
    }
    case "role_gap": {
      const level = asNumber(payload.employee_level);
      const post = asNumber(payload.post_level);
      if (fact.polarity === "hit") {
        return post === null ? `${who} : niveau exact` : `${who} : niveau ${post} exact`;
      }
      if (level !== null && post !== null) {
        return `${who} : niveau ${level} sur poste ${post}`;
      }
      return `${who} : adéquation rôle`;
    }
    default:
      return null;
  }
}

export function formatFactLine(fact: ScoreFact, ctx: FactFormatCtx = {}): string {
  if (payloadEmpty(fact.payload) && fact.message) {
    return fact.message;
  }
  if (!knownKind(fact.kind)) {
    return payloadEmpty(fact.payload) ? fact.kind : `${fact.kind} ${rawPayload(fact.payload)}`;
  }
  return formatKnownLine(fact, ctx) ?? (payloadEmpty(fact.payload) ? factTitle(fact.kind) : rawPayload(fact.payload));
}

export function formatRecapMeasure(cell: StatusCell): string {
  const payload = cell.payload;
  switch (cell.kind) {
    case "rest_between_days": {
      if (cell.ok) {
        return "min 11h";
      }
      const jourA = weekdayFr(undefined, asInt(payload.day_index) ?? asInt(payload.day_index_a));
      const jourB = weekdayFr(undefined, asInt(payload.day_index_b));
      if (asNumber(payload.end_minutes) !== null) {
        return `${jourA} ${clock(payload.end_minutes)} → ${jourB} ${clock(payload.start_minutes_b)}`;
      }
      return "moins de 11 h";
    }
    case "weekly_rest_days": {
      const tightest = asNumber(payload.tightest) ?? asNumber(payload.rest_days);
      const required = asNumber(payload.required) ?? 2;
      if (tightest === null) {
        return "";
      }
      return `${tightest} / ${required} j.`;
    }
    case "max_coupure": {
      const maxGap = asNumber(payload.max_gap_hours);
      const gapMin = asNumber(payload.gap_minutes);
      const hours = maxGap ?? (gapMin !== null ? gapMin / 60 : null);
      if (hours === null) {
        return "";
      }
      return `max ${hoursLabel(hours)}`;
    }
    case "max_daily_hours": {
      const hours = asNumber(payload.max_hours) ?? asNumber(payload.hours);
      if (hours === null) {
        return "";
      }
      return `max ${hoursLabel(hours)}`;
    }
    case "max_weekly_hours": {
      const a = asNumber(payload.hours_week_0);
      const b = asNumber(payload.hours_week_7);
      if (a === null || b === null) {
        return "";
      }
      return `${hoursLabel(a)} / ${hoursLabel(b)}`;
    }
    case "contract_hours": {
      const a = asNumber(payload.hours_week_0);
      const b = asNumber(payload.hours_week_7);
      const contracted = asNumber(payload.contracted);
      if (a === null || b === null || contracted === null) {
        const hours = asNumber(payload.hours);
        if (hours !== null && contracted !== null) {
          return `${hoursLabel(hours)} / ${hoursLabel(contracted)}`;
        }
        return "";
      }
      return `${hoursLabel(a)} · ${hoursLabel(b)} / ${hoursLabel(contracted)}`;
    }
    case "unavailability": {
      const slots = asNumber(payload.slot_count);
      if (cell.ok) {
        return slots === null ? "" : `${slots} créneaux`;
      }
      const weekday = asString(payload.weekday);
      const service = asString(payload.service_id);
      if (weekday || service) {
        return `${weekdayFr(weekday)} ${serviceFr(service)}`;
      }
      return "";
    }
    case "consecutive_rest_days": {
      if (cell.ok) {
        const left = asString(payload.left_weekday);
        const right = asString(payload.right_weekday);
        if (left && right) {
          return `${WEEKDAY_FR[left] ?? left}–${WEEKDAY_FR[right] ?? right}`;
        }
        return "";
      }
      return `sem. ${weekLabel(asInt(payload.week_start), "ab")}`;
    }
    case "weekend_rest_day": {
      if (cell.ok) {
        const off = asString(payload.off);
        const short = off === "sunday" ? "dim" : off === "saturday" ? "sam" : off ?? "sam";
        return short;
      }
      return `sem. ${weekLabel(asInt(payload.week_start), "ab")}`;
    }
    case "weekend_every_two_weeks":
    case "weekend_even_weeks":
    case "weekend_odd_weeks": {
      const key =
        asString(payload.weekend) ?? (cell.kind === "weekend_even_weeks" ? "even" : cell.kind === "weekend_odd_weeks" ? "odd" : "every_two");
      return WEEKEND_FR[key] ?? key;
    }
    case "max_mornings":
    case "max_middays":
    case "max_evenings":
    case "max_coupures": {
      const limit = asNumber(payload.limit);
      const a = asNumber(payload.count_week_0) ?? asNumber(payload.count);
      const b = asNumber(payload.count_week_7) ?? a;
      if (limit === null || a === null || b === null) {
        return "";
      }
      return `max ${limit} · ${a} / ${b} posés`;
    }
    default:
      if (!knownKind(cell.kind)) {
        return payloadEmpty(payload) ? cell.kind : `${cell.kind} ${rawPayload(payload)}`;
      }
      return payloadEmpty(payload) ? "" : rawPayload(payload);
  }
}

export function formatRecapCell(cell: StatusCell): string {
  const measure = formatRecapMeasure(cell);
  if (cell.ok) {
    return measure ? `OK · ${measure}` : "OK";
  }
  return measure || "Non tenu";
}

export function composeScoreResumes(
  stats: PlanningStats | undefined,
  legalRows: LegalRow[] | undefined,
  wishRows: WishRow[] | undefined,
  facts: ScoreFact[],
): Record<string, string> {
  const empty = facts.filter((fact) => fact.kind === "empty_post" && fact.polarity === "miss").length;
  const heldPosts = facts.filter((fact) => fact.kind === "post_held" && fact.polarity === "hit").length;
  const emptyCount = empty || stats?.empty || 0;
  const resumes: Record<string, string> = {};
  if (heldPosts + emptyCount > 0) {
    resumes.couverture = `${heldPosts} / ${heldPosts + emptyCount} postes tenus`;
  }

  const legalCells = (legalRows ?? []).flatMap((row) => Object.values(row.cells).filter((cell): cell is StatusCell => Boolean(cell)));
  if (legalCells.length > 0) {
    const ok = legalCells.filter((cell) => cell.ok).length;
    resumes.legal = `${ok} / ${legalCells.length} cellules légales`;
  }

  const occupation: string[] = [];
  if (stats) {
    occupation.push(`${hoursLabel(stats.hours.assigned)} occupées / ${hoursLabel(stats.hours.contracted)}`);
  }
  const indispoCells = (wishRows ?? [])
    .map((row) => row.cells.indispo)
    .filter((cell): cell is StatusCell => cell !== undefined && cell !== null);
  if (indispoCells.length > 0) {
    const ok = indispoCells.filter((cell) => cell.ok).length;
    occupation.push(`${ok}/${indispoCells.length} indispos respectées`);
  }
  if (occupation.length > 0) {
    resumes.contrat = occupation.join("\n");
  }

  if (stats) {
    resumes.wellbeing = `${stats.wellbeing.held} / ${stats.wellbeing.total} souhaits tenus`;
    resumes.roles = `${stats.assignments} affectés · ${stats.below_role} poste en sous-rôle / ${stats.assignments}`;
  }
  return resumes;
}

export function nameMap(people: { id: string; name: string }[]): Map<string, string> {
  return new Map(people.map((person) => [person.id, person.name]));
}
