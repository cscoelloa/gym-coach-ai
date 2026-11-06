import { Anillo } from "@/ds/Anillo";
import { Icono } from "@/ds/Icono";
import { SetRow } from "@/ds/SetRow";
import { WeekStrip, type DiaDeLaSemana } from "@/ds/WeekStrip";

const SEMANA: DiaDeLaSemana[] = [
  { inicial: "L", numero: 3, entrenado: true },
  { inicial: "M", numero: 4 },
  { inicial: "X", numero: 5, entrenado: true },
  { inicial: "J", numero: 6 },
  { inicial: "V", numero: 7, entrenado: true, hoy: true },
  { inicial: "S", numero: 8, planificado: true, futuro: true },
  { inicial: "D", numero: 9, futuro: true },
];

const TENDENCIA = [42, 40, 44, 39, 35, 36, 31, 28, 29, 24, 20, 17];

function Tendencia() {
  const ancho = 160;
  const alto = 56;
  const paso = ancho / (TENDENCIA.length - 1);
  const puntos = TENDENCIA.map((y, i) => `${(i * paso).toFixed(1)},${y}`);
  const ultimoY = TENDENCIA[TENDENCIA.length - 1] ?? 0;
  return (
    <svg viewBox={`0 0 ${ancho} ${alto}`} className="h-14 w-full text-data" preserveAspectRatio="none">
      <defs>
        <linearGradient id="vitrina-relleno" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity="0.28" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={`0,${alto} ${puntos.join(" ")} ${ancho},${alto}`} fill="url(#vitrina-relleno)" />
      <polyline
        points={puntos.join(" ")}
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
      <circle cx={ancho} cy={ultimoY} r="3.5" fill="currentColor" />
    </svg>
  );
}

export function Vitrina() {
  return (
    <div className="auth-vitrina" aria-hidden="true">
      <div className="vitrina-fila">
        <div className="vitrina-card vitrina-constancia">
          <Anillo hecho={3} total={4} etiqueta="3 de 4" tamano={76} grosor={8}>
            <span className="metric-md">3</span>
            <span className="caption text-ink-muted">de 4</span>
          </Anillo>
          <div className="min-w-0">
            <p className="tag text-ink-subtle">Constancia</p>
            <p className="flex items-baseline gap-1">
              <Icono nombre="fuego" className="size-5 self-center text-primary" />
              <span className="metric-xl">6</span>
              <span className="stat-tile-unit">semanas</span>
            </p>
          </div>
        </div>

        <div className="vitrina-card vitrina-progreso">
          <p className="tag text-ink-subtle">Volumen</p>
          <p className="metric-md text-data">+12 %</p>
          <Tendencia />
        </div>
      </div>

      <div className="vitrina-card vitrina-semana">
        <WeekStrip dias={SEMANA} />
      </div>

      <div className="vitrina-card vitrina-series">
        <p className="title-sm mb-2">Press de banca</p>
        <div className="flex flex-col gap-1.5">
          <SetRow numero={2} peso="80" reps={8} estado="hecha" />
          <SetRow numero={3} peso="82.5" reps={6} estado="activa" />
        </div>
      </div>
    </div>
  );
}
