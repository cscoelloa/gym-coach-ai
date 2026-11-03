import type { ScriptableContext } from "chart.js";

export type TokensDeGrafica = {
  acento: string;
  tinta: string;
  rejilla: string;
  meta: string;
  fondoTooltip: string;
  tintaTooltip: string;
};

export function tokens(): TokensDeGrafica {
  const estilo = getComputedStyle(document.documentElement);
  const leer = (nombre: string, respaldo: string) =>
    estilo.getPropertyValue(nombre).trim() || respaldo;

  return {
    acento: leer("--chart-accent", "#0f766e"),
    tinta: leer("--chart-ink", "#48484d"),
    rejilla: leer("--chart-grid", "#e3e3e8"),
    meta: leer("--chart-goal", "#935300"),
    fondoTooltip: leer("--chart-tooltip-bg", "#1c1c1e"),
    tintaTooltip: leer("--chart-tooltip-ink", "#ffffff"),
  };
}

export function degradado(contexto: ScriptableContext<"line">, color: string) {
  const { ctx, chartArea } = contexto.chart;
  if (!chartArea) return "transparent";
  const g = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
  g.addColorStop(0, `${color}55`);
  g.addColorStop(1, `${color}00`);
  return g;
}

export function radioDelUltimo(total: number) {
  return (contexto: ScriptableContext<"line">) => (contexto.dataIndex === total - 1 ? 4 : 0);
}
