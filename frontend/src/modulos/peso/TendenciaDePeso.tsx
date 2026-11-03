import { Badge } from "@/ds/Badge";
import { Card } from "@/ds/Card";
import { GraficaDePeso } from "@/ds/GraficaDePeso";

import type { ResumenDePeso } from "./api";

export function TendenciaDePeso({
  serie,
  ultimo,
}: {
  serie: ResumenDePeso["serie"];
  ultimo: ResumenDePeso["ultimo"];
}) {
  return (
    <Card>
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="section-kicker">Lectura visual</p>
          <h2 className="title-lg">Tendencia</h2>
        </div>
        {ultimo && <Badge tono="info">{ultimo.weight_kg} kg</Badge>}
      </div>

      {serie ? (
        <GraficaDePeso serie={serie} />
      ) : (
        <p className="empty-hint">Registra tu peso unos días y aquí verás la tendencia.</p>
      )}
    </Card>
  );
}
