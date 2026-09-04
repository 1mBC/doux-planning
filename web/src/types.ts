/** Types = GET /v1/examples/saint-cloud. See contracts/http/v1-examples.md. */

export type LegalRule = {
  id: string;
  label_fr: string;
  severity: string;
};

export type LegalContext = {
  id: string;
  kind: string;
  label: string;
  rules: LegalRule[];
};

export type EmployeeRole = {
  name: string;
  level: number;
  team: string;
};

export type Employee = {
  id: string;
  name: string;
  role: EmployeeRole;
  team: string;
};

export type Restaurant = {
  id: string;
  name: string;
  team: string;
  hours: Record<string, unknown>;
  employees: Employee[];
};

export type Assignment = {
  employee_id: string;
  day_index: number;
  weekday: string;
  service_id: "midday" | "evening";
  team: string;
  start_minutes: number;
  end_minutes: number;
  post_level: number;
  duration_hours: number;
};

export type WarningItem = {
  severity: "interdit" | "couverture" | "souhait";
  code: string;
  message: string;
  employee_id: string | null;
  day_index: number | null;
};

export type PlanningHoursStats = {
  assigned: number;
  contracted: number;
  percent: number;
};

export type PlanningWellbeingStats = {
  held: number;
  total: number;
};

export type PlanningStats = {
  assignments: number;
  empty: number;
  interdit: number;
  below_role: number;
  hours: PlanningHoursStats;
  wellbeing: PlanningWellbeingStats;
};

export type StatusCell = {
  ok: boolean;
  text: string;
};

export type LegalRow = {
  name: string;
  employee_id: string;
  cells: Record<string, StatusCell | undefined>;
};

export type WishCol = {
  key: string;
  label: string;
};

export type WishRow = {
  name: string;
  employee_id: string;
  cells: Record<string, StatusCell | null>;
};

export type Planning = {
  search_effort: string;
  calendars: number;
  seconds: number;
  assignments: Assignment[];
  warnings: WarningItem[];
  stats: PlanningStats;
  legal_rows: LegalRow[];
  wish_cols: WishCol[];
  wish_rows: WishRow[];
};

export type ExamplePayload = {
  example: string;
  legal: LegalContext;
  restaurant: Restaurant;
  planning: Planning;
};

export type Gesture = "retune" | "replace" | "swap" | "fill";

export type ShiftIdentity = {
  employee_id: string;
  day_index: number;
  weekday: string;
  service_id: "midday" | "evening";
  team: string;
  start_minutes: number;
  end_minutes: number;
  post_level: number;
};

export type FillSlot = {
  employee_id: string;
  day_index: number;
  weekday: string;
  service_id: "midday" | "evening";
  team: string;
};

export const SCORE_FIELDS = [
  "empty",
  "interdit",
  "hours_miss",
  "souhait",
  "below_role",
  "overqualification",
] as const;

export type ScoreField = (typeof SCORE_FIELDS)[number];

export type Score = Record<ScoreField, number>;

export type ContractKind = "closer" | "farther" | "excess";

export type RoleFitKind = "better" | "worse";

export type ContractImpact = {
  employee_id: string;
  week_start: 0 | 7;
  current_hours: number;
  trial_hours: number;
  contracted: number;
  kind: ContractKind;
};

export type RoleFit = {
  current_gap: number;
  trial_gap: number;
  kind: RoleFitKind;
};

export type Impact = {
  new_interdits: WarningItem[];
  broken_wishes: WarningItem[];
  contract: ContractImpact[];
  coverage_added: WarningItem[];
  coverage_removed: WarningItem[];
  role_fit: RoleFit[];
};

export type PreviewProposal = {
  rank: number;
  gesture: Gesture;
  start_minutes: number | null;
  end_minutes: number | null;
  employee_id: string | null;
  partner: Assignment | null;
  impact: Impact;
  current_score: Score;
  trial_score: Score;
};

export type HistoryCran = {
  index: number;
  gesture: Gesture;
  shift: Assignment | null;
  slot: FillSlot | null;
  employee_id: string | null;
  start_minutes: number | null;
  end_minutes: number | null;
  partner: Assignment | null;
  impact: Impact;
};

export type HistoryEntry = {
  index: number;
  gesture: Gesture;
  shift: ShiftIdentity | null;
  slot: FillSlot | null;
  proposal: PreviewProposal | null;
};

export type SandboxMeta = {
  target: string;
  history_length: number;
};

export type SandboxRestaurant = {
  id: string;
  name: string;
  employees: Employee[];
};

export type SandboxPlanning = {
  assignments: Assignment[];
  warnings: WarningItem[];
};

export type SandboxState = {
  sandbox: SandboxMeta;
  restaurant: SandboxRestaurant;
  planning: SandboxPlanning;
  score: Score;
  history: HistoryCran[];
};

export function toShiftIdentity(shift: Assignment): ShiftIdentity {
  return {
    employee_id: shift.employee_id,
    day_index: shift.day_index,
    weekday: shift.weekday,
    service_id: shift.service_id,
    team: shift.team,
    start_minutes: shift.start_minutes,
    end_minutes: shift.end_minutes,
    post_level: shift.post_level,
  };
}
