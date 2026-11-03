#!/bin/sh
set -eu

ORIGEN="${1:-$(git rev-parse --abbrev-ref HEAD)}"
RAMA="deploy"

EXCLUIR='
^\.docs/
^\.claude/
^\.github/
^DESIGN/
^(AGENTS|CLAUDE|README)\.md$
^skills-lock\.json$
^\.env\.example$
^docker-compose\.yml$
^conftest\.py$
^pyproject\.toml$
^requirements-dev\.txt$
^scripts/(generar_iconos\.py|crear-rama-deploy\.sh)$
^apps/[^/]+/tests/
(^|/)LEEME\.md$
(^|/)\.gitkeep$
^frontend/e2e/
^frontend/playwright\.config\.ts$
^frontend/vitest\.setup\.ts$
^frontend/src/test/
\.test\.tsx?$
'

IMPRESCINDIBLES='
manage.py
requirements.txt
Procfile
railway.toml
railpack.json
nixpacks.toml
NOTICE.md
LICENSE
scripts/build-frontend.sh
scripts/start-web.sh
scripts/check_frontend.py
Dockerfile
.dockerignore
despliegue/casa/compose.yml
despliegue/casa/Caddyfile
despliegue/casa/env.ejemplo
scripts/casa.sh
scripts/casa_secretos.py
config/settings/prod.py
templates/spa.html
assets/app.css
frontend/package.json
frontend/package-lock.json
frontend/vite.config.ts
frontend/tsconfig.json
frontend/src/main.tsx
apps/workouts/bodymap/LICENSE
apps/workouts/bodymap/NOTICE
'

git rev-parse --verify --quiet "$ORIGEN^{commit}" >/dev/null || {
  echo "No existe la rama o el commit «$ORIGEN»." >&2
  exit 1
}
if [ "$(git rev-parse --abbrev-ref HEAD)" = "$RAMA" ]; then
  echo "Estás en la rama «$RAMA»: cámbiate a otra antes de regenerarla." >&2
  exit 1
fi
if [ -n "$(git status --porcelain --untracked-files=no)" ] && [ "$ORIGEN" = "$(git rev-parse --abbrev-ref HEAD)" ]; then
  echo "Aviso: hay cambios sin commitear en «$ORIGEN» y no entrarán en «$RAMA»." >&2
fi

DIR="$(mktemp -d)/$RAMA"
LISTA="$(mktemp)"
limpiar() {
  git worktree remove --force "$DIR" 2>/dev/null || true
  rmdir "$(dirname "$DIR")" 2>/dev/null || true
  rm -f "$LISTA"
}
trap limpiar EXIT

git worktree add --quiet --detach "$DIR" "$ORIGEN"

PATRON="$(printf '%s' "$EXCLUIR" | grep -v '^$' | paste -sd '|' -)"
git -C "$DIR" ls-files | grep -E "$PATRON" > "$LISTA" || true
if [ ! -s "$LISTA" ]; then
  echo "No había nada que quitar: ¿cambió la estructura del proyecto?" >&2
  exit 1
fi
git -C "$DIR" rm -q --pathspec-from-file="$LISTA"

FALTAN=""
for archivo in $IMPRESCINDIBLES; do
  [ -f "$DIR/$archivo" ] || FALTAN="$FALTAN $archivo"
done
if [ -n "$FALTAN" ]; then
  echo "La rama saldría sin archivos que el despliegue necesita:$FALTAN" >&2
  echo "Revisa la lista EXCLUIR de este script. No se ha commiteado nada." >&2
  exit 1
fi

QUITADOS="$(wc -l < "$LISTA" | tr -d ' ')"
QUEDAN="$(git -C "$DIR" ls-files | wc -l | tr -d ' ')"
BASE="$(git rev-parse --short "$ORIGEN")"
git -C "$DIR" commit -q -F - <<EOF
Rama deploy: solo lo que hace falta para desplegar

Generada con scripts/crear-rama-deploy.sh desde $ORIGEN ($BASE): quita $QUITADOS archivos de
documentación, bitácoras, tests y herramientas de desarrollo, y conserva $QUEDAN.
EOF
git branch -f "$RAMA" "$(git -C "$DIR" rev-parse HEAD)"

echo "Rama «$RAMA» regenerada desde $ORIGEN ($BASE): $QUEDAN archivos, $QUITADOS quitados."
echo "Para publicarla:  git push --force-with-lease origin $RAMA"
