//! Captura de pantalla y ventanas en Windows.
//!
//! Envuelve `windows-capture` (Windows Graphics Capture API). El frame mas
//! reciente se guarda en un buffer global para que el comando
//! `get_capture_frame` lo sirva como PNG en base64; el evento
//! `capture-frame-ready` avisa al WebView para que lo pida.
//!
//! La sesion corre en un hilo propio (`start_free_threaded`), nunca en el
//! hilo de Tauri: `Capture::start` se queda esperando y bloquearia la UI.

use base64::Engine;
use image::{ImageFormat, ImageBuffer, Rgba};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex, OnceLock};
use windows_capture::capture::GraphicsCaptureApiHandler;
use windows_capture::frame::Frame;
use windows_capture::graphics_capture_api::InternalCaptureControl;
use windows_capture::monitor::Monitor;
use windows_capture::settings::{
    ColorFormat, CursorCaptureSettings, DirtyRegionSettings, DrawBorderSettings,
    MinimumUpdateIntervalSettings, SecondaryWindowSettings, Settings,
};
use windows_capture::window::Window;

/// Ultimo frame capturado: bytes RGBA + dimensiones.
struct FrameBuffer {
    rgba: Vec<u8>,
    width: u32,
    height: u32,
    /// Epoch del frame, para que el consumidor detecte uno nuevo.
    seq: u64,
}

fn ultimo_frame() -> &'static Mutex<Option<FrameBuffer>> {
    static BUF: OnceLock<Mutex<Option<FrameBuffer>>> = OnceLock::new();
    BUF.get_or_init(|| Mutex::new(None))
}

fn secuencia() -> &'static AtomicU64 {
    static SEQ: OnceLock<AtomicU64> = OnceLock::new();
    SEQ.get_or_init(|| AtomicU64::new(0))
}

/// Control de la sesion activa. `None` = no hay captura corriendo.
fn control() -> &'static Mutex<Option<CaptureStop>> {
    static CTRL: OnceLock<Mutex<Option<CaptureStop>>> = OnceLock::new();
    CTRL.get_or_init(|| Mutex::new(None))
}

/// Lo unico que hace falta guardar para poder parar la captura.
struct CaptureStop(Arc<AtomicBool>);

impl Drop for CaptureStop {
    fn drop(&mut self) {
        self.0.store(true, Ordering::SeqCst);
    }
}

// ── Handler ────────────────────────────────────────────────────────

/// Recibe frames de Windows Graphics Capture y los copia al buffer global.
///
/// No guarda nada mas: el buffer global es la unica fuente de verdad para que
/// el comando IPC y el WebView nunca vean datos distintos.
struct FrameSink;

type CaptureError = Box<dyn std::error::Error + Send + Sync>;

impl GraphicsCaptureApiHandler for FrameSink {
    type Flags = (i32, i32);
    type Error = CaptureError;

    fn new(_ctx: windows_capture::capture::Context<Self::Flags>) -> Result<Self, Self::Error> {
        Ok(Self)
    }

    fn on_frame_arrived(
        &mut self,
        frame: &mut Frame,
        _control: InternalCaptureControl,
    ) -> Result<(), Self::Error> {
        let width = frame.width();
        let height = frame.height();
        // Pedimos el buffer ya sin padding y comprobamos el orden de canales:
        // con `ColorFormat::Rgba8` el frame suele llegar en RGBA, pero
        // Windows puede servir BGRA; solo intercambiamos en ese caso.
        let fb = frame.buffer()?;
        let mut crudo = Vec::new();
        let sin_padding = fb.as_nopadding_buffer(&mut crudo);
        let bgra = matches!(fb.color_format(), ColorFormat::Bgra8);
        let mut rgba = Vec::with_capacity(sin_padding.len());
        for px in sin_padding.chunks_exact(4) {
            if bgra {
                rgba.extend_from_slice(&[px[2], px[1], px[0], px[3]]);
            } else {
                rgba.extend_from_slice(px);
            }
        }

        let seq = secuencia().fetch_add(1, Ordering::Relaxed) + 1;
        if let Ok(mut buf) = ultimo_frame().try_lock() {
            *buf = Some(FrameBuffer {
                rgba,
                width,
                height,
                seq,
            });
        } else {
            tracing::debug!("frame {seq} descartado: el consumidor aun no ha liberado el buffer");
        }
        Ok(())
    }

    fn on_closed(&mut self) -> Result<(), Self::Error> {
        tracing::info!("sesion de captura cerrada por Windows");
        Ok(())
    }
}

// ── Arranque / parada ──────────────────────────────────────────────

/// Inicia captura del monitor principal o de una ventana concreta.
///
/// `target` admite:
///   - `None` o `"monitor"` / `"primary"` -> monitor principal
///   - `"window:<titulo>"`                -> ventana cuyo titulo contiene eso
///   - `"window-exact:<titulo>"`          -> coincidencia exacta
///
/// Devuelve un resumen legible para la UI (tipo, titulo, dimensiones).
pub fn start(
    target: Option<&str>,
    include_cursor: bool,
    max_fps: Option<i32>,
) -> Result<String, String> {
    if control().lock().map(|g| g.is_some()).unwrap_or(false) {
        return Err("ya hay una captura activa".into());
    }

    let target = target.unwrap_or("monitor").to_string();
    match target.as_str() {
        "monitor" | "primary" | "screen" | "all" => {
            let monitor = Monitor::primary().map_err(|e| format!("monitor principal: {e}"))?;
            let (w, h) = (
                monitor.width().map_err(|e| e.to_string())?,
                monitor.height().map_err(|e| e.to_string())?,
            );
            let name = monitor.name().unwrap_or_else(|_| "monitor".into());
            let settings = build_settings(monitor, include_cursor, max_fps, (w as i32, h as i32));
            arrancar(settings, format!("monitor «{name}» {w}x{h}"))
        }
        other => {
            let (exacto, consulta) = match other.strip_prefix("window:") {
                Some(q) => (false, q),
                None => match other.strip_prefix("window-exact:") {
                    Some(q) => (true, q),
                    None => (false, other),
                },
            };
            if consulta.is_empty() {
                return Err("filtro de ventana vacio".into());
            }
            let ventana = if exacto {
                Window::from_name(consulta)
            } else {
                Window::from_contains_name(consulta)
            }
            .map_err(|e| format!("no encuentro la ventana «{consulta}»: {e}"))?;

            let titulo = ventana.title().unwrap_or_else(|_| consulta.into());
            let (w, h) = (
                ventana.width().map_err(|e| e.to_string())?,
                ventana.height().map_err(|e| e.to_string())?,
            );
            let settings = build_settings(ventana, include_cursor, max_fps, (w, h));
            arrancar(settings, format!("ventana «{titulo}» {w}x{h}"))
        }
    }
}

/// Lanza la sesion de captura en su propio hilo y registra el control de parada.
///
/// Genericos en `T` porque `Monitor` y `Window` son tipos distintos y cada rama
/// del `match` de `start` necesita su propio `Settings<_, T>`.
fn arrancar<T>(settings: Settings<(i32, i32), T>, descripcion: String) -> Result<String, String>
where
    T: TryInto<windows_capture::settings::GraphicsCaptureItemType> + Send + 'static,
{
    let handle = <FrameSink as GraphicsCaptureApiHandler>::start_free_threaded(settings)
        .map_err(|e| format!("no arranca Windows Graphics Capture: {e}"))?;

    *control().lock().map_err(|_| "estado de captura envenenado")? =
        Some(CaptureStop(handle.halt_handle()));

    tracing::info!("captura iniciada: {descripcion}");
    Ok(descripcion)
}

fn build_settings<T>(
    item: T,
    cursor: bool,
    max_fps: Option<i32>,
    flags: (i32, i32),
) -> Settings<(i32, i32), T>
where
    T: TryInto<windows_capture::settings::GraphicsCaptureItemType> + Send + 'static,
{
    Settings::new(
        item,
        if cursor {
            CursorCaptureSettings::WithoutCursor
        } else {
            CursorCaptureSettings::Default
        },
        DrawBorderSettings::Default,
        SecondaryWindowSettings::Default,
        MinimumUpdateIntervalSettings::Custom(std::time::Duration::from_millis(
            (1000 / max_fps.unwrap_or(10).clamp(1, 60)) as u64,
        )),
        DirtyRegionSettings::Default,
        ColorFormat::Rgba8,
        flags,
    )
}

/// Marca la captura activa para que pare sola. No bloquea: el hilo de captura
/// termina en su propio tiempo.
pub fn stop() -> Result<(), String> {
    match control().lock() {
        Ok(mut g) => {
            let habia = g.is_some();
            *g = None; // Drop -> halt_handle a true
            if habia {
                *ultimo_frame().lock().map_err(|_| "buffer envenenado")? = None;
            }
            Ok(())
        }
        Err(_) => Err("estado de captura envenenado".into()),
    }
}

pub fn activa() -> bool {
    control().lock().map(|g| g.is_some()).unwrap_or(false)
}

/// Numero de frame recibido hasta ahora. El WebView lo usa para no volver a
/// codificar a PNG un frame que ya tiene.
pub fn frames_recibidos() -> u64 {
    secuencia().load(Ordering::Relaxed)
}

/// Ultimo frame como PNG en base64 (`data:image/png;base64,...`).
///
/// Escala a un ancho maximo antes de codificar: un monitor 4K son ~33 MB de
/// RGBA crudos y un PNG de eso tarda segundos. 1600 px de ancho basta para que
/// Daniela lea la pantalla, y hace la respuesta ~1 MB.
pub fn frame_png_base64(max_ancho: u32) -> Result<Option<String>, String> {
    let (rgba, width, height, _seq) = {
        let buf = ultimo_frame().lock().map_err(|_| "buffer de frame envenenado")?;
        match buf.as_ref() {
            Some(f) => (f.rgba.clone(), f.width, f.height, f.seq),
            None => return Ok(None),
        }
    };

    if width == 0 || height == 0 {
        return Ok(None);
    }

    let img: ImageBuffer<Rgba<u8>, _> =
        ImageBuffer::from_raw(width, height, rgba).ok_or("frame con dimensiones invalidas")?;

    let img = if max_ancho > 0 && width > max_ancho {
        let alto = (height as f64 * max_ancho as f64 / width as f64).round() as u32;
        image::imageops::resize(
            &img,
            max_ancho,
            alto.max(1),
            image::imageops::FilterType::Triangle,
        )
    } else {
        img
    };

    let mut png = Vec::new();
    img.write_to(&mut std::io::Cursor::new(&mut png), ImageFormat::Png)
        .map_err(|e| format!("no se codifica el PNG: {e}"))?;

    Ok(Some(format!(
        "data:image/png;base64,{}",
        base64::engine::general_purpose::STANDARD.encode(&png)
    )))
}

// ── Inventario de ventanas y monitores ────────────────────────────

#[derive(serde::Serialize, Clone)]
pub struct WinInfo {
    pub titulo: String,
    pub proceso: String,
    pub x: i32,
    pub y: i32,
    pub ancho: i32,
    pub alto: i32,
}

#[derive(serde::Serialize, Clone)]
pub struct MonitorInfo {
    pub indice: usize,
    pub nombre: String,
    pub dispositivo: String,
    pub ancho: u32,
    pub alto: u32,
    pub hz: u32,
}

/// Ventanas visibles con titulo, para que el usuario elija que capturar.
pub fn listar_ventanas() -> Result<Vec<WinInfo>, String> {
    let mut out = Vec::new();
    for w in Window::enumerate().map_err(|e| format!("no se enumeran ventanas: {e}"))? {
        if !w.is_valid() {
            continue;
        }
        // Sin titulo = ventana oculta, tool window o splash: no interestan.
        let Ok(titulo) = w.title() else { continue };
        if titulo.trim().is_empty() {
            continue;
        }
        let (x, y) = match w.rect() {
            Ok(r) => (r.left, r.top),
            Err(_) => (0, 0),
        };
        let (ancho, alto) = match (w.width(), w.height()) {
            (Ok(a), Ok(h)) => (a, h),
            _ => continue,
        };
        if ancho <= 1 || alto <= 1 {
            continue; // minimizada o ya destruida
        }
        out.push(WinInfo {
            titulo,
            proceso: w.process_name().unwrap_or_else(|_| "desconocido".into()),
            x,
            y,
            ancho,
            alto,
        });
    }
    Ok(out)
}

pub fn listar_monitores() -> Result<Vec<MonitorInfo>, String> {
    let mut out = Vec::new();
    for m in Monitor::enumerate().map_err(|e| format!("no se enumeran monitores: {e}"))? {
        let indice = m.index().unwrap_or(out.len());
        out.push(MonitorInfo {
            indice,
            nombre: m.name().unwrap_or_else(|_| format!("monitor {indice}")),
            dispositivo: m.device_name().unwrap_or_default(),
            ancho: m.width().unwrap_or(0),
            alto: m.height().unwrap_or(0),
            hz: m.refresh_rate().unwrap_or(0),
        });
    }
    Ok(out)
}