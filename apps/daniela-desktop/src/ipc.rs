//! Comandos Tauri (`invoke`) que el WebView puede llamar.
//!
//! Regla: los comandos son finos. No transforman datos ni deciden politica;
//! delegan en `state` / `capture` y devuelven un error legible en castellano
//! cuando algo falla. El WebView decide como mostrarlo.

use crate::state::{AppState, AvatarState, Config, Morphs, SysInfo};
use std::sync::Arc;
use tauri::{AppHandle, Emitter, Manager, State};
use tauri_plugin_opener::OpenerExt;
use tauri_plugin_store::StoreExt;

type R<T> = Result<T, String>;

// ── Helpers internos (aceptan Arc<AppState> directamente) ──────────

fn get_avatar_state_inner(state: &Arc<AppState>) -> R<AvatarState> {
    Ok(state.estado())
}

fn set_avatar_state_inner(app: &AppHandle, state: &Arc<AppState>, nuevo: String) -> R<AvatarState> {
    let e = AvatarState::from_str(&nuevo).ok_or_else(|| format!("estado desconocido: {nuevo}"))?;
    state.set_estado(e);
    let _ = app.emit("avatar-state", e.as_str());
    Ok(e)
}

fn set_morph_inner(state: &Arc<AppState>, name: String, value: f32) -> R<Morphs> {
    let mut m = state.morphs.write();
    if !m.set(&name, value) {
        return Err(format!("morph desconocido: {name}"));
    }
    Ok(*m)
}

fn get_morphs_inner(state: &Arc<AppState>) -> Morphs {
    *state.morphs.read()
}

fn report_active_window_inner(state: &Arc<AppState>, titulo: Option<String>) -> R<()> {
    *state.ventana_activa.write() = titulo;
    Ok(())
}

fn start_capture_inner(state: &Arc<AppState>, objetivo: Option<String>) -> R<String> {
    let cfg = state.cfg().capture;
    let objetivo = objetivo.unwrap_or_else(|| cfg.objetivo.clone());
    crate::capture::start(
        Some(&objetivo),
        true, // con cursor: si lee la pantalla para ayudar, el cursor importa
        Some(cfg.fps),
    )
}

fn stop_capture_inner() -> R<()> {
    crate::capture::stop()
}

fn capture_status_inner() -> serde_json::Value {
    serde_json::json!({
        "activa": crate::capture::activa(),
        "frames": crate::capture::frames_recibidos(),
    })
}

fn get_capture_frame_inner(max_ancho: Option<u32>) -> R<Option<String>> {
    crate::capture::frame_png_base64(max_ancho.unwrap_or(1600))
}

fn list_windows_inner() -> R<Vec<crate::capture::WinInfo>> {
    crate::capture::listar_ventanas()
}

fn list_monitors_inner() -> R<Vec<crate::capture::MonitorInfo>> {
    crate::capture::listar_monitores()
}

fn toggle_avatar_inner(app: &AppHandle) -> R<bool> {
    let Some(w) = app.get_webview_window("main") else {
        return Err("no encuentro la ventana del avatar".into());
    };
    let visible = w.is_visible().unwrap_or(false);
    if visible {
        w.hide().map_err(|e| e.to_string())?;
    } else {
        w.show().map_err(|e| e.to_string())?;
        w.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(!visible)
}

fn set_avatar_position_inner(state: &Arc<AppState>, x: i32, y: i32) -> (i32, i32) {
    *state.posicion.write() = (x, y);
    (x, y)
}

fn get_avatar_position_inner(state: &Arc<AppState>) -> (i32, i32) {
    *state.posicion.read()
}

pub(crate) fn show_menu_inner(app: &AppHandle, state: &Arc<AppState>, pestana: Option<String>) -> R<()> {
    let tab = pestana.unwrap_or_else(|| state.cfg().menu.pestana_inicial);
    *state.pestana.write() = tab.clone();
    *state.menu_visible.write() = true;

    if let Some(w) = app.get_webview_window("menu") {
        w.show().map_err(|e| e.to_string())?;
        w.set_focus().map_err(|e| e.to_string())?;
    }
    let _ = app.emit("menu-tab", &tab);
    Ok(())
}

pub(crate) fn hide_menu_inner(app: &AppHandle, state: &Arc<AppState>) -> R<()> {
    *state.menu_visible.write() = false;
    if let Some(w) = app.get_webview_window("menu") {
        w.hide().map_err(|e| e.to_string())?;
    }
    Ok(())
}

fn set_menu_tab_inner(app: &AppHandle, state: &Arc<AppState>, tab: String) -> R<()> {
    *state.pestana.write() = tab.clone();
    let _ = app.emit("menu-tab", &tab);
    Ok(())
}

fn system_info_inner() -> R<SysInfo> {
    use sysinfo::{MemoryRefreshKind, RefreshKind, System};

    // Solo memoria: leer la CPU de sysinfo cuesta ~50 ms y desde el WebView se
    // pide cada segundo. El CPU lo reporta el propio WebView o Prometheus.
    let s = System::new_with_specifics(RefreshKind::new().with_memory(MemoryRefreshKind::everything()));
    let total = s.total_memory();
    let used = s.used_memory();
    let ram_pct = if total > 0 { (used as f64 / total as f64) * 100.0 } else { 0.0 };

    Ok(SysInfo {
        cpu_pct: 0.0,
        ram_pct: ram_pct as f32,
        ram_total_gb: total as f64 / 1_073_741_824.0,
        ram_used_gb: used as f64 / 1_073_741_824.0,
        host: hostname(),
        os: std::env::consts::OS.to_string(),
        bateria: None,
    })
}

fn hostname() -> String {
    std::env::var("COMPUTERNAME")
        .or_else(|_| std::env::var("HOSTNAME"))
        .unwrap_or_else(|_| "desconocido".into())
}

fn open_url_inner(app: &AppHandle, url: String) -> R<()> {
    if !(url.starts_with("http://") || url.starts_with("https://")) {
        return Err(format!("solo se abren URLs http(s): {url}"));
    }
    app.opener().open_url(url, None::<&str>).map_err(|e| e.to_string())
}

fn get_config_inner(state: &Arc<AppState>) -> Config {
    state.cfg()
}

fn set_config_inner(app: &AppHandle, state: &Arc<AppState>, config: Config) -> R<()> {
    let store = app
        .store("daniela-config.json")
        .map_err(|e| format!("no abro el almacen: {e}"))?;
    let json = serde_json::to_value(&config).map_err(|e| e.to_string())?;
    store.set("config", json);
    store.save().map_err(|e| e.to_string())?;
    *state.config.write() = config;
    let _ = app.emit("config-changed", ());
    Ok(())
}

// ── Wrappers publicos para `invoke` desde JS (aceptan tauri::State) ──

#[tauri::command]
pub fn get_avatar_state(state: State<'_, Arc<AppState>>) -> R<AvatarState> {
    get_avatar_state_inner(state.inner())
}

#[tauri::command]
pub fn set_avatar_state(app: AppHandle, state: State<'_, Arc<AppState>>, nuevo: String) -> R<AvatarState> {
    set_avatar_state_inner(&app, state.inner(), nuevo)
}

#[tauri::command]
pub fn set_morph(state: State<'_, Arc<AppState>>, name: String, value: f32) -> R<Morphs> {
    set_morph_inner(state.inner(), name, value)
}

#[tauri::command]
pub fn get_morphs(state: State<'_, Arc<AppState>>) -> Morphs {
    get_morphs_inner(state.inner())
}

#[tauri::command]
pub fn report_active_window(state: State<'_, Arc<AppState>>, titulo: Option<String>) -> R<()> {
    report_active_window_inner(state.inner(), titulo)
}

#[tauri::command]
pub fn start_capture(state: State<'_, Arc<AppState>>, objetivo: Option<String>) -> R<String> {
    start_capture_inner(state.inner(), objetivo)
}

#[tauri::command]
pub fn stop_capture() -> R<()> {
    stop_capture_inner()
}

#[tauri::command]
pub fn capture_status() -> serde_json::Value {
    capture_status_inner()
}

#[tauri::command]
pub fn get_capture_frame(max_ancho: Option<u32>) -> R<Option<String>> {
    get_capture_frame_inner(max_ancho)
}

#[tauri::command]
pub fn list_windows() -> R<Vec<crate::capture::WinInfo>> {
    list_windows_inner()
}

#[tauri::command]
pub fn list_monitors() -> R<Vec<crate::capture::MonitorInfo>> {
    list_monitors_inner()
}

#[tauri::command]
pub fn toggle_avatar(app: AppHandle) -> R<bool> {
    toggle_avatar_inner(&app)
}

#[tauri::command]
pub fn set_avatar_position(state: State<'_, Arc<AppState>>, x: i32, y: i32) -> (i32, i32) {
    set_avatar_position_inner(state.inner(), x, y)
}

#[tauri::command]
pub fn get_avatar_position(state: State<'_, Arc<AppState>>) -> (i32, i32) {
    get_avatar_position_inner(state.inner())
}

#[tauri::command]
pub fn show_menu(app: AppHandle, state: State<'_, Arc<AppState>>, pestana: Option<String>) -> R<()> {
    show_menu_inner(&app, state.inner(), pestana)
}

#[tauri::command]
pub fn hide_menu(app: AppHandle, state: State<'_, Arc<AppState>>) -> R<()> {
    hide_menu_inner(&app, state.inner())
}

#[tauri::command]
pub fn set_menu_tab(app: AppHandle, state: State<'_, Arc<AppState>>, tab: String) -> R<()> {
    set_menu_tab_inner(&app, state.inner(), tab)
}

#[tauri::command]
pub fn system_info() -> R<SysInfo> {
    system_info_inner()
}

#[tauri::command]
pub fn open_url(app: AppHandle, url: String) -> R<()> {
    open_url_inner(&app, url)
}

#[tauri::command]
pub fn get_config(state: State<'_, Arc<AppState>>) -> Config {
    get_config_inner(state.inner())
}

#[tauri::command]
pub fn set_config(app: AppHandle, state: State<'_, Arc<AppState>>, config: Config) -> R<()> {
    set_config_inner(&app, state.inner(), config)
}