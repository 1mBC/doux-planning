import { useState, type CSSProperties, type KeyboardEvent } from "react";
import type { LegalCol } from "./generate";
import type { CycleScore, Employee, LegalRow, PlanningStats, ScoreFact, StatusCell, WishCol, WishRow } from "./types";
import { formatCycleNote, type WeekLabelScheme } from "./format";
import {
  composeScoreResumes,
  evaluateMisses,
  factCategory,
  factSubcategory,
  factsForAxis,
  formatFactLine,
  formatRecapMeasure,
  nameMap,
  sortFactsForTable,
} from "./scoreFacts";

const NOTE_LABELS: { key: keyof CycleScore["notes"]; label: string; axis: string }[] = [
  { key: "couverture", label: "Couverture /10", axis: "couverture" },
  { key: "legal", label: "Légal /10", axis: "legal" },
  { key: "contrat", label: "Contrat /10", axis: "contrat" },
  { key: "wellbeing", label: "Bien-être /10", axis: "wellbeing" },
  { key: "roles", label: "Rôles /10", axis: "roles" },
];

function noteHue(note: number): number {
  return 12 * note;
}

function noteTint(note: number | null, global: boolean): CSSProperties | undefined {
  if (note === null || !Number.isFinite(note)) {
    return undefined;
  }
  const hue = noteHue(note);
  if (global) {
    return {
      background: `hsl(${hue}, 82%, 86%)`,
      borderColor: `hsl(${hue}, 60%, 38%)`,
    };
  }
  return {
    background: `hsl(${hue}, 70%, 92%)`,
    borderColor: `hsl(${hue}, 55%, 58%)`,
  };
}

function noteDigitColor(note: number | null): CSSProperties | undefined {
  if (note === null || !Number.isFinite(note)) {
    return undefined;
  }
  return { color: `hsl(${noteHue(note)}, 70%, 28%)` };
}

function ScoreGauge({ note }: { note: number | null }) {
  if (note === null || !Number.isFinite(note)) {
    return <div className="score-gauge" aria-hidden="true" />;
  }
  const hue = noteHue(note);
  return (
    <div className="score-gauge" aria-hidden="true">
      <div
        className="score-gauge-fill"
        style={{
          width: `${Number((note * 10).toFixed(1))}%`,
          background: `hsl(${hue}, 70%, 45%)`,
        }}
      />
    </div>
  );
}

function RecapCellView({ cell }: { cell: StatusCell | null | undefined }) {
  if (!cell) {
    return null;
  }
  const measure = formatRecapMeasure(cell);
  const mark = cell.ok ? "✅" : "⚠️";
  return (
    <>
      {mark}
      {measure ? ` ${measure}` : ""}
    </>
  );
}

export function FactTable({
  facts,
  employees = [],
  weekScheme = "ab",
  emptyLabel = "Aucun fait sur cet axe.",
}: {
  facts: ScoreFact[];
  employees?: Pick<Employee, "id" | "name">[];
  weekScheme?: WeekLabelScheme;
  emptyLabel?: string;
}) {
  const names = nameMap(employees);
  const rows = sortFactsForTable(facts);
  return (
    <table className="matrix fact-table">
      <thead>
        <tr>
          <th>Catégorie</th>
          <th>Sous-catégorie</th>
          <th>Statut</th>
          <th>Détail</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 ? (
          <tr>
            <td colSpan={4} className="score-fact-empty">
              {emptyLabel}
            </td>
          </tr>
        ) : (
          rows.map((fact, index) => (
            <tr
              key={`${fact.polarity}-${fact.kind}-${fact.employee_id}-${fact.day_index}-${index}`}
              className={fact.polarity === "miss" ? "score-fact-miss" : "score-fact-hit"}
            >
              <td>{factCategory(fact.axis)}</td>
              <td>{factSubcategory(fact.kind)}</td>
              <td className="fact-status">{fact.polarity === "miss" ? "⚠️" : "✅"}</td>
              <td>{formatFactLine(fact, { names, weekScheme })}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}

export function CycleScoreNotes({
  score,
  facts = [],
  stats,
  legalRows,
  wishRows,
  employees = [],
  weekScheme = "ab",
}: {
  score: CycleScore | undefined;
  facts?: ScoreFact[];
  stats?: PlanningStats;
  legalRows?: LegalRow[];
  wishRows?: WishRow[];
  employees?: Pick<Employee, "id" | "name">[];
  weekScheme?: WeekLabelScheme;
}) {
  const [openAxis, setOpenAxis] = useState<string | null>(null);
  if (!score) {
    return null;
  }
  const resumes = composeScoreResumes(stats, legalRows, wishRows, facts);
  const items = [
    {
      axis: "global",
      value: formatCycleNote(score.global),
      label: "Globale /10",
      note: score.global,
      resume: null as string | null,
      global: true,
    },
    ...NOTE_LABELS.map((item) => ({
      axis: item.axis,
      value: formatCycleNote(score.notes[item.key]),
      label: item.label,
      note: score.notes[item.key],
      resume: resumes[item.key] ?? null,
      global: false,
    })),
  ];
  const listed = openAxis ? factsForAxis(facts, openAxis) : [];

  function toggle(axis: string) {
    setOpenAxis((current) => (current === axis ? null : axis));
  }

  function onKey(event: KeyboardEvent<HTMLDivElement>, axis: string) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggle(axis);
    }
  }

  return (
    <div className="score-notes">
      <div className="stats score-stats">
        {items.map((item) => (
          <div
            key={item.label}
            className={[item.global ? "stat score-global" : "stat", "score-pill", openAxis === item.axis ? "is-open" : ""]
              .filter(Boolean)
              .join(" ")}
            style={noteTint(item.note, item.global)}
            role="button"
            tabIndex={0}
            aria-pressed={openAxis === item.axis}
            aria-expanded={openAxis === item.axis}
            onClick={() => toggle(item.axis)}
            onKeyDown={(event) => onKey(event, item.axis)}
          >
            <span>{item.label}</span>
            <div className="score-note-row">
              <b style={noteDigitColor(item.note)}>{item.value}</b>
              <ScoreGauge note={item.note} />
            </div>
            {!item.global && item.resume ? <p className="score-resume">{item.resume}</p> : null}
          </div>
        ))}
      </div>
      {openAxis ? <FactTable facts={listed} employees={employees} weekScheme={weekScheme} /> : null}
    </div>
  );
}

export function AlertsList({
  facts,
  employees = [],
  weekScheme = "ab",
}: {
  facts: ScoreFact[];
  employees?: Pick<Employee, "id" | "name">[];
  weekScheme?: WeekLabelScheme;
}) {
  return (
    <section>
      <h2>Alertes</h2>
      <FactTable facts={evaluateMisses(facts)} employees={employees} weekScheme={weekScheme} emptyLabel="Aucune alerte." />
    </section>
  );
}

function recapPeople(legalRows: LegalRow[], wishRows: WishRow[]): { employee_id: string; name: string }[] {
  const people: { employee_id: string; name: string }[] = [];
  const seen = new Set<string>();
  for (const row of legalRows) {
    people.push({ employee_id: row.employee_id, name: row.name });
    seen.add(row.employee_id);
  }
  for (const row of wishRows) {
    if (!seen.has(row.employee_id)) {
      people.push({ employee_id: row.employee_id, name: row.name });
      seen.add(row.employee_id);
    }
  }
  return people;
}

export function LegalAndContractRecap({
  legalCols,
  legalRows,
  wishCols,
  wishRows,
}: {
  legalCols: LegalCol[];
  legalRows: LegalRow[];
  wishCols: WishCol[];
  wishRows: WishRow[];
}) {
  const extra = wishCols.filter((col) => col.key === "contrat" || col.key === "indispo");
  const legalById = new Map(legalRows.map((row) => [row.employee_id, row]));
  const wishById = new Map(wishRows.map((row) => [row.employee_id, row]));
  const people = recapPeople(legalRows, wishRows);
  return (
    <section>
      <h2>Légal & Contrat</h2>
      <table className="matrix">
        <thead>
          <tr>
            <th>Personne</th>
            {legalCols.map((col) => (
              <th key={col.id}>{col.label_fr}</th>
            ))}
            {extra.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {people.map((person) => {
            const legal = legalById.get(person.employee_id);
            const wish = wishById.get(person.employee_id);
            return (
              <tr key={person.employee_id}>
                <td>{person.name}</td>
                {legalCols.map((col) => {
                  const cell = legal?.cells[col.id];
                  return (
                    <td key={col.id} className={cell && !cell.ok ? "cell-bad" : undefined}>
                      <RecapCellView cell={cell} />
                    </td>
                  );
                })}
                {extra.map((col) => {
                  const cell = wish?.cells[col.key];
                  return (
                    <td key={col.key} className={cell && !cell.ok ? "cell-bad" : undefined}>
                      <RecapCellView cell={cell} />
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

export function WellbeingRecap({ wishCols, wishRows }: { wishCols: WishCol[]; wishRows: WishRow[] }) {
  const cols = wishCols.filter((col) => col.key !== "contrat" && col.key !== "indispo");
  if (cols.length === 0) {
    return null;
  }
  return (
    <section>
      <h2>Bien-être</h2>
      <table className="matrix">
        <thead>
          <tr>
            <th>Personne</th>
            {cols.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {wishRows.map((row) => (
            <tr key={row.employee_id}>
              <td>{row.name}</td>
              {cols.map((col) => {
                const cell = row.cells[col.key];
                return (
                  <td key={col.key} className={cell && !cell.ok ? "cell-bad" : undefined}>
                    <RecapCellView cell={cell} />
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
