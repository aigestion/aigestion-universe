#!/system/bin/sh
# AUDITORIA PROFUNDA - FASE 6: CPU, bateria, wakelocks, duplicados finales
R=/storage/emulated/0
echo "===== AA. TOP CPU ====="
top -b -n 1 2>/dev/null | head -35
echo
echo "===== AB. CARGA MEDIA / CPU ====="
cat /proc/loadavg 2>/dev/null
echo "-- cpuinfo --"
grep -E "processor|model name|cpu MHz" /proc/cpuinfo 2>/dev/null | head -12
echo
echo "===== AC. BATERIA POR PROCESO (dumpsys batterystats top) ====="
dumpsys batterystats --charged 2>/dev/null | grep -iE "^ *[0-9]+ *[a-z]" | head -5
dumpsys batterystats 2>/dev/null | sed -n '/Estimated power use/,/^$/p' | head -35
echo
echo "===== AD. WAKELOCKS ====="
dumpsys power 2>/dev/null | sed -n '/Wake Locks/,/^$/p' | head -30
echo
echo "===== AE. ALARMAS / JOBSCHEDULER ====="
dumpsys jobscheduler 2>/dev/null | grep -cE "JOB" 2>/dev/null
echo
echo "===== AF. DUPLICADOS EN DANIELAOS/QUEUE ====="
md5sum $R/DanielaOS/Queue/* 2>/dev/null
echo
echo "===== AG. TRASH DETALLE ====="
find $R/.trash-storage -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -20
echo "-- total trash --"
du -sk $R/.trash-storage 2>/dev/null
echo
echo "===== AH. GRABACIONES HUERFANAS ====="
md5sum $R/TermuxAudioRecording_*.m4a 2>/dev/null
echo
echo "===== AI. TERMUX: esta instalado llama/ollama? ====="
ls /data/data/com.termux/files/usr/bin 2>/dev/null | head -5
echo "(si sale vacio, /data/data es inaccesible desde adb - normal)"
echo
echo "===== AJ. ESPACIO TOTAL RECLAMABLE ESTIMADO ====="
echo "gemma2-2b.bin duplicado:"; stat -c '%s' $R/Documents/NexusAI/gemma2-2b.bin 2>/dev/null
echo "trash:"; du -sk $R/.trash-storage 2>/dev/null | cut -f1
echo "FIN-FASE6"
