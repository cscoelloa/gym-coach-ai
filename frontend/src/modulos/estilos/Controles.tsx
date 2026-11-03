import { useState } from "react";

import { Badge } from "@/ds/Badge";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Campo } from "@/ds/Campo";
import { Card } from "@/ds/Card";
import { Chip, FilaDeChips } from "@/ds/Chip";
import { Icono } from "@/ds/Icono";
import { ProgressBar } from "@/ds/ProgressBar";
import { SegmentedControl } from "@/ds/SegmentedControl";
import { NotaDeStat, StatTile } from "@/ds/StatTile";

import { Seccion } from "./Seccion";

export function Controles() {
  const [vista, setVista] = useState<"hoy" | "semana" | "historial">("hoy");
  const [filtro, setFiltro] = useState("pecho");

  return (
    <>
      <Seccion
        titulo="Button"
        nota="Cápsulas, como en iOS. Cuatro variantes y tres alturas: 48 px, 40 en compacto y 56 para la acción principal de una pantalla."
      >
        <Card className="space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <Button variante="primary">
              <Icono nombre="mas" />
              Añadir serie
            </Button>
            <Button variante="secondary">Ver historial</Button>
            <Button variante="ghost">Cambiar ejercicio</Button>
            <Button variante="danger">Eliminar serie</Button>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button variante="primary" tamano="sm">
              Nueva rutina
            </Button>
            <Button variante="secondary" tamano="sm">
              Duplicar
            </Button>
            <Button variante="primary" tamano="lg">
              Empezar
            </Button>
            <Button variante="primary" disabled>
              Guardar rutina
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <EnlaceBoton a="/ejercicios/" variante="secondary" tamano="sm">
              Ver ejercicios
            </EnlaceBoton>
            <span className="body-sm text-ink-muted">
              ↑ un <code>EnlaceBoton</code>: navega, no muta.
            </span>
          </div>
        </Card>
      </Seccion>

      <Seccion
        titulo="Chip"
        nota="Filtro de una dimensión sobre el catálogo. Sustituye a los desplegables."
      >
        <Card>
          <FilaDeChips>
            {[
              { clave: "todos", etiqueta: "Todos", n: 148 },
              { clave: "pecho", etiqueta: "Pecho", n: 22 },
              { clave: "espalda", etiqueta: "Espalda", n: 27 },
              { clave: "pierna", etiqueta: "Pierna", n: 31 },
              { clave: "hombro", etiqueta: "Hombro", n: 18 },
              { clave: "core", etiqueta: "Core", n: 14 },
            ].map((c) => (
              <Chip
                key={c.clave}
                activo={filtro === c.clave}
                recuento={c.n}
                onClick={() => setFiltro(c.clave)}
              >
                {c.etiqueta}
              </Chip>
            ))}
          </FilaDeChips>
        </Card>
      </Seccion>

      <Seccion
        titulo="Badge"
        nota="Estado en una palabra. Siempre con texto: el color es refuerzo y nunca el único portador — verde y rojo son indistinguibles en deuteranopia y eso no se arregla cambiando los tonos."
      >
        <Card className="flex flex-wrap items-center gap-2">
          <Badge tono="record">récord</Badge>
          <Badge tono="done">completada</Badge>
          <Badge tono="warn">descarga</Badge>
          <Badge tono="down">−4 %</Badge>
          <Badge tono="info">cardio</Badge>
          <Badge tono="neutral">barra</Badge>
        </Card>
      </Seccion>

      <Seccion
        titulo="Field"
        nota="El texto de campo mide 17 px, el cuerpo de iOS, y nunca baja de 16: por debajo, Safari en iOS hace zoom al enfocar y descoloca la página entera."
      >
        <Card className="grid grid-cols-1 gap-4 sm:grid-cols-[minmax(0,1fr)_9rem_9rem]">
          <Campo
            etiqueta="Nombre de la rutina"
            defaultValue="Empuje A"
            ayuda="Se muestra en Inicio y en el historial."
          />
          <Campo
            etiqueta="Carga (kg)"
            className="field-num"
            inputMode="decimal"
            defaultValue="82.5"
            ayuda="La última vez: 80"
          />
          <Campo
            etiqueta="Reps"
            className="field-num"
            inputMode="numeric"
            defaultValue="0"
            errores={["Escribe al menos 1."]}
          />
        </Card>
      </Seccion>

      <Seccion
        titulo="SegmentedControl"
        nota="Cambio entre vistas del mismo contenido, no entre destinos."
      >
        <Card>
          <SegmentedControl
            etiqueta="Vista de inicio"
            valor={vista}
            onCambio={setVista}
            opciones={[
              { valor: "hoy", etiqueta: "Hoy" },
              { valor: "semana", etiqueta: "Semana" },
              { valor: "historial", etiqueta: "Historial" },
            ]}
          />
        </Card>
      </Seccion>

      <Seccion
        titulo="ProgressBar"
        nota="En data por defecto. Solo la sesión en curso la lleva en primary, porque ahí el avance es la acción y no un dato que se consulta."
      >
        <Card className="space-y-5">
          <ProgressBar etiqueta="Series de hoy" hecho={9} total={16} marca />
          <ProgressBar etiqueta="Volumen de la semana" hecho={12480} total={14000} unidad="kg" />
        </Card>
      </Seccion>

      <Seccion
        titulo="StatTile"
        nota="Una cifra con su nombre y, si aporta, su comparación con el periodo anterior. Sin datos detrás se dice una sola vez, y un cero sin cobertura no es un cero."
      >
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatTile etiqueta="Volumen total" valor="12 480" unidad="kg">
            <Badge tono="done">+6 %</Badge>
            <NotaDeStat>vs. semana pasada</NotaDeStat>
          </StatTile>
          <StatTile etiqueta="Series" valor={64}>
            <Badge tono="down">−4 %</Badge>
            <NotaDeStat>vs. semana pasada</NotaDeStat>
          </StatTile>
          <StatTile etiqueta="Carga máxima" valor={110} unidad="kg">
            <Badge tono="record">récord</Badge>
            <NotaDeStat>peso muerto</NotaDeStat>
          </StatTile>
          <StatTile etiqueta="Cardio" valor={null} vacio="Sin registros todavía." />
        </div>
      </Seccion>
    </>
  );
}
