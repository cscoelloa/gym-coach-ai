import { Link } from "react-router";

import { Icono } from "@/ds/Icono";

import type { RutinaEnBiblioteca } from "./api";

function Portada({ imagenes }: { imagenes: string[] }) {
  if (!imagenes.length) {
    return (
      <div className="rutina-portada rutina-portada-vacia" aria-hidden="true">
        <Icono nombre="entrenar" className="size-7" />
      </div>
    );
  }
  return (
    <div className="rutina-portada" aria-hidden="true">
      {imagenes.slice(0, 4).map((src, i) => (
        <img key={i} src={src} alt="" loading="lazy" />
      ))}
    </div>
  );
}

export function TarjetaDeRutina({ rutina }: { rutina: RutinaEnBiblioteca }) {
  return (
    <Link to={`/rutinas/${rutina.id}/`} className="rutina-card hover:no-underline">
      <Portada imagenes={rutina.imagenes} />
      <div className="min-w-0 p-3">
        <h3 className="title-sm truncate text-ink">{rutina.nombre}</h3>
        <p className="caption mt-0.5 text-ink-muted">
          {rutina.n_ejercicios} ejercicio{rutina.n_ejercicios !== 1 ? "s" : ""} ·{" "}
          {rutina.dias.length ? rutina.dias.join(", ") : "sin asignar"}
        </p>
      </div>
    </Link>
  );
}
