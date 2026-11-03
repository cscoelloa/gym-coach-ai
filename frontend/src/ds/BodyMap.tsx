import { useMapaCorporal, type RegionDelMapa } from "@/api/mapaCorporal";

export type NivelesPorMusculo = Record<string, number>;

export function BodyMap({
  niveles,
  activo,
  onMusculo,
  leyenda,
  compacto = false,
}: {
  niveles: NivelesPorMusculo;
  activo?: string;
  onMusculo?: (musculo: string) => void;
  leyenda?: string;
  compacto?: boolean;
}) {
  const { data: mapa, isPending } = useMapaCorporal();

  if (isPending || !mapa) {
    return <div className={compacto ? "h-40" : "h-64"} aria-busy="true" />;
  }

  const clase = (region: RegionDelMapa) => {
    if (region.musculo === null) return "bm-inert";
    if (region.musculo === activo) return "bm-on";
    return `bm-${niveles[region.musculo] ?? 0}`;
  };

  return (
    <div>
      <div
        className={`mx-auto grid grid-cols-2 gap-2 ${compacto ? "max-w-[13rem]" : "max-w-sm"}`}
      >
        {mapa.vistas.map((vista) => (
          <figure className="m-0" key={vista.nombre}>
            <svg
              className="body-map"
              viewBox={vista.viewbox}
              role="img"
              aria-label={`Musculatura, vista ${
                vista.nombre === "front" ? "frontal" : "dorsal"
              }`}
            >
              {vista.regiones.map((region) => {
                const trazado = (
                  <path
                    className={clase(region)}
                    d={region.d}
                    aria-hidden={region.musculo === null || undefined}
                  >
                    {region.musculo !== null && <title>{region.etiqueta}</title>}
                  </path>
                );

                if (!onMusculo || region.musculo === null) {
                  return <g key={region.id}>{trazado}</g>;
                }

                const musculo = region.musculo;
                return (
                  <g
                    key={region.id}
                    className="bm-hit"
                    role="button"
                    tabIndex={0}
                    aria-label={`Filtrar por ${region.etiqueta}`}
                    aria-pressed={musculo === activo}
                    onClick={() => onMusculo(musculo)}
                    onKeyDown={(evento) => {
                      if (evento.key === "Enter" || evento.key === " ") {
                        evento.preventDefault();
                        onMusculo(musculo);
                      }
                    }}
                  >
                    {trazado}
                  </g>
                );
              })}
            </svg>
            <figcaption className="tag mt-1 text-center text-ink-subtle">{vista.titulo}</figcaption>
          </figure>
        ))}
      </div>

      {leyenda && <p className="caption mt-3 text-center text-ink-muted">{leyenda}</p>}
    </div>
  );
}
