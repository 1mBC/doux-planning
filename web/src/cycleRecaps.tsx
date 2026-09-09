import { useState, type CSSProperties, type KeyboardEvent } from "react";
import type { LegalCol, PublishedCycle } from "./generate";
import type { CycleScore, Employee, LegalRow, PlanningStats, ScoreFact, WishRow } from "./types";
import { formatCycleNote, type WeekLabelScheme } from "./format";
import {
  composeScoreResumes,
  evaluateMisses,
  factSeverityLabel,
  factTitle,
  factsForAxis,
  formatFactLine,
  formatRecapCell,
  nameMap,
} from "./scoreFacts";

const NOTE_LABELS: { key: keyof CycleScore["notes"]; label: string; axis: string }[] = [
  { key: "couverture", label: "Couverture /10", axis: "couverture" },
  { key: "legal", label: "Légal /10", axis: "legal" },
  { key: "contrat", label: "Occupation /10", axis: "contrat" },
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
  const names = nameMap(employees);
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
            <b style={noteDigitColor(item.note)}>{item.value}</b>
            <ScoreGauge note={item.note} />
            <span>{item.label}</span>
            {!item.global && item.resume ? <p className="score-resume">{item.resume}</p> : null}
          </div>
        ))}
      </div>
      {openAxis ? (
        <ol className="score-fact-list" aria-label="Détail des notes">
          {listed.length === 0 ? (
            <li className="score-fact-empty">Aucun fait sur cet axe.</li>
          ) : (
            listed.map((fact, index) => (
              <li
                key={`${fact.polarity}-${fact.kind}-${fact.employee_id}-${fact.day_index}-${index}`}
                className={fact.polarity === "miss" ? "score-fact-miss" : "score-fact-hit"}
              >
                <span className="sev">{factSeverityLabel(fact)}</span>
                <span className="code">{factTitle(fact.kind)}</span>
                <span className="msg">{formatFactLine(fact, { names, weekScheme })}</span>
              </li>
            ))
          )}
        </ol>
      ) : null}
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
  const misses = evaluateMisses(facts);
  const names = nameMap(employees);
  return (
    <section>
      <h2>Alertes</h2>
      <p className="sub">
        {misses.length} alerte{misses.length > 1 ? "s" : ""} — manques d’évaluation.
      </p>
      <ol className="warnings">
        {misses.map((fact, index) => (
          <li
            key={`${fact.kind}-${fact.employee_id}-${fact.day_index}-${index}`}
            className={fact.severity ? `warn-${fact.severity}` : undefined}
          >
            <span className="sev">{factSeverityLabel(fact)}</span>
            <span className="code">{factTitle(fact.kind)}</span>
            <span className="msg">{formatFactLine(fact, { names, weekScheme })}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function LegalRecap({ cols, rows }: { cols: LegalCol[]; rows: PublishedCycle["legal_rows"] }) {
  return (
    <section>
      <h2>Règles légales</h2>
      <p className="sub">Plafonds interdits, mesurés sur le cycle.</p>
      <table className="matrix">
        <thead>
          <tr>
            <th>Personne</th>
            {cols.map((col) => (
              <th key={col.id}>{col.label_fr}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.employee_id}>
              <td>{row.name}</td>
              {cols.map((col) => {
                const cell = row.cells[col.id];
                return (
                  <td key={col.id} className={cell && !cell.ok ? "cell-bad" : undefined}>
                    {cell ? formatRecapCell(cell) : ""}
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

export function WishRecap({ cycle }: { cycle: PublishedCycle }) {
  return (
    <section>
      <h2>Souhaits bien-être</h2>
      <p className="sub">Colonnes du cycle. Case vide = non émis.</p>
      <table className="matrix">
        <thead>
          <tr>
            <th>Personne</th>
            {cycle.wish_cols.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {cycle.wish_rows.map((row) => (
            <tr key={row.employee_id}>
              <td>{row.name}</td>
              {cycle.wish_cols.map((col) => {
                const cell = row.cells[col.key];
                return (
                  <td key={col.key} className={cell && !cell.ok ? "cell-bad" : undefined}>
                    {cell ? formatRecapCell(cell) : ""}
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
