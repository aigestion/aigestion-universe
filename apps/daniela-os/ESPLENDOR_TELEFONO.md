# Máximo Esplendor — 16 ideas épicas para el Pixel

**Pixel 8a · Tensor G3 · Android 17 (SDK 37) · 8 GB RAM · 46 GB libres**
Todo verificado en el dispositivo con `pm list features` y `getprop`. **Todo gratis ($0/mes).**

> Antes de las ideas: ya tienes **15 módulos y 162 rutas** escritos y probados en el PC.
> El móvil tiene **2 endpoints falsos**. La idea nº 1 no es una idea nueva: es la que
> desbloquea las otras 15.

---

## ✅ Estado: FASE 10 IMPLEMENTADA (E-19 … E-26)

Las 8 capacidades de hardware que estaban declaradas y sin usar están ahora escritas,
probadas y **subidas al móvil**.

**218 rutas reales** (162 → 218, +56) · 35 módulos en `/sdcard/DanielaOS/deploy/` ·
**0 `os.system` / 0 `shell=True`** (escaneo AST).

| # | Módulo | Rutas | Qué hace | Cómo degrada |
|---|---|---|---|---|
| E-19 | `wifi_rtt.py` | 7 | Posición interior sin GPS: huella WiFi + barómetro para la planta | Sin RTT usa solo RSSI; sin barómetro, ignora la planta |
| E-20 | `wifi_aware.py` | 6 | Malla sin infraestructura: beacon UDP + 4 transportes → sincroniza E-11 | Sin WiFi Aware cae a hotspot y luego a LAN |
| E-21 | `context_hub.py` | 8 | El wakelock de 10 días pasa a decidirse con batería, temperatura y hora | Sin coprocesador usa `termux-job-scheduler` |
| E-22 | `silicon_vault.py` | 8 | Secretos cifrados con clave derivada; nunca en texto plano | Sin Titan M2 avisa `almacen: archivo` |
| E-23 | `desktop_mode.py` | 7 | El Pixel como ordenador por USB-C → HDMI | Sin pantalla externa lo dice, no falla |
| E-24 | `live_wallpaper.py` | 6 | Fondo que cambia con el contexto (9 temas, PNG generado a mano) | Sin `termux-wallpaper` guarda el PNG igual |
| E-25 | `nfc_hce.py` | 8 | El móvil como llave: desafío-respuesta HMAC + TOTP, clave por cerradura | Sin `termux-nfc` sigue emitiendo códigos |
| E-26 | `stereo_vision.py` | 6 | Profundidad real con dos fotos, sin OpenCV ni numpy | Con dos fotos iguales te pide que muevas el móvil |

### Lo que se probó antes de subirlo
- **E-19**: cocina→conf 0,95 · salón→conf 0,96 · mitad del camino→conf 0,47.
- **E-20**: descarta payloads no JSON, no se descubre a sí mismo, expira peers.
- **E-21**: matriz completa — sano mantiene · 18 % suelta · 45 °C suelta ·
  enchufado mantiene · emergencia fuerza mantener.
- **E-22**: el texto plano no aparece en disco · PIN malo rechaza ·
  cifrado manipulado se detecta.
- **E-24**: 6 temas generan PNG válidos de 360×780.
- **E-25**: reto reutilizado se rechaza · claves distintas por cerradura ·
  6 fallos seguidos bloquean 300 s.
- **E-26**: la caja sintética (disparidad 20) se detecta más cerca que el fondo (8)
  en 0,5 s; PNG corrupto da error controlado.

### Dos decisiones que conviene conocer
- **HCE real no es posible desde Termux** sin root: Android no deja registrar un
  `HostApduService` por línea de comandos. En vez de fingirlo, el módulo hace la
  mitad que de verdad importa (la criptográfica, correcta y con claves separadas)
  y deja el enganche listo para cuando exista app.
- **Estéreo de movimiento**, no dos cámaras a la vez: haces una foto, mueves el
  móvil unos centímetros, haces otra. Es lo que haces tú con la cabeza. La vía de
  dos sensores simultáneos necesita rectificar ópticas distintas y está marcada
  como experimental.

---

## Lo que el teléfono puede hacer y no sabías

Verificado hoy en tu dispositivo:

| Capacidad | Evidencia | Por qué importa |
|---|---|---|
| `com.google.android.aicore` | **instalado** | Gemini Nano on-device: IA gratis, offline y privada |
| `wifi.rtt` | presente | Posición interior a **1–2 m sin GPS** |
| `wifi.aware` | presente | Malla P2P **sin router ni internet** |
| `context_hub` | presente | Sensores always-on en coprocesador, **sin despertar la CPU** |
| `strongbox_keystore` + `device_unique_attestation` | Titan M2 | Llaves en silicio, no en un `.env` |
| `nfc.hce` + `nfc.ese` + `com.nxp.mifare` | completo | El móvil como tarjeta, llave y lector |
| `camera.capability.raw` + `manual_sensor` + `concurrent` | nivel FULL | Dos cámaras a la vez, en RAW |
| `freeform_window_management` + `activities_on_secondary_displays` | activos | **Modo escritorio** real |
| `sensor.barometer` | presente | Detecta la planta de un edificio |
| `virtualization_framework` | presente | Puede correr máquinas virtuales |
| `vulkan.compute` + Tensor G3 | NPU/TPU | Inferencia acelerada por hardware |
| `ADAPTIVE_CHARGING` | presente | Batería sana durante años |

---

## NIVEL 1 · El cimiento

### 1 · Daniela nativa de verdad
**Esfuerzo:** 10 min · **Impacto:** desbloquea todo

El móvil sirve `/` y `/api/skills/dispatch`, y el dispatcher responde `200 OK` **sin ejecutar nada**.
Hay 162 rutas esperando en `/sdcard/DanielaOS/deploy/`.

```sh
# En Termux:
bash /sdcard/DanielaOS/deploy/install.sh
```

Sin esto, las otras 15 ideas son decorado sobre un maniquí.

### 2 · Cerebro local gratis: Gemini Nano (con red de seguridad)
**Esfuerzo:** 4 h · **Impacto:** crítico · **Hardware:** `aicore` + Tensor G3

`com.google.android.aicore` ya está en el teléfono: es el motor que sirve **Gemini Nano**,
un modelo que corre en la NPU. Cero euros, cero latencia de red, cero datos saliendo del móvil.

> ⚠️ **Honestidad**: el acceso de terceros a Gemini Nano está **capatado por Google**
> (lista blanca de apps). Puede que no se pueda usar desde Termux.
> **Red de seguridad**: el plan B es mejor a corto plazo — ver idea 3.

### 3 · Daniela Offline con llama.cpp y el modelo que YA tienes
**Esfuerzo:** 6 h · **Impacto:** crítico · **Ahorro:** 500 MB y un cuarto motor

Ya hay un GGUF en el móvil y no lo estamos usando:

```
/sdcard/Android/data/com.llmproxy/files/models/
  Qwen_Qwen2.5-0.5B-Instruct-GGUF/qwen2.5-0.5b-instruct-q4_k_m.gguf   491 MB
```

**E-13 no debe descargar un modelo nuevo.** Compila `llama.cpp` con `OpenBLAS`/`Vulkan`
(Tensor G3 tiene GPU Vulkan) y apunta al GGUF existente. Daniela razonando en el
bolsillo, en el metro, en el avión, sin red y sin factura.

---

## NIVEL 2 · El esplendor que se ve

### 4 · Modo escritorio: el Pixel es un ordenador
**Esfuerzo:** 2 h · **Impacto:** alto · **Hardware:** `freeform_window_management`

El dispositivo declara **ventanas libres** y **actividades en pantallas secundarias**.
Con un cable USB-C→HDMI y **Termux:X11**, el móvil se convierte en un PC Linux de
bolsillo: Daniela a pantalla completa, teclado y ratón Bluetooth. Gratis.

### 5 · Wallpaper vivo gobernado por Daniela
**Esfuerzo:** 3 h · **Impacto:** medio-alto (el que más se *nota*)

`live_wallpaper` está soportado y el **context engine (E-05)** ya distingue
`durmiendo / en_casa / caminando / en_vehículo / en_mano`. Que el fondo cambie con
el contexto: el teléfono deja de ser "un móvil con una app" y pasa a *ser* Daniela.

### 6 · Cara y voz: Termux:Styling + widget vivo
**Esfuerzo:** 1 h · **Impacto:** medio

Terminal con la paleta de Daniela (cian `#00ffff` / magenta `#ff0055` sobre `#0b0f19`)
y un widget en la pantalla de inicio con su estado real, no un icono bonito.

---

## NIVEL 3 · Superpoderes de hardware

### 7 · Posición interior al metro sin GPS — WiFi RTT
**Esfuerzo:** 5 h · **Impacto:** alto · **Hardware:** `wifi.rtt`

E-12 (Nodos Urbanos) quería saber "estoy en casa" sin encender el GPS.
**WiFi RTT (802.11mc)** mide la distancia real a los puntos de acceso por tiempo de
vuelo del paquete: precisión de **1–2 metros** y un consumo mínimo. Sumado al
**barómetro** para distinguir la planta, Daniela sabrá *en qué habitación* estás
sin gastar batería.

### 8 · Malla sin infraestructura — WiFi Aware
**Esfuerzo:** 5 h · **Impacto:** alto · **Hardware:** `wifi.aware`

E-11 (Daniela Mesh) sincroniza por HTTP y necesita red. **WiFi Aware** permite que dos
dispositivos se descubran y se hablen **sin router, sin internet y sin emparejamiento**.
Daniela Mesh de verdad: en el metro, en el campo, en un avión.

### 9 · Daniela siempre encendida sin wakelock — Context Hub
**Esfuerzo:** 6 h · **Impacto:** crítico (batería) · **Hardware:** `context_hub`

Hoy el teléfono lleva **10 días sin suspensión profunda** por un `PARTIAL_WAKE_LOCK`.
El **Context Hub** es un coprocesador que vigila acelerómetro, pasos y luz consumiendo
milivatios, y solo despierta a la CPU cuando pasa algo relevante.

Es la solución elegante al problema de fondo: **Daniela sigue viva y el móvil duerme.**
Además hace el wakelock *battery-aware*: se suelta con batería baja o de noche.

### 10 · Las llaves de Daniela en silicio — Titan M2
**Esfuerzo:** 3 h · **Impacto:** crítico (seguridad) · **Hardware:** `strongbox_keystore`

Tenemos un **P0 abierto**: una `GEMINI_API_KEY` real trackeada en git. El móvil tiene
StrongBox (`=300`), keystore de hardware (`=500`) y atestación de dispositivo.

`termux-keystore` guarda ahí la API key y el PIN: **la clave nunca existe como texto
plano en disco**. Un `.env` se puede filtrar; un secreto en Titan M2 no se puede extraer.

### 11 · El móvil como llave y tarjeta — NFC HCE
**Esfuerzo:** 4 h · **Impacto:** alto · **Hardware:** `nfc.hce`, `nfc.ese`, `com.nxp.mifare`

E-08 solo *lee* tags. Con **HCE** el Pixel *emula*: tarjetas, llaves, identificaciones.
Y con `com.nxp.mifare` lee tags reales del mundo, no solo los que compres tú.
Daniela abre la puerta de casa al acercar el móvil.

### 12 · Ojos de verdad — cámara RAW concurrente
**Esfuerzo:** 4 h · **Impacto:** alto · **Hardware:** `camera.concurrent`, `raw`, `manual_sensor`

El dispositivo es **nivel FULL**: puede abrir **dos cámaras a la vez**, capturar en RAW y
controlar el sensor a mano. E-screen vision pasaría de "analizar una captura" a
**visión estéreo** con profundidad real.

---

## NIVEL 4 · Autonomía radical

### 13 · Syncthing: PC ↔ Pixel sin nube
**Esfuerzo:** 1 h · **Impacto:** alto

P2P, cifrado, sin servidor, sin cuota, sin límites. Complementa E-11: los CRDT resuelven
*conflictos*, Syncthing mueve *ficheros*. Juntos son Dropbox gratis y privado.

### 14 · Cloudflare Tunnel bien hecho (o apagado)
**Esfuerzo:** 30 min · **Impacto:** seguridad

Hoy hay un túnel público apuntando a un servidor que **no ejecuta nada**. Dos opciones,
y mantenerlo como está no es una de ellas:
- **Apagarlo**: `sv down cloudflared` en Termux.
- **Arreglarlo**: apuntarlo a DanielaOS real (`:5000`) con el token `X-Pixel-Token`
  y tener a Daniela accesible desde cualquier parte, gratis.

### 15 · Sandbox con virtualización
**Esfuerzo:** 8 h · **Impacto:** medio · **Hardware:** `virtualization_framework`

Daniela ejecuta código. Hoy lo ejecuta donde vive. Con el framework de virtualización
puede lanzar una VM ligera como **jaula desechable** para código que no se atreve a
correr en el sistema principal. Seguridad de verdad para un agente autónomo.

### 16 · El móvil como servidor, el PC como cliente
**Esfuerzo:** 6 h · **Impacto:** transformador

Invertir la arquitectura: PRoot + Ubuntu en Termux + X11 + los 162 endpoints de
DanielaOS corriendo **en el Pixel**. El PC deja de ser el cerebro y pasa a ser una
ventana más. Daniela vive en tu bolsillo y se proyecta donde haga falta.

---

## Orden recomendado

| Cuándo | Ideas | Resultado |
|---|---|---|
| **Hoy** | 1 · 14 | El móvil deja de mentir y deja de estar expuesto |
| **Semana 1** | 3 · 6 · 13 | Daniela razonando offline, con cara y con sync |
| **Semana 2** | 10 · 9 | Cerramos el P0 de seguridad y el wakelock de 10 días |
| **Mes 1** | 5 · 7 · 8 · 4 | Se ve, se mueve y se despliega en pantalla grande |
| **Mes 2** | 11 · 12 · 2 · 16 | Superpoderes de hardware y arquitectura invertida |
| **Después** | 15 | Jaula para código no confiable |

---

## Métrica de "esplendor"

Cómo saber que vas bien:

| Hoy | Objetivo |
|---|---|
| 2 endpoints (uno falso) | **218 rutas reales** ✅ escritas, falta instalar |
| Swap al 98,5 % | **< 60 %** (E-21 ataca la causa) |
| Wakelock de 10 días | **< 1 h al día** ✅ módulo listo |
| 4 motores de IA sin usar ninguno | **1 motor, en la NPU** |
| API key en texto plano | **clave en Titan M2** ✅ módulo listo |
| 64 GB usados | **63 GB** (46 libres) |
| El PC manda | **Daniela vive en el móvil** ← falta esto |

### El único paso que queda pendiente (lo haces tú, 1 minuto)

En Termux, en el móvil:

```bash
cp -r /sdcard/DanielaOS/deploy ~/daniela-os && cd ~/daniela-os && bash install.sh
```

Hasta que eso no corra, las 218 rutas viven en el PC y en `/sdcard`, pero el
móvil sigue sirviendo el HUD falso del puerto 8082.

### Avisos que siguen abiertos
1. **Rotar la Gemini API key y purgar `.env` del historial** (P0). Los módulos
   nuevos no la usan, pero el historial de git la sigue conteniendo.
2. **`cloudflared` expone a internet el HUD falso** del 8082. Decidir si se apaga.
3. 46 commits sin pushear (GitHub auth no disponible desde aquí).
