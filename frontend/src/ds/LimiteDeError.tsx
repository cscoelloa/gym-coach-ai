import { Component, type ErrorInfo, type ReactNode } from "react";

export class LimiteDeError extends Component<
  { children: ReactNode },
  { fallo: Error | null }
> {
  state: { fallo: Error | null } = { fallo: null };

  static getDerivedStateFromError(fallo: Error) {
    return { fallo };
  }

  componentDidCatch(fallo: Error, info: ErrorInfo) {
    console.error("Fallo al pintar la pantalla:", fallo, info.componentStack);
  }

  render() {
    if (!this.state.fallo) return this.props.children;

    return (
      <main className="px-4 py-6 sm:px-6 sm:py-8">
        <div className="mx-auto max-w-md">
          <div className="empty-state">
            <span className="empty-title">Algo se ha roto en esta pantalla</span>
            <p>
              No se ha perdido nada de lo que tengas guardado. Si acaba de haber una actualización,
              recargar suele bastar.
            </p>
            <button
              className="btn btn-primary btn-sm"
              type="button"
              onClick={() => window.location.reload()}
            >
              Recargar
            </button>
          </div>
        </div>
      </main>
    );
  }
}
