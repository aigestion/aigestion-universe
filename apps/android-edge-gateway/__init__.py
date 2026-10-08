"""aig Mobile App - arbol unico de cliente (PWA + servicios edge + Pixel).

`mobile-app/` NO es un paquete Python (el nombre lleva guion), asi que este
fichero no se importa nunca: se deja solo como documentacion del arbol. Los
subpaquetes (`services`, `bridges`, `core`, `api`) se importan EN PLANO, con
`mobile-app/` el primero de ``sys.path`` (lo hace ``main.py`` y ``run.py``):

    from services.sensors import stereo_vision
    from bridges.comms import safe_exec
    from core.autonomy import daniela_mesh

Estructura (unificacion 2026-09-29, antes ``android_app/``):

    mobile-app/services/{sensors,security,mesh,ui,iot}
    mobile-app/bridges/{comms,pixel}
    mobile-app/core/{autonomy,context,ci}
    mobile-app/api/
    mobile-app/index.html, js/, css/, sw.js, manifest.json   (PWA)
"""

__version__ = "1.0.0"
__author__ = "aig"
