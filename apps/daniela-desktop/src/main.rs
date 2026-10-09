//! Daniela Desktop: avatar 3D flotante para Windows.
//!
//! Dos ventanas WebView2:
//!   - `main` (avatar): 280x280, sin marco, transparente, siempre encima.
//!   - `menu` (vision): 900x700, normal, con las 4+M subpestanas.
//!
//! El "cerebro" sigue siendo el backend Python de Daniela (GEV, memoria,
//! engines); este binario es solo la presencia en el escritorio.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod capture;
mod ipc;
mod state;

use std::sync::Arc;
use tauri::menu::{Menu, MenuItem, PredefinedMenuItem};
use tauri::tray::TrayIconBuilder;
use tauri::{Emitter, Manager};
use tauri_plugin_store::StoreExt;

use state::AppState;

/// Atajo global: Win+Alt+D enfoca/oculta el avatar.
const HOTKEY: &str = "Win+Alt+D";

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, sc, ev| {
                    use tauri_plugin_global_shortcut::ShortcutState;
                    if ev.id == sc.id() && ev.state == ShortcutState::Pressed {
                        let _ = ipc::toggle_avatar(app.clone());
                    }
                })
                .build(),
        )
        .manage(Arc::new(AppState::new()))
        .invoke_handler(tauri::generate_handler![
            ipc::get_avatar_state,
            ipc::set_avatar_state,
            ipc::set_morph,
            ipc::get_morphs,
            ipc::report_active_window,
            ipc::start_capture,
            ipc::stop_capture,
            ipc::capture_status,
            ipc::get_capture_frame,
            ipc::list_windows,
            ipc::list_monitors,
            ipc::toggle_avatar,
            ipc::set_avatar_position,
            ipc::get_avatar_position,
            ipc::show_menu,
            ipc::hide_menu,
            ipc::set_menu_tab,
            ipc::system_info,
            ipc::open_url,
            ipc::get_config,
            ipc::set_config,
        ])
        .setup(|app| {
            let handle = app.handle().clone();

            // Config persistida. Si no existe, la de por defecto.
            let store = handle.store("daniela-config.json")?;
            if store.get("config").is_none() {
                store.set("config", serde_json::to_value(state::Config::default())?);
                store.save()?;
            }
            if let Some(cfg) = store.get("config").and_then(|v| serde_json::from_value::<state::Config>(v).ok()) {
                *handle.state::<Arc<AppState>>().config.write() = cfg;
            }

            // La ventana del avatar no debe robar el foco al arrancar: aparece
            // en su esquina y espera a que la busquen.
            if let Some(w) = handle.get_webview_window("main") {
                let (x, y) = *handle.state::<Arc<AppState>>().posicion.read();
                let _ = w.set_position(tauri::Position::Physical(tauri::PhysicalPosition { x, y }));
                let _ = w.show();
            }
            let _ = handle
                .get_webview_window("menu")
                .map(|w| w.hide());

            crear_tray(&handle)?;
            registrar_hotkey(&handle)?;
            forzar_topmost();

            Ok(())
        })
        .on_window_event(|win, ev| {
            // Cerrar la ventana del avatar con la X es "adormecerla", no salir:
            // el proceso sigue vivo en la bandeja. Salir es explicito (tray).
            if let tauri::WindowEvent::CloseRequested { api, .. } = ev {
                if win.label() == "main" {
                    api.prevent_close();
                    let _ = win.hide();
                    if let Some(s) = win.app_handle().try_state::<Arc<AppState>>() {
                        s.set_estado(state::AvatarState::Sleeping);
                        let _ = win.app_handle().emit("avatar-state", "sleeping");
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("no se pudo iniciar Daniela Desktop");
}

fn crear_tray(handle: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    let mostrar = MenuItem::with_id(handle, "mostrar", "Enfocar a Daniela", true, None::<&str>)?;
    let menu = MenuItem::with_id(handle, "menu", "Abrir Vision Menu", true, None::<&str>)?;
    let captura = MenuItem::with_id(handle, "captura", "Capturar pantalla", true, None::<&str>)?;
    let s1 = PredefinedMenuItem::separator(handle)?;
    let salir = MenuItem::with_id(handle, "salir", "Salir", true, None::<&str>)?;

    let m = Menu::with_items(handle, &[&mostrar, &menu, &captura, &s1, &salir])?;

    let _tray = TrayIconBuilder::new()
        .icon(app_icon())
        .tooltip("Daniela")
        .menu(&m)
        .on_menu_event(|app, ev| {
            let state = app.state::<Arc<AppState>>();
            match ev.id().as_ref() {
                "mostrar" => {
                    let _ = ipc::toggle_avatar(app.clone());
                }
                "menu" => {
                    let _ = ipc::show_menu_inner(&app, &state.inner().clone(), None);
                }
                "captura" => {
                    let alterna = crate::capture::activa();
                    let _ = if alterna {
                        crate::capture::stop()
                    } else {
                        match crate::capture::start(Some("monitor"), true, Some(10)) {
                            Ok(desc) => {
                                let _ = app.emit("capture-state", true);
                                let _ = app.emit(
                                    "avatar-say",
                                    format!("Capturando {desc}. Dime que necesitas."),
                                );
                                Ok(())
                            }
                            Err(e) => Err(e),
                        }
                    };
                    let _ = app.emit("capture-state", !alterna);
                }
                "salir" => app.exit(0),
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, ev| {
            // Doble clic en la bandeja = abrir el vision menu.
            if let tauri::tray::TrayIconEvent::Click {
                button: tauri::tray::MouseButton::Left,
                button_state: tauri::tray::MouseButtonState::Up,
                ..
            } = ev
            {
                let app = tray.app_handle();
                let state = app.state::<Arc<AppState>>();
                let visible = app
                    .get_webview_window("menu")
                    .and_then(|w| w.is_visible().ok())
                    .unwrap_or(false);
                if visible {
                    let _ = ipc::hide_menu_inner(&app, &state.inner().clone());
                } else {
                    let _ = ipc::show_menu_inner(&app, &state.inner().clone(), None);
                }
            }
        })
        .build(handle)?;
    Ok(())
}

fn registrar_hotkey(handle: &tauri::AppHandle) -> Result<(), Box<dyn std::error::Error>> {
    use tauri_plugin_global_shortcut::GlobalShortcutExt;
    // El atajo global necesita permiso de primer plano en algunos setups; si
    // falla, la app sigue usable con el raton.
    if let Err(e) = handle.global_shortcut().register(HOTKEY) {
        tracing::warn!("no se pudo registrar {HOTKEY}: {e}");
    }
    Ok(())
}

/// Mantiene la ventana del avatar como TOPMOST aunque el DWM u otras apps
/// intenten poner algo encima. Hilo propio, cada 2 s. Sin SHOWWINDOW a
/// proposito: si el usuario oculta el avatar (bandeja), debe seguir oculto.
fn forzar_topmost() {
    std::thread::spawn(|| {
        use windows::{
            core::w,
            Win32::UI::WindowsAndMessaging::{
                FindWindowW, SetWindowPos, HWND_TOPMOST, SWP_NOACTIVATE, SWP_NOMOVE, SWP_NOSIZE,
            },
        };
        loop {
            std::thread::sleep(std::time::Duration::from_secs(2));
            unsafe {
                if let Ok(hwnd) = FindWindowW(None, w!("Daniela")) {
                    let _ = SetWindowPos(
                        hwnd,
                        HWND_TOPMOST,
                        0,
                        0,
                        0,
                        0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
                    );
                }
            }
        }
    });
}

fn app_icon() -> tauri::image::Image<'static> {
    // Sin icono propio, un rectangulo solido: la bandeja sigue siendo usable.
    tauri::image::Image::new_owned(vec![56, 189, 248, 255], 1, 1)
}

fn main() {
    run();
}