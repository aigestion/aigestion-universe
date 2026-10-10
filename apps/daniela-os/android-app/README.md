# aig · app Android (Kotlin + Jetpack Compose)

Cliente nativo para el backend de Daniela OS. La PWA vive en
[`mobile-app/`](../mobile-app/); esta carpeta es la app
empaquetable como APK.

## Build

> **Requisitos:** JDK 17+, Android SDK (`compileSdk 34`) y Gradle 8.6.
> No hay `gradle-wrapper.jar` versionado (es binario): ábrelo con Android Studio
> o genera el wrapper con una instalación local de Gradle:
>
> ```bash
> gradle wrapper --gradle-version 8.6
> ./gradlew :app:assembleDebug
> ```

## Configurar la URL del backend

La IP **no está escrita en el código Kotlin**. Se resuelve en este orden:

1. **En tiempo de ejecución** → diálogo *Cambiar URL* en la tarjeta de conexión
   (persistida en `SharedPreferences`).
2. **En tiempo de build** → `apiBaseUrl` de `gradle.properties`:

   ```bash
   ./gradlew :app:assembleDebug -PapiBaseUrl=http://192.168.1.50:5000
   # o editando android-app/gradle.properties → apiBaseUrl=...
   ```

3. Si no hay nada, el valor por defecto es `http://192.168.1.170:5000`.

## Estructura

```
app/src/main/java/com/aigestion/mobile/
├── MainActivity.kt              # Compose UI (única Activity)
├── data/
│   ├── ChatApi.kt               # POST /api/chat + GET /api/status
│   └── SettingsRepository.kt    # SharedPreferences + BuildConfig.API_BASE_URL
└── ui/
    └── AppViewModel.kt          # StateFlow<AppState>, sobrevive a rotaciones
```

## Bugs corregidos en el refactor

| Antes | Ahora |
|---|---|
| `lifecycleScope.launch` + `HttpURLConnection` bloqueante → `NetworkOnMainThreadException`, Enviar nunca funcionaba | `withContext(Dispatchers.IO)` |
| Payload armado a mano: `"{\"message\":\"$command\"}"` → un `"` o salto de línea rompía la petición (e inyectaba campos) | `JSONObject.put(...)` |
| `connection.inputStream` en 4xx/5xx → `Error: null` | `errorStream` + mensaje HTTP real |
| `disconnect()` no se ejecutaba si fallaba el parse | `finally` |
| Sin ViewModel → rotar la pantalla perdía todo el estado | `AppViewModel` + `StateFlow` |
| IP hardcodeada en `MainActivity` | `BuildConfig.API_BASE_URL` + ajustes |
| El manifest usaba `package=`, que AGP 8 rechaza | `namespace` en `build.gradle` |
| Faltaban `settings.gradle`, build raíz, `gradle.properties`, `proguard-rules.pro`, `res/` (tema + iconos) | todos añadidos |
| `org.json:json` de Maven | eliminado (choca con `android.jar`) |

## Nota

Esta app habla con `mobile-app/core/autonomy/daniela_os.py` (`/api/status` y
`/api/chat` con `{"message": ...}` → `{"type", "response"}`). El
`server-unificado.js` usa otra forma (`{"mensaje": ...}` → `{"respuesta"}`);
`ChatApi.parseChat` admite ambos.
