#!/system/bin/sh
# AUDITORIA PROFUNDA - FASE 1: mapa completo del almacenamiento
O=/sdcard/DanielaOS/audit
mkdir -p $O
echo "===== 1. MONTURAS Y ALMACENAMIENTO ====="
df -h 2>/dev/null
echo
echo "===== 2. RAIZ DEL TELEFONO ====="
ls -la / 2>/dev/null
echo
echo "===== 3. /sdcard PRIMER NIVEL (tamano) ====="
cd /sdcard 2>/dev/null && du -sk * 2>/dev/null | sort -rn | head -60
echo
echo "===== 4. /storage ====="
ls -la /storage 2>/dev/null
echo "--- emulated ---"
ls -la /storage/emulated 2>/dev/null
echo
echo "===== 5. /data/local/tmp (accesible) ====="
ls -la /data/local/tmp 2>/dev/null
echo
echo "===== 6. /mnt y /mnt/* ====="
ls -la /mnt 2>/dev/null
for m in /mnt/*; do echo "-- $m"; ls -la "$m" 2>/dev/null | head -20; done
echo
echo "===== 7. CUENTAS /storage/emulated ====="
ls -la /storage/emulated/0 2>/dev/null | head -40
echo
echo "===== 8. TOTAL FICHEROS EN /sdcard ====="
find /sdcard -type f 2>/dev/null | wc -l
echo "===== 9. TOTAL DIRECTORIOS EN /sdcard ====="
find /sdcard -type d 2>/dev/null | wc -l
echo "FIN-FASE1"
