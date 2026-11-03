import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from "chart.js";
import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";

import { useTema } from "@/lib/tema";

import type { SerieDePeso } from "../GraficaDePeso";
import { degradado, radioDelUltimo, tokens } from "./tema";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip);

export function Lienzo({ serie, unidad = "kg" }: { serie: SerieDePeso; unidad?: string }) {
  const { tema } = useTema();
  const [color, setColor] = useState(tokens);

  useEffect(() => {
    const id = requestAnimationFrame(() => setColor(tokens()));
    return () => cancelAnimationFrame(id);
  }, [tema]);

  const datos: ChartData<"line"> = {
    labels: serie.labels,
    datasets: [
      {
        label: `Peso (${unidad})`,
        data: serie.values,
        borderColor: color.acento,
        borderWidth: 2,
        tension: 0.25,
        fill: true,
        backgroundColor: (contexto) => degradado(contexto, color.acento),
        pointRadius: radioDelUltimo(serie.values.length),
        pointBackgroundColor: color.acento,
        pointHoverRadius: 5,
        pointHoverBorderWidth: 2,
        pointHoverBackgroundColor: color.acento,
        pointHitRadius: 24,
      },
      ...(serie.goal === null
        ? []
        : [
            {
              label: "Meta",
              data: serie.labels.map(() => serie.goal as number),
              borderColor: color.meta,
              borderWidth: 1.5,
              borderDash: [6, 4],
              pointRadius: 0,
              pointHitRadius: 0,
              fill: false,
            },
          ]),
    ],
  };

  const opciones: ChartOptions<"line"> = {
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
          label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} ${unidad}`,
        },
      },
    },
    interaction: { mode: "index", intersect: false },
    scales: {
      x: { ticks: { color: color.tinta, maxTicksLimit: 6 }, grid: { display: false } },
      y: { ticks: { color: color.tinta, maxTicksLimit: 5 }, grid: { color: color.rejilla } },
    },
  };

  return (
    <div className="chart-box">
      <Line data={datos} options={opciones} aria-label="Evolución del peso corporal" />
    </div>
  );
}
