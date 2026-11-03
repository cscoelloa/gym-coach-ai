export function Desplegable({
  etiqueta,
  valor,
  opciones,
  onCambio,
  ayuda,
}: {
  etiqueta: string;
  valor: string;
  opciones: { valor: string; etiqueta: string }[];
  onCambio: (valor: string) => void;
  ayuda?: string;
}) {
  const id = `sel-${etiqueta.replace(/\s+/g, "-").toLowerCase()}`;
  return (
    <div className="field">
      <label htmlFor={id}>{etiqueta}</label>
      <select id={id} value={valor} onChange={(evento) => onCambio(evento.target.value)}>
        {opciones.map((opcion) => (
          <option key={opcion.valor} value={opcion.valor}>
            {opcion.etiqueta}
          </option>
        ))}
      </select>
      {ayuda && <span className="helptext">{ayuda}</span>}
    </div>
  );
}
