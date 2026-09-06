import type { LegalCol, PublishedCycle } from "./generate";
import type { PlanningStats } from "./types";

export function CycleStats({ stats }: { stats: PlanningStats }) {
  const items: { value: string; label: string; tone?: "ok" | "warn" }[] = [
    { value: String(stats.assignments), label: "Shifts posés" },
    { value: String(stats.empty), label: "Postes vides", tone: stats.empty === 0 ? "ok" : "warn" },
    {
      value: String(stats.interdit),
      label: "Alertes légales",
      tone: stats.interdit === 0 ? "ok" : "warn",
    },
    {
      value: `${stats.below_role} / ${stats.assignments}`,
      label: "Shifts sous le rôle",
      tone: stats.below_role === 0 ? "ok" : "warn",
    },
    {
      value: `${stats.hours.percent} %`,
      label: "Heures vs contrat",
      tone: stats.hours.percent === 100 ? "ok" : "warn",
    },
    {
      value: `${stats.wellbeing.held} / ${stats.wellbeing.total}`,
      label: "Souhaits bien-être",
      tone: stats.wellbeing.held === stats.wellbeing.total ? "ok" : "warn",
    },
  ];
  return (
    <div className="stats">
      {items.map((item) => (
        <div key={item.label} className={`stat ${item.tone ?? ""}`}>
          <b>{item.value}</b>
          <span>{item.label}</span>
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
