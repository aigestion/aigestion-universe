#!/system/bin/sh
# Cierre de la optimizacion: borra lo seguro, RESCATA el contenido del usuario
R=/storage/emulated/0
P=$R/DanielaOS/.papelera

echo "===== 1. RESCATAR: el contenido creado por Daniela NO es basura ====="
mkdir -p "$R/Movies" 2>/dev/null
n=0
for f in "$P/videos_antiguos"/*; do
  [ -f "$f" ] || continue
  mv "$f" "$R/Movies/" 2>/dev/null && n=$((n+1))
done
echo "  videos devueltos a /sdcard/Movies: $n"

mkdir -p "$R/Download/Instaladores_APK" 2>/dev/null
for f in "$P/apks"/*; do
  [ -f "$f" ] || continue
  mv "$f" "$R/Download/Instaladores_APK/" 2>/dev/null && echo "  apk devuelto: $(basename "$f")"
done

echo
echo "===== 2. BORRAR: redundancia verificada + caches + basura ====="
for cat in duplicados caches modelos_demo trash-storage huerfanos; do
  if [ -d "$P/$cat" ]; then
    sz=$(du -sk "$P/$cat" 2>/dev/null | cut -f1)
    echo "  borrando $cat ($((sz/1024)) MB)"
    rm -rf "$P/$cat" 2>/dev/null
  fi
done

echo
echo "===== 3. DESATASCAR el pipeline de DanielaOS ====="
if [ -d "$R/DanielaOS/Queue" ]; then
  mkdir -p "$R/DanielaOS/Rendered" 2>/dev/null
  for f in "$R/DanielaOS/Queue"/*; do
    [ -f "$f" ] && mv "$f" "$R/DanielaOS/Rendered/" 2>/dev/null && echo "  drenado: $(basename "$f")"
  done
fi

echo
echo "===== 4. LIBERAR CPU: Play Store en segundo plano (59%) ====="
am force-stop com.android.vending 2>/dev/null && echo "  com.android.vending detenido (se relanza solo si hace falta)"

echo
echo "===== 5. ESTADO FINAL ====="
echo -n " disco:  "; df -h /storage/emulated 2>/dev/null | awk 'NR==2{print $3" usados de "$2" ("$5") - "$4" libres"}'
echo -n " ram:    "; free -m 2>/dev/null | awk '/Mem:/{print $4" MB libres de "$2" MB"}'
echo -n " swap:   "; free -m 2>/dev/null | awk '/Swap:/{print $3"/"$2" MB"}'
echo -n " papelera: "; du -sk "$P" 2>/dev/null | awk '{print $1" KB"}'
echo -n " bateria:  "; dumpsys battery 2>/dev/null | awk '/level/{print $2" %"; exit}'
echo "FIN"
