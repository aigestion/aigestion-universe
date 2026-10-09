//! Estado compartido del proceso.
//!
//! Un solo `AppState` vive en el `tauri::Builder::manage()`. El WebView no
//! guarda estado de verdad: siempre pregunta por aqui, de modo que la UI y el
//! backend no puedan divergir.

use parking_lot::RwLock;
use serde::{Deserialize, Serialize};

// ── Configuracion persistida ───────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct Config {
    pub avatar: AvatarConfig,
    pub voice: VoiceConfig,
    pub capture: CaptureConfig,
    pub menu: MenuConfig,
    pub comportamiento: BehaviorConfig,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            avatar: AvatarConfig::default(),
            voice: VoiceConfig::default(),
            capture: CaptureConfig::default(),
            menu: MenuConfig::default(),
            comportamiento: BehaviorConfig::default(),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct AvatarConfig {
    /// Multiplicador de tamano (0.5 .. 2.0).
    pub escala: f32,
    pub opacidad: f32,
    /// Minutos sin interaccion antes de dormir.
    pub auto_sleep_min: u64,
    /// Perfil de personalidad (companion, focus, mentor, playful, guardian).
    pub personalidad: String,
    /// Segundos que Daniela aguanta "encendida" antes de LetsPlay con aburrimiento.
    pub timeout_descanso: u64,
}

impl Default for AvatarConfig {
    fn default() -> Self {
        Self {
            escala: 0.2,
            opacidad: 1.0,
            auto_sleep_min: 30,
            personalidad: "companion".into(),
            timeout_descanso: 45,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct VoiceConfig {
    pub habilitada: bool,
    pub velocidad: f32,
    pub tono: f32,
    pub volumen: f32,
    /// Idioma BCP-47 para Web Speech (`es-ES`, `en-US`...).
    pub idioma: String,
    /// Usar TTS neuronal del servidor (`/api/voice/tts`) en vez del dispositivo.
    pub tts_servidor: bool,
}

impl Default for VoiceConfig {
    fn default() -> Self {
        Self {
            habilitada: true,
            velocidad: 1.0,
            tono: 1.05,
            volumen: 0.8,
            idioma: "es-ES".into(),
            tts_servidor: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct CaptureConfig {
    pub habilitada: bool,
    /// Pedir confirmacion en cada captura.
    pub confirmar_siempre: bool,
    /// Objetivo por defecto: `monitor` o `window:<titulo>`.
    pub objetivo: String,
    /// Ancho maximo del PNG servido (px). 0 = sin escalar.
    pub ancho_max: u32,
    /// Fotogramas por segundo solicitados a WGC.
    pub fps: i32,
}

impl Default for CaptureConfig {
    fn default() -> Self {
        Self {
            habilitada: false,
            confirmar_siempre: true,
            objetivo: "monitor".into(),
            ancho_max: 1600,
            fps: 10,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct MenuConfig {
    pub pestana_inicial: String,
    /// Origen del backend Daniela (Flask). `None` = misma ventana.
    pub backend: String,
}

impl Default for MenuConfig {
    fn default() -> Self {
        Self {
            pestana_inicial: "gev".into(),
            backend: "http://127.0.0.1:9200".into(),
        }
    }
}

/// Ajustes de las conductas "wow": ambiente, aburrimiento y proactividad.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", default)]
pub struct BehaviorConfig {
    /// Burbuja de texto al despertar.
    pub hablar_al_despertar: bool,
    /// Reaccionar a la ventana activa (inclinar la cabeza).
    pub notar_ventana_activa: bool,
    /// Mirar al cursor tras unos segundos de inactividad.
    pub seguir_cursor: bool,
    /// Celebraciones (commits, tests, deploys) con particulas.
    pub celebrar_logros: bool,
    /// Permitir micro-acciones de aburrimiento (bostezar, tararear...).
    pub micro_acciones: bool,
    /// Semilla de la personalidad: fija behaviors, cambia la "vibe".
    pub semilla: Option<u64>,
}

impl Default for BehaviorConfig {
    fn default() -> Self {
        Self {
            hablar_al_despertar: true,
            notar_ventana_activa: true,
            seguir_cursor: true,
            celebrar_logros: true,
            micro_acciones: true,
            semilla: None,
        }
    }
}

// ── Estado vivo ────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AvatarState {
    /// Dormida: casi no renderiza, noMolesta.
    Sleeping,
    /// Encendida, esperando.
    Idle,
    /// Escuchando al usuario.
    Listening,
    /// Procesando / pensando.
    Thinking,
    /// Hablando.
    Talking,
    /// Encendida pero aburrida: sigh, bostezos, micro-acciones.
    Resting,
}

impl AvatarState {
    pub fn as_str(self) -> &'static str {
        match self {
            AvatarState::Sleeping => "sleeping",
            AvatarState::Idle => "idle",
            AvatarState::Listening => "listening",
            AvatarState::Thinking => "thinking",
            AvatarState::Talking => "talking",
            AvatarState::Resting => "resting",
        }
    }

    pub fn from_str(s: &str) -> Option<Self> {
        Some(match s {
            "sleeping" => AvatarState::Sleeping,
            "idle" => AvatarState::Idle,
            "listening" => AvatarState::Listening,
            "thinking" => AvatarState::Thinking,
            "talking" => AvatarState::Talking,
            "resting" => AvatarState::Resting,
            _ => return None,
        })
    }
}

/// Los 8 morph targets del GLB rigged + los procedurales.
#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Morphs {
    pub blink: f32,
    pub jaw_open: f32,
    pub brow_up: f32,
    pub brow_furrow: f32,
    pub smile: f32,
    pub sigh: f32,
    pub brow_down: f32,
    pub head_tilt: f32,
}

impl Morphs {
    pub fn set(&mut self, name: &str, value: f32) -> bool {
        let v = value.clamp(0.0, 1.0);
        match name {
            "blink" => self.blink = v,
            "jawOpen" => self.jaw_open = v,
            "browUp" => self.brow_up = v,
            "browFurrow" => self.brow_furrow = v,
            "browDown" => self.brow_down = v,
            "smile" => self.smile = v,
            "sigh" => self.sigh = v,
            // headTilt es bipolar: -1..1, no se recorta arriba.
            "headTilt" => self.head_tilt = value.clamp(-1.0, 1.0),
            _ => return false,
        }
        true
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SysInfo {
    pub cpu_pct: f32,
    pub ram_pct: f32,
    pub ram_total_gb: f64,
    pub ram_used_gb: f64,
    pub host: String,
    pub os: String,
    /// Carga detectada de bateria 0..1, o `None` en sobremesa.
    pub bateria: Option<f32>,
}

pub struct AppState {
    pub config: RwLock<Config>,
    pub avatar_state: RwLock<AvatarState>,
    pub morphs: RwLock<Morphs>,
    pub menu_visible: RwLock<bool>,
    pub pestana: RwLock<String>,
    /// Ventana activa vista por la Ultima vez (para "notar ventana activa").
    pub ventana_activa: RwLock<Option<String>>,
    /// Posicion persistida de la ventana del avatar.
    pub posicion: RwLock<(i32, i32)>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            config: RwLock::new(Config::default()),
            avatar_state: RwLock::new(AvatarState::Sleeping),
            morphs: RwLock::new(Morphs::default()),
            menu_visible: RwLock::new(false),
            pestana: RwLock::new("gev".into()),
            ventana_activa: RwLock::new(None),
            posicion: RwLock::new((120, 120)),
        }
    }

    pub fn cfg(&self) -> Config {
        self.config.read().clone()
    }

    pub fn estado(&self) -> AvatarState {
        *self.avatar_state.read()
    }

    pub fn set_estado(&self, e: AvatarState) {
        *self.avatar_state.write() = e;
    }
}