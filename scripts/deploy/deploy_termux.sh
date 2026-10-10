#!/bin/bash
# =============================================================================
#  🔴 OJO: este script es de TERMUX (el movil), NO del PC.
# =============================================================================
#  Hace tres cosas que en el PC serian destructivas:
#    1) `pkill -9 -f "python3"` -> mata TODOS los procesos python del PC,
#       incluido el propio DanielaOS.
#    2) `git add .` + `git commit` sin revisar -> cuela lo que sea.
#    3) `git push origin main --force` -> reescribe el historial de main.
#  Y apunta a ~/apps/aig-MONOREPO, que en el PC no existe.
#
#  El despliegue de produccion en el PC es:  ./scripts/deploy/deploy_prod.sh
#
#  Guardia (E-36): si no estamos en Termux, no se ejecuta nada.
# =============================================================================
if [ -z "${PREFIX:-}" ] || ! printf '%s' "${PREFIX}" | grep -q "com.termux"; then
  echo "ERROR: este script es SOLO para Termux (movil) y se ha bloqueado." >&2
  echo "       Motivo: hace 'pkill -9 -f python3' y 'git push --force' a main." >&2
  echo "       Para desplegar en el PC usa: ./scripts/deploy/deploy_prod.sh" >&2
  exit 1
fi

echo "[DESPLIEGUE] Iniciando orquestación de DANIELA OS..."

# 1. Comprobar instalación de dependencias
cd ~/apps/aig-MONOREPO

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
