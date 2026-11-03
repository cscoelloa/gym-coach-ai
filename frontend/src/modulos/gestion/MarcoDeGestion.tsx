import type { ReactNode } from "react";
import { NavLink } from "react-router";

const SECCIONES = [
  { a: "/gestion/", etiqueta: "Resumen", exacto: true },
  { a: "/gestion/ia/", etiqueta: "IA" },
  { a: "/gestion/generaciones/", etiqueta: "Auditoría" },
  { a: "/gestion/usuarios/", etiqueta: "Usuarios" },
  { a: "/gestion/catalogo/", etiqueta: "Catálogo" },
];

export function MarcoDeGestion({ children }: { children: ReactNode }) {
  return (
    <div className="mb-6">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="badge badge-neutral">Gestión</span>
        <p className="body-sm text-ink-muted">Configuración y auditoría. Solo para el equipo.</p>
      </div>

      <nav className="chip-row mb-6" aria-label="Secciones de gestión">
        {SECCIONES.map((seccion) => (
          <NavLink
            className={({ isActive }) => `chip ${isActive ? "chip-on" : ""}`.trim()}
            end={seccion.exacto}
            key={seccion.a}
            to={seccion.a}
          >
            {seccion.etiqueta}
          </NavLink>
        ))}
      </nav>

      {children}
    </div>
  );
}
