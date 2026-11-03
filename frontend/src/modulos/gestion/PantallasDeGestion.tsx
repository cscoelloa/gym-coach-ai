import { Auditoria } from "./Auditoria";
import { CatalogoYMetricas } from "./CatalogoYMetricas";
import { GestionDeIa } from "./ia/GestionDeIa";
import { MarcoDeGestion } from "./MarcoDeGestion";
import { ResumenDeGestion } from "./ResumenDeGestion";
import { Usuarios } from "./Usuarios";

export function Resumen() {
  return (
    <MarcoDeGestion>
      <ResumenDeGestion />
    </MarcoDeGestion>
  );
}

export function Ia() {
  return (
    <MarcoDeGestion>
      <GestionDeIa />
    </MarcoDeGestion>
  );
}

export function Generaciones() {
  return (
    <MarcoDeGestion>
      <Auditoria />
    </MarcoDeGestion>
  );
}

export function Cuentas() {
  return (
    <MarcoDeGestion>
      <Usuarios />
    </MarcoDeGestion>
  );
}

export function Catalogo() {
  return (
    <MarcoDeGestion>
      <CatalogoYMetricas />
    </MarcoDeGestion>
  );
}
