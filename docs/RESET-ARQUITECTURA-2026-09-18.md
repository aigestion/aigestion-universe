# RESET DE ARQUITECTURA — 2026-09-18

> Auditoría medida, no estimada. Todo lo que sigue se comprobó ejecutando el
> sistema. Los números son reales; donde no pude medir algo, lo digo.

## Veredicto en una línea

**El sistema no está roto: está fragmentado y sin cerebro.** Corren 17 contenedores
y 14 interfaces web, pero el núcleo de decisión (`aig_core.py`) es un
**stub que devuelve respuestas simuladas**, el 45% de las rutas dependen de un
móvil que no está conectado, y de 5 proveedores de IA **solo funciona 1**.

---

# 1. MAPA DE AGENTES ACTUAL

## 1.1 La capa que de verdad ejecuta: `daniela_os.py`

| Dato | Valor medido |
|---|---|
| Fichero | `daniela_os.py` — **1.130 líneas** |
| Módulos que intenta registrar | **122** |
| Rutas reales en el mapa | **397** |
| Módulos que fallan al cargar | **0** (arranca limpio) |
| Dónde corre | Contenedor `aig-daniela`, **:5000**, imagen del **13-sep** |

⚠️ El contenedor está **congelado el 13-sep**: tiene los ficheros nuevos
(`model_router.py`, `urban_nodes.py`…) pero su `daniela_os.py` es viejo, así que
**no los registra**. Por eso `/api/router/status`, `/api/urban/status`,
`/api/guard/status` y `/api/vault/status` dan **404 en producción** aunque en local
existan.

## 1.2 Los agentes reales: quién está conectado y quién no

Esto es lo importante. **Los agentes "de negocio" NO están conectados.**

### ✅ Cableados (tienen rutas en el mapa)

| Agente | Prefijo | Rutas |
|---|---|---|
| `agent_marketplace` | `/api/agents` | 9 |
| `agent_court` | `/api/court` | 4 |
| `agent_invoice_graph` | `/api/invoice` | 4 |
| `agent_scoreboard` | `/api/scoreboard` | 2 |
| `agent_expediente` | `/api/expediente` | 2 |
| `agent_cad_studio` | `/api/cad` | 2 |
| `memory_semantic` | `/api/memory` | 4 |
| `plugin_health` | `/api/plugins` | 10 |
| `integrity_guard` | `/api/integrity` | 4 |
| `piper_engine` | `/api/voice` | 8 |

### ❌ NO cableados — código muerto (3 copias cada uno, 0 rutas)

`agent_calendario` · `agent_correo` · `agent_documentos` · `agent_redes` ·
`agent_vigia` · `agent_epic_ideas` · `auto_swarm_dispatcher` (**0 usos en todo el
repo**) · `swarm_planner` · `swarm_intelligence` · `code_generation_agent` ·
`cyber_sentinel`

`daniela_os.py` **no los importa**. Sus únicas referencias son sus propias copias
(`agents/`, raíz, `agents/`) y tests autogenerados. **Existen 3 veces
cada uno y no los llama nadie.**

## 1.3 Desencadenantes y entregables (lo que hay de verdad)

| Vía | Cómo se dispara | Qué produce | Estado |
|---|---|---|---|
| `/api/chat` | Mensaje del usuario + PIN | Comandos slash: `/core`, `/pipeline`, `/swarm`… | ⚠️ **el core es simulado** |
| `/api/pixel/*` | Petición HTTP al móvil | Sensores, cámara, IR, NFC, malla… | ❌ **móvil inalcanzable** |
| Contenedores | Docker Compose | 14 UIs | ⚠️ sin jerarquía |
| `agent_vigia` | *debería* ser 24/7 | Monitorización | ❌ no conectado |
| `agent_calendario`/`correo`/`redes` | *deberían* ser programados | Contenido, email | ❌ no conectados |

---

# 2. FLUJO DE TRABAJO SIMPLIFICADO (explicado a un CEO)

Hoy, cuando tú escribes una orden, pasa esto:

```
  TÚ escribes en el chat
        │
        ▼
  [1] El mensaje llega a Daniela OS (:5000)      ✅ funciona
        │
        ▼
  [2] Se busca el "cerebro" (aig_core)     ⚠️ es un STUB
        │
        ▼
  [3] El cerebro responde:
      "Respuesta simulada a la consulta: ..."    ❌ NO es IA de verdad
        │
        ▼
  [4] Se te devuelve ese texto                    ❌ Respuesta vacía de contenido
```

**En lenguaje de empresa:** tienes una recepcionista excelente (Daniela OS, 397
funciones), pero **el director general al que le pasa las notas es un maniquí que
contesta "recibido" a todo**. El trabajo real (escribir, decidir, buscar) no lo hace
nadie.

**Dónde SÍ hay IA de verdad:** en módulos sueltos (`model_router`, `local_brain`,
`voice`, los engines de los contenedores). **Ninguno está conectado al chat.**

---

# 3. PLAN "DANIELA OMNIPRESENTE" (unificación de front)

## 3.1 El punto de partida

Hoy hay **14 interfaces web** y **48 ficheros HTML**:

| Puerto | Título | Veredicto |
|---|---|---|
| :5000 | Daniela OS | ✅ **el backend bueno** |
| :9200 | **Daniela Omnipresente** | ⚠️ isla (146 líneas, 6 rutas) |
| :9300 | Hermes Epic - 50 Ideas | 🗑️ catálogo de ideas |
| :3002 | FreeLLMAPI | ✅ **útil** (router de LLM) |
| :9500 / :9600 | Frontend v1 / v2 | 🗑️ duplicados |
| :9997 | Dashboard | 🗑️ |
| :9998 / :9999 | Perf / Security | 🗑️ paneles de métricas |
| :9400 / :9700 / :9800 | Optimization / Infra / Agent | 🗑️ paneles de métricas |
| :8090 | aig Mobile | ⚠️ candidato a única UI móvil |
| :5020 | Epic PC Experience | 🗑️ |

## 3.2 La decisión (una frase)

**No construyas nada nuevo. Usa lo que ya funciona y apaga lo demás.**

- **Un backend**: `daniela_os.py` (:5000). Ya tiene 397 rutas. No se toca.
- **Una puerta**: nginx (ya corre en :80/:443). Todo entra por aquí.
- **Una pantalla**: una sola SPA servida por el backend.
- **Una voz**: Piper (ya implementado, `/api/voice/piper/*`).

## 3.3 Arquitectura objetivo

```
   PC (navegador)                Pixel 8a (navegador)
        │                               │
        └──────────┬────────────────────┘
                   ▼
        [ NGINX :80/:443 ]  ← ÚNICA PUERTA (ya existe)
                   │
                   ▼
        [ daniela_os.py :5000 ]  ← ÚNICO BACKEND (397 rutas, ya existe)
             │         │
             │         └──► Piper TTS  (la única voz)
             │
             └──► [ FreeLLMAPI :3002 ]  ← ÚNICO proveedor de IA
                       │
                       └──► OpenRouter  (el ÚNICO que responde hoy)

   Se APAGAN: :9200 :9300 :9500 :9600 :9997 :9998 :9999 :9400 :9700 :9800 :5020
   → de 14 interfaces a 1
```

## 3.4 Para que llegue al móvil por Tailscale

**Prerrequisito que falta**: Tailscale **no está instalado en el PC** (solo en el
móvil, `100.65.50.219`). El instalador ya está descargado en
`data/instaladores/tailscale-setup-amd64.msi` — lo tienes que ejecutar tú (pide UAC)
con **la misma cuenta** que el móvil.

Después: el móvil abre `http://<ip-tailscale-del-PC>/` → nginx → misma pantalla
única. **Sin abrir puertos a internet.**

## 3.5 Pasos ejecutables (en orden)

| # | Acción | Riesgo |
|---|---|---|
| 1 | **Arreglar el cerebro** (ver §4.1) | bajo |
| 2 | Conectar el chat al `model_router` real | bajo |
| 3 | Instalar Tailscale en el PC (tú, UAC) | nulo |
| 4 | Añadir nginx → `/` sirve la SPA única | bajo |
| 5 | `docker compose stop` de los 10 contenedores de UI | nulo (reversible) |
| 6 | Vaciar el RAG y reindexar | bajo |

---

# 4. DIAGNÓSTICO DE SALUD — por qué sientes que "no funciona nada"

**Porque es cierto en gran parte.** Seis causas, todas medidas:

### 4.1 🔴 El cerebro es un stub (la causa nº 1)

`aig_core.py:147`:

```python
answer = f"Respuesta simulada a la consulta: '{query}'"
```

No es un bug: es un **placeholder que se quedó en producción**. Todo lo que pase por
`/core` devuelve una frase enlatada. **El sistema no "piensa".**

### 4.2 🔴 El 45% de las rutas dependen del móvil, y el móvil no responde

**178 de 397 rutas son `/api/pixel/*`.** Medido:

| Destino | Resultado |
|---|---|
| Pixel por LAN `192.168.1.133:8080` | ❌ inalcanzable |
| Pixel por Tailscale `100.65.50.219:8080` | ❌ inalcanzable |
| Gateway Termux `:8082` | ❌ caído |

→ Sensores, cámara, IR, NFC, malla, portapapeles, ADB: **todo muerto**.

### 4.3 🔴 De 5 proveedores de IA, solo 1 funciona

| Proveedor | HTTP | Estado |
|---|---|---|
| OpenRouter | **200** | ✅ **el único vivo** |
| Gemini | **401** | ❌ (la clave es un token OAuth, no una API key) |
| Groq | **403** | ❌ |
| DashScope | **401** | ❌ |
| Ollama (local) | — | ❌ apagado |
| Supabase | **200** | ✅ |

### 4.4 🔴 La base de conocimiento está VACÍA

`data/memory_rag.db` → `rag_docs: **0 filas**`, `memory_links: **0 filas**`.
Y `sqlite-vec` ni se carga: `no such module: vec0`.
**Daniela no recuerda nada porque no hay nada que recordar.**

### 4.5 🔴 Producción va 5 días por detrás

El contenedor se construyó el **13-sep**. Los módulos de los últimos días
(router, urban, guard, vault, Piper) **no están activos en :5000**.

### 4.6 🟡 Fragmentación de interfaz

14 interfaces, 48 HTML, 17 contenedores, 6 agentes muertos con 3 copias cada uno.
**No hay una pantalla que sea "la buena".**

## 4.7 Lo que SÍ funciona hoy

Para que no parezca todo negro:

- ✅ Daniela OS arranca **limpio**: 397 rutas, 0 módulos caídos
- ✅ Los 17 contenedores están **arriba y healthy**
- ✅ OpenRouter y Supabase responden
- ✅ Los 939 tests pasan
- ✅ La suite, el CI y el CD están en verde

**El andamio está bien. Falta el motor y el volante.**

---

# 5. QUÉ HARÍA HOY (orden estricto)

| # | Acción | Por qué primero | Esfuerzo |
|---|---|---|---|
| **1** | **Rebuild del contenedor Daniela** | sin esto, nada de lo nuevo está activo | 5 min |
| **2** | **Conectar el chat a OpenRouter** (el único proveedor vivo) | convierte el stub en IA real | 1 h |
| **3** | **Arrancar Ollama** (`ollama serve` + `nomic-embed-text`) | IA local gratis + embeddings | 15 min |
| **4** | **Reindexar el RAG** (hoy 0 documentos) | da memoria a Daniela | 30 min |
| **5** | **Tailscale en el PC** (tú, UAC) | desbloquea el móvil | 10 min |
| **6** | **Apagar las 10 UIs duplicadas** | una sola pantalla | 10 min |
| **7** | **Reconectar el móvil** (`adb connect` / Termux) | devuelve las 178 rutas | depende |

⚠️ Los puntos 1, 2, 3 y 4 son **código y configuración**: los puedo hacer yo.
El 5 lo tienes que hacer tú (pide UAC). El 7 depende del estado del teléfono.

---

## Anexo: cómo se midió

```bash
# arranque real y rutas
PYTHONPATH=. ./.venv/Scripts/python.exe -c "import daniela_os; print(len(list(daniela_os.app.url_map.iter_rules())))"

# contenedores
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# proveedores de IA  (sin proxy: HTTP_PROXY rompe las llamadas locales)
curl -s --noproxy '*' http://127.0.0.1:PUERTO/

# RAG
sqlite3 data/memory_rag.db "select count(*) from rag_docs"
```

⚠️ **`HTTP_PROXY` está activo** en este PC: sin `--noproxy '*'` las llamadas a
`localhost` devuelven **502** y parecen caídas cuando no lo están. Ya nos pasó.
