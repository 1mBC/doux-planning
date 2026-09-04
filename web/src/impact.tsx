import { dayThenClock, formatClock, formatContractPercents, hoursDeltaMinutes, SERVICE_ROWS } from "./format";
import type { ContractImpact, Employee, FillSlot, Gesture, Impact, PreviewProposal, RoleFit, ShiftIdentity } from "./types";

export function employeeName(employees: Employee[], id: string | null): string {
  if (!id) {
    return "—";
  }
  return employees.find((person) => person.id === id)?.name ?? id;
}

function weekLabel(weekStart: 0 | 7): string {
  return weekStart === 0 ? "sem. A" : "sem. B";
}

function contractPhrase(row: ContractImpact): string {
  const minutes = hoursDeltaMinutes(row.current_hours, row.trial_hours);
  if (row.kind === "closer") {
    return `gagné ${minutes} min`;
  }
  if (row.kind === "farther") {
    return `perdu ${Math.abs(minutes)} min`;
  }
  return `excès ${Math.abs(minutes)} min`;
}

function contractLine(row: ContractImpact, employees: Employee[]): string {
  const phrase = `${employeeName(employees, row.employee_id)} · ${weekLabel(row.week_start)} · ${contractPhrase(row)}`;
  const percents = formatContractPercents(row.current_hours, row.trial_hours, row.contracted);
  return percents ? `${phrase} ${percents}` : phrase;
}

function changedContract(impact: Impact): ContractImpact[] {
  return impact.contract.filter((row) => row.current_hours !== row.trial_hours);
}

function roleFitLine(row: RoleFit): string {
  if (row.kind === "better") {
    return `poste plus proche du niveau (−${row.current_gap - row.trial_gap})`;
  }
  return `surqualification +${row.trial_gap - row.current_gap}`;
}

function RoleFitLines({ rows }: { rows: RoleFit[] }) {
  return (
    <>
      {rows.map((row, index) => (
        <li key={`role-${row.kind}-${index}`} className={row.kind === "better" ? "impact-green" : "impact-red"}>
          {roleFitLine(row)}
        </li>
      ))}
    </>
  );
}

export function HoursImpact({ impact, employees }: { impact: Impact; employees: Employee[] }) {
  const contracts = changedContract(impact);
  if (
    impact.new_interdits.length === 0 &&
    impact.coverage_added.length === 0 &&
    contracts.length === 0 &&
    impact.role_fit.length === 0
  ) {
    return <p className="sub">Aucun impact listé.</p>;
  }
  return (
    <ul className="impact-list">
      {impact.new_interdits.map((warning, index) => (
        <li key={`interdit-${warning.code}-${index}`} className="impact-orange">
          {warning.message}
        </li>
      ))}
      {impact.coverage_added.map((warning, index) => (
        <li key={`couverture-${warning.code}-${index}`} className="impact-orange">
          {warning.message}
        </li>
      ))}
      {contracts.map((row) => (
        <li
          key={`${row.employee_id}-${row.week_start}`}
          className={row.kind === "closer" ? "impact-green" : "impact-red"}
        >
          {contractLine(row, employees)}
        </li>
      ))}
      <RoleFitLines rows={impact.role_fit} />
    </ul>
  );
}

export function SwapReplaceImpact({ impact, employees }: { impact: Impact; employees: Employee[] }) {
  const contracts = changedContract(impact);
  if (
    impact.new_interdits.length === 0 &&
    impact.broken_wishes.length === 0 &&
    contracts.length === 0 &&
    impact.role_fit.length === 0
  ) {
    return <p className="sub">Aucun impact listé.</p>;
  }
  return (
    <ul className="impact-list">
      {impact.new_interdits.map((warning, index) => (
        <li key={`interdit-${warning.code}-${index}`} className="impact-red">
          {warning.message}
        </li>
      ))}
      {impact.broken_wishes.map((warning, index) => (
        <li key={`souhait-${warning.code}-${index}`} className="impact-orange">
          {warning.message}
        </li>
      ))}
      {contracts.map((row) => (
        <li
          key={`${row.employee_id}-${row.week_start}`}
          className={row.kind === "closer" ? "impact-green" : "impact-yellow"}
        >
          {contractLine(row, employees)}
        </li>
      ))}
      <RoleFitLines rows={impact.role_fit} />
    </ul>
  );
}

export function slotSummary(shift: ShiftIdentity, employees: Employee[]): string {
  const service = SERVICE_ROWS.find((row) => row.id === shift.service_id)?.label ?? shift.service_id;
  return `${employeeName(employees, shift.employee_id)} · ${dayThenClock(shift.day_index, shift.start_minutes, shift.end_minutes)} · ${service}`;
}

export function cranHow(
  gesture: Gesture,
  shift: ShiftIdentity,
  proposal: PreviewProposal,
  employees: Employee[],
): string {
  if (gesture === "retune" && proposal.start_minutes !== null && proposal.end_minutes !== null) {
    return `Horaires ${formatClock(shift.start_minutes)} – ${formatClock(shift.end_minutes)} → ${formatClock(proposal.start_minutes)} – ${formatClock(proposal.end_minutes)}`;
  }
  if (gesture === "replace") {
    return `Personne ${employeeName(employees, shift.employee_id)} → ${employeeName(employees, proposal.employee_id)}`;
  }
  if (proposal.partner) {
    return `Échangé avec ${employeeName(employees, proposal.partner.employee_id)} · ${dayThenClock(proposal.partner.day_index, proposal.partner.start_minutes, proposal.partner.end_minutes)}`;
  }
  return "Échange";
}

export function fillSlotSummary(slot: FillSlot, proposal: PreviewProposal, employees: Employee[]): string {
  const service = SERVICE_ROWS.find((row) => row.id === slot.service_id)?.label ?? slot.service_id;
  if (proposal.start_minutes !== null && proposal.end_minutes !== null) {
    return `${employeeName(employees, slot.employee_id)} · ${dayThenClock(slot.day_index, proposal.start_minutes, proposal.end_minutes)} · ${service}`;
  }
  return `${employeeName(employees, slot.employee_id)} · ${service}`;
}

export function fillHow(slot: FillSlot, proposal: PreviewProposal, employees: Employee[]): string {
  const hours =
    proposal.start_minutes !== null && proposal.end_minutes !== null
      ? `${formatClock(proposal.start_minutes)} – ${formatClock(proposal.end_minutes)}`
      : null;
  if (proposal.employee_id && proposal.employee_id !== slot.employee_id) {
    const line = `Personne ${employeeName(employees, slot.employee_id)} → ${employeeName(employees, proposal.employee_id)}`;
    return hours ? `${line} · ${hours}` : line;
  }
  return hours ? `Horaires ${hours}` : "Créneau posé";
}

export function GestureImpact({
  gesture,
  impact,
  employees,
}: {
  gesture: Gesture;
  impact: Impact;
  employees: Employee[];
}) {
  if (gesture === "retune") {
    return <HoursImpact impact={impact} employees={employees} />;
  }
  return <SwapReplaceImpact impact={impact} employees={employees} />;
}
