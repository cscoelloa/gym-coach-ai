import type { VarianteDeBoton } from "./Button";
import { Button } from "./Button";
import { Panel } from "./Panel";

export function Confirmacion({
  titulo,
  mensaje,
  confirmar = "Sí, continuar",
  cancelar = "Cancelar",
  variante = "danger",
  onConfirmar,
  onCancelar,
}: {
  titulo: string;
  mensaje: string;
  confirmar?: string;
  cancelar?: string;
  variante?: VarianteDeBoton;
  onConfirmar: () => void;
  onCancelar: () => void;
}) {
  return (
    <Panel titulo={titulo} onCerrar={onCancelar}>
      <p>{mensaje}</p>
      <div className="form-actions">
        <Button variante={variante} onClick={onConfirmar}>
          {confirmar}
        </Button>
        <Button onClick={onCancelar}>
          {cancelar}
        </Button>
      </div>
    </Panel>
  );
}
