#!/system/bin/sh
# AUDITORIA PROFUNDA - FASE 5: DanielaOS, trash, y CONFLICTOS de servicios
R=/storage/emulated/0
echo "===== T. DANIELAOS (ls -laR) ====="
ls -laR $R/DanielaOS 2>/dev/null | head -70
echo
echo "===== U. .trash-storage ====="
du -sk $R/.trash-storage 2>/dev/null
find $R/.trash-storage -maxdepth 2 2>/dev/null | head -20
echo
echo "===== V. PROCESOS (todos) ====="
ps -A -o PID,UID,NAME,ARGS 2>/dev/null | grep -viE "^\s*PID" | head -70
echo
echo "===== W. PUERTOS A LA ESCUCHA ====="
cat /proc/net/tcp 2>/dev/null | awk 'NR>1{print $2, $4}' | head -40
echo "-- IPv6 --"
cat /proc/net/tcp6 2>/dev/null | awk 'NR>1{print $2, $4}' | head -20
echo
echo "===== X. PROCESOS PYTHON / SERVIDORES ====="
ps -A -o PID,NAME,ARGS 2>/dev/null | grep -iE "python|node|server|flask|termux|guardian|cloudflare|sshd" | head -40
echo
echo "===== Y. BATERIA / MEMORIA / TERMICA ====="
dumpsys battery 2>/dev/null | grep -iE "level|temperature|status|health" | head -8
echo "-- meminfo --"
head -6 /proc/meminfo 2>/dev/null
echo "-- thermal --"
dumpsys thermalservice 2>/dev/null | head -12
echo
echo "===== Z. APPS CON MAS CONSUMO (usagestats muestra) ====="
dumpsys usagestats 2>/dev/null | grep -A3 "com.google.ai.edge.gallery\|com.llmproxy\|com.termux" | head -30
echo "FIN-FASE5"
