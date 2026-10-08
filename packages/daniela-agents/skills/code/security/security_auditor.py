"""Skill: Daniela experta en auditorías (secops).

Conocimiento + ejecución: responde qué mirar, ejecuta el harness y explica
los hallazgos en lenguaje humano. Contrato: devuelve SIEMPRE str.
"""
import logging
import os

# ── Conocimiento experto (OWASP + WiFi + supply chain, resumido) ──

CONOCIMIENTO = {
    "owasp": (
        "OWASP Top 10 (2021): 1) control de acceso roto, 2) fallos "
        "criptográficos, 3) inyección, 4) diseño inseguro, 5) mala "
        "configuración, 6) componentes vulnerables, 7) auth rota, "
        "8) integridad de datos/software, 9) fallos de logging, 10) SSRF. "
        "En tu casa los más probables: 5 (puertos 0.0.0.0, HTTP plano, "
        "cabeceras ausentes), 7 (endpoints sin auth, JWT con fallback) y "
        "6 (dependencias con CVE)."
    ),
    "wifi": (
        "WiFi segura: WPA3 (o WPA2-AES, nunca WEP/TKIP), clave de 20+ "
        "caracteres, WPS desactivado, firmware del router al día, red de "
        "invitados para IoT, y revisar periódicamente los dispositivos "
        "conectados. Un dispositivo desconocido = posible intruso: cambia "
        "la clave y expulsa."
    ),
    "secretos": (
        "Secretos: nunca en el repo (ni en docs ni en compose con valores "
        "reales), siempre en .env ignorado; rotar lo filtrado; sin fallbacks "
        "por defecto en código; la bóveda (silicon_vault) para lo sensible."
    ),
    "supply": (
        "Supply chain: fijar versiones, auditar con pip-audit/npm audit/OSV, "
        "SBOM, y actualizar lo que tenga CVE que te afecte (que el paquete "
        "sea vulnerable no significa que tu uso lo sea: mira si usas la "
        "función afectada)."
    ),
    "movil": (
        "Pixel/Termux: paquetes al día (pkg upgrade), sshd con clave (no "
        "password) o apagado, ADB por red apagado salvo uso puntual, "
        "termux-wake-lock solo si hace falta, revisar permisos de "
        "termux-setup-storage, y no exponer puertos a la WiFi sin token."
    ),
}

GRAVEDAD_CONSEJO = {
    "critica": "actúa HOY: aísla, cierra o rota antes de seguir usando eso.",
    "alta": "esta semana: es explotable por alguien en tu red.",
    "media": "este mes: endurece cuando toques ese servicio.",
    "baja": "higiene: aplícalo en la próxima pasada.",
    "info": "informativo: no requiere acción.",
}


def _responde_conocimiento(cmd: str) -> str | None:
    for clave, texto in CONOCIMIENTO.items():
        if clave in cmd or (
            clave == "wifi" and ("red" in cmd or "intruso" in cmd)
        ) or (
            clave == "secretos" and ("clave" in cmd or "password" in cmd)
        ):
            return f"[AUDITORÍA]: {texto}"
    return None


def _ejecutar(perfil: str) -> str:
    try:
        from secops.runner import ejecutar, guardar, resumen_para_daniela
    except Exception as e:  # noqa: BLE001 - árbol parcial
        logging.warning("security_auditor: secops no importable: %s", e)
        return "[AUDITORÍA]: el harness no está disponible en este equipo."
    try:
        informe = ejecutar(perfil=perfil)
        guardar(informe)
        return "[AUDITORÍA]: " + resumen_para_daniela(informe)
    except Exception as e:  # noqa: BLE001 - la auditoría nunca debe tumbar el chat
        logging.warning("security_auditor: fallo ejecutando: %s", e)
        return f"[AUDITORÍA]: no pude completar la auditoría ({e})."


def _ultimo_informe() -> str:
    ruta = os.path.join("data", "secops", "reports", "latest.json")
    if not os.path.exists(ruta):
        return "[AUDITORÍA]: aún no hay informes. Pídeme 'audita'."
    try:
        import json

        from secops.runner import resumen_para_daniela

        with open(ruta, encoding="utf-8") as fh:
            return "[AUDITORÍA] (último informe): " + resumen_para_daniela(json.load(fh))
    except Exception as e:  # noqa: BLE001
        return f"[AUDITORÍA]: no pude leer el informe ({e})."


def process_audit_command(command):
    """
    Skill: Auditoría de seguridad -> secops (real).

    Entiende: 'audita' / 'audita completo' / 'última auditoría' /
    preguntas de conocimiento (owasp, wifi, secretos, supply, movil).
    Contrato: devuelve SIEMPRE str.
    """
    cmd = (command or "").lower()
    if "completo" in cmd or "completa" in cmd or "fondo" in cmd:
        return _ejecutar("completo")
    if "audita" in cmd or "auditoría" in cmd or "audit" in cmd or "escanea" in cmd:
        if "últim" in cmd or "informe" in cmd or "report" in cmd:
            return _ultimo_informe()
        return _ejecutar("rapido")
    if "últim" in cmd and ("informe" in cmd or "report" in cmd or "auditor" in cmd):
        return _ultimo_informe()
    respuesta = _responde_conocimiento(cmd)
    if respuesta:
        return respuesta
    return (
        "[AUDITORÍA]: sé auditar tu PC, tu Pixel y tu WiFi. Pídeme 'audita' "
        "(rápida), 'audita completo' (con red), 'último informe', o pregúntame "
        "por owasp, wifi, secretos, supply o móvil."
    )
