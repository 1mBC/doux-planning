import * as XLSX from "xlsx";
import { CONTEXT_SERVICES, type ConfigEmployee, type RestaurantContext, type TeamId } from "./context";
import { DAYS_FR, formatClock, formatDuration, weekLabelPair, type WeekLabelScheme } from "./format";
import type { PublishedCycle } from "./generate";

export type PlanningExport = {
  export_version: 1;
  kind: "planning";
  team: TeamId;
  restaurant_name: string;
  week_labels: WeekLabelScheme;
  employees: ConfigEmployee[];
  assignments: PublishedCycle["assignments"];
  warnings: PublishedCycle["warnings"];
  stats: PublishedCycle["stats"];
  legal_cols: PublishedCycle["legal_cols"];
  legal_rows: PublishedCycle["legal_rows"];
  wish_cols: PublishedCycle["wish_cols"];
  wish_rows: PublishedCycle["wish_rows"];
};

export type PlanningExportFormat = "json" | "csv" | "xlsx" | "jpeg";

function serviceLabel(id: string): string {
  return CONTEXT_SERVICES.find((item) => item.id === id)?.label ?? id;
}

function dayLabel(dayIndex: number): string {
  return DAYS_FR[((dayIndex % 7) + 7) % 7];
}

export function planningExportFilename(name: string, team: TeamId, format: PlanningExportFormat): string {
  const trimmed = name.trim();
  const slug = trimmed
    ? trimmed
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "") || "planning"
    : "planning";
  const ext = format === "jpeg" ? "jpg" : format;
  return `${slug}-${team}.${ext}`;
}

export function buildPlanningExport(
  ctx: RestaurantContext,
  team: TeamId,
  cycle: PublishedCycle,
): PlanningExport {
  return {
    export_version: 1,
    kind: "planning",
    team,
    restaurant_name: ctx.name,
    week_labels: ctx.week_labels,
    employees: ctx.employees
      .filter((person) => person.team === team)
      .map(({ invite_token: _token, ...rest }): ConfigEmployee => rest),
    assignments: cycle.assignments,
    warnings: cycle.warnings,
    stats: cycle.stats,
    legal_cols: cycle.legal_cols,
    legal_rows: cycle.legal_rows,
    wish_cols: cycle.wish_cols,
    wish_rows: cycle.wish_rows,
  };
}

function gridRows(payload: PlanningExport): string[][] {
  const names = new Map(payload.employees.map((person) => [person.id, person.name]));
  return payload.assignments.map((shift) => [
    names.get(shift.employee_id) ?? shift.employee_id,
    dayLabel(shift.day_index),
    serviceLabel(shift.service_id),
    formatClock(shift.start_minutes),
    formatClock(shift.end_minutes),
    formatDuration(shift.duration_hours),
  ]);
}

function metadataRows(payload: PlanningExport): string[][] {
  return [
    ["Restaurant", payload.restaurant_name],
    ["Équipe", payload.team === "salle" ? "Salle" : "Cuisine"],
    ["Libellés", weekLabelPair(payload.week_labels)],
  ];
}

function csvEscape(value: string): string {
  if (/[",\n]/.test(value)) {
    return `"${value.replaceAll('"', '""')}"`;
  }
  return value;
}

function toCsv(payload: PlanningExport): string {
  const header = ["Personne", "Jour", "Service", "Début", "Fin", "Heures"];
  const lines = [
    ...metadataRows(payload).map((row) => row.map(csvEscape).join(",")),
    "",
    header.join(","),
    ...gridRows(payload).map((row) => row.map(csvEscape).join(",")),
  ];
  return `${lines.join("\n")}\n`;
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function downloadJson(payload: PlanningExport): void {
  downloadBlob(
    new Blob([JSON.stringify(payload)], { type: "application/json" }),
    planningExportFilename(payload.restaurant_name, payload.team, "json"),
  );
}

function downloadCsv(payload: PlanningExport): void {
  downloadBlob(
    new Blob([toCsv(payload)], { type: "text/csv;charset=utf-8" }),
    planningExportFilename(payload.restaurant_name, payload.team, "csv"),
  );
}

function downloadXlsx(payload: PlanningExport): void {
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, XLSX.utils.aoa_to_sheet(metadataRows(payload)), "Métadonnées");
  XLSX.utils.book_append_sheet(
    workbook,
    XLSX.utils.aoa_to_sheet([["Personne", "Jour", "Service", "Début", "Fin", "Heures"], ...gridRows(payload)]),
    "Grille",
  );
  const bytes = XLSX.write(workbook, { bookType: "xlsx", type: "array" }) as ArrayBuffer;
  downloadBlob(
    new Blob([bytes], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }),
    planningExportFilename(payload.restaurant_name, payload.team, "xlsx"),
  );
}

function cssColor(value: string, fallback: string): string {
  return value && value !== "rgba(0, 0, 0, 0)" && value !== "transparent" ? value : fallback;
}

function paintSheet(sheet: HTMLElement): HTMLCanvasElement {
  const scrolls = [...sheet.querySelectorAll<HTMLElement>(".scroll")];
  const previous = scrolls.map((el) => el.style.overflow);
  for (const el of scrolls) {
    el.style.overflow = "visible";
  }
  const title = sheet.querySelector("h3")?.textContent ?? "";
  const table = sheet.querySelector("table.plan");
  const width = Math.max(sheet.scrollWidth, table?.scrollWidth ?? 0, 640);
  const height = Math.max(sheet.scrollHeight, table ? table.scrollHeight + 36 : 48, 80);
  const canvas = document.createElement("canvas");
  canvas.width = Math.ceil(width);
  canvas.height = Math.ceil(height);
  const gfx = canvas.getContext("2d");
  if (!gfx) {
    throw new Error("canvas JPEG indisponible");
  }
  gfx.fillStyle = "#ffffff";
  gfx.fillRect(0, 0, canvas.width, canvas.height);
  gfx.fillStyle = "#1a1a1a";
  gfx.font = "600 16px sans-serif";
  gfx.fillText(title, 8, 22);
  if (table) {
    const origin = table.getBoundingClientRect();
    const top = 32;
    for (const row of table.querySelectorAll("tr")) {
      for (const cell of row.querySelectorAll("th, td")) {
        const box = cell.getBoundingClientRect();
        const x = box.left - origin.left;
        const y = box.top - origin.top + top;
        const style = getComputedStyle(cell);
        gfx.fillStyle = cssColor(style.backgroundColor, "#ffffff");
        gfx.fillRect(x, y, box.width, box.height);
        gfx.strokeStyle = "#d5d8dd";
        gfx.strokeRect(x, y, box.width, box.height);
        const text = (cell.textContent ?? "").replace(/\s+/g, " ").trim();
        if (text) {
          gfx.fillStyle = cssColor(style.color, "#1a1a1a");
          gfx.font = `${style.fontWeight} 11px sans-serif`;
          gfx.fillText(text, x + 3, y + Math.min(14, box.height - 3), Math.max(box.width - 6, 8));
        }
      }
    }
  }
  scrolls.forEach((el, index) => {
    el.style.overflow = previous[index] ?? "";
  });
  return canvas;
}

async function downloadJpeg(sheets: HTMLElement[], payload: PlanningExport): Promise<void> {
  const canvases = sheets.map((sheet) => paintSheet(sheet));
  const width = Math.max(...canvases.map((item) => item.width), 1);
  const height = canvases.reduce((sum, item) => sum + item.height, 0) || 1;
  const out = document.createElement("canvas");
  out.width = width;
  out.height = height;
  const gfx = out.getContext("2d");
  if (!gfx) {
    throw new Error("canvas JPEG indisponible");
  }
  gfx.fillStyle = "#ffffff";
  gfx.fillRect(0, 0, width, height);
  let top = 0;
  for (const canvas of canvases) {
    gfx.drawImage(canvas, 0, top);
    top += canvas.height;
  }
  const blob = await new Promise<Blob>((resolve, reject) => {
    out.toBlob((next) => (next ? resolve(next) : reject(new Error("JPEG vide"))), "image/jpeg", 0.92);
  });
  downloadBlob(blob, planningExportFilename(payload.restaurant_name, payload.team, "jpeg"));
}

export async function exportPublishedPlanning(
  payload: PlanningExport,
  format: PlanningExportFormat,
  sheets: HTMLElement[],
): Promise<void> {
  if (format === "json") {
    downloadJson(payload);
    return;
  }
  if (format === "csv") {
    downloadCsv(payload);
    return;
  }
  if (format === "xlsx") {
    downloadXlsx(payload);
    return;
  }
  await downloadJpeg(sheets, payload);
}
