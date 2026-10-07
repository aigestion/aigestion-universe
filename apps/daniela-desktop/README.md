# daniela-desktop

Daniela OS desktop client — Tauri 2.0 (Rust + WebView).

- Rust 1.70+ · Tauri 2.0
- Transparent, frameless-capable window
- Commands: `greet`, `pair_device`
- Connects to Daniela Core at `localhost:9200`

## Build

```bash
cd src-tauri
cargo build --release
# or
cargo tauri build
```

## Dev

```bash
cargo tauri dev
```

The desktop shell loads `src/index.html` (or the Neural Shell
at `http://localhost:3000` in dev mode via `devUrl`).

## Pairing

`pair_device` command computes a challenge fingerprint.
Full HMAC-SHA256 challenge-response lives in
`skills/connectors/android/pairing.py` (shared with mobile).
