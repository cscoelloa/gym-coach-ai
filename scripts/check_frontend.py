import json
import sys
from pathlib import Path


def verificar(dist: Path) -> None:
    manifiesto = json.loads((dist / ".vite" / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(manifiesto, dict) or "src/main.tsx" not in manifiesto:
        raise ValueError("El manifiesto no contiene src/main.tsx.")
    for entrada in manifiesto.values():
        archivos = [entrada["file"], *entrada.get("css", []), *entrada.get("assets", [])]
        for archivo in archivos:
            ruta = (dist / archivo).resolve()
            if not ruta.is_relative_to(dist.resolve()) or not ruta.is_file():
                raise ValueError(f"Falta un archivo del frontend: {archivo}")
        for referencia in [*entrada.get("imports", []), *entrada.get("dynamicImports", [])]:
            if referencia not in manifiesto:
                raise ValueError(f"Falta una entrada del manifiesto: {referencia}")


if __name__ == "__main__":
    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    try:
        verificar(dist)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(
            f"Frontend incompleto: {error}\n"
            "Construye la imagen con `sh scripts/build-frontend.sh` desde la raíz del repo. "
            "En Railway usa railway.toml y railpack.json; nixpacks.toml solo aplica a Nixpacks.",
            file=sys.stderr,
        )
        sys.exit(1)
    print("Frontend verificado: manifiesto y archivos de Vite presentes.")
