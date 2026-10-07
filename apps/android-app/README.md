# android-app

Native Android client for Daniela OS — Kotlin + Jetpack Compose.

- Package: `com.aigestion.mobile`
- Min SDK 24 · Target SDK 34 · Compile SDK 34
- Kotlin 1.9.22 · Gradle 8.6 · AGP 8.3.0 · Compose BOM 2024.06.00
- Ktor client for networking · DataStore for pairing persistence

## Build

```bash
./gradlew assembleDebug      # debug APK
./gradlew assembleRelease    # release APK (sign manually)
```

## Pairing

PC ↔ Pixel uses HMAC-SHA256 challenge-response (`pairing/PairingManager.kt`).
The shared `PIXEL_TOKEN` never travels over the wire — only the HMAC digest does.
PC side: `skills/connectors/android/pairing.py`.

## Screens

- Home — coherence / empathy / nodes / engines tiles
- Pair — challenge-response QR + 6-char code
- Engines — live swarm engine health + load
- Memory — three-tier vault (episodic / semantic / procedural)
