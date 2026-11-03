export function Placa({ className = "" }: { className?: string }) {
  return (
    <span className={`brand-mark ${className}`.trim()} aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        className="size-[62%]"
        fill="none"
        stroke="currentColor"
        strokeWidth={2.4}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M6.5 6.5v11M17.5 6.5v11M3 9.5v5M21 9.5v5M6.5 12h11" />
      </svg>
    </span>
  );
}

export function Marca() {
  return (
    <>
      <Placa />
      <span className="brand-name title-sm text-ink">
        Project<span className="text-primary">/Gym</span>
      </span>
    </>
  );
}
