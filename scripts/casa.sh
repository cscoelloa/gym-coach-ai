#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

export MSYS_NO_PATHCONV=1

ENTORNO=docker/.env
RESPALDOS=respaldos
CONSERVAR=14

compose() {
  docker compose -f docker/compose.yml --env-file "$ENTORNO" "$@"
}

exige_entorno() {
  if [ ! -f "$ENTORNO" ]; then
    echo "No existe $ENTORNO. Créalo con: sh scripts/casa.sh preparar <tu-pc>.<tailnet>.ts.net" >&2
    exit 1
  fi
}

orden="${1:-}"
[ $# -gt 0 ] && shift

case "$orden" in
  preparar)
    if [ $# -lt 1 ] || [ $# -gt 2 ]; then
      echo "Uso: sh scripts/casa.sh preparar <tu-pc>.<tailnet>.ts.net [correo-para-los-avisos]" >&2
      exit 2
    fi
    if [ -f "$ENTORNO" ]; then
      echo "$ENTORNO ya existe y no se sobrescribe. Si de verdad quieres empezar de cero, bórralo" >&2
      echo "a mano (y con él, el volumen de la base de datos: sh scripts/casa.sh parar -v)." >&2
      exit 1
    fi
    if ! docker build -t gym-casa:latest .; then
      echo "La imagen no se pudo construir. Si el error dice «certificate verify failed», un" >&2
      echo "antivirus está inspeccionando el HTTPS: sh scripts/casa.sh certificado, y repite." >&2
      exit 1
    fi
    umask 077
    if ! docker run --rm gym-casa:latest python scripts/casa_secretos.py "$@" > "$ENTORNO"; then
      rm -f "$ENTORNO"
      exit 1
    fi
    echo "Creado $ENTORNO. Guarda una copia fuera del PC: sin él no se descifran las claves de IA."
    if [ $# -lt 2 ]; then
      echo "Sin correo no hay avisos push. Para activarlos: sh scripts/casa.sh avisos <tu-correo>"
    fi
    echo "Siguiente: sh scripts/casa.sh subir"
    ;;

  avisos)
    exige_entorno
    if [ $# -ne 1 ]; then
      echo "Uso: sh scripts/casa.sh avisos <tu-correo>   (Apple rechaza correos de juguete)" >&2
      exit 2
    fi
    if grep -q '^VAPID_PUBLIC_KEY=.' "$ENTORNO"; then
      echo "El .env ya tiene claves VAPID. Cambiarlas invalida las suscripciones: no se tocan." >&2
      exit 1
    fi
    nuevas=$(docker run --rm gym-casa:latest python scripts/casa_secretos.py --vapid "$1")
    resto=$(grep -v '^VAPID_' "$ENTORNO" || true)
    printf '%s\n%s\n' "$resto" "$nuevas" > "$ENTORNO"
    echo "Avisos push activados en $ENTORNO. Aplícalo con: sh scripts/casa.sh subir"
    ;;

  certificado)
    cn="${1:-}"
    if [ -z "$cn" ]; then
      emisor=$(echo | openssl s_client -connect pypi.org:443 -servername pypi.org 2>/dev/null \
        | openssl x509 -noout -issuer -nameopt multiline 2>/dev/null \
        | sed -n 's/^ *commonName *= *//p')
      if [ -z "$emisor" ]; then
        echo "No se pudo leer el certificado de pypi.org. Pasa el nombre a mano:" >&2
        echo "  sh scripts/casa.sh certificado \"<CN de la raíz>\"" >&2
        exit 1
      fi
      echo "El certificado de pypi.org lo firma: $emisor"
      cn="$emisor"
    fi
    mkdir -p docker/certificados
    destino="docker/certificados/$(printf '%s' "$cn" | tr -c 'A-Za-z0-9._-' '_').crt"
    pem=$(CN_BUSCADO="$cn" powershell -NoProfile -Command '
      $c = Get-ChildItem Cert:\LocalMachine\Root, Cert:\CurrentUser\Root |
        Where-Object { $_.Subject -match ("CN=" + [regex]::Escape($env:CN_BUSCADO) + "(,|$)") } |
        Select-Object -First 1
      if ($c) {
        "-----BEGIN CERTIFICATE-----"
        [Convert]::ToBase64String($c.RawData, "InsertLineBreaks")
        "-----END CERTIFICATE-----"
      }
    ' | tr -d '\r')
    case "$pem" in
      "-----BEGIN CERTIFICATE-----"*) ;;
      *)
        echo "«$cn» no es una raíz del almacén de Windows: no hay nada que exportar." >&2
        echo "Si pypi.org lo firma una CA pública, no hay inspección de HTTPS y no hace falta." >&2
        exit 1
        ;;
    esac
    printf '%s\n' "$pem" > "$destino"
    echo "Exportado a $destino (ignorado por git). La imagen confiará en él."
    ;;

  subir)
    exige_entorno
    compose up -d --build --remove-orphans
    compose ps
    echo "Si es la primera vez: sh scripts/casa.sh catalogo && sh scripts/casa.sh admin"
    ;;

  parar)
    exige_entorno
    compose down "$@"
    ;;

  estado)
    exige_entorno
    compose ps
    ;;

  logs)
    exige_entorno
    compose logs --tail 200 -f "$@"
    ;;

  catalogo)
    exige_entorno
    if [ ! -d vendor/exercises-dataset ]; then
      echo "Falta vendor/exercises-dataset (ver el README)." >&2
      exit 1
    fi
    compose run --rm herramientas python manage.py import_catalog --source /datos
    compose run --rm herramientas python manage.py sync_metrics
    compose run --rm herramientas python manage.py seed_prompts
    ;;

  admin)
    exige_entorno
    compose run --rm herramientas python manage.py createsuperuser
    ;;

  respaldo)
    exige_entorno
    mkdir -p "$RESPALDOS"
    archivo="$RESPALDOS/gym-$(date +%Y%m%d-%H%M%S).sql.gz"
    compose exec -T db pg_dump -U gym -d gym --clean --if-exists --no-owner | gzip > "$archivo"
    if [ "$(gzip -dc "$archivo" | head -c 100 | wc -c)" -lt 100 ]; then
      rm -f "$archivo"
      echo "El respaldo salió vacío: ¿está arrancada la base de datos? (sh scripts/casa.sh estado)" >&2
      exit 1
    fi
    ls -1t "$RESPALDOS"/gym-*.sql.gz | tail -n +$((CONSERVAR + 1)) | while read -r viejo; do
      rm -f -- "$viejo"
    done
    echo "Respaldo en $archivo (se conservan los $CONSERVAR últimos)."
    ;;

  respaldo-media)
    exige_entorno
    mkdir -p "$RESPALDOS"
    archivo="$RESPALDOS/media-$(date +%Y%m%d-%H%M%S).tar.gz"
    compose exec -T web tar czf - -C /app media > "$archivo"
    ls -1t "$RESPALDOS"/media-*.tar.gz | tail -n +3 | while read -r viejo; do
      rm -f -- "$viejo"
    done
    echo "Imágenes y documentos en $archivo (se conservan los 2 últimos)."
    ;;

  restaurar)
    exige_entorno
    if [ $# -ne 1 ] || [ ! -f "$1" ]; then
      echo "Uso: sh scripts/casa.sh restaurar respaldos/gym-AAAAMMDD-HHMMSS.sql.gz" >&2
      exit 2
    fi
    echo "Esto SUSTITUYE todos los datos actuales por los de $1."
    printf "Escribe RESTAURAR para seguir: "
    read -r confirmacion
    if [ "$confirmacion" != "RESTAURAR" ]; then
      echo "Cancelado."
      exit 1
    fi
    compose stop web worker beat caddy
    gzip -dc "$1" | compose exec -T db psql -U gym -d gym -v ON_ERROR_STOP=1 --quiet -o /dev/null
    compose up -d
    echo "Restaurado. Si el respaldo es de otro .env, vuelve a poner la clave de IA en Gestión → IA."
    ;;

  *)
    cat <<'USO'
La aplicación en tu PC, detrás de Tailscale. Se ejecuta desde Git Bash.

  sh scripts/casa.sh preparar <tu-pc>.<tailnet>.ts.net [correo]   crea docker/.env
  sh scripts/casa.sh certificado [CN]  exporta la raíz de un antivirus que inspecciona HTTPS
  sh scripts/casa.sh avisos <correo>   activa el aviso push (añade las claves VAPID al .env)
  sh scripts/casa.sh subir             construye y arranca (también para actualizar)
  sh scripts/casa.sh catalogo          importa el catálogo, las métricas y los prompts
  sh scripts/casa.sh admin             crea tu cuenta de administrador
  sh scripts/casa.sh estado | logs [servicio] | parar
  sh scripts/casa.sh respaldo          copia de la base de datos en respaldos/
  sh scripts/casa.sh respaldo-media    copia de las imágenes y documentos subidos
  sh scripts/casa.sh restaurar <respaldos/gym-….sql.gz>

Los pasos de Tailscale y de Windows están en el README, sección «Despliegue».
USO
    exit 2
    ;;
esac
