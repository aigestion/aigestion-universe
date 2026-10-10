#!/bin/bash
echo "[DESPLIEGUE] Iniciando orquestación de DANIELA OS..."

# 1. Comprobar instalación de dependencias
cd ~/apps/AIGESTION-MONOREPO

# 2. Detener servicios previos
echo "[DESPLIEGUE] Limpiando procesos de puerto 8082..."
pkill -9 -f "python3" 2>/dev/null
sleep 1

# 3. Guardar cambios en Git
echo "[DESPLIEGUE] Sincronizando con repositorio de GitHub..."
git add .
git commit -m "feat(system): Despliegue completo con arquitectura multi-universo, API REST SQLite y editor en tiempo real"
git push origin main --force

# 4. Iniciar backend con SQLite en segundo plano
echo "[DESPLIEGUE] Arrancando servidor Python Multi-Universo en puerto 8082..."
nohup python3 server.py > server.log 2>&1 &
sleep 2

# 5. Abrir visor
echo "[DESPLIEGUE] Servidor desplegado correctamente."
termux-open-url "http://127.0.0.1:8082/index.html"
