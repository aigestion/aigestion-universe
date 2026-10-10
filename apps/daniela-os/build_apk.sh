#!/data/data/com.termux/files/usr/bin/bash

echo "================================================="
echo "⚡ DANIELA OS - COMPILADOR NATIVO APK (PWA/TWA) ⚡"
echo "================================================="

# 1. Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "📦 Instalando Node.js..."
    pkg install nodejs -y
fi

# 2. Verificar Bubblewrap CLI (Compilador TWA oficial de Google)
if ! command -v bubblewrap &> /dev/null; then
    echo "📦 Instalando @bubblewrap/cli..."
    npm install -g @bubblewrap/cli
fi

# 3. Crear directorio de compilación
BUILD_DIR="apk_build"
mkdir -p $BUILD_DIR

echo "🔧 Generando manifesto táctico y configuración TWA..."
cat << 'JSON' > twa-manifest.json
{
  "packageId": "net.aigestion.daniela.os",
  "host": "localhost",
  "name": "Daniela OS Tactical Center",
  "launcherName": "DanielaOS",
  "display": "standalone",
  "themeColor": "#010308",
  "navigationColor": "#010308",
  "backgroundColor": "#010308",
  "enableNotifications": true,
  "startUrl": "/voice_interface.html",
  "appVersionName": "3.4.0",
  "appVersionCode": 34,
  "signingKey": {
    "path": "./android.keystore",
    "alias": "daniela_key"
  }
}
JSON

echo "✅ Configuración lista para empaquetado en $BUILD_DIR."
echo "🚀 Para compilar en APK instalable ejecuta:"
echo "   bubblewrap build --manifest=twa-manifest.json"
echo "================================================="
