import { Button } from "./Button";

export function Paginacion({
  pagina,
  total,
  hayAnterior,
  haySiguiente,
  ocupado = false,
  onCambio,
}: {
  pagina: number;
  total?: number;
  hayAnterior: boolean;
  haySiguiente: boolean;
  ocupado?: boolean;
  onCambio: (pagina: number) => void;
}) {
  if (!hayAnterior && !haySiguiente) return null;

  return (
    <nav className="mt-4 flex items-center justify-center gap-3" aria-label="Paginación">
      <Button
        variante="secondary"
        tamano="sm"
        disabled={!hayAnterior || ocupado}
        onClick={() => onCambio(pagina - 1)}
      >
        Anterior
      </Button>
      <span className="metric-sm whitespace-nowrap text-ink-muted">
        <span className="max-[22.49rem]:sr-only">Página </span>
        {total ? `${pagina} de ${total}` : pagina}
      </span>
      <Button
        variante="secondary"
        tamano="sm"
        disabled={!haySiguiente || ocupado}
        onClick={() => onCambio(pagina + 1)}
      >
        Siguiente
      </Button>
    </nav>
  );
}
