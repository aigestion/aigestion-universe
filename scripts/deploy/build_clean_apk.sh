#!/data/data/com.termux/files/usr/bin/bash

echo "================================================="
echo "⚡ DANIELA OS - INSTALACIÓN NATIVA COMPATIBLE ⚡"
echo "================================================="

BUILD_DIR="native-apk-build"
mkdir -p $BUILD_DIR/assets
mkdir -p $BUILD_DIR/res/drawable

# Copiar activos WebGL
cp voice_interface.html $BUILD_DIR/assets/index.html
cp sw.js $BUILD_DIR/assets/sw.js 2>/dev/null || true
cp manifest.json $BUILD_DIR/assets/manifest.json 2>/dev/null || true

# AndroidManifest estándar sin atributos incompatibles
cat << 'XML' > $BUILD_DIR/AndroidManifest.xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="net.aig.daniela.os"
    android:versionCode="41"
    android:versionName="4.1.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application android:label="Daniela OS">
        <activity
            android:name="android.webkit.WebView"
            android:label="Daniela OS"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
XML

ANDROID_JAR="$PREFIX/share/aapt/android-30.jar"

echo "📦 Empaquetando APK con aapt..."
aapt package -f -m \
    -S $BUILD_DIR/res \
    -A $BUILD_DIR/assets \
    -M $BUILD_DIR/AndroidManifest.xml \
    -I "$ANDROID_JAR" \
    -F DanielaOS_unsigned.apk

if [ ! -f "DanielaOS_unsigned.apk" ]; then
    echo "❌ Error al generar el APK no firmado."
    exit 1
fi

if [ ! -f "daniela_keystore.jks" ]; then
    echo "🔑 Generando clave de firma..."
    keytool -genkey -v -keystore daniela_keystore.jks \
        -alias daniela_key -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass daniela123 -keypass daniela123 \
        -dname "CN=aig, OU=Tactical, O=DanielaOS, L=Local, S=State, C=ES"
fi

echo "🖋️ Firmando paquete..."
apksigner sign --ks daniela_keystore.jks \
    --ks-pass pass:daniela123 \
    --out DanielaOS_v4.1_Clean.apk DanielaOS_unsigned.apk

rm -f DanielaOS_unsigned.apk

echo "================================================="
echo "✅ ¡APK GENERADA CON ÉXITO!"
echo "📦 Paquete listo: DanielaOS_v4.1_Clean.apk"
echo "================================================="
