#!/usr/bin/env bash
# backup_volumes.sh - snapshot de volumes Docker a ~/DanielaBackups/.
#
# Uso:
#   ./scripts/deploy/backup_volumes.sh --list      # que hay
#   ./scripts/deploy/backup_volumes.sh --dry-run   # que haria
#   ./scripts/deploy/backup_volumes.sh             # lo hace
#
# Cubre los volumes de los composes (aig_* + aig_* legacy).
# Restaura con: docker run --rm -v VOL:/dst -v ~/DanielaBackups:/src \
#   alpine tar xzf /src/<fichero> -C /dst
set -u
# Sin esto, Git bash reescribe /c/... a C:\... al llamar a docker.exe y el
# mount -v se parte por el ':' (medido 2026-09-23: tar escribia en
# 'C:/Program Files/Git/dst/').
export MSYS_NO_PATHCONV=1
BACKUP_DIR="${BACKUP_DIR:-$HOME/DanielaBackups/volumes}"
STAMP="$(date +%Y%m%d_%H%M%S)"

vols="$(docker volume ls --format '{{.Name}}' | grep -E 'redis|grafana|prometheus' || true)"
if [ -z "$vols" ]; then
  echo "sin volumes coincidentes"; exit 0
fi

case "${1:---go}" in
  --list) echo "$vols"; exit 0 ;;
  --dry-run) modo=DRY ;;
  *) modo=GO ;;
esac

mkdir -p "$BACKUP_DIR"
for v in $vols; do
  dest="$BACKUP_DIR/vol-${v}-${STAMP}.tgz"
  if [ "$modo" = DRY ]; then
    echo "DRY-RUN: $v -> $dest"
  else
    docker run --rm -v "$v:/src:ro" -v "$BACKUP_DIR:/dst" \
      alpine tar czf "/dst/$(basename "$dest")" -C /src . \
      && echo "OK: $dest"
  fi
done

# Retencion: ultimos 3 por volumen (un backup completo pesa ~120MB).
if [ "$modo" != DRY ]; then
  for v in $vols; do
    # shellcheck disable=SC2012
    ls -t "$BACKUP_DIR"/vol-"${v}"-*.tgz 2>/dev/null | tail -n +4 | xargs -r rm -f
  done
  echo "retencion: 3 por volumen"
fi
