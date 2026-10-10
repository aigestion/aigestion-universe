# Open CADStudio en Daniela OS — Text-to-Parametric-CAD

`agents/agent_cad_studio.py`: del lenguaje natural a
OpenSCAD paramétrico, con validación, BOM y exports honestos.

## Capas (sin teatro)

| Capa | Qué hace | Sin qué no funciona |
|------|----------|---------------------|
| Biblioteca offline | carcasa RPi5+VESa+vents, caja, soporte (parámetros validados) | nada: siempre disponible |
| LLM (Groq primero, fallback router) | piezas libres no catalogadas | `GROQ_API_KEY` o cualquier clave del router |
| Validación sin kernel | balanceo, anti-Python, bounds de parámetros | — |
| Análisis | bbox + volumen **ESTIMADO** por primitivas (sin booleanos) | etiquetado como estimado siempre |
| BOM | gramos PLA (1.24 g/cm³, relleno 25% supuestos) + €/kg 20 | supuestos documentados en el propio BOM |
| Exports | `.scad` siempre; `.stl/.png` (OpenSCAD), `.step` (FreeCAD), G-code (slicer) | toolchain ausente aquí → `no disponible` + receta |

## Toolchain instalado (2026-09-11, verificado)

| Herramienta | Version | Ruta | Desbloquea |
|-------------|---------|------|------------|
| OpenSCAD | 2021.01 (portable GitHub) | `C:\Users\Alejandro\_TOOLS\CAD\openscad` | `.stl`, preview `.png` |
| Blender | 4.5.13 LTS (portable oficial) | `...\CAD\blender` | renders (script `scripts/blender_render_stl.py`) |
| cadquery 2.8 (+OCP 7.9) | pip (`pip install -e .[cad]`) | venv | `.step` (malla→shell cosido) |

En PATH de usuario (nuevas terminales). FreeCAD **no instalado**:
su instalador exige admin y el portable es `.7z` sin lector aquí;
STEP sale por cadquery igualmente (shell cosido, aproximado).

## Probar sin instalar nada

```bash
python agent_cad_studio.py disenar "carcasa raspberry pi 5 vesa" --json
python agent_cad_studio.py validar data/cad/carcasa-raspberry-pi-5-vesa.scad
python agent_cad_studio.py estado
```

Con toolchain (Windows):

```powershell
winget install OpenSCAD.OpenSCAD   # .stl/.png
# FreeCAD (STEP) y PrusaSlicer (G-code): instaladores oficiales
```

## Integración

- Core: intent `cad` → módulo `cad_studio` (keywords: cad, stl,
  pieza, imprimir, openscad, freecad, 3d...). `do_default` diseña
  desde la query.
- Rutas: `/api/cad/disenar`, `/api/cad/estado` (265 → 267 reglas).
- Vault: `cad/disenos`. Ledger `data/cad/disenos.jsonl` (ignorado).
- `publicar <slug>`: commit **explícito** del `.scad` (nada automático).

## Límites honestos

- Sin kernel geométrico no hay booleanos reales, tolerancias
  simuladas ni FEA: la validación es estática + bounds.
- El volumen ignora sustracciones (`difference`): sobreestima a
  propósito y lo dice.
- Renders fotorrealistas (Blender/CDP) y slicing real requieren el
  toolchain: el módulo lo detecta y lo declara, no lo finge.
