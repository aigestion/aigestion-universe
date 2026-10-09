# daniela-desktop

Daniela OS desktop client — Tauri 2 + WebView2 (Rust + Three.js).

Avatar 3D flotante de Daniela (60×60, transparente, always-on-top real vía
`HWND_TOPMOST`), Vision Menu con 7 pestañas y captura de pantalla Windows.

- Rust 1.77+ · Tauri 2 · MSVC (`x86_64-pc-windows-msvc`)
- Frontend: `resources/` (`avatar.html`, `menu.html`, Three.js r165 vendorizado,
  GLB `daniela3d_rigged.glb` 4.5 MB + fallback 75 MB)
- Backend: Flask Daniela OS en `http://127.0.0.1:9200` (GEV, memoria, engines)
- Comandos IPC: avatar state/morphs, menú, captura, `system_info`, `open_url`, config

## Build (MSVC obligatorio)

```powershell
.\build.ps1
# o manual:
$tc="$env:USERPROFILE\.rustup\toolchains\stable-x86_64-pc-windows-msvc"
$env:PATH="$tc\bin;$env:PATH"; $env:RUSTUP_TOOLCHAIN="stable-x86_64-pc-windows-msvc"
cargo build --release --target x86_64-pc-windows-msvc
```

## Run (backend + app)

```powershell
# desde la raíz del monorepo:
.\start_aigestion_universe.ps1 -SoloDesktop
```

## Interacción

- 1 clic → despierta/escucha · 2 clics → Vision Menu · clic derecho → contextual
- Atajo global `Win+Alt+D`, bandeja del sistema

## Pairing

Challenge-response PC↔Pixel en `packages/daniela-core` (ver `skills/connectors/android/pairing.py` en legado).
