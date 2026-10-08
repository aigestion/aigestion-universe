"""aig core — orquestador, adapters, auth/billing/analytics.

Importación perezosa: los submódulos se resuelven bajo demanda
(`from core.daniela_os_core import DanielaCore`). No hay
re-exports eager para no pagar coste de arranque en Termux/Pixel.
"""
