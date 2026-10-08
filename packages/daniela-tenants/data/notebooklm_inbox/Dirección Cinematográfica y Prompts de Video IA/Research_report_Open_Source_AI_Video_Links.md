### Reporte de Investigación: Recursos y Enlaces Open-Source para Producción Audiovisual IA

Este reporte recopila repositorios oficiales, flujos de trabajo (workflows de ComfyUI), modelos en Hugging Face y guías técnicas para conectar los modelos de video e imagen de código abierto a tu proyecto cinematográfico.

---

#### 🔧 Repositorios y Modelos Oficiales

| # | Título | Fuente | Tipo |
| --- | --- | --- | --- |
| 1 | [Tencent HunyuanVideo GitHub](https://github.com/Tencent-Hunyuan/HunyuanVideo) | Tencent | 🔧 Technical |
| 2 | [HunyuanVideo-1.5 en Hugging Face](https://huggingface.co/tencent/HunyuanVideo-1.5) | Hugging Face | 📄 Research / Model |
| 3 | [Lightricks LTX-2.3 en Hugging Face](https://huggingface.co/Lightricks/LTX-2.3) | Lightricks | 📄 Research / Model |

**(1)** Repositorio oficial del modelo open-source de generación de video HunyuanVideo, que incluye integración nativa para ComfyUI y versiones optimizadas.
**(2)** Repositorio oficial de pesos y configuraciones para HunyuanVideo 1.5 en Hugging Face, con soporte para baja VRAM y cuantizaciones FP8/GGUF.
**(3)** Modelo open-source unificado para generación sincrónica de video y audio en alta calidad de la familia LTX-Video.

---

#### ⚙️ Workflows de ComfyUI y Nodos de Control

| # | Título | Fuente | Tipo |
| --- | --- | --- | --- |
| 1 | [ComfyUI Examples (Official Repo)](https://github.com/comfyanonymous/ComfyUI_examples) | GitHub / ComfyUI | 🌐 Overview / Workflows |
| 2 | [ComfyLab Workflows en Español](https://github.com/comfylab-es/comfylab-workflows) | GitHub / ComfyLab | 🔧 Technical / Workflows |
| 3 | [ComfyUI-HunyuanVideoWrapper (Kijai)](https://github.com/kijai/ComfyUI-HunyuanVideoWrapper) | GitHub / Kijai | 🔧 Technical / Custom Nodes |

**(1)** Repositorio oficial con ejemplos descargables en formato JSON/WebP para Flux, HunyuanVideo, Wan 2.1, LTX-Video y Mochi.
**(2)** Colección de workflows en español probados en GPUs de 4GB a 24GB VRAM para HunyuanVideo, Flux Kontext, Wan 2.1 y LTXV.
**(3)** Nodos personalizados para ejecutar HunyuanVideo en ComfyUI con soporte FP8, parches de velocidad y aceleración de memoria.

---

#### 📋 Documentación y Guías de Configuración

| # | Título | Fuente | Tipo |
| --- | --- | --- | --- |
| 1 | [ComfyUI Docs - Tutorial Flux.1](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image) | ComfyUI Docs | 📋 Technical Guide |
| 2 | [ComfyUI Docs - Kandinsky 5.0](https://docs.comfy.org/tutorials/video/kandinsky/kandinsky-5) | ComfyUI Docs | 📋 Technical Guide |

**(1)** Guía paso a paso para configurar Flux.1 Dev y Schnell en ComfyUI, utilizando versiones FP8 para bajo consumo de VRAM.
**(2)** Documentación para integrar Kandinsky 5.0 Lite para generación de video open-source de hasta 10 segundos.

---

#### Temas Clave Identificados

* **Integración Nativa en ComfyUI** : La mayoría de los modelos líderes (Flux, HunyuanVideo, Wan 2.1, LTX-2.3) cuentan con nodos nativos o wrappers mantenidos activamente por la comunidad.
* **Optimización para GPUs Domésticas** : El uso de versiones cuantizadas en FP8 y GGUF permite ejecutar estos modelos en tarjetas gráficas con 6GB a 12GB de VRAM o en entornos como Google Colab.
* **Consistencia Cinematográfica** : Integración de motores de imagen (como Flux.1) para fotogramas iniciales y modelos de video (como HunyuanVideo o LTX) para la animación.

---

*Investigación realizada el 01/10/2026.*