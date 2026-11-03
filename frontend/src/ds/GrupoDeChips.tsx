import { Chip, FilaDeChips } from "./Chip";

export type Opcion = { valor: string; etiqueta: string; n: number };

export function GrupoDeChips({
  titulo,
  opciones,
  activo,
  onElegir,
}: {
  titulo: string;
  opciones: Opcion[];
  activo: string;
  onElegir: (valor: string) => void;
}) {
  if (!opciones.length) return null;

  return (
    <>
      <p className="section-kicker">{titulo}</p>
      <FilaDeChips>
        {opciones.map((opcion) => (
          <Chip
            key={opcion.valor}
            activo={opcion.valor === activo}
            recuento={opcion.n}
            onClick={() => onElegir(opcion.valor === activo ? "" : opcion.valor)}
          >
            {opcion.etiqueta}
          </Chip>
        ))}
      </FilaDeChips>
    </>
  );
}
