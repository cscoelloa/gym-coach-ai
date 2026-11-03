import { useId, type InputHTMLAttributes } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "id"> & {
  etiqueta: string;
  ayuda?: string;
  errores?: string[];
  multilinea?: boolean;
  filas?: number;
};

export function Campo({
  etiqueta,
  ayuda,
  errores,
  multilinea = false,
  filas = 3,
  className = "",
  ...resto
}: Props) {
  const id = useId();
  const idAyuda = `${id}-ayuda`;
  const idError = `${id}-error`;
  const tieneError = Boolean(errores?.length);

  const descrito = [tieneError ? idError : null, ayuda ? idAyuda : null]
    .filter(Boolean)
    .join(" ");

  const comunes = {
    id,
    className: `${className} ${tieneError ? "border-danger" : ""}`.trim(),
    "aria-invalid": tieneError || undefined,
    "aria-describedby": descrito || undefined,
  };

  return (
    <div className="field">
      <label htmlFor={id}>{etiqueta}</label>
      {multilinea ? (
        <textarea
          {...comunes}
          rows={filas}
          {...(resto as React.TextareaHTMLAttributes<HTMLTextAreaElement>)}
        />
      ) : (
        <input {...comunes} {...resto} />
      )}
      {ayuda && (
        <span className="helptext" id={idAyuda}>
          {ayuda}
        </span>
      )}
      {tieneError && (
        <p className="errorlist" id={idError}>
          {errores!.join(" ")}
        </p>
      )}
    </div>
  );
}
