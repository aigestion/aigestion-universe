#!/data/data/com.termux/files/usr/bin/bash

echo "================================================="
echo "⚡ DANIELA OS - BUILDER APK NATIVO (OFFICIAL JAR) ⚡"
echo "================================================="

BUILD_DIR="native-apk-build"
mkdir -p $BUILD_DIR/assets
mkdir -p $BUILD_DIR/res/drawable

# 1. Preparar activos WebGL
cp voice_interface.html $BUILD_DIR/assets/index.html
cp sw.js $BUILD_DIR/assets/sw.js 2>/dev/null || true
cp manifest.json $BUILD_DIR/assets/manifest.json 2>/dev/null || true

# 2. Generar AndroidManifest.xml
cat << 'XML' > $BUILD_DIR/AndroidManifest.xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="net.aigestion.daniela.os"
    android:versionCode="40"
    android:versionName="4.0.0">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.VIBRATE" />

    <application
        android:label="Daniela OS"
        android:hardwareAccelerated="true"
        android:usesCleartextTraffic="true">
        <activity
            android:name="android.webkit.WebView"
            android:label="Daniela OS"
            android:configChanges="orientation|keyboardHidden|screenSize"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
XML

# 3. Descarga mediante espejo persistente de Google Maven / Android SDK
mkdir -p $PREFIX/share/aapt
ANDROID_JAR="$PREFIX/share/aapt/android-30.jar"
rm -f "$ANDROID_JAR"

echo "📥 Descargando Framework Jar desde repositorio oficial..."
curl -f -L "https://dl.google.com/android/repository/platform-29_r05.zip" -o platform.zip 2>/dev/null || true

if [ -f "platform.zip" ]; then
    unzip -q platform.zip "android-10/android.jar" -d . 2>/dev/null || true
    mv android-10/android.jar "$ANDROID_JAR" 2>/dev/null || true
    rm -rf platform.zip android-10
fi

# Respaldo vía repositorio secundario si la extracción zip falló
if [ ! -f "$ANDROID_JAR" ]; then
    curl -f -L "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/brut.apktool/apktool-lib/src/main/resources/prebuilt/android-30.jar" -o "$ANDROID_JAR" 2>/dev/null || \
    curl -f -L "https://github.com/skylot/jadx/raw/master/jadx-core/src/test/resources/libs/android-29.jar" -o "$ANDROID_JAR"
fi

echo "📍 Usando Framework Jar: $ANDROID_JAR"

# 4. Empaquetado preliminar con aapt
echo "📦 Empaquetando recursos con aapt..."
aapt package -f -m \
    -S $BUILD_DIR/res \
    -A $BUILD_DIR/assets \
    -M $BUILD_DIR/AndroidManifest.xml \
    -I "$ANDROID_JAR" \
    -F DanielaOS_unsigned.apk

if [ ! -f "DanielaOS_unsigned.apk" ]; then
    echo "❌ Error: Falló la creación del APK base no firmado."
    exit 1
fi

# 5. Generar clave si no existe
if [ ! -f "daniela_keystore.jks" ]; then
    echo "🔑 Generando clave de firma release..."
    keytool -genkey -v -keystore daniela_keystore.jks \
        -alias daniela_key -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass daniela123 -keypass daniela123 \
        -dname "CN=AIGestion, OU=Tactical, O=DanielaOS, L=Local, S=State, C=ES"
fi

# 6. Firmar APK
echo "🖋️ Firmando paquete APK..."
apksigner sign --ks daniela_keystore.jks \
    --ks-pass pass:daniela123 \
    --out DanielaOS_v4.0.apk DanielaOS_unsigned.apk

rm -f DanielaOS_unsigned.apk

echo "================================================="
echo "✅ ¡COMPILACIÓN COMPLETADA EXITOSAMENTE!"
echo "📦 Archivo listo: DanielaOS_v4.0.apk"
echo "================================================="
