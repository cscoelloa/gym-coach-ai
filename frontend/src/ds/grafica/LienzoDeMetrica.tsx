import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
  type TooltipItem,
} from "chart.js";
import { useEffect, useState } from "react";
import { Bar, Line } from "react-chartjs-2";

import { useTema } from "@/lib/tema";

import type { PuntoDeMetrica } from "../GraficaDeMetrica";
import { degradado, radioDelUltimo, tokens } from "./tema";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Filler, Tooltip);

export function LienzoDeMetrica({
  serie,
  tipo,
  unidad = "",
}: {
  serie: PuntoDeMetrica[];
  tipo: "line" | "bar";
  unidad?: string;
}) {
  const { tema } = useTema();
  const [color, setColor] = useState(tokens);

  useEffect(() => {
    const id = requestAnimationFrame(() => setColor(tokens()));
    return () => cancelAnimationFrame(id);
  }, [tema]);

  const esLinea = tipo === "line";
  const etiquetas = serie.map((punto) => punto.label);
  const valores = serie.map((punto) => punto.value);

  const comun = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: color.fondoTooltip,
        titleColor: color.tintaTooltip,
        bodyColor: color.tintaTooltip,
        padding: 10,
        displayColors: false,
        callbacks: {
          label: (ctx: TooltipItem<"line" | "bar">) =>
            `${esLinea ? ctx.parsed.y : ctx.parsed.x} ${unidad}`.trim(),
        },
      },
    },
  };

  if (esLinea) {
    const datos: ChartData<"line"> = {
      labels: etiquetas,
      datasets: [
        {
          data: valores,
          borderColor: color.acento,
          borderWidth: 2,
          tension: 0.25,
          fill: true,
          backgroundColor: (contexto) => degradado(contexto, color.acento),
          pointRadius: radioDelUltimo(valores.length),
          pointBackgroundColor: color.acento,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: color.acento,
          pointHitRadius: 24,
        },
      ],
    };

    const opciones: ChartOptions<"line"> = {
      ...comun,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { color: color.tinta, maxTicksLimit: 8 }, grid: { display: false } },
        y: { ticks: { color: color.tinta, maxTicksLimit: 5 }, grid: { color: color.rejilla } },
      },
    };

    return (
      <div className="chart-box">
        <Line data={datos} options={opciones} />
      </div>
    );
  }

  const datos: ChartData<"bar"> = {
    labels: etiquetas,
    datasets: [
      {
        data: valores,
        backgroundColor: color.acento,
        borderWidth: 0,
        borderRadius: 4,
        borderSkipped: false,
      },
    ],
  };

  const opciones: ChartOptions<"bar"> = {
    ...comun,
    indexAxis: "y",
    interaction: { mode: "nearest", intersect: false },
    scales: {
      x: { ticks: { color: color.tinta }, grid: { color: color.rejilla }, beginAtZero: true },
      y: { ticks: { color: color.tinta }, grid: { display: false } },
    },
  };

  return (
    <div className="chart-box">
      <Bar data={datos} options={opciones} />
    </div>
  );
}
