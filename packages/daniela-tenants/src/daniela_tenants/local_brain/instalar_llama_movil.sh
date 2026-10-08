#!/data/data/com.termux/files/usr/bin/bash
# Generado por local_brain.py (E-13) el 2026-09-11 20:54:03
# NO descarga ningun modelo: reutiliza el GGUF que ya hay en el
# movil (com.llmproxy, Qwen2.5-0.5B, 0,46 GB). El movil va justo
# de memoria (swap al 98,5 %) y solo cabe UN modelo a la vez.
set -e
echo '== 1. dependencias =='
pkg install -y git cmake clang make
echo '== 2. compilar llama.cpp =='
[ -d ~/llama.cpp ] || git clone --depth 1 https://github.com/ggerganov/llama.cpp ~/llama.cpp
cd ~/llama.cpp
cmake -B build -DLLAMA_CURL=OFF
cmake --build build -j4
echo '== 3. buscar el GGUF que ya existe =='
GGUF=$(find /data/data /sdcard -name '*.gguf' 2>/dev/null | head -1)
if [ -z "$GGUF" ]; then
  echo 'NO se encontro ningun GGUF. Descarga uno pequeno a mano.'
  exit 1
fi
echo "usando: $GGUF"
echo '== 4. arrancar en el puerto 8083 =='
./build/bin/llama-server -m "$GGUF" -c 2048 --port 8083 --host 0.0.0.0
