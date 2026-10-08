"""aig sil — SIL engine + autofix.

Importación perezosa: los submódulos se resuelven bajo demanda
(`from sil import sil_engine`). No hay re-exports
eager para no pagar coste de arranque en Termux/Pixel.
"""
