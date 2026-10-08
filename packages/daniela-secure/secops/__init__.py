"""secops: auditoría de seguridad continua de Daniela (PC + Pixel + LAN).

Harness 100% stdlib (sin dependencias nuevas): funciona en el PC y en
Termux. Cada auditor devuelve `Finding`; `runner` los agrega en un informe
JSON en `data/secops/` y un resumen que Daniela lee en el chat (`/audita`).

Motores externos (opcionales, nunca obligatorios): Nuclei si hay binario en
`bin/nuclei/` (ver `secops/nuclei.py`); si no está, se reporta como hallazgo
informativo y el resto sigue funcionando.
"""
from secops.models import Finding, counts, ordenar, to_dict

__all__ = ["Finding", "counts", "ordenar", "to_dict"]
