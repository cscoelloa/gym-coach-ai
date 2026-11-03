import { EnlaceBoton } from "@/ds/Button";
import { Card, Pill, TablaDesplazable } from "@/ds/Card";
import { EmptyState } from "@/ds/EmptyState";
import { Hint } from "@/ds/Hint";
import { Icono } from "@/ds/Icono";
import { StatTile } from "@/ds/StatTile";
import { HeatCell, WeekStrip } from "@/ds/WeekStrip";

import { Seccion } from "./Seccion";

const SEMANA = [
  { inicial: "L", numero: 15, entrenado: true },
  { inicial: "M", numero: 16, hoy: true, entrenado: true },
  { inicial: "X", numero: 17, planificado: true },
  { inicial: "J", numero: 18, futuro: true },
  { inicial: "V", numero: 19, futuro: true },
  { inicial: "S", numero: 20, futuro: true },
  { inicial: "D", numero: 21, futuro: true },
] as const;

export function DatosYVacios() {
  return (
    <>
      <Seccion
        titulo="EmptyState"
        nota="Lo que ocupa el sitio de una lista sin contenido. Dice qué falta y cómo empezar, no solo que está vacío. Su hermano pequeño es la línea de empty-hint que pone StatTile."
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <EmptyState
            titulo="Aún no tienes rutinas"
            glifo={<Icono nombre="barra" className="size-6" />}
            acciones={
              <>
                <EnlaceBoton a="/plan/" variante="primary" tamano="sm">
                  Crear rutina
                </EnlaceBoton>
                <EnlaceBoton a="/ejercicios/" variante="ghost" tamano="sm">
                  Ver ejercicios
                </EnlaceBoton>
              </>
            }
          >
            Arma una con los ejercicios que ya haces y la aplicación precargará tus cargas en cada
            sesión.
          </EmptyState>

          <Card className="flex flex-col justify-center">
            <StatTile etiqueta="Cardio" valor={null} vacio="Sin registros de cardio esta semana." />
          </Card>
        </div>
      </Seccion>

      <Seccion
        titulo="Semana y actividad"
        nota="El estado se lee sin depender del color: punto lleno = entrenado, hueco = planificado, nada = día libre."
      >
        <Card>
          <WeekStrip dias={SEMANA} />

          <p className="section-kicker mt-5">Escala de actividad</p>
          <div className="flex items-center gap-1">
            {([0, 1, 2, 3, 4] as const).map((nivel) => (
              <HeatCell key={nivel} nivel={nivel} />
            ))}
            <span className="caption ml-2 text-ink-muted">de menos a más volumen</span>
          </div>
        </Card>
      </Seccion>

      <Seccion titulo="Píldoras, sugerencias y tablas">
        <Card className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Pill>Pecho</Pill>
            <Pill>Barra</Pill>
            <Pill activa>Unilateral</Pill>
            <Pill>
              Mejor: <span className="num">110</span> kg
            </Pill>
          </div>

          <Hint>
            Has cerrado las cuatro series en el rango alto. Sube a 85 kg la próxima vez.
          </Hint>

          <TablaDesplazable>
            <thead>
              <tr className="tag text-left text-ink-subtle">
                <th className="px-3 py-2">Semana</th>
                <th className="px-3 py-2 text-right">Volumen</th>
                <th className="px-3 py-2 text-right">Series</th>
                <th className="px-3 py-2 text-right">Cobertura</th>
              </tr>
            </thead>
            <tbody className="body-sm">
              {[
                { semana: "8 sep", volumen: "11 940", series: 61, cobertura: "100 %" },
                { semana: "15 sep", volumen: "12 480", series: 64, cobertura: "86 %" },
              ].map((fila) => (
                <tr className="border-b border-line" key={fila.semana}>
                  <td className="px-3 py-2">{fila.semana}</td>
                  <td className="num px-3 py-2 text-right">{fila.volumen}</td>
                  <td className="num px-3 py-2 text-right">{fila.series}</td>
                  <td className="num px-3 py-2 text-right">{fila.cobertura}</td>
                </tr>
              ))}
            </tbody>
          </TablaDesplazable>
        </Card>
      </Seccion>
    </>
  );
}
