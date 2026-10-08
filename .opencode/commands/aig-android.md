# /aig-android - Android development (Kotlin + Jetpack Compose)

Desarrollo app nativa Daniela OS: `daniela-os/android-app/` (com.aigestion.mobile)

## Config
- Kotlin 1.9.22, Gradle 8.6, AGP 8.3.0
- Compose 1.5.8, Material 3
- Min SDK 24, Target SDK 34

## Comandos
```bash
# Build debug
cd daniela-os/android-app && ./gradlew assembleDebug

# Test unit
./gradlew testDebugUnitTest

# Test instrumented (requiere Pixel/emulator)
./gradlew connectedDebugAndroidTest

# Lint
./gradlew lintDebug

# Install en Pixel (ADB)
./gradlew installDebug
adb logcat -s DanielaOS:*
```

## Pairing PC ↔ Pixel
```bash
python skills/connectors/android/pairing.py --challenge
# En Pixel: aceptar challenge → genera token emparejamiento
```

## PWA + Edge (frontend/apps/android-app/mobile-app/)
```bash
# Termux API Gateway (30 endpoints)
python api/termux_api_gateway.py

# Pair challenge endpoint
curl -X POST http://pixel:port/api/pair/challenge
```

## Nomenclatura (docs/ESTANDARES-ORGANIZACION.md)
- `android` = plataforma (connectors/scripts/marker)
- `android-app` = solo la app
- `pixel` = hardware
- `termux` = runtime
- `mobile-app` = PWA tree (puntero 36B)
EOF