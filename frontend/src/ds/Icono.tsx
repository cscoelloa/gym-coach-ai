export const TRAZADOS = {
  luna: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />,
  sol: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </>
  ),
  mas: <path d="M12 5v14M5 12h14" />,
  chevronIzquierda: <path d="m15 18-6-6 6-6" />,
  chevronDerecha: <path d="m9 18 6-6-6-6" />,
  chevronArriba: <path d="m18 15-6-6-6 6" />,
  chevronAbajo: <path d="m6 9 6 6 6-6" />,
  comprobado: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.5 2.5 2.5 4.5-5" />
    </>
  ),
  error: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m15 9-6 6M9 9l6 6" />
    </>
  ),
  aviso: (
    <>
      <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4M12 17h.01" />
    </>
  ),
  informacion: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </>
  ),

  inicio: (
    <>
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V21h14V9.5" />
    </>
  ),
  plan: (
    <>
      <rect x="3" y="4" width="18" height="17" rx="2" />
      <path d="M3 9h18M8 2v4M16 2v4" />
    </>
  ),
  entrenar: <path d="M6.5 6.5v11M17.5 6.5v11M3 9.5v5M21 9.5v5M6.5 12h11" />,
  progreso: <path d="M5 21V10M12 21V4M19 21v-7" />,
  ejercicios: <path d="M4 6h16M4 12h16M4 18h16" />,

  barra: <path d="M3 9v6M6 7v10M18 7v10M21 9v6M6 12h12" />,
  zancada: <path d="M12 4v7M7 20l5-9 5 9" />,
  mancuerna: <path d="M4 12h16M7 8v8M17 8v8" />,
  lupa: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </>
  ),

  campana: (
    <>
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.7 21a2 2 0 0 1-3.4 0" />
    </>
  ),
  persona: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
  escudo: <path d="M12 2 4 6v6c0 5 3.4 9.4 8 10 4.6-.6 8-5 8-10V6Z" />,
  salir: (
    <>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <path d="m16 17 5-5-5-5M21 12H9" />
    </>
  ),
  sistema: (
    <>
      <rect x="6" y="2.5" width="12" height="19" rx="2.5" />
      <path d="M10.5 18.5h3" />
    </>
  ),
  cerrar: <path d="M18 6 6 18M6 6l12 12" />,
  pausa: <path d="M9 5v14M15 5v14" />,
  fuego: (
    <path d="M12 22c3.9 0 7-2.6 7-6.6 0-3.2-2-5.6-3.6-7.4-.4 1.6-1.4 2.7-2.6 3.2C13 7.6 11.6 4.4 9 2c0 3.8-4 6.4-4 11.4C5 19.2 8.1 22 12 22Z" />
  ),
  trofeo: (
    <>
      <path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0Z" />
      <path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3" />
    </>
  ),
  reloj: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  bascula: (
    <>
      <rect x="3.5" y="3.5" width="17" height="17" rx="4" />
      <path d="M8.5 10a5 5 0 0 1 7 0M12 10l1.3-1.6" />
    </>
  ),
  rayo: <path d="M13 2 4 14h7l-1 8 9-12h-7Z" />,
  diana: (
    <>
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="5" />
      <circle cx="12" cy="12" r="1" />
    </>
  ),
  reproducir: <path d="M7 4.5v15l12-7.5Z" />,
  pantallaEncendida: (
    <>
      <rect x="7" y="2.5" width="10" height="19" rx="2.5" />
      <path d="M11 18.5h2M3.5 9v6M20.5 9v6" />
    </>
  ),

  compartir: (
    <>
      <path d="M12 3v12M8 7l4-4 4 4" />
      <path d="M8 10H6a1 1 0 0 0-1 1v9a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-9a1 1 0 0 0-1-1h-2" />
    </>
  ),
  instalar: (
    <>
      <path d="M12 3v12M7 10l5 5 5-5" />
      <path d="M5 21h14" />
    </>
  ),
  sinConexion: (
    <>
      <path d="M2 8.8a15 15 0 0 1 4.2-2.6M9.6 5.2A15 15 0 0 1 22 8.8M5 12.6a10 10 0 0 1 3.4-2M14 10.3a10 10 0 0 1 5 2.3M8.5 16.4a5 5 0 0 1 7 0M12 20h.01" />
      <path d="m3 3 18 18" />
    </>
  ),
  recargar: (
    <>
      <path d="M21 12a9 9 0 1 1-2.6-6.4L21 8" />
      <path d="M21 3v5h-5" />
    </>
  ),
} as const;

export type NombreDeIcono = keyof typeof TRAZADOS;

type Props = {
  nombre: NombreDeIcono;
  className?: string;
};

export function Icono({ nombre, className = "size-5" }: Props) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {TRAZADOS[nombre]}
    </svg>
  );
}
