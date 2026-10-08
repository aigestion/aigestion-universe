#!/system/bin/sh
# AUDITORIA PROFUNDA - FASE 4: duplicados reales (md5) + apps + estado DanielaOS
R=/storage/emulated/0
echo "===== N. MD5 DE LOS DOS .bin DE 1.5 GB (NexusAI) ====="
md5sum $R/Documents/NexusAI/gemma_soberano.bin 2>/dev/null
md5sum $R/Documents/NexusAI/gemma2-2b.bin 2>/dev/null
echo
echo "===== N2. MD5 DE LOS DOS .litertlm DE 289 MB ====="
md5sum $R/Android/data/com.google.ai.edge.gallery/files/TinyGarden_270M/20260225/tiny_garden.litertlm 2>/dev/null
md5sum $R/Android/data/com.google.ai.edge.gallery/files/MobileActions_270M/20260218/mobile_actions.litertlm 2>/dev/null
echo
echo "===== N3. DUPLICADOS POR TAMANO EN /sdcard (solo >1 MB) ====="
find $R/ -type f -size +1000k -printf '%s\n' 2>/dev/null | sort -n | uniq -d > /data/local/tmp/_dupsz.txt 2>/dev/null
wc -l < /data/local/tmp/_dupsz.txt
echo "-- grupos de tamano repetido (top 20) --"
find $R/ -type f -size +1000k -printf '%s\n' 2>/dev/null | sort -n | uniq -c | sort -rn | head -20
echo
echo "===== O. MD5 DE LOS PNG SOSPECHOSOS ====="
md5sum $R/Pictures/*.png 2>/dev/null | head -20
md5sum $R/DanielaOS/*.png 2>/dev/null | head -20
echo
echo "===== P. PAQUETES INSTALADOS (relacionados) ====="
pm list packages 2>/dev/null | grep -iE "termux|llmproxy|edge.gallery|heliboard|daniela|nexus|llama" 
echo "-- total paquetes --"
pm list packages 2>/dev/null | wc -l
echo
echo "===== Q. ULTIMO USO DE LAS APPS DE IA ====="
for p in com.google.ai.edge.gallery com.llmproxy com.termux com.termux.api com.termux.boot com.termux.widget; do
  echo "--- $p"
  stat -c '%y %n' /data/data/$p 2>/dev/null
  dumpsys package $p 2>/dev/null | grep -iE "lastUpdateTime|firstInstallTime|versionName" | head -4
done
echo
echo "===== R. ESTADO DE DANIELAOS ====="
find $R/DanielaOS -printf '%s\t%y\t%p\n' 2>/dev/null | sort -k3 | head -60
echo
echo "===== S. DIRECTORIOS VACIOS EN /sdcard ====="
find $R/ -type d -empty 2>/dev/null | head -40
echo "FIN-FASE4"
