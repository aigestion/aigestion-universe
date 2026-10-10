#!/system/bin/sh
# ==========================================================================
#  optimizar_telefono.sh — DanielaOS · Auditoria y optimizacion del Pixel
# ==========================================================================
#  REGLA DE SEGURIDAD: este script NUNCA borra. Todo lo que "limpia" lo
#  MUEVE a /sdcard/DanielaOS/.papelera/<categoria>/ para que puedas
#  recuperarlo. Solo cuando tu lo decidas se vacia esa papelera.
#
#  Uso (dentro de Termux o `adb shell`):
#     sh optimizar_telefono.sh              -> informe + simulacro (no toca nada)
#     sh optimizar_telefono.sh --nivel1     -> duplicados exactos + caches
#     sh optimizar_telefono.sh --nivel2     -> + modelos demo y videos viejos
#     sh optimizar_telefono.sh --nivel3     -> + decisiones de modelos LLM
#     sh optimizar_telefono.sh --todo       -> nivel1 + nivel2
#     sh optimizar_telefono.sh --restaurar  -> devuelve todo desde la papelera
# ==========================================================================

R=/storage/emulated/0
P=$R/DanielaOS/.papelera
OUT=$R/DanielaOS/audit
mkdir -p "$OUT" 2>/dev/null
LOG=$OUT/optimizacion.log

MODO=simular
case "$1" in
  --nivel1) MODO=n1 ;;
  --nivel2) MODO=n2 ;;
  --nivel3) MODO=n3 ;;
  --todo)   MODO=todo ;;
  --restaurar) MODO=restaurar ;;
esac

TOTAL=0
MOVIDOS=0

# ---------------------------------------------------------------- utilidades
# OJO: el shell de Android hace aritmetica de 32 bits con signo, asi que un
# total en BYTES desborda a partir de 2 GB. Todo el script acumula en KB.
humano() {   # kibibytes -> texto legible
  k=$1
  if [ "$k" -ge 1048576 ]; then
    echo "$(( k / 1048576 )).$(( (k % 1048576) / 104857 )) GB"
  elif [ "$k" -ge 1024 ]; then
    echo "$(( k / 1024 )).$(( (k % 1024) / 102 )) MB"
  else
    echo "$k KB"
  fi
}

# mover_a_papelera <ruta> <categoria> [md5_esperado]
#   Si se pasa md5_esperado, SOLO mueve si coincide. Asi un duplicado
#   "por tamaño" que en realidad sea otro archivo nunca se pierde.
mover_a_papelera() {
  f="$1"; cat="$2"; esperado="$3"
  [ -f "$f" ] || { echo "  - omite (no existe): $f"; return 0; }

  if [ -n "$esperado" ]; then
    real=$(md5sum "$f" 2>/dev/null | cut -d' ' -f1)
    if [ "$real" != "$esperado" ]; then
      echo "  ! ABORTADO: md5 no coincide en $f"
      echo "    esperado=$esperado real=$real  -> no se toca"
      return 0
    fi
  fi

  sz=$(stat -c '%s' "$f" 2>/dev/null || echo 0)
  szk=$(( sz / 1024 ))
  echo "  + $(humano $szk)  $f"

  if [ "$MODO" = simular ]; then
    TOTAL=$((TOTAL + szk)); MOVIDOS=$((MOVIDOS + 1)); return 0
  fi

  mkdir -p "$P/$cat" 2>/dev/null
  if mv "$f" "$P/$cat/" 2>/dev/null; then
    TOTAL=$((TOTAL + szk)); MOVIDOS=$((MOVIDOS + 1))
    echo "$(date '+%F %T') MOVIDO $sz $f -> $P/$cat/" >> "$LOG"
  else
    echo "  ! no se pudo mover: $f"
  fi
}

echo "=================================================================="
echo " OPTIMIZADOR DANIELAOS — $(date '+%F %T')"
echo " modo: $MODO"
echo " papelera: $P   (nada se borra, todo se mueve)"
echo "=================================================================="

# ------------------------------------------------------------- RESTAURAR
if [ "$MODO" = restaurar ]; then
  if [ ! -d "$P" ]; then echo "No hay papelera. Nada que restaurar."; exit 0; fi
  n=0
  for f in $(find "$P" -type f 2>/dev/null); do
    orig=$(grep -F "$(basename "$f")" "$LOG" 2>/dev/null | tail -1 | awk '{print $4}')
    if [ -n "$orig" ]; then
      mkdir -p "$(dirname "$orig")" 2>/dev/null
      mv "$f" "$orig" 2>/dev/null && { echo "  restaurado: $orig"; n=$((n+1)); }
    else
      echo "  sin ruta original registrada: $f"
    fi
  done
  echo "Restaurados: $n"
  exit 0
fi

# =========================== NIVEL 1 =====================================
# Duplicados exactos (md5 verificado) + caches regenerables + basura
echo
echo "--- NIVEL 1: duplicados exactos, caches y basura -------------------"

# 1) Duplicado EXACTO de 1.5 GB (md5 identico a gemma_soberano.bin)
mover_a_papelera "$R/Documents/NexusAI/gemma2-2b.bin" duplicados \
  814d0dc106a099f581ffad0fad0218c0

# 2) Caches de Google AI Edge Gallery (se regeneran solos al abrir la app)
G=$R/Android/data/com.google.ai.edge.gallery/files
for c in \
  "$G/Gemma_4_E2B_it/6e5c4f1e395deb959c494953478fa5cec4b8008f/gemma-4-E2B-it.litertlm_1778889714_2588147712_mldrift_weight_cache.bin" \
  "$G/Gemma_4_E2B_it/6e5c4f1e395deb959c494953478fa5cec4b8008f/gemma-4-E2B-it.litertlm.vision_encoder_1778889714_2588147712_mldrift_weight_cache.bin" \
  "$G/Gemma_4_E2B_it/6e5c4f1e395deb959c494953478fa5cec4b8008f/gemma-4-E2B-it.litertlm_1778889714_2588147712.static_audio_encoder.xnnpack_cache" \
  "$G/Gemma_4_E2B_it/6e5c4f1e395deb959c494953478fa5cec4b8008f/gemma-4-E2B-it.litertlm_1778889714_2588147712_mldrift_program_cache.bin" \
  "$G/Gemma_4_E2B_it/6e5c4f1e395deb959c494953478fa5cec4b8008f/gemma-4-E2B-it.litertlm_1778889714_2588147712.audio_adapter.xnnpack_cache" \
  "$G/TinyGarden_270M/20260225/tiny_garden.litertlm.xnnpack_cache_1778890677_288964608" \
  "$G/MobileActions_270M/20260218/mobile_actions.litertlm.xnnpack_cache_1775661562_288964608"
do
  mover_a_papelera "$c" caches
done

# 3) Duplicado EXACTO de imagen generada (md5 identico al otro PNG)
mover_a_papelera "$R/DanielaOS/Queue/daniela_1787576885.png" duplicados \
  3bae783204965913b02716e07912438c

# 4) Grabaciones huerfanas de Termux en la raiz de /sdcard
for a in $R/TermuxAudioRecording_*.m4a; do
  [ -f "$a" ] && mover_a_papelera "$a" huerfanos
done

# 5) Cache de Google Maps (se regenera)
mover_a_papelera \
  "$R/Android/data/com.google.android.apps.maps/cache/diskcache/map_cache.db" caches

# 6) Papelera del gestor de archivos (.trash-storage)
if [ -d "$R/.trash-storage" ]; then
  sz=$(du -sk "$R/.trash-storage" 2>/dev/null | cut -f1)
  [ -z "$sz" ] && sz=0
  echo "  + $(humano $sz)  $R/.trash-storage (papelera del gestor de archivos)"
  TOTAL=$((TOTAL + sz)); MOVIDOS=$((MOVIDOS + 1))
  if [ "$MODO" != simular ]; then
    mkdir -p "$P/trash-storage" 2>/dev/null
    mv "$R/.trash-storage"/* "$P/trash-storage/" 2>/dev/null
    rmdir "$R/.trash-storage" 2>/dev/null
    echo "$(date '+%F %T') MOVIDO $sz $R/.trash-storage" >> "$LOG"
  fi
fi

# =========================== NIVEL 2 =====================================
if [ "$MODO" = n2 ] || [ "$MODO" = todo ] || [ "$MODO" = n3 ]; then
echo
echo "--- NIVEL 2: modelos demo y renders antiguos -----------------------"

# Modelos de DEMOSTRACION de AI Edge Gallery (no son tuyos, son ejemplos)
mover_a_papelera "$G/TinyGarden_270M/20260225/tiny_garden.litertlm" modelos_demo
mover_a_papelera "$G/MobileActions_270M/20260218/mobile_actions.litertlm" modelos_demo

# Videos generados por Daniela (ya publicados o superados)
for v in "$R/Movies"/output_*.mp4 "$R/Movies"/daniela_loop.mp4 \
         "$R/Movies"/daniela_animated.mp4; do
  [ -f "$v" ] && mover_a_papelera "$v" videos_antiguos
done

# APK ya descargado
mover_a_papelera "$R/Download/Instaladores_APK/HeliBoard_4.1-release.apk" apks
fi

# =========================== NIVEL 3 =====================================
if [ "$MODO" = n3 ]; then
echo
echo "--- NIVEL 3: decision sobre modelos LLM (lee el informe) -----------"
mover_a_papelera \
  "$R/Android/data/com.llmproxy/files/models/Qwen_Qwen2.5-0.5B-Instruct-GGUF/qwen2.5-0.5b-instruct-q4_k_m.gguf" \
  modelos_llm
mover_a_papelera "$R/Documents/NexusAI/gemma_soberano.bin" modelos_llm
fi

# =========================== RESUMEN =====================================
echo
echo "=================================================================="
if [ "$MODO" = simular ]; then
  echo " SIMULACRO — no se ha tocado NADA"
else
  echo " EJECUTADO — todo esta en $P"
fi
echo " elementos: $MOVIDOS"
echo " espacio liberado: $(humano $TOTAL)"
echo
echo " Para recuperar algo:  sh $0 --restaurar"
echo " Para vaciar la papelera cuando estes seguro:"
echo "   rm -rf $P"
echo "=================================================================="

# ---- recordatorio de salud del sistema -----------------------------------
echo
echo "--- ESTADO ACTUAL DEL SISTEMA -------------------------------------"
echo -n " memoria libre:   "; free -m 2>/dev/null | awk '/Mem:/{print $4" MB"}'
echo -n " swap en uso:     "; free -m 2>/dev/null | awk '/Swap:/{print $3"/"$2" MB"}'
echo -n " almacenamiento:  "; df -h /storage/emulated 2>/dev/null | awk 'NR==2{print $3" usados de "$2" ("$5")"}'
echo -n " bateria:         "; dumpsys battery 2>/dev/null | awk '/level/{print $2" %"; exit}'
echo
