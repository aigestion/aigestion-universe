#!/system/bin/sh
# AUDITORIA PROFUNDA - FASE 2: inventario completo + pesos por carpeta
R=/storage/emulated/0
echo "===== A. TOTALES ====="
echo -n "ficheros: "; find $R/ -type f 2>/dev/null | wc -l
echo -n "directorios: "; find $R/ -type d 2>/dev/null | wc -l
echo -n "enlaces rotos: "; find $R/ -xtype l 2>/dev/null | wc -l
echo
echo "===== B. PESO POR CARPETA (nivel 1) ====="
du -sk $R/* 2>/dev/null | sort -rn
echo
echo "===== C. PESO POR CARPETA (nivel 2) ====="
du -sk $R/*/* 2>/dev/null | sort -rn | head -50
echo
echo "===== D. DOCUMENTS (3 GB, sospechoso) ====="
du -sk $R/Documents/* 2>/dev/null | sort -rn | head -40
echo "-- ficheros sueltos en Documents --"
find $R/Documents -maxdepth 1 -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -30
echo
echo "===== E. ANDROID (5.8 GB) ====="
du -sk $R/Android/* 2>/dev/null | sort -rn | head -20
echo "-- Android/data --"
du -sk $R/Android/data/* 2>/dev/null | sort -rn | head -25
echo "-- Android/media --"
du -sk $R/Android/media/* 2>/dev/null | sort -rn | head -20
echo "-- Android/obb --"
du -sk $R/Android/obb/* 2>/dev/null | sort -rn | head -20
echo
echo "===== F. DOWNLOAD ====="
du -sk $R/Download/* 2>/dev/null | sort -rn | head -30
echo
echo "===== G. DCIM / PICTURES / MOVIES ====="
du -sk $R/DCIM/* 2>/dev/null | sort -rn | head -20
du -sk $R/Pictures/* 2>/dev/null | sort -rn | head -20
du -sk $R/Movies/* 2>/dev/null | sort -rn | head -20
echo "FIN-FASE2"
