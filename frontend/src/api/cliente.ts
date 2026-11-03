export type ErroresPorCampo = Record<string, string[]>;

export class ErrorDeApi extends Error {
  readonly estado: number;
  readonly porCampo: ErroresPorCampo;
  readonly codigo: string | null;

  constructor(
    estado: number,
    mensaje: string,
    porCampo: ErroresPorCampo = {},
    codigo: string | null = null,
  ) {
    super(mensaje);
    this.name = "ErrorDeApi";
    this.estado = estado;
    this.porCampo = porCampo;
    this.codigo = codigo;
  }

  get esSinSesion(): boolean {
    return this.estado === 401;
  }
}

function leerCookie(nombre: string): string {
  const encontrada = document.cookie
    .split("; ")
    .find((trozo) => trozo.startsWith(`${nombre}=`));
  return encontrada ? decodeURIComponent(encontrada.slice(nombre.length + 1)) : "";
}

const SIN_CUERPO = new Set(["GET", "HEAD"]);

type Opciones = {
  metodo?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  cuerpo?: unknown;
  signal?: AbortSignal;
};

function traducirError(estado: number, cuerpo: unknown): ErrorDeApi {
  if (typeof cuerpo === "object" && cuerpo !== null) {
    const datos = cuerpo as Record<string, unknown>;
    const codigo = typeof datos["codigo"] === "string" ? datos["codigo"] : null;

    if (typeof datos["detail"] === "string") {
      return new ErrorDeApi(estado, datos["detail"], {}, codigo);
    }

    const porCampo: ErroresPorCampo = {};
    function recoger(valor: unknown, campo: string) {
      if (Array.isArray(valor) && valor.every((item) => typeof item === "string")) {
        porCampo[campo] = valor;
      } else if (typeof valor === "object" && valor !== null) {
        for (const [clave, hijo] of Object.entries(valor)) recoger(hijo, `${campo}.${clave}`);
      } else porCampo[campo] = [String(valor)];
    }
    for (const [campo, valor] of Object.entries(datos)) recoger(valor, campo);

    const generales = porCampo["non_field_errors"] ?? porCampo["detail"];
    const mensaje = generales?.[0] ?? "No se ha podido completar la operación.";
    return new ErrorDeApi(estado, mensaje, porCampo, codigo);
  }

  return new ErrorDeApi(estado, "No se ha podido completar la operación.");
}

export async function api<T = unknown>(camino: string, opciones: Opciones = {}): Promise<T> {
  const metodo = opciones.metodo ?? "GET";
  const esFormulario = opciones.cuerpo instanceof FormData;

  const cabeceras: Record<string, string> = {};
  if (!SIN_CUERPO.has(metodo)) {
    if (!esFormulario) cabeceras["Content-Type"] = "application/json";
    cabeceras["X-CSRFToken"] = leerCookie("csrftoken");
  }

  let respuesta: Response;
  try {
    respuesta = await fetch(camino, {
      method: metodo,
      headers: cabeceras,
      credentials: "same-origin",
      body:
        opciones.cuerpo === undefined
          ? undefined
          : esFormulario
            ? (opciones.cuerpo as FormData)
            : JSON.stringify(opciones.cuerpo),
      signal: opciones.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ErrorDeApi(0, "No hay conexión con el servidor.");
  }

  if (respuesta.status === 204) return undefined as T;

  const esJson = respuesta.headers.get("content-type")?.includes("application/json");
  const cuerpo = esJson ? await respuesta.json() : await respuesta.text();

  if (!respuesta.ok) throw traducirError(respuesta.status, cuerpo);

  return cuerpo as T;
}
