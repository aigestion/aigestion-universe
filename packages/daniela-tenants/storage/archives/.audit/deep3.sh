#!/system/bin/sh
# AUDITORIA PROFUNDA - FASE 3: dentro de los gigantes + duplicados
R=/storage/emulated/0
echo "===== H. com.google.ai.edge.gallery (4.6 GB) ====="
find $R/Android/data/com.google.ai.edge.gallery -maxdepth 3 2>/dev/null | head -40
echo "-- ficheros >5 MB --"
find $R/Android/data/com.google.ai.edge.gallery -type f -size +5000k -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -25
echo
echo "===== I. Documents/NexusAI (3.1 GB) ====="
du -sk $R/Documents/NexusAI/* 2>/dev/null | sort -rn | head -30
echo "-- ficheros >5 MB --"
find $R/Documents/NexusAI -type f -size +5000k -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -30
echo
echo "===== J. Download/DanielaControl (295 MB) ====="
du -sk $R/Download/DanielaControl/* 2>/dev/null | sort -rn | head -30
echo "===== J2. Download/Daniela_Organizado ====="
du -sk $R/Download/Daniela_Organizado/* 2>/dev/null | sort -rn | head -20
echo "===== J3. Download/Instaladores_APK ====="
ls -la $R/Download/Instaladores_APK 2>/dev/null | head -30
echo
echo "===== K. Android/media/com.whatsapp.w4b (580 MB) ====="
du -sk $R/Android/media/com.whatsapp.w4b/* 2>/dev/null | sort -rn | head -15
echo
echo "===== L. TOP 40 FICHEROS MAS GRANDES DE /sdcard ====="
find $R/ -type f -size +8000k -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -40
echo
echo "===== M. MODELOS LLM / IA EN EL TELEFONO (conflicto potencial) ====="
find $R/ -type f \( -name '*.gguf' -o -name '*.task' -o -name '*.bin' -o -name '*.tflite' -o -name '*.onnx' -o -name '*.litertlm' \) -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -40
echo "FIN-FASE3"
