import type { CSSProperties } from "react";
import type { LegalCol, PublishedCycle } from "./generate";
import type { CycleScore } from "./types";
import { formatCycleNote } from "./format";

const NOTE_LABELS: { key: keyof CycleScore["notes"]; label: string }[] = [
  { key: "couverture", label: "Couverture /10" },
  { key: "legal", label: "Légal /10" },
  { key: "contrat", label: "Occupation /10" },
  { key: "wellbeing", label: "Bien-être /10" },
  { key: "roles", label: "Rôles /10" },
];

function noteTint(note: number | null): CSSProperties | undefined {
  if (note === null || !Number.isFinite(note)) {
    return undefined;
  }
  const hue = 12 * note;
  return {
    background: `hsl(${hue}, 70%, 92%)`,
    borderColor: `hsl(${hue}, 55%, 58%)`,
  };
}

function noteDigitColor(note: number | null): CSSProperties | undefined {
  if (note === null || !Number.isFinite(note)) {
    return undefined;
  }
  return { color: `hsl(${12 * note}, 70%, 28%)` };
}

export function CycleScoreNotes({ score }: { score: CycleScore | undefined }) {
  if (!score) {
    return null;
  }
  const items = [
    ...NOTE_LABELS.map((item) => ({
      value: formatCycleNote(score.notes[item.key]),
      label: item.label,
      note: score.notes[item.key],
      resume: score.resumes[item.key],
      global: false,
    })),
    {
      value: formatCycleNote(score.global),
      label: "Globale /10",
      note: score.global,
      resume: null as string | null,
      global: true,
    },
  ];
  return (
    <div className="stats score-stats">
      {items.map((item) => (
        <div key={item.label} className={item.global ? "stat score-global" : "stat"} style={noteTint(item.note)}>
          <b style={noteDigitColor(item.note)}>{item.value}</b>
          <span>{item.label}</span>
          {!item.global && item.resume ? <p className="score-resume">{item.resume}</p> : null}
        </div>
      ))}
    </div>
  );
}

export function LegalRecap({ cols, rows }: { cols: LegalCol[]; rows: PublishedCycle["legal_rows"] }) {
  return (
    <section>
      <h2>Règles légales</h2>
      <p className="sub">Plafonds interdits, mesurés sur le cycle. Texte moteur tel quel.</p>
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
                    {cell?.text ?? ""}
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
                    {cell ? cell.text : ""}
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
