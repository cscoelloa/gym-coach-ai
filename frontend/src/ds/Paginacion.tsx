import { Button } from "./Button";

export function Paginacion({
  pagina,
  hayAnterior,
  haySiguiente,
  onCambio,
}: {
  pagina: number;
  hayAnterior: boolean;
  haySiguiente: boolean;
  onCambio: (pagina: number) => void;
}) {
  if (!hayAnterior && !haySiguiente) return null;

  return (
    <nav className="mt-4 flex items-center justify-center gap-3" aria-label="Paginación">
      <Button
        variante="secondary"
        tamano="sm"
        disabled={!hayAnterior}
        onClick={() => onCambio(pagina - 1)}
      >
        Anterior
      </Button>
      <span className="metric-sm text-ink-muted">Página {pagina}</span>
      <Button
        variante="secondary"
        tamano="sm"
        disabled={!haySiguiente}
        onClick={() => onCambio(pagina + 1)}
      >
        Siguiente
      </Button>
    </nav>
  );
}
