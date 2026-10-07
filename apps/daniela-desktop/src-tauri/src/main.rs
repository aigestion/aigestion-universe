#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use tauri::Manager;

#[derive(Serialize, Deserialize)]
struct PairPayload {
    challenge: String,
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hola, {}! Daniela Desktop listo.", name)
}

#[tauri::command]
fn pair_device(challenge: String) -> Result<String, String> {
    // In production: HMAC-SHA256 with PIXEL_TOKEN (see PairingManager).
    // Here we just echo the challenge fingerprint.
    let fingerprint = format!("{:x}", md5_simple(&challenge));
    Ok(fingerprint)
}

fn md5_simple(input: &str) -> u128 {
    // Lightweight non-crypto fingerprint for display only.
    let mut hash: u128 = 0xcbf29ce484222325;
    for b in input.bytes() {
        hash ^= b as u128;
        hash = hash.wrapping_mul(0x100000001b3);
    }
    hash
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![greet, pair_device])
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();
            let _ = window.set_shadow(true);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
