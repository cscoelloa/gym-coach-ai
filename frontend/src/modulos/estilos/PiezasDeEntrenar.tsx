import { useState } from "react";

import { Badge } from "@/ds/Badge";
import { Button } from "@/ds/Button";
import { Card } from "@/ds/Card";
import { ExerciseCard } from "@/ds/ExerciseCard";
import { Icono } from "@/ds/Icono";
import { RestTimer } from "@/ds/RestTimer";
import { RoutineCard } from "@/ds/RoutineCard";
import { CabeceraDeSeries, SetRow } from "@/ds/SetRow";
import { ConfirmarSerie, Stepper } from "@/ds/Stepper";

import { Seccion } from "./Seccion";

const EMPUJE = [
  { nombre: "Press de banca", series: "4 × 8" },
  { nombre: "Press militar", series: "4 × 10" },
  { nombre: "Fondos en paralelas", series: "3 × 12" },
];

const PIERNA = [
  { nombre: "Sentadilla trasera", series: "5 × 5" },
  { nombre: "Peso muerto rumano", series: "4 × 8" },
  { nombre: "Prensa", series: "4 × 12" },
  { nombre: "Curl femoral", series: "3 × 12" },
  { nombre: "Gemelo de pie", series: "4 × 15" },
];

export function PiezasDeEntrenar() {
  const [kg, setKg] = useState("82.5");
  const [reps, setReps] = useState("8");
  const [confirmada, setConfirmada] = useState(false);

  return (
    <>
      <Seccion
        titulo="SetRow"
        nota="La pieza central del producto: la pantalla de entrenamiento activo es una pila de estas filas. Cuatro columnas fijas para que las cifras queden alineadas entre series."
      >
        <Card className="p-3">
          <p className="ex-name mb-2">
            Press de banca <span className="metric-sm text-ink-muted">4 × 8</span>
          </p>
          <CabeceraDeSeries />
          <SetRow numero={1} peso="80" reps={8} estado="hecha" />
          <SetRow numero={2} peso="82.5" reps={8} estado="hecha">
            <Badge tono="record">récord</Badge>
          </SetRow>
          <SetRow numero={3} peso="82.5" reps={8} estado="activa" />
          <SetRow numero={4} peso="82.5" reps={8} />
        </Card>
      </Seccion>

      <Seccion
        titulo="Stepper"
        nota="Los botones miden 44 px porque se pulsan con el pulgar sudado entre series. El campo sigue en medio y se puede escribir: subir de 60 a 100 kg a golpes de «+» son cuarenta pulsaciones."
      >
        <Card className="grid grid-cols-1 gap-3 min-[22.5rem]:grid-cols-2 sm:grid-cols-4">
          <Stepper etiqueta="kg" valor={kg} onCambio={setKg} paso={2.5} decimal />
          <Stepper etiqueta="Reps" valor={reps} onCambio={setReps} minimo={1} />
          <div>
            <span className="config-label">Confirmar</span>
            <div className="flex gap-2">
              <ConfirmarSerie
                hecha={confirmada}
                etiqueta="Confirmar la serie 3"
                onClick={() => setConfirmada((previo) => !previo)}
              />
              <ConfirmarSerie etiqueta="Confirmar la serie 4" disabled />
            </div>
          </div>
        </Card>
        <p className="body-sm mt-4 mb-2 text-ink-muted">
          En el modo foco van en grande (<code>tamano=&quot;lg&quot;</code>, 56 px), dentro de la
          barra de registrar:
        </p>
        <Card className="space-y-3">
          <div className="grid grid-cols-1 gap-3 min-[25rem]:grid-cols-2">
            <Stepper etiqueta="kg" valor={kg} onCambio={setKg} paso={2.5} decimal tamano="lg" />
            <Stepper etiqueta="Reps" valor={reps} onCambio={setReps} minimo={1} tamano="lg" />
          </div>
          <Button variante="primary" tamano="lg" bloque>
            Registrar serie
          </Button>
        </Card>
      </Seccion>

      <Seccion
        titulo="ExerciseCard"
        nota="Fila del catálogo: nombre, grupo y equipamiento, y la última carga registrada."
      >
        <div className="space-y-3">
          <ExerciseCard
            nombre="press de banca"
            grupo="Pecho"
            equipamiento="Barra"
            ultima="82.5 kg × 8"
            glifo={<Icono nombre="barra" className="size-6" />}
          />
          <ExerciseCard
            nombre="zancada búlgara"
            grupo="Pierna"
            equipamiento="Peso corporal"
            glifo={<Icono nombre="zancada" className="size-6" />}
          />
        </div>
      </Seccion>

      <Seccion titulo="RoutineCard" nota="La plantilla de un entrenamiento, con la acción de empezar.">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <RoutineCard nombre="Empuje A" dias="Lun · Jue" ejercicios={EMPUJE} insignia={<Badge tono="done">hoy</Badge>}>
            <Button variante="primary" tamano="sm">
              Empezar
            </Button>
            <Button variante="ghost" tamano="sm">
              Editar
            </Button>
          </RoutineCard>

          <RoutineCard
            nombre="Pierna completa"
            dias="Mié"
            ejercicios={PIERNA}
            insignia={<Badge tono="warn">2 semanas</Badge>}
          >
            <Button variante="primary" tamano="sm">
              Empezar
            </Button>
            <Button variante="ghost" tamano="sm">
              Editar
            </Button>
          </RoutineCard>
        </div>
      </Seccion>

      <Seccion
        titulo="RestTimer"
        nota="El anillo se lee de un vistazo sin enfocar el número: cuánto queda es una proporción, y una proporción se ve antes como forma que como cifra."
      >
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <RestTimer restante={62} total={90} siguiente="Serie 3 · 82.5 kg × 8">
            <Button variante="secondary" tamano="sm">
              +30 s
            </Button>
            <Button variante="secondary" tamano="sm">
              Saltar
            </Button>
          </RestTimer>

          <RestTimer restante={8} total={90} siguiente="Serie 1 · 10 reps">
            <Button variante="secondary" tamano="sm">
              Saltar
            </Button>
          </RestTimer>
        </div>
        <p className="body-sm mt-4 mb-2 text-ink-muted">
          En una sola fila (<code>compacto</code>), encima de la barra de registrar:
        </p>
        <RestTimer compacto restante={62} total={90} siguiente="Serie 3 · 82.5 kg × 8">
          <Button variante="ghost" tamano="sm">
            +30 s
          </Button>
          <Button variante="secondary" tamano="sm">
            Saltar
          </Button>
        </RestTimer>
      </Seccion>
    </>
  );
}
