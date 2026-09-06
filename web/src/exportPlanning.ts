import * as XLSX from "xlsx";
import {
  CONTEXT_SERVICES,
  type ConfigEmployee,
  type ContextServiceId,
  type RestaurantContext,
  type TeamId,
} from "./context";
import { DAYS_FR, formatClock, formatDuration, weekLabelPair, weekSheetTitle, type WeekLabelScheme } from "./format";
import type { PublishedCycle } from "./generate";

const DAYS_XLSX = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"] as const;

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

function xlsxServiceLabel(id: string): string {
  if (id === "morning") {
    return "PDJ";
  }
  if (id === "midday") {
    return "DJ";
  }
  if (id === "evening") {
    return "Dîner";
  }
  return serviceLabel(id);
}

function formatExportStamp(at = new Date()): string {
  return at.toLocaleString("fr-FR");
}

function applyCellStyle(sheet: XLSX.WorkSheet, row: number, col: number, style: Record<string, unknown>) {
  const addr = XLSX.utils.encode_cell({ r: row, c: col });
  const cell = sheet[addr];
  if (cell) {
    cell.s = style;
  }
}

function xlsxWeekSheet(
  payload: PlanningExport,
  offered: ContextServiceId[],
  weekOffset: 0 | 7,
): XLSX.WorkSheet {
  const colCount = 2 + DAYS_XLSX.length * 3;
  const title = `Planning validé en date du : ${formatExportStamp()}`;
  const headerDays: string[] = ["Personne", "Service"];
  const headerFields: string[] = ["", ""];
  for (const day of DAYS_XLSX) {
    headerDays.push(day, "", "");
    headerFields.push("DEBUT", "FIN", "NB HEURES");
  }
  const rows: (string | number)[][] = [[title], headerDays, headerFields];
  const names = payload.employees;
  for (const person of names) {
    for (const service of offered) {
      const line: (string | number)[] = [person.name, xlsxServiceLabel(service)];
      for (let day = 0; day < 7; day++) {
        const shift = payload.assignments.find(
          (item) =>
            item.employee_id === person.id && item.day_index === weekOffset + day && item.service_id === service,
        );
        if (shift) {
          line.push(
            formatClock(shift.start_minutes),
            formatClock(shift.end_minutes),
            formatDuration(shift.duration_hours),
          );
        } else {
          line.push("", "", "");
        }
      }
      rows.push(line);
    }
  }
  const sheet = XLSX.utils.aoa_to_sheet(rows);
  sheet["!merges"] = [
    { s: { r: 0, c: 0 }, e: { r: 0, c: colCount - 1 } },
    ...DAYS_XLSX.map((_, index) => ({
      s: { r: 1, c: 2 + index * 3 },
      e: { r: 1, c: 4 + index * 3 },
    })),
  ];
  sheet["!cols"] = [{ wch: 18 }, { wch: 10 }, ...Array.from({ length: DAYS_XLSX.length * 3 }, () => ({ wch: 11 }))];
  const titleStyle = {
    font: { bold: true, sz: 14, color: { rgb: "1A365D" } },
    fill: { fgColor: { rgb: "E2E8F0" } },
  };
  const dayStyle = {
    font: { bold: true, color: { rgb: "FFFFFF" } },
    fill: { fgColor: { rgb: "2B6CB0" } },
    alignment: { horizontal: "center" },
  };
  const subStyle = {
    font: { bold: true, color: { rgb: "1A365D" } },
    fill: { fgColor: { rgb: "BEE3F8" } },
    alignment: { horizontal: "center" },
  };
  const stripeStyle = { fill: { fgColor: { rgb: "F7FAFC" } } };
  applyCellStyle(sheet, 0, 0, titleStyle);
  for (let col = 0; col < colCount; col++) {
    applyCellStyle(sheet, 1, col, dayStyle);
    applyCellStyle(sheet, 2, col, subStyle);
  }
  const dataStart = 3;
  for (let row = dataStart; row < rows.length; row++) {
    if ((row - dataStart) % 2 === 1) {
      for (let col = 0; col < colCount; col++) {
        applyCellStyle(sheet, row, col, stripeStyle);
      }
    }
  }
  return sheet;
}

function downloadXlsx(payload: PlanningExport, offered: ContextServiceId[]): void {
  const services = offered.length
    ? offered
    : (CONTEXT_SERVICES.map((item) => item.id).filter((id) =>
        payload.assignments.some((shift) => shift.service_id === id),
      ) as ContextServiceId[]);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, xlsxWeekSheet(payload, services, 0), weekSheetTitle(payload.week_labels, 0));
  XLSX.utils.book_append_sheet(workbook, xlsxWeekSheet(payload, services, 7), weekSheetTitle(payload.week_labels, 7));
  const bytes = XLSX.write(workbook, { bookType: "xlsx", type: "array", cellStyles: true }) as ArrayBuffer;
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
  const height = Math.max(sheet.scrollHeight, table ? table.scrollHeight + 48 : 56, 80);
  const scale = Math.max(window.devicePixelRatio || 1, 2);
  const canvas = document.createElement("canvas");
  canvas.width = Math.ceil(width * scale);
  canvas.height = Math.ceil(height * scale);
  const gfx = canvas.getContext("2d");
  if (!gfx) {
    throw new Error("canvas JPEG indisponible");
  }
  gfx.setTransform(scale, 0, 0, scale, 0, 0);
  gfx.fillStyle = "#ffffff";
  gfx.fillRect(0, 0, width, height);
  gfx.fillStyle = "#1a1a1a";
  gfx.font = "600 18px sans-serif";
  gfx.fillText(title, 8, 26);
  if (table) {
    const origin = table.getBoundingClientRect();
    const top = 36;
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
          gfx.font = `${style.fontWeight} 13px sans-serif`;
          gfx.fillText(text, x + 4, y + Math.min(18, box.height - 4), Math.max(box.width - 8, 8));
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
    out.toBlob((next) => (next ? resolve(next) : reject(new Error("JPEG vide"))), "image/jpeg", 0.95);
  });
  downloadBlob(blob, planningExportFilename(payload.restaurant_name, payload.team, "jpeg"));
}

export async function exportPublishedPlanning(
  payload: PlanningExport,
  format: PlanningExportFormat,
  sheets: HTMLElement[],
  offeredServices: ContextServiceId[] = [],
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
    downloadXlsx(payload, offeredServices);
    return;
  }
  await downloadJpeg(sheets, payload);
}
