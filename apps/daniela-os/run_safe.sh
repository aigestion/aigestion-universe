#!/bin/bash
# Centinela de Rescate Daniela OS
cd ~/daniela-os

python app_daniela.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "⚠️ ERROR DETECTADO EN EL SERVIDOR. Ejecutando Rollback de Seguridad..."
    git reset --hard HEAD~1
    echo "✅ Sistema restaurado al último estado estable. Reconstruyendo..."
    python app_daniela.py
fi
