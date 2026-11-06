import { Card } from "@/ds/Card";

import { Seccion } from "./Seccion";

const SUPERFICIES = [
  { token: "surface-000", clase: "bg-surface-000", para: "Fondo de pantalla" },
  { token: "surface-100", clase: "bg-surface-100", para: "Fondo de tarjeta" },
  { token: "surface-200", clase: "bg-surface-200", para: "Elevada en tarjeta" },
  { token: "surface-300", clase: "bg-surface-300", para: "Opción elegida" },
  { token: "surface-inset", clase: "bg-surface-inset", para: "Campo numérico" },
] as const;

const ACENTOS = [
  { token: "primary-fill", clase: "bg-primary-fill", para: "La acción, de relleno" },
  { token: "primary", clase: "bg-primary", para: "La acción, de tinta" },
  { token: "data", clase: "bg-data", para: "El dato" },
  { token: "success", clase: "bg-success", para: "Hecho" },
  { token: "warning", clase: "bg-warning", para: "Aviso" },
  { token: "danger", clase: "bg-danger", para: "Peligro" },
  { token: "line-strong", clase: "bg-line-strong", para: "Borde de control" },
] as const;

const TIPOGRAFIA = [
  { clase: "display-lg", muestra: "Empuje A" },
  { clase: "display-md", muestra: "Tu semana" },
  { clase: "title-lg", muestra: "Press de banca" },
  { clase: "title-md", muestra: "Peso corporal" },
  { clase: "title-sm", muestra: "Series efectivas" },
  { clase: "body", muestra: "Cuatro series de ocho a doce repeticiones." },
  { clase: "body-sm", muestra: "Descanso de noventa segundos entre series." },
  { clase: "label", muestra: "Carga (kg)" },
  { clase: "caption", muestra: "vs. semana pasada" },
  { clase: "metric-2xl", muestra: "12" },
  { clase: "metric-xl", muestra: "92,5" },
  { clase: "metric-lg", muestra: "1 240" },
  { clase: "metric-md", muestra: "12 480" },
  { clase: "metric-sm", muestra: "4 × 8" },
  { clase: "tag", muestra: "récord" },
] as const;

export function Fundamentos() {
  return (
    <>
      <Seccion
        titulo="Color"
        nota={
          <>
            Un color por significado: la <strong className="text-ink">lima</strong> es la acción,
            el progreso y el logro; el <strong className="text-ink">violeta</strong> es el dato; la{" "}
            <strong className="text-ink">menta</strong> es lo hecho. En claro la lima solo rellena
            —con texto casi negro y un borde oliva— y, cuando tiene que ser tinta, pasa a oliva.
            Una serie de gráfica del color del botón principal invitaría a pulsarla.
          </>
        }
      >
        <h3 className="mb-2">Superficies</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {SUPERFICIES.map((s) => (
            <div key={s.token} className="card p-3">
              <span className={`hairline block h-10 rounded-sm border ${s.clase}`} />
              <span className="tag mt-2 block text-ink-subtle">{s.token}</span>
              <span className="caption text-ink-muted">{s.para}</span>
            </div>
          ))}
        </div>

        <h3 className="mb-2 mt-5">Acento y estado</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          {ACENTOS.map((a) => (
            <div key={a.token} className="card p-3">
              <span className={`block h-10 rounded-sm ${a.clase}`} />
              <span className="tag mt-2 block text-ink-subtle">{a.token}</span>
              <span className="caption text-ink-muted">{a.para}</span>
            </div>
          ))}
        </div>
      </Seccion>

      <Seccion
        titulo="Tipografía"
        nota={
          <>
            Inter para todo, con la escala de iOS: título grande de 34 px y cuerpo de 17. Los números
            que importan se leen de un vistazo: ganan tamaño, no peso. Toda cifra va con dígitos
            tabulares, para que las columnas de kg no bailen.
            Autoalojada: la CSP declara <code>font-src: 'self'</code> y un enlace a Google Fonts
            quedaría bloqueado sin más rastro que una tipografía que no es la que se pidió.
          </>
        }
      >
        <Card className="space-y-3">
          {TIPOGRAFIA.map((t) => (
            <div key={t.clase} className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <span className="tag w-28 shrink-0 text-ink-subtle">{t.clase}</span>
              <span className={t.clase}>{t.muestra}</span>
            </div>
          ))}
        </Card>
      </Seccion>
    </>
  );
}
