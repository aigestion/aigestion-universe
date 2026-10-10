# Auditoría Profunda del Pixel — DanielaOS

**Fecha:** 2026-09-10 · **Dispositivo:** Pixel 8a · **Android:** 17 (`CP2A.260805.005`, build `user`)
**Método:** ADB (sin root) + `dumpsys` + verificación MD5 de cada duplicado
**Alcance:** las 3 capas accesibles — `/storage/emulated/0` (completo), `/data/local/tmp`, y el
espacio de procesos/servicios. El home de Termux (`/data/data/com.termux/...`) sigue sellado
por Android; se audita desde fuera por `ps`/puertos.

---

## 1. Radiografía general

| Métrica | Valor | Estado |
|---|---|---|
| Almacenamiento | 68 GB usados de 110 GB (62 %) | OK |
| Ficheros en /sdcard | 6.853 | — |
| Directorios | 1.052 | — |
| Enlaces rotos | 0 | OK |
| Paquetes instalados | 468 | — |
| RAM libre | 332 MB de 7.573 MB (4 %) | **CRÍTICO** |
| Swap usado | 3.728 MB de 3.786 MB (**98,5 %**) | **CRÍTICO** |
| Batería | 86 %, 32,1 °C | OK |
| Temperatura CPU (LITTLE) | **77 °C** | ALTO |
| Carga media (1/5/15 min) | 4,19 / 5,84 / 5,79 | ALTO |
| Pantalla | bloqueada, IP 192.168.1.133/24 | — |

---

## 2. Dónde está realmente el espacio

| Ruta | Tamaño | Veredicto |
|---|---:|---|
| `Android/data/com.google.ai.edge.gallery` | 4,66 GB | Modelo Gemma 4 E2B + **1,48 GB de caché** |
| `Documents/NexusAI` | 3,19 GB | **Dos ficheros idénticos** de 1,52 GiB |
| `DCIM/Camera` | 726 MB | Tuyo — intocable |
| `Android/media/com.whatsapp.w4b` | 580 MB | Medio de WhatsApp Business |
| `Movies/` | 475 MB | 13 vídeos generados por Daniela |
| `Android/data/com.llmproxy` | 480 MB | Modelo Qwen 0.5B GGUF |
| `Download/` | 379 MB | APKs, OCR, organizado |
| `Pictures/` | 151 MB | Capturas + un duplicado |
| `.trash-storage/` | 86 MB | Papelera del gestor de ficheros |
| `DanielaOS/` | 3,7 MB | Nuestro bundle |

---

## 3. Redundancia confirmada (verificada por MD5, no por tamaño)

### 3.1 Duplicado exacto de 1,52 GiB — el hallazgo gordo

```
814d0dc106a099f581ffad0fad0218c0  Documents/NexusAI/gemma_soberano.bin
814d0dc106a099f581ffad0fad0218c0  Documents/NexusAI/gemma2-2b.bin
```

Mismo MD5, mismo tamaño (1.629.509.152 bytes). Son **el mismo fichero con dos nombres**.
Uno sobra. → **+1,52 GiB**

### 3.2 Cachés regenerables de Google AI Edge Gallery — 1,48 GiB

| Fichero | Tamaño |
|---|---:|
| `gemma-4-E2B-it.litertlm_..._mldrift_weight_cache.bin` | 746 MB |
| `tiny_garden.litertlm.xnnpack_cache_...` | 260 MB |
| `mobile_actions.litertlm.xnnpack_cache_...` | 260 MB |
| `...vision_encoder_..._mldrift_weight_cache.bin` | 145 MB |
| `...static_audio_encoder.xnnpack_cache` | 87 MB |
| `..._mldrift_program_cache.bin` | 12 MB |
| `...audio_adapter.xnnpack_cache` | 9 MB |

No son datos: son compilaciones que la app **regenera sola** al abrirla. → **+1,48 GiB**

### 3.3 Otros duplicados y basura

| Elemento | Tamaño | Nota |
|---|---:|---|
| `.trash-storage/` | 86 MB | Papelera olvidada; incluye `solicitudcambiotitularidaasmovil.pdf` y su copia `(2)` |
| `DanielaOS/Queue/daniela_1787576885.png` | 1,4 MB | MD5 `3bae7832…` idéntico a `daniela_1787403364.png` |
| 5 × `TermuxAudioRecording_2026-08-04_*.m4a` | 6,7 MB | Huérfanas en la raíz de /sdcard |
| `apps.maps/.../map_cache.db` | 26 MB | Caché de Maps |
| `Pictures/1787399351571.png` | 1,5 MB | MD5 `3bae7832…` idéntico al anterior |

**Total Nivel 1 + 2 ejecutado: 4,1 GB** (31 elementos, 257 ficheros)

---

## 4. Conflictos detectados

### 4.1 Cuatro stacks de LLM local compitiendo — el conflicto estructural

Tienes **tres** motores de IA locales instalados, y E-13 (Daniela Offline) iba a ser el cuarto:

| Stack | Modelo | Tamaño | Formato |
|---|---|---:|---|
| `com.google.ai.edge.gallery` | Gemma 4 E2B | 2,59 GB | `.litertlm` (LiteRT) |
| `Documents/NexusAI` | Gemma (soberano) | 1,52 GB | `.bin` propietario |
| `com.llmproxy` | Qwen2.5-0.5B | 0,46 GB | **GGUF** |
| E-13 Daniela Offline (planeado) | ¿otro? | ~0,5 GB | llama.cpp |

**Decisión recomendada:** E-13 **no debe descargar un modelo nuevo**. Debe apuntar
llama.cpp al GGUF que ya existe en `com.llmproxy`. Eso evita el cuarto modelo, ahorra
500 MB y elimina el conflicto. Los dos Gemma (LiteRT y .bin) no son intercambiables con
llama.cpp, así que o se quedan para la app de Google o se van.

### 4.2 `cloudflared` está exponiendo el HUD **falso** a internet

```
28646  cloudflared  cloudflared tunnel --protocol http2 --url http://localhost:8082
28539  python3      python3 server.py
```

`server.py` es el **MOCK** que descubrimos en la auditoría anterior: solo responde `/` y
`/api/skills/dispatch`, y el dispatcher devuelve siempre `200 OK` sin ejecutar nada.
Hay un túnel público apuntando a un servidor de mentira. Es un agujero de seguridad
(cualquiera con la URL puede golpear el endpoint) y un desperdicio de CPU/RAM/batería.

**Acción:** o se sustituye por `daniela_os.py` real, o se para el túnel.

### 4.3 Wakelock de Termux activo desde hace **10 días**

```
PARTIAL_WAKE_LOCK 'termux:service-wakelock'  ACQ=-10d20h31m25s  (uid=10431 pid=17077)
```

El teléfono **no ha entrado en suspensión profunda en casi 11 días**. Es la causa más
probable del calor (77 °C) y del consumo en reposo. Probablemente lo tiene nuestro
`daemon_24_7.py` para mantener a Daniela viva — decisión legítima, pero hay que hacerla
*battery-aware* (soltar el wakelock con batería baja o de noche).

### 4.4 Memoria al límite

Swap al **98,5 %** y 332 MB libres. Con 468 paquetes y un modelo de 2,6 GB cargable,
el sistema está al borde del *thrashing*. Cargar Gemma 4 E2B en RAM es inviable ahora mismo.

### 4.5 Play Store comiéndose la CPU

```
6909  com.android.vending:background   59,3 % CPU   20 min de CPU acumulados
```

Junto con su job de fondo (`PhoneskyJobServiceBackground`) y 659 trabajos programados.

### 4.6 Pipeline de DanielaOS atascado

`DanielaOS/Queue/` tiene 4 ficheros desde el 22–24 de agosto y `Rendered/` está **vacío**.
Nada consume la cola: el render se cayó y nunca se reanudó.

---

## 5. Qué se ha ejecutado

Se movieron **4,1 GB** (31 elementos / 257 ficheros) a:

```
/sdcard/DanielaOS/.papelera/
  ├── duplicados/      1,59 GB   (gemma2-2b.bin, PNG duplicado)
  ├── caches/          1,58 GB   (cachés AI Edge + Maps)
  ├── modelos_demo/      565 MB  (TinyGarden, MobileActions)
  ├── videos_antiguos/   468 MB  (13 renders de Daniela)
  ├── trash-storage/      88 MB
  ├── apks/               22 MB  (HeliBoard)
  └── huerfanos/         6,9 MB  (grabaciones Termux)
```

**Nada se ha borrado.** Todo es recuperable.

> ⚠️ El espacio solo se libera de verdad al vaciar la papelera. Mientras esté ahí,
> los 4,1 GB siguen ocupando disco (es lo que la hace segura).

---

## 6. Cómo revertir o terminar

```sh
# Ver qué hay en la papelera y cuánto ocupa
du -sh /sdcard/DanielaOS/.papelera/*

# Recuperar TODO a su sitio original
sh /sdcard/DanielaOS/deploy/optimizar_telefono.sh --restaurar

# Cuando estés seguro, liberar de verdad los 4,1 GB
rm -rf /sdcard/DanielaOS/.papelera
```

---

## 7. Pendiente de tu decisión

| # | Decisión | Impacto |
|---|---|---:|
| 1 | ¿Vaciar la papelera? (libera los 4,1 GB) | +4,1 GB |
| 2 | ¿Mantener el túnel `cloudflared` al HUD falso? | seguridad |
| 3 | ¿Qué modelo LLM se queda: Gemma 4 E2B (2,6 GB), NexusAI (1,5 GB) o Qwen GGUF (0,46 GB)? | hasta +4,1 GB |
| 4 | ¿Wakelock 24/7 o modo *battery-aware*? | batería |
| 5 | ¿Reiniciar el pipeline de `DanielaOS/Queue`? | funcional |
| 6 | ¿Desinstalar `com.llmproxy` o reutilizarlo para E-13? | evita 4.º modelo |
| 7 | Ejecutar `install.sh` en Termux para desplegar los 26 módulos | despliegue |

---

## 8. Recomendación de orden

1. **Ya** — mata el túnel `cloudflared` si no lo usas (riesgo de seguridad real).
2. **Hoy** — revisa la papelera; si todo cuadra, `rm -rf` y recupera 4,1 GB.
3. **Hoy** — decide el modelo LLM único. Con swap al 98 %, solo cabe **uno**.
   Mi consejo: **Qwen 0.5B GGUF** (0,46 GB) como cerebro local de Daniela +
   Gemma 4 E2B solo cuando estés enchufado.
4. **Esta semana** — E-13 debe reutilizar ese GGUF, no descargar otro.
5. **Esta semana** — haz el wakelock *battery-aware*.
