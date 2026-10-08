# /phone - Daniela OS Phone (Pixel + Termux)

Trabaja con **Daniela OS Phone** - runtime nativo Android + PWA edge.

## Ámbito
- `daniela-os/phone/agents/` - brain, caller, initiative, missions, scout, social, swarm, web
- `daniela-os/android-app/` - app nativa Kotlin + Jetpack Compose (com.aigestion.mobile)
- `frontend/apps/android-app/mobile-app/` - PWA + servicios Python edge
  - `api/termux_api_gateway.py` - 30 endpoints (incl. `/api/pair/challenge`)
  - `services/`, `bridges/`, `core/`, `api/`
- `skills/connectors/android/pairing.py` - PC↔Pixel challenge-response

## Nomenclatura (docs/ESTANDARES-ORGANIZACION.md)
- `android` = plataforma (connectors/scripts/marker)
- `android-app` = solo la app
- `pixel` = hardware concreto
- `termux` = runtime en el móvil
- `mobile-app` = árbol único cliente (puntero 36B en raíz)

## Operaciones típicas
- Pairing PC-Pixel
- Desplegar agents en phone/
- Build Android (Gradle 8.6, AGP 8.3.0, Compose 1.5.8)
- Termux API gateway
- Sync offline-first

## Reglas
- Gate antes de commit
- Nunca push
- Min SDK 24, Target SDK 34
EOF