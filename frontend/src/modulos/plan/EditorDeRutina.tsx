import { useParams } from "react-router";

import { ErrorDeApi } from "@/api/cliente";
import { Aviso } from "@/ds/Aviso";
import { AvisoPasajero } from "@/ds/AvisoPasajero";
import { BarraDeAcciones } from "@/ds/BarraDeAcciones";
import { Button, EnlaceBoton } from "@/ds/Button";
import { Cabecera } from "@/ds/Cabecera";
import { Campo } from "@/ds/Campo";
import { EmptyState } from "@/ds/EmptyState";
import { Cargando, ErrorDePantalla } from "@/ds/estados";
import { Icono } from "@/ds/Icono";
import { Panel } from "@/ds/Panel";
import { nombreDeEjercicio } from "@/lib/texto";

import { useRutina, type Rutina } from "./api";
import { Configuracion } from "./Configuracion";
import { ListaDelBorrador } from "./ListaDelBorrador";
import { SelectorDeEjercicios } from "./SelectorDeEjercicios";
import { useBusquedaDeEjercicios } from "./useBusquedaDeEjercicios";
import { useEditorDeRutina } from "./useEditorDeRutina";

export function EditorDeRutina({ nueva = false }: { nueva?: boolean }) {
  const { id = "" } = useParams();
  const consulta = useRutina(nueva ? NaN : Number(id));

  if (nueva) return <Editor key="nueva" />;
  if (consulta.isPending) return <Cargando />;
  if (consulta.error instanceof ErrorDeApi && consulta.error.estado === 404) {
    return (
      <EmptyState
        titulo="Rutina no disponible"
        acciones={
          <EnlaceBoton a="/plan/" variante="primary">
            Volver al plan
          </EnlaceBoton>
        }
      >
        Esa rutina no es tuya o ya no existe.
      </EmptyState>
    );
  }
  if (consulta.error || !consulta.data) return <ErrorDePantalla onReintentar={consulta.refetch} />;
  return <Editor key={consulta.data.id} rutina={consulta.data} />;
}

function Editor({ rutina }: { rutina?: Rutina }) {
  const e = useEditorDeRutina(rutina);
  const busqueda = useBusquedaDeEjercicios();
  const { borrador, campos } = e;
  const anadidos = new Map(
    borrador.exercises.map((f) => [
      f.exercise,
      `${f.target_sets}×${f.target_reps_min}–${f.target_reps_max}`,
    ]),
  );

  return (
    <div className="routine-editor mx-auto max-w-3xl">
      <Cabecera
        titulo={e.rutinaId ? "Editar rutina" : "Nueva rutina"}
        hero="primary"
        descripcion="Tu entrenamiento, ejercicio a ejercicio."
      />

      <fieldset disabled={e.guardar.isPending || e.borrar.isPending} className="min-w-0 space-y-5">
        <div className="card">
          <Campo
            etiqueta="Nombre"
            placeholder="Ej. Empuje A"
            value={borrador.name}
            maxLength={120}
            onChange={(ev) => e.cambiar({ ...borrador, name: ev.target.value })}
            errores={campos["name"]}
          />
          <details open={borrador.description ? true : undefined}>
            <summary className="body-sm cursor-pointer py-2.5 text-primary">
              Descripción opcional
            </summary>
            <Campo
              etiqueta="Descripción"
              multilinea
              value={borrador.description}
              onChange={(ev) => e.cambiar({ ...borrador, description: ev.target.value })}
              errores={campos["description"]}
            />
          </details>
        </div>

        {e.dias.length > 0 && (
          <Aviso tono="informacion">
            Asignada a {e.dias.join(", ")}. Los cambios guardados se aplican a todos esos días.
          </Aviso>
        )}

        <ListaDelBorrador e={e} />

        {(e.errorLocal || e.guardar.error) && (
          <Aviso tono="error" urgente>
            {e.errorLocal ||
              (e.guardar.error instanceof ErrorDeApi
                ? e.guardar.error.message
                : "No se pudo guardar. Tus cambios siguen aquí.")}
            {campos["exercises"]?.join(" ")}
          </Aviso>
        )}
        <AvisoPasajero marca={e.exitoEn}>
          Rutina guardada. Ya puedes asignarla a tu semana o entrenar.
        </AvisoPasajero>

        <BarraDeAcciones>
          <span className="caption text-ink-muted" role="status">
            {e.guardar.isPending
              ? "Guardando…"
              : e.pendiente
                ? "Cambios sin guardar"
                : e.rutinaId
                  ? "Todo guardado"
                  : "Borrador · aún no guardado"}
          </span>
          <Button
            variante="primary"
            disabled={e.guardar.isPending || (!!e.rutinaId && !e.pendiente)}
            onClick={e.enviar}
          >
            {e.guardar.isPending ? "Guardando…" : e.rutinaId ? "Guardar cambios" : "Guardar rutina"}
          </Button>
          <EnlaceBoton a="/plan/" variante="ghost">
            {e.pendiente || !e.rutinaId ? "Cancelar" : "Volver al plan"}
          </EnlaceBoton>
        </BarraDeAcciones>

        {e.rutinaId && (
          <div className="card flex flex-wrap items-center gap-3">
            <Button
              variante="primary"
              disabled={e.pendiente || !borrador.exercises.length || e.empezar.isPending}
              onClick={e.entrenar}
            >
              <Icono nombre="entrenar" className="size-5" />
              Entrenar
            </Button>
            <EnlaceBoton a="/plan/">Asignar a la semana</EnlaceBoton>
            {e.pendiente && (
              <p className="caption w-full text-ink-muted">Guarda los cambios antes de entrenar.</p>
            )}
          </div>
        )}
        {e.empezar.error && (
          <Aviso tono="error">No se pudo empezar el entrenamiento. Inténtalo de nuevo.</Aviso>
        )}
        {e.rutinaId && (
          <button
            type="button"
            className="body-sm py-3 font-medium text-danger"
            onClick={() => e.setHoja("borrar")}
          >
            Eliminar rutina
          </button>
        )}
      </fieldset>

      {e.hoja === "buscar" && (
        <Panel
          titulo="Añadir ejercicio"
          onCerrar={() => e.setHoja(null)}
          accion={
            <Button variante="primary" tamano="sm" onClick={() => e.setHoja(null)}>
              {anadidos.size ? `Listo (${anadidos.size})` : "Listo"}
            </Button>
          }
        >
          <SelectorDeEjercicios busqueda={busqueda} onElegir={e.seleccionar} anadidos={anadidos} />
        </Panel>
      )}

      {e.hoja === "configurar" && e.elegido && (
        <Panel
          titulo={nombreDeEjercicio(e.elegido.exercise_detail.name)}
          onCerrar={e.cerrarFicha}
        >
          <Configuracion
            key={e.elegido.clave}
            fila={e.elegido}
            existente={borrador.exercises.some((f) => f.clave === e.elegido!.clave)}
            onAtras={() => e.setHoja("buscar")}
            onQuitar={() => e.quitar(e.elegido!.clave)}
            onConfirmar={e.aplicar}
          />
        </Panel>
      )}

      {e.hoja === "borrar" && (
        <Panel titulo="Eliminar rutina" onCerrar={() => e.setHoja(null)}>
          <p className="body">
            Se eliminará «{borrador.name}». Sus días pasarán a descanso. Los entrenamientos
            registrados se conservan.
          </p>
          {e.borrar.error && (
            <div className="mt-3">
              <Aviso tono="error">No se pudo eliminar la rutina.</Aviso>
            </div>
          )}
          <div className="form-actions">
            <Button variante="danger" disabled={e.borrar.isPending} onClick={e.eliminar}>
              Sí, eliminar rutina
            </Button>
            <Button onClick={() => e.setHoja(null)}>Cancelar</Button>
          </div>
        </Panel>
      )}
    </div>
  );
}
