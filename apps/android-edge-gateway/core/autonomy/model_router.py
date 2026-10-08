#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
model_router.py — E-32 · Un cerebro, muchos proveedores, cero interrupciones
==========================================================================

El problema, tal cual lo hemos sufrido
--------------------------------------
Daniela dependia de UNA sola API. Cuando esa API fallaba —cuota agotada, clave
caducada, un proveedor caido, o simplemente un modulo que no cargaba el .env—,
Daniela se quedaba muda y no habia forma de saber por que.

Mientras tanto, en `.env.master` habia **ocho claves de proveedores distintos
sin usar**: Groq, OpenRouter, Anthropic, Cohere, HuggingFace, Ollama local...
Todas gratis en su capa basica. Todas muertas de risa.

Este modulo las pone en fila: si el primero falla, cae al siguiente.

La regla de seguridad de siempre
--------------------------------
La lista de proveedores esta **cerrada y escrita aqui**. Nunca se acepta una URL
que venga de una peticion HTTP: si alguien pudiera inyectar `url_base`, tendria
un servidor haciendo peticiones a donde le diera la gana (SSRF). Lo unico
configurable por API es el ORDEN y el modelo, y ambos se validan contra la lista.

Las claves nunca se registran, nunca se devuelven por la API y nunca se escriben
en el estado: solo se guarda un prefijo y la longitud, para poder distinguir
"clave mal puesta" de "clave caducada" sin exponerla.

Uso
---
    GET  /api/router/status      estado general y proveedor activo
    GET  /api/router/providers   la lista y como esta cada uno
    POST /api/router/ask         {"prompt": "...", "proveedor": "opcional"}
    POST /api/router/test        sonda todos y guarda el resultado
    GET  /api/router/history     ultimas respuestas
    GET  /api/router/config      configuracion
    POST /api/router/config      cambiar orden, modelo o TTL
"""

from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request

# --------------------------------------------------------------------------
#  Rutas y constantes
# --------------------------------------------------------------------------
# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "model_router"
STATE_FILE = DATA_DIR / "estado.json"
HISTORY_FILE = DATA_DIR / "historial.json"

MAX_HISTORIAL = 50
TIMEOUT_SONDA = 30  # la sonda es corta: solo queremos saber si respira
TIMEOUT_LOCAL = 150  # PERO un modelo local hay que cargarlo en memoria la
# primera vez: medido, daniela-local tarda 28,7 s en
# frio y qwen3.5 37,9 s. Con 12 s (o incluso 30) daba
# ReadTimeout y parecia caido estando perfectamente.
# Solo los proveedores locales reciben esta paciencia;
# la nube sigue con timeout corto para no arrastrar
# la caida a un proveedor remoto lento.
TIMEOUT_LLAMADA = 60  # una respuesta real puede tardar mas
# OJO: no bajar de aqui. Los modelos con "pensamiento" (gemini-2.5) gastan
# parte del presupuesto razonando: con 8 tokens la respuesta llegaba vacia y
# parecia un fallo de la API cuando en realidad la API habia contestado 200.
MAX_TOKENS_SONDA = 64

# Hay un proxy en el entorno (HTTP_PROXY acaba en :54176). Va bien para internet
# pero revienta los proveedores LOCALES: intenta resolver host.docker.internal
# o localhost a traves de si mismo y devuelve 502. Para lo local, sin proxy.
SIN_PROXY = {"http": None, "https": None}

# Sube este numero cuando cambie un valor por defecto. Si no, la configuracion
# guardada manda sobre la nueva y un modelo retirado (command-r, eliminado por
# Cohere en 2025) se queda pegado para siempre sin forma de enterarse.
# v3 (2026-10-05): cadena SOLO GRATIS + modelos vigentes (medidos en vivo).
CONFIG_VERSION = 3

CONFIG_DEFAULT: Dict[str, Any] = {
    "version": CONFIG_VERSION,
    # 🔴 CADENA SOLO GRATIS (2026-10-05): google dejo de ser el proveedor unico.
    # Orden inicial, pero el que responde va solo al frente (orden_efectivo) y
    # si uno corta cuota se salta y vuelve en ttl_cuota_s. Nada de anthropic
    # ni cohere: son de pago (DE_PAGO los filtra aunque alguien los pida).
    "orden": ["gemini", "openrouter", "groq", "deepseek", "qwen", "mistral", "ollama"],
    "modelos": {
        "gemini": "gemini-2.5-flash",
        # NVIDIA gratis via OpenRouter: nemotron-3.5-lightning responde OK
        # (medido 2026-10-05) y ya era el modelo por defecto de autofix/swarm.
        "openrouter": "nvidia/nemotron-3.5-lightning:free",
        # 'llama-3.1-8b-instant' fue dado de baja (404). Vigente medido
        # contra GET /openai/v1/models el 2026-10-05.
        "groq": "qwen/qwen3.8-27b",
        "deepseek": "deepseek-chat",
        "qwen": "qwen-turbo",
        "mistral": "mistral-small-latest",
        "anthropic": "claude-3-5-haiku-20241022",
        # 'command-r' fue RETIRADO por Cohere el 15-09-2025 (daba 404).
        "cohere": "command-a-03-2025",
        # Modelo local propio de Daniela, ya descargado en Ollama
        # (junto con qwen3.5, deepseek-coder y nomic-embed-text).
        "ollama": "daniela-local:latest",
        "huggingface": "mistralai/Mistral-7B-Instruct-v0.2",
    },
    "ttl_salud_s": 900,  # 15 min: no queremos gastar cuota sondeando
    # Un proveedor que corta cuota NO esta caido: se salta poco rato y se
    # reintenta. Sin esto, un 429 de Gemini dejaba a Daniela muda 15 min.
    "ttl_cuota_s": 180,
    "sonda_auto_min": 30,  # hilo de fondo
    "reintentos": 1,
}


# --------------------------------------------------------------------------
#  Proveedores — LISTA CERRADA
# --------------------------------------------------------------------------
@dataclass
class Proveedor:
    """Un proveedor de inferencia. La URL es fija: nunca viene de fuera."""

    id: str
    nombre: str
    claves_env: List[str]  # la primera que tenga valor, gana
    url: str  # FIJA, escrita aqui
    modelo_por_defecto: str
    auth: str  # query | bearer | x-api-key | ninguna
    local: bool = False
    activo: bool = True


PROVEEDORES: List[Proveedor] = [
    Proveedor(
        id="gemini",
        nombre="Google Gemini",
        claves_env=["GEMINI_API_KEY"],
        url="https://generativelanguage.googleapis.com/v1beta/models",
        modelo_por_defecto="gemini-2.5-flash",
        auth="query",
    ),
    Proveedor(
        id="deepseek", nombre="DeepSeek", claves_env=["DEEPSEEK_API_KEY"],
        url="https://api.deepseek.com/v1/chat/completions",
        modelo_por_defecto="deepseek-chat", auth="bearer",
    ),
    Proveedor(
        # Groq ya se usa en el proyecto y es rapidisimo: buen primer respaldo.
        id="groq",
        nombre="Groq",
        claves_env=["GROQ_API_KEY"],
        url="https://api.groq.com/openai/v1/chat/completions",
        modelo_por_defecto="llama-3.1-8b-instant",
        auth="bearer",
    ),
    Proveedor(
        id="openrouter",
        nombre="OpenRouter",
        claves_env=["OPENROUTER_API_KEY"],
        url="https://openrouter.ai/api/v1/chat/completions",
        modelo_por_defecto="meta-llama/llama-3.1-8b-instruct:free",
        auth="bearer",
    ),
    Proveedor(
        id="anthropic",
        nombre="Anthropic Claude",
        claves_env=["ANTHROPIC_API_KEY", "CLAUDE_API_KEY"],
        url="https://api.anthropic.com/v1/messages",
        modelo_por_defecto="claude-3-5-haiku-20241022",
        auth="x-api-key",
    ),
    Proveedor(
        # OJO: el endpoint /v1/chat de Cohere ya no existe (daba 404).
        # La API actual es v2 y el host es api.cohere.com, no api.cohere.ai.
        id="cohere",
        nombre="Cohere",
        claves_env=["COHERE_API_KEY"],
        url="https://api.cohere.com/v2/chat",
        modelo_por_defecto="command-a-03-2025",
        auth="bearer",
    ),
    Proveedor(
        # Ollama no necesita clave: es local y gratis de verdad. Si esta caido,
        # simplemente no responde y seguimos con el siguiente.
        id="ollama",
        nombre="Ollama local",
        claves_env=["OLLAMA_HOST", "LOCAL_LLM_URL"],
        url="/api/chat",
        modelo_por_defecto="daniela-local:latest",
        auth="ninguna",
        local=True,
    ),
    Proveedor(
        id="qwen", nombre="Qwen (DashScope)",
        claves_env=["QWEN_API_KEY", "DASHSCOPE_API_KEY"],
        url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        modelo_por_defecto="qwen-turbo", auth="bearer",
    ),
    Proveedor(
        # Clave gratuita del repo (verify-free.js: 100 req/min). Medido
        # 2026-10-05: respondia CUOTA (rate limit), asi que entra en cadena
        # con su propia cuarentena corta.
        id="mistral", nombre="Mistral AI",
        claves_env=["MISTRAL_API_KEY"],
        url="https://api.mistral.ai/v1/chat/completions",
        modelo_por_defecto="mistral-small-latest", auth="bearer",
    ),
    Proveedor(
        id="huggingface", nombre="HuggingFace Inference",
        claves_env=["HUGGINGFACE_API_KEY", "HF_TOKEN"],
        url="https://api-inference.huggingface.co/models",
        modelo_por_defecto="mistralai/Mistral-7B-Instruct-v0.2",
        auth="bearer",
    ),
]

POR_ID: Dict[str, Proveedor] = {p.id: p for p in PROVEEDORES}

# Proveedores DE PAGO: quedan en la lista cerrada (alguien puede consultarlos
# por API) pero nunca entran en la cadena por defecto ni en una orden guardada.
# La politica del repo es "gratis siempre" (docs/POLITICA-GRATIS.md).
DE_PAGO = frozenset({"anthropic", "cohere"})

# Frases tipicas de proveedor que acaba de cortar cuota o limitar velocidad.
# Un 429 no significa "caido": por eso su cuarentena (ttl_cuota_s) es corta.
INDICADORES_CUOTA = (
    "http 429", "http 430", "rate limit", "rate_limited", "too many requests",
    "quota", "resource exhausted", "free quota", "tokens per min",
    "requests per day", "credits", "billing", "exhausted",
)


def es_cuota(texto: str) -> bool:
    """¿El fallo es por cuota/rate limit y no porque el proveedor este caido?"""
    t = (texto or "").lower()
    return any(m in t for m in INDICADORES_CUOTA)


# --------------------------------------------------------------------------
#  Utilidades
# --------------------------------------------------------------------------
def _redactar(clave: str) -> str:
    """Huella de una clave sin revelarla.

    Guardar `AQ.Ab8RN6...` (10 caracteres) basta para distinguir dos claves
    distintas o ver que se pego la vieja, y no sirve para usarla.
    """
    if not clave:
        return ""
    return f"{clave[:10]}...({len(clave)})"


def _clave_de(prov: Proveedor) -> str:
    for var in prov.claves_env:
        v = (os.getenv(var) or "").strip()
        if v:
            return v
    return ""


def _norm_ollama(url_base: str) -> str:
    """OLLAMA_HOST suele venir como host:port; lo dejamos como URL base."""
    s = (url_base or "").strip()
    if not s:
        return ""
    if not s.startswith("http"):
        s = f"http://{s}"
    return s.rstrip("/")


# --------------------------------------------------------------------------
#  Llamadas — una funcion por proveedor, todas sin shell
# --------------------------------------------------------------------------
def _gemini(
    prov: Proveedor, modelo: str, clave: str, prompt: str, max_tokens: int, timeout: int
) -> Tuple[bool, str, str]:
    import requests

    url = f"{prov.url}/{modelo}:generateContent?key={clave}"
    conf: Dict[str, Any] = {"maxOutputTokens": max_tokens}
    if max_tokens <= MAX_TOKENS_SONDA:
        # Los modelos 2.5 "piensan" antes de responder y ese razonamiento
        # CONSUME el presupuesto de tokens. En la sonda eso es fatal: a veces
        # gastaba los 64 en pensar y llegaba una respuesta vacia con
        # finishReason=MAX_TOKENS, pareciendo que la API estaba caida cuando
        # habia contestado 200. Para sondear, pensamiento desactivado.
        conf["thinkingConfig"] = {"thinkingBudget": 0}
    r = requests.post(
        url,
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": conf},
        timeout=timeout,
    )
    if r.status_code != 200:
        return False, "", f"HTTP {r.status_code}: {r.text[:180]}"
    try:
        d = r.json()
    except ValueError:
        return False, "", "respuesta no era JSON"
    cands = d.get("candidates") or []
    if not cands:
        # Tipico cuando salta el filtro de seguridad: la API responde 200
        # pero no trae candidatos. Sin esto parecia un fallo de red.
        fb = d.get("promptFeedback") or {}
        return (
            False,
            "",
            ("sin candidatos (blockReason=" f"{fb.get('blockReason', 'desconocido')})"),
        )
    c = cands[0]
    partes = (c.get("content") or {}).get("parts") or []
    if not partes:
        return False, "", ("respuesta vacia (finishReason=" f"{c.get('finishReason', '?')})")
    txt = "".join(p.get("text", "") for p in partes).strip()
    if not txt:
        return False, "", "respuesta vacia"
    return True, txt, ""


def _openai_compatible(
    prov: Proveedor, modelo: str, clave: str, prompt: str, max_tokens: int, timeout: int
) -> Tuple[bool, str, str]:
    """Groq y OpenRouter comparten el formato de OpenAI."""
    import requests

    headers = {"Authorization": f"Bearer {clave}", "Content-Type": "application/json"}
    if prov.id == "openrouter":
        # OpenRouter pide estas dos cabeceras para ranking; son opcionales.
        headers["HTTP-Referer"] = "https://aig.local"
        headers["X-Title"] = "DanielaOS"
    r = requests.post(
        prov.url,
        headers=headers,
        json={
            "model": modelo,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    if r.status_code != 200:
        return False, "", f"HTTP {r.status_code}: {r.text[:180]}"
    try:
        txt = r.json()["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError):
        return False, "", "respuesta sin el formato esperado"
    return True, txt, ""


def _anthropic(
    prov: Proveedor, modelo: str, clave: str, prompt: str, max_tokens: int, timeout: int
) -> Tuple[bool, str, str]:
    import requests

    r = requests.post(
        prov.url,
        headers={
            "x-api-key": clave,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json={
            "model": modelo,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    if r.status_code != 200:
        return False, "", f"HTTP {r.status_code}: {r.text[:180]}"
    try:
        txt = r.json()["content"][0]["text"]
    except (ValueError, KeyError, IndexError):
        return False, "", "respuesta sin el formato esperado"
    return True, txt, ""


def _cohere(
    prov: Proveedor, modelo: str, clave: str, prompt: str, max_tokens: int, timeout: int
) -> Tuple[bool, str, str]:
    import requests

    r = requests.post(
        prov.url,
        headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
        json={
            "model": modelo,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    if r.status_code != 200:
        return False, "", f"HTTP {r.status_code}: {r.text[:180]}"
    try:
        # v2 devuelve message.content como LISTA de bloques {"type":"text"}
        bloques = r.json()["message"]["content"]
        txt = "".join(b.get("text", "") for b in bloques).strip()
    except (ValueError, KeyError, IndexError, TypeError):
        return False, "", "respuesta sin el formato esperado"
    if not txt:
        return False, "", "respuesta vacia"
    return True, txt, ""


def _bases_ollama() -> List[str]:
    """Direcciones donde podria estar Ollama, en orden de probabilidad.

    `OLLAMA_HOST` valia `http://host.docker.internal:11434`, que solo resuelve
    DENTRO de Docker: en el PC a secas da 502. Y `LOCAL_LLM_URL` traia la ruta
    completa (`/api/generate`), Asi que se normaliza todo y se anade localhost
    como ultimo recurso: si Ollama esta arriba en el PC, se encuentra.
    """
    vistos, bases = set(), []
    for var in ("LOCAL_LLM_URL", "OLLAMA_HOST"):
        v = (os.getenv(var) or "").strip()
        if not v:
            continue
        base = _norm_ollama(v)
        # quitar la ruta si venia incluida (/api/generate, /api/chat...)
        m = re.match(r"^(https?://[^/]+)", base)
        if m:
            base = m.group(1)
        if base and base not in vistos:
            vistos.add(base)
            bases.append(base)
    for extra in ("http://localhost:11434", "http://127.0.0.1:11434"):
        if extra not in vistos:
            vistos.add(extra)
            bases.append(extra)
    return bases


def _ollama(
    prov: Proveedor, modelo: str, clave: str, prompt: str, max_tokens: int, timeout: int
) -> Tuple[bool, str, str]:
    """Ollama es local: SIN proxy y probando varias direcciones."""
    import requests

    errores = []
    for base in _bases_ollama():
        try:
            r = requests.post(
                f"{base}/api/chat",
                json={
                    "model": modelo,
                    "stream": False,
                    "messages": [{"role": "user", "content": prompt}],
                    "options": {"num_predict": max_tokens},
                },
                timeout=timeout,
                proxies=SIN_PROXY,
            )
        except Exception as e:  # noqa: BLE001
            errores.append(f"{base}: {type(e).__name__}")
            continue
        if r.status_code != 200:
            errores.append(f"{base}: HTTP {r.status_code}")
            continue
        try:
            txt = (r.json().get("message") or {}).get("content", "") or ""
        except ValueError:
            errores.append(f"{base}: respuesta no era JSON")
            continue
        if not txt.strip():
            errores.append(f"{base}: respuesta vacia")
            continue
        return True, txt.strip(), ""
    return False, "", "ollama no disponible -> " + "; ".join(errores[:3])


def _huggingface(
    prov: Proveedor, modelo: str, clave: str, prompt: str, max_tokens: int, timeout: int
) -> Tuple[bool, str, str]:
    import requests

    r = requests.post(
        f"{prov.url}/{modelo}",
        headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
        json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
        timeout=timeout,
    )
    if r.status_code != 200:
        return False, "", f"HTTP {r.status_code}: {r.text[:180]}"
    try:
        d = r.json()
        if isinstance(d, list):
            txt = d[0].get("generated_text", "")
        else:
            txt = d.get("generated_text", "")
    except (ValueError, AttributeError):
        return False, "", "respuesta sin el formato esperado"
    return True, txt, ""


LLAMADORES: Dict[str, Callable[..., Tuple[bool, str, str]]] = {
    "gemini": _gemini,
    "deepseek": _openai_compatible,
    "groq": _openai_compatible,
    "openrouter": _openai_compatible,
    "anthropic": _anthropic,
    "cohere": _cohere,
    "qwen": _openai_compatible,
    "mistral": _openai_compatible,
    "ollama": _ollama,
    "huggingface": _huggingface,
}


# --------------------------------------------------------------------------
#  Enrutador
# --------------------------------------------------------------------------
class EnrutadorModelos:
    """Prueba proveedores en orden y se queda con el primero que responde."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config: Dict[str, Any] = json.loads(json.dumps(CONFIG_DEFAULT))
        self._lock = threading.RLock()
        self.salud: Dict[str, Dict[str, Any]] = {}
        self.historial: List[Dict[str, Any]] = []
        self.ultimo_exitoso: Optional[str] = None
        self._hilo: Optional[threading.Thread] = None
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.cargar()
        if config:
            self._aplicar_config(config)

    # ------------------------------------------------------------ persistencia
    def cargar(self) -> None:
        try:
            if STATE_FILE.exists():
                d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                if isinstance(d, dict):
                    self.salud = d.get("salud", {}) or {}
                    self.ultimo_exitoso = d.get("ultimo_exitoso")
                    cfg = d.get("config")
                    if isinstance(cfg, dict):
                        if cfg.get("version") == CONFIG_VERSION:
                            self._aplicar_config(cfg)
                        else:
                            # Version distinta: los valores por defecto han
                            # cambiado. Se conserva lo que el usuario eligio
                            # (orden, tiempos) pero NO los modelos, que pueden
                            # estar retirados.
                            cfg = {
                                k: v
                                for k, v in cfg.items()
                                if k in ("orden", "ttl_salud_s", "sonda_auto_min", "reintentos")
                            }
                            self._aplicar_config(cfg)
        except (OSError, ValueError):
            pass
        try:
            if HISTORY_FILE.exists():
                h = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(h, list):
                    self.historial = h[-MAX_HISTORIAL:]
        except (OSError, ValueError):
            pass

    def guardar(self) -> None:
        try:
            STATE_FILE.write_text(
                json.dumps(
                    {
                        "salud": self.salud,
                        "ultimo_exitoso": self.ultimo_exitoso,
                        "config": self.config,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            HISTORY_FILE.write_text(
                json.dumps(self.historial[-MAX_HISTORIAL:], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _aplicar_config(self, cfg: Dict[str, Any]) -> None:
        """Solo acepta claves conocidas y orden/modelos de la lista cerrada."""
        if "orden" in cfg:
            # DE_PAGO siempre fuera: ni el orden guardado ni un pedido por API
            # pueden meter un proveedor de pago en la cadena.
            orden = [p for p in cfg["orden"] if p in POR_ID and p not in DE_PAGO]
            for p in CONFIG_DEFAULT["orden"]:
                if p not in orden and p in POR_ID:
                    orden.append(p)
            if orden:
                self.config["orden"] = orden
        if "modelos" in cfg and isinstance(cfg["modelos"], dict):
            for k, v in cfg["modelos"].items():
                if k in POR_ID and isinstance(v, str) and v.strip():
                    self.config["modelos"][k] = v.strip()
        for k in ("ttl_salud_s", "sonda_auto_min", "reintentos"):
            if k in cfg:
                try:
                    self.config[k] = int(cfg[k])
                except (TypeError, ValueError):
                    pass

    # ------------------------------------------------------------ estado
    def datos_proveedor(self, prov: Proveedor) -> Dict[str, Any]:
        clave = _clave_de(prov)
        modelo = self.config["modelos"].get(prov.id, prov.modelo_por_defecto)
        s = self.salud.get(prov.id, {})
        return {
            "id": prov.id,
            "nombre": prov.nombre,
            "modelo": modelo,
            "local": prov.local,
            "tiene_clave": bool(clave),
            "clave_huella": _redactar(clave) if not prov.local else "(sin clave: local)",
            "url": prov.url if not prov.local else _norm_ollama(clave) or "(no definido)",
            "auth": prov.auth,
            "salud": s.get("ok"),
            "latencia_ms": s.get("latencia_ms"),
            "error": s.get("error", ""),
            "motivo": s.get("motivo", ""),
            "ttl_s": s.get("ttl"),
            "comprobado_hace_s": (round(time.time() - s["cuando"]) if s.get("cuando") else None),
        }

    def lista(self) -> List[Dict[str, Any]]:
        return [self.datos_proveedor(p) for p in PROVEEDORES]

    def orden_efectivo(self) -> List[str]:
        """El orden configurado, pero el que funciono va primero.

        Si el ultimo que respondio bien sigue sano, empezar por el evita
        perder tiempo con un proveedor que sabemos que esta caido.
        """
        orden = list(self.config["orden"])
        if self.ultimo_exitoso and self.ultimo_exitoso in orden:
            s = self.salud.get(self.ultimo_exitoso, {})
            if s.get("ok"):
                orden.remove(self.ultimo_exitoso)
                orden.insert(0, self.ultimo_exitoso)
        return orden

    # ------------------------------------------------------------ sonda
    def sondar(self, prov_id: str, forzar: bool = False) -> Dict[str, Any]:
        prov = POR_ID.get(prov_id)
        if not prov:
            return {"ok": False, "error": "proveedor desconocido"}
        with self._lock:
            s = self.salud.get(prov_id, {})
            if (
                not forzar
                and s.get("cuando")
                and time.time() - s["cuando"] < s.get("ttl", self.config["ttl_salud_s"])
            ):
                return dict(s)

            clave = _clave_de(prov)
            if not clave:
                res = {"ok": False, "error": "sin clave configurada", "cuando": time.time()}
                self.salud[prov_id] = res
                self.guardar()
                return res

            t0 = time.time()
            try:
                ok, _, err = LLAMADORES[prov.id](
                    prov,
                    self.config["modelos"].get(prov.id, prov.modelo_por_defecto),
                    clave,
                    "di OK",
                    MAX_TOKENS_SONDA,
                    TIMEOUT_LOCAL if prov.local else TIMEOUT_SONDA,
                )
            except Exception as e:  # noqa: BLE001
                ok, err = False, f"{type(e).__name__}: {e}"
            fallo = (err or "sin respuesta")[:300]
            res = {
                "ok": bool(ok),
                "error": "" if ok else fallo,
                "latencia_ms": round((time.time() - t0) * 1000),
                "cuando": time.time(),
            }
            if not ok:
                # Cuota cortada: cuarentena corta y marcada; caida: la de siempre.
                res["motivo"] = "cuota" if es_cuota(fallo) else "fallo"
                res["ttl"] = (
                    self.config.get("ttl_cuota_s", 180)
                    if res["motivo"] == "cuota"
                    else self.config["ttl_salud_s"]
                )
            self.salud[prov_id] = res
            self.guardar()
            return res

    def sondar_todos(self, forzar: bool = False) -> Dict[str, Any]:
        return {p.id: self.sondar(p.id, forzar=forzar) for p in PROVEEDORES}

    # ------------------------------------------------------------ respuesta
    def responder(
        self, prompt: str, proveedor: Optional[str] = None, max_tokens: int = 512
    ) -> Dict[str, Any]:
        """Intenta en orden y devuelve la primera respuesta buena.

        Devuelve SIEMPRE el rastro de intentos: si algo falla, hay que poder
        ver que se intento y por que, no solo un "no funciona".
        """
        prompt = (prompt or "").strip()
        if not prompt:
            return {"ok": False, "error": "prompt vacio"}
        if len(prompt) > 8000:
            return {"ok": False, "error": "prompt demasiado largo (max 8000)"}

        objetivo = [proveedor] if proveedor else self.orden_efectivo()
        intentos: List[Dict[str, Any]] = []

        with self._lock:
            for pid in objetivo:
                prov = POR_ID.get(pid)
                if not prov:
                    intentos.append(
                        {"proveedor": pid, "ok": False, "error": "proveedor desconocido"}
                    )
                    continue
                if proveedor is None and not prov.local:
                    s = self.salud.get(pid, {})
                    if s.get("ok") is False and (
                        time.time() - s.get("cuando", 0)
                        < s.get("ttl", self.config["ttl_salud_s"])
                    ):
                        # Sabemos que esta caido (o que corto cuota) y el
                        # aviso es reciente: ni lo intentamos, seguimos.
                        cuota = s.get("motivo") == "cuota"
                        intentos.append(
                            {
                                "proveedor": pid,
                                "ok": False,
                                "error": (
                                    "en cuarentena por cuota: " if cuota
                                    else "descartado por sonda reciente: "
                                )
                                + (s.get("error", "")[:120]),
                                "omitido": True,
                            }
                        )
                        continue

                clave = _clave_de(prov)
                if not clave:
                    intentos.append(
                        {"proveedor": pid, "ok": False, "error": "sin clave configurada"}
                    )
                    continue

                for intento in range(self.config["reintentos"] + 1):
                    t0 = time.time()
                    modelo = self.config["modelos"].get(prov.id, prov.modelo_por_defecto)
                    try:
                        ok, texto, err = LLAMADORES[prov.id](
                            prov,
                            modelo,
                            clave,
                            prompt,
                            max_tokens,
                            TIMEOUT_LOCAL if prov.local else TIMEOUT_LLAMADA,
                        )
                    except Exception as e:  # noqa: BLE001
                        ok, texto, err = False, "", f"{type(e).__name__}: {e}"
                    lat = round((time.time() - t0) * 1000)
                    if ok:
                        self.ultimo_exitoso = pid
                        self.salud[pid] = {
                            "ok": True,
                            "error": "",
                            "latencia_ms": lat,
                            "cuando": time.time(),
                        }
                        salida = {
                            "ok": True,
                            "proveedor": pid,
                            "modelo": modelo,
                            "texto": texto,
                            "latencia_ms": lat,
                            "intentos": intentos
                            + [{"proveedor": pid, "ok": True, "latencia_ms": lat}],
                        }
                        self.historial.append(
                            {
                                "cuando": time.time(),
                                "proveedor": pid,
                                "modelo": modelo,
                                "prompt": prompt[:120],
                                "latencia_ms": lat,
                                "caracteres": len(texto),
                            }
                        )
                        self.guardar()
                        return salida
                    intentos.append(
                        {
                            "proveedor": pid,
                            "ok": False,
                            "error": (err or "")[:200],
                            "latencia_ms": lat,
                            "intento": intento + 1,
                        }
                    )
                # si llegamos aqui, este proveedor fallo: marcarlo. Si fue por
                # cuota, su cuarentena es corta (ttl_cuota_s) para volver en
                # cuanto se descontamine, no esperar los 15 min de caida real.
                ultimo_error = (intentos[-1].get("error", "") if intentos else "")[:300]
                cuota = es_cuota(ultimo_error)
                self.salud[pid] = {
                    "ok": False,
                    "error": ultimo_error,
                    "latencia_ms": intentos[-1].get("latencia_ms") if intentos else None,
                    "cuando": time.time(),
                    "motivo": "cuota" if cuota else "fallo",
                    "ttl": (
                        self.config.get("ttl_cuota_s", 180)
                        if cuota
                        else self.config["ttl_salud_s"]
                    ),
                }
            self.guardar()
            return {"ok": False, "error": "ningun proveedor respondio", "intentos": intentos}

    # ------------------------------------------------------------ hilo
    def iniciar(self) -> None:
        if self._hilo and self._hilo.is_alive():
            return

        def bucle() -> None:
            while True:
                time.sleep(max(60, self.config["sonda_auto_min"] * 60))
                try:
                    self.sondar_todos(forzar=True)
                except Exception:  # noqa: BLE001
                    pass

        self._hilo = threading.Thread(target=bucle, daemon=True)
        self._hilo.start()

    def estado(self) -> Dict[str, Any]:
        with self._lock:
            vivos = [k for k, v in self.salud.items() if v.get("ok")]
            con_clave = [p.id for p in PROVEEDORES if _clave_de(p)]
            return {
                "ok": True,
                "proveedores": len(PROVEEDORES),
                "con_clave": con_clave,
                "disponibles_ahora": vivos,
                "ultimo_exitoso": self.ultimo_exitoso,
                "orden_efectivo": self.orden_efectivo(),
                "orden_configurado": self.config["orden"],
                "config": self.config,
                "respuestas": len(self.historial),
            }


_INSTANCIA: Optional[EnrutadorModelos] = None
_LOCK = threading.RLock()


def get_instance() -> EnrutadorModelos:
    global _INSTANCIA
    with _LOCK:
        if _INSTANCIA is None:
            _INSTANCIA = EnrutadorModelos()
        return _INSTANCIA


# --------------------------------------------------------------------------
#  Rutas Flask — endpoints EXPLICITOS (Flask choca si dos modulos usan el
#  mismo nombre de funcion: dos `_status` revientan el arranque entero)
# --------------------------------------------------------------------------
def register_router_routes(app) -> None:
    bp = Blueprint("router_modelos", __name__)

    @bp.route("/api/router/status", methods=["GET"])
    def router_status():
        return jsonify(get_instance().estado())

    @bp.route("/api/router/providers", methods=["GET"])
    def router_providers():
        return jsonify({"ok": True, "proveedores": get_instance().lista()})

    @bp.route("/api/router/ask", methods=["POST"])
    def router_ask():
        d = request.get_json(silent=True) or {}
        r = get_instance().responder(
            prompt=str(d.get("prompt", "")),
            proveedor=d.get("proveedor") or None,
            max_tokens=int(d.get("max_tokens", 512) or 512),
        )
        return jsonify(r), (200 if r.get("ok") else 502)

    @bp.route("/api/router/test", methods=["POST", "GET"])
    def router_test():
        d = request.get_json(silent=True) or {}
        forzar = bool(d.get("forzar", True))
        return jsonify({"ok": True, "resultado": get_instance().sondar_todos(forzar=forzar)})

    @bp.route("/api/router/history", methods=["GET"])
    def router_history():
        h = get_instance().historial
        return jsonify({"ok": True, "total": len(h), "ultimas": h[-20:]})

    @bp.route("/api/router/config", methods=["GET", "POST"])
    def router_config():
        en = get_instance()
        if request.method == "GET":
            return jsonify({"ok": True, "config": en.config})
        d = request.get_json(silent=True) or {}
        with en._lock:
            en._aplicar_config(d)
            en.guardar()
        return jsonify({"ok": True, "config": en.config})

    app.register_blueprint(bp)
    get_instance().iniciar()
    print(
        "[Model Router] Routes registered: /api/router/* "
        "(status, providers, ask, test, history, config)"
    )


# --------------------------------------------------------------------------
#  Demo
# --------------------------------------------------------------------------
def _cargar_env() -> None:
    """Carga .env si podemos. Dentro de DanielaOS ya lo hace ella, pero el
    demo se lanza suelto y si no, todas las claves saldrian vacias."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # noqa: BLE001
        pass


def _demo(preguntar: bool = False) -> None:
    _cargar_env()
    print("=" * 70)
    print(" E-32 · ENRUTADOR DE MODELOS — un cerebro, muchos proveedores")
    print("=" * 70)

    en = EnrutadorModelos()
    print("\n-- proveedores de la lista cerrada --")
    for p in en.lista():
        marca = "con clave" if p["tiene_clave"] else "SIN CLAVE"
        print(f"  {p['id']:<12} {marca:<10} {p['modelo'][:34]:<34} " f"{p['clave_huella']}")

    print("\n-- clave nunca se muestra entera, solo la huella --")
    print("   (arriba: prefijo de 10 caracteres + longitud)")

    print("\n-- sonda real (lanza una peticion minuscula a cada uno) --")
    res = en.sondar_todos(forzar=True)
    for pid, r in res.items():
        if r.get("ok"):
            print(f"   {pid:<12} OK       {r.get('latencia_ms')} ms")
        else:
            print(f"   {pid:<12} FALLO    {(r.get('error') or '')[:60]}")

    vivos = [k for k, v in res.items() if v.get("ok")]
    print(f"\n   proveedores vivos: {len(vivos)} -> {vivos}")

    if preguntar and vivos:
        print("\n-- respuesta real --")
        r = en.responder("Responde con una sola palabra: hola")
        if r.get("ok"):
            print(f"   proveedor : {r['proveedor']} ({r['modelo']})")
            print(f"   latencia  : {r['latencia_ms']} ms")
            print(f"   texto     : {r['texto'][:120]}")
        else:
            print("   fallo:", r.get("error"))
            for i in r.get("intentos", []):
                print("     -", i.get("proveedor"), "->", (i.get("error") or "")[:80])
    elif not vivos:
        print("\n   ningun proveedor respondio: revisa claves y conexion")

    print("\n-- el caido se descarta solo en la siguiente llamada --")
    print("   orden efectivo:", en.orden_efectivo())
    print("=" * 70)


if __name__ == "__main__":
    _demo(preguntar="--preguntar" in sys.argv)

# Alias para compatibilidad
ModelRouter = EnrutadorModelos