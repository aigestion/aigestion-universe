# Guía Rápida: Comparativa de Modelos de Video e Imagen IA Open-Source, Requisitos de VRAM y Workflows en ComfyUI

### 1. Evaluación Técnica y Comparativa de Modelos Principales (HunyuanVideo, Wan 2.1/2.2, LTX-2.3, Flux.1)

En el panorama actual de la inteligencia artificial generativa audiovisual, los modelos de código abierto (*open-source*) han alcanzado un nivel de madurez técnica capaz de rivalizar directamente con las alternativas propietarias de código cerrado. Para los realizadores independientes y directores técnicos, comprender la arquitectura subyacente de estos modelos y optimizar los recursos de memoria gráfica (VRAM) resulta estratégicamente fundamental. Esta comprensión permite maximizar la calidad cinematográfica y la eficiencia operacional sin depender de infraestructuras comerciales restrictivas ni incurrir en costes desmedidos de procesamiento local.

#### 1.1 Análisis de Modelos de Video de Gran Escala (HunyuanVideo y Wan 2.1 / 2.2)

*   **HunyuanVideo (Tencent):**
    *   **Arquitectura y Parámetros:** Modelo fundacional de generación de video de gran escala con más de 13 mil millones de parámetros (13B). Utiliza una arquitectura de difusión basada en Transformer (*Diffusion Transformer* o DiT) con un diseño híbrido *"Dual-stream to Single-stream"*. En la fase *dual-stream*, los *tokens* de video y texto se procesan de forma independiente en bloques Transformer dedicados para evitar interferencias modales; posteriormente, en la fase *single-stream*, los *tokens* de ambas modalidades se concatenan para lograr una fusión multimodal profunda.
    *   **Codificación y Compresión:** Incorpora como codificador de texto un Modelo de Lenguaje Multimodal (MLLM) basado en `llava-llama-3-8b` (con estructura *Decoder-Only* y ajuste fino de instrucciones visuales), respaldado por un refinador bidireccional de *tokens*. Para la compresión espacio-temporal, implementa un 3D VAE alimentado por convoluciones causales (*CausalConv3D*), registrando tasas de compresión exactas de $4\times$ en la dimensión temporal (longitud de fotogramas), $8\times$ en la dimensión espacial (ancho y alto) y $16\times$ en los canales latentes.
    *   **Exigencias de VRAM y Optimización:** La ejecución estándar a precisión `bf16` exige 60 GB de VRAM para secuencias en resolución 720p (1280x720 a 129 fotogramas) y 45 GB de VRAM para resolución 544p (960x544 a 129 fotogramas). Para habilitar la inferencia en GPUs comerciales de menor capacidad, Tencent distribuye pesos cuantizados en **FP8** (`mp_rank_00_model_states_fp8.pt`) acompañados de su mapa de escalado (`mp_rank_00_model_states_fp8_map.pt`). Su ejecución bajo el modo `fp8_scaled` reduce el consumo en ~10 GB de VRAM conservando una precisión matemática equivalente a `bf16`. Asimismo, el sistema admite la descarga de capas a RAM (*CPU offload* mediante `--use-cpu-offload`) e inferencia paralela multi-GPU mediante la tecnología de paralelismo de secuencias unificado (USP) de xDiT, parametrizada a través de `--ulysses-degree` y `--ring-degree`.

*   **Wan 2.1 y Wan 2.2:**
    *   **Rendimiento y Capacidades Cinemáticas:** Wan 2.1 destaca en tareas de animación de imagen a video (*Image-to-Video* o I2V), ofreciendo una destacada coherencia espacial y dinamismo orgánico. Wan 2.2 introduce una arquitectura basada en mezcla de expertos (*Mixture of Experts* o MoE) dividida en dos redes especializadas: el experto de alto ruido (*HighNoise*), encargado de las etapas iniciales de muestreo para definir la estructura geométrica global y los límites del movimiento, y el experto de bajo ruido (*LowNoise*), que asume el proceso en las etapas finales para refinar texturas finas y detalles fotográficos. A nivel operacional, la alternancia o carga simultánea de ambos módulos MoE exige una gestión estricta de VRAM en ComfyUI, requiriendo el intercambio dinámico de pesos en GPU o disponer de un búfer de 24 GB de VRAM para mantener ambos modelos en memoria sin *swapping*.

#### 1.2 Análisis de Modelos Unificados y de Imagen (LTX-2.3 y Flux.1)

*   **LTX-2.3 (Lightricks):**
    *   **Arquitectura Unificada de Video y Audio:** Con 22 mil millones de parámetros (22B en su versión `ltx-2.3-22b-dev`), LTX-2.3 es un modelo DiT que sintetiza video y audio sincrónico de forma conjunta. Esta generación simultánea se logra muestreando latentes unificados de audio y video dentro del mismo pase directo (*forward pass*) de la red. Utiliza como codificador de texto el modelo `gemma-3-12b-it`.
    *   **Versiones, Reglas de Dimensión y Upscaling:** Incluye la variante *distilled* (`ltx-2.3-22b-distilled`), optimizada para inferencia ultra rápida en 8 pasos con CFG=1. El modelo impone reglas geométricas estrictas: las dimensiones de ancho y alto deben ser divisibles por 32, mientras que el número total de fotogramas debe cumplir la fórmula $8k + 1$ (ej. 9, 17, 25, 129 fotogramas). Cuando una entrada no cumple con esta divisibilidad, el tensor de entrada debe rellenarse (*padding*) con valores `-1` antes de la inferencia y recortarse (*crop*) en el array de salida post-generación. Para flujos de alta resolución y elevada tasa de FPS, la arquitectura integra escaladores latentes espaciales (`ltx-2.3-spatial-upscaler-x2-1.1` y `ltx-2.3-spatial-upscaler-x1.5-1.0`) y temporales (`ltx-2.3-temporal-upscaler-x2-1.0`).

*   **Flux.1 (Black Forest Labs):**
    *   **Variantes del Modelo:** Desarrollado sobre una arquitectura híbrida Transformer-Difusión de 12 mil millones de parámetros (12B), se divide en tres versiones: *Flux.1 [pro]* (comercial, vía API), *Flux.1 [dev]* (orientado a máxima calidad fotográfica y fidelidad al prompt, bajo licencia no comercial) y *Flux.1 [schnell]* (licencia Apache 2.0, diseñado para inferencias rápidas en 4 pasos).
    *   **Rutas de Instalación y Cuantización FP8:** La variante completa requiere la carga modular de codificadores, VAE y modelo de difusión en directorios específicos de ComfyUI:
        *   Codificadores de texto T5 y CLIP (`clip_l.safetensors`, `t5xxl_fp16.safetensors` o `t5xxl_fp8_e4m3fn.safetensors`): `ComfyUI/models/text_encoders/` (o `ComfyUI/models/clip/`).
        *   Autoencoder VAE (`ae.safetensors`): `ComfyUI/models/vae/`.
        *   Modelo de Difusión (`flux1-dev.safetensors` / `flux1-schnell.safetensors`): `ComfyUI/models/diffusion_models/`.
        *   *FP8 Checkpoints unificados* (`flux1-dev-fp8.safetensors` y `flux1-schnell-fp8.safetensors`): combinan todos los componentes cuantizados en un solo archivo y deben alojarse en `ComfyUI/models/checkpoints/`.

#### 1.3 Cuadro Comparativo de Especificaciones Técnicas y VRAM

| Modelo | Arquitectura / Parámetros | Requisitos de VRAM (Full / FP8 / Offload) | Formato de Entrada / Salida | Casos de Uso Primarios |
| :--- | :--- | :--- | :--- | :--- |
| **HunyuanVideo** | Dual-to-Single Stream DiT (13B) + MLLM (`llava-llama-3-8b`) + 3D VAE | • **Full (`bf16`):** 60 GB (720p) / 45 GB (544p)<br>• **FP8 (`fp8_scaled`):** ~35–50 GB pico<br>• **CPU Offload:** ~12–24 GB VRAM<br>• **Multi-GPU:** Distribución xDiT (`ulysses`/`ring`) | Texto / Imagen $\rightarrow$ Video (720p/544p a 129f, MP4) | Generación de video cinematográfico de gran escala con amplio dinamismo y alta resolución. |
| **Wan 2.1 / 2.2** | DiT (Wan 2.1) / MoE (*HighNoise* + *LowNoise*) (Wan 2.2) | • **Nativo:** 24 GB VRAM (RTX 3090/4090)<br>• **Optimizado:** 8–12 GB VRAM con cuantización y *swapping* de expertos MoE | Imagen / Texto $\rightarrow$ Video | Animación *Image-to-Video* (I2V) de alta fidelidad y representación de secuencias de acción complejas. |
| **LTX-2.3** | DiT Unificado Video-Audio (22B) + `gemma-3-12b-it` | • **Base / Distilled:** 12–24 GB VRAM<br>• **Offload:** 8 GB+ VRAM<br>• Inferencia *Distilled* en 8 pasos (CFG=1) | Texto / Imagen $\rightarrow$ Video + Audio sincrónico (Divisibilidad: Ancho/Alto/32; Frames $8k+1$) | Producción ágil de secuencias de video con pista de audio sincrónica integrada en una sola pasada. |
| **Flux.1 [dev]** | Híbrido Transformer-Difusión (12B) | • **Full (`t5xxl_fp16`):** >32 GB VRAM<br>• **FP8 Text Encoder:** ~16–24 GB VRAM<br>• **FP8 Checkpoint:** ~12–16 GB VRAM | Texto $\rightarrow$ Imagen | Creación de fotogramas maestros y *keyframes* base con máxima fidelidad conceptual y calidad fotográfica. |
| **Flux.1 [schnell]** | Híbrido Transformer-Difusión (12B, 4 pasos) | • **FP8 Checkpoint:** 6–12 GB VRAM<br>• Inferencia ultra rápida en 4 pasos | Texto $\rightarrow$ Imagen | Generación ágil de *concept art*, guiones gráficos (*storyboards*) y recursos visuales en tiempo real. |

Comprender el rendimiento de estos modelos en hardware local establece la base técnica necesaria para evaluar cuándo ejecutar procesos internamente y cuándo resulta conveniente externalizarlos a plataformas de procesamiento gratuito en la nube.

---

### 2. Alternativas de Ejecución Gratuita en la Nube y Entornos de Cero Costo

Para los creadores audiovisuales que no disponen de tarjetas gráficas de gama alta o cuyas GPUs domésticas se encuentran limitadas en el rango de los 4 GB a 8 GB de VRAM, el ecosistema de inteligencia artificial ofrece infraestructuras en la nube totalmente gratuitas. Estas plataformas permiten ejecutar modelos pesados de video e imagen sin asumir costes directos de cómputo local.

#### 2.1 Entornos de Código Abierto y Notebooks Cloud (Google Colab, Hugging Face, Kaggle)

*   **Google Colab (Tier Gratuito):** Asigna instancias con aceleración por GPU (típicamente NVIDIA T4 con 16 GB de VRAM). Resulta adecuado para ejecutar entornos basados en la librería `diffusers` de Hugging Face o implementaciones ligeras de modelos cuantizados mediante *scripts* en Python.
*   **Hugging Face Spaces:** Permite desplegar y ejecutar aplicaciones interactivas desarrolladas en Gradio o Streamlit de forma gratuita. Proporciona acceso a demostraciones públicas de LTX-2.3 o HunyuanVideo mediante espacios comunitarios sin consumo de recursos locales.
*   **Kaggle Code Notebooks:** Otorga hasta 30 horas semanales de cómputo gratuito en GPUs NVIDIA T4 o P100. Es un entorno idóneo para clonar repositorios oficiales (como `Lightricks/LTX-2`), descargar pesos directamente mediante `hf download` e instalar dependencias optimizadas vía `uv sync`.

#### 2.2 Plataformas Web Generativas Gratis (RunningHub, SeaArt, Liblib, Tensor.art)

*   **RunningHub:** Plataforma web especializada en la ejecución en la nube de flujos de trabajo (*workflows*) de ComfyUI. Permite cargar archivos JSON personalizados y procesar nodos pesados de video e imagen aprovechando hardware remoto.
*   **Tensor.art y SeaArt:** Interfaces generativas que otorgan créditos y cuotas diarias renovables. Permiten ejecutar modelos como Flux.1, Stable Diffusion XL y adaptadores LoRA sin necesidad de configurar código local.
*   **Liblib:** Entorno enfocado en el despliegue de modelos y control de generación de imagen y video, idóneo para probar configuraciones visuales avanzadas a coste cero.

#### 2.3 Estrategia de Rotación de Tiers Gratuitos en Proveedores Comerciales

Diversas plataformas comerciales proporcionan créditos diarios o semanales renovables sin requerir tarjeta de crédito. A continuación, se presenta un plan estructurado de "rotación diaria de proveedores" diseñado para maximizar el rendimiento audiovisual a coste cero:

1.  **Bloque de Generación de Imagen Base y Keyframes (Mañanas):**
    *   *Ideogram / Leonardo AI:* Utilizar la cuota renovable diaria (~150 créditos en Leonardo / cuota diaria en Ideogram) para definir el estilo estético, generar el diseño visual de personajes y crear entre 15 y 20 imágenes de referencia (*keyframes*).
2.  **Bloque de Animación Text-to-Video e Image-to-Video (Tardes - Fase A):**
    *   *Kling AI:* Asignar los 66 créditos diarios gratuitos para animar de 3 a 6 tomas donde se requiera expresividad facial o movimientos complejos (*Image-to-Video*).
    *   *Luma Dream Machine:* Emplear las generaciones gratuitas diarias para procesar de 2 a 4 tomas que exijan desplazamientos de cámara panorámicos o movimientos de simulación física.
3.  **Bloque de Animación y Efectos Secundarios (Tardes - Fase B):**
    *   *Runway (Gen-2 / Gen-3):* Reservar la cuota mensual/diaria para tomas cinematográficas puntuales que requieran transformaciones de video a video (*Video-to-Video*).
    *   *Pika / Haiper AI / Vidu:* Completar entre 4 y 8 tomas secundarias del *storyboard* (planos de detalle, recursos ambientales o insertos de cobertura), aprovechando sus sistemas de créditos renovables.

**Rendimiento Estimado Diario:** La aplicación rigurosa de esta rotación permite obtener un rendimiento medio diario de **15 a 20 fotogramas maestros (*keyframes*)** y de **10 a 15 clips de video planos (*raw clips*)**, suficientes para ensamblar la estructura visual de una secuencia cinematográfica corta cada día.

El uso estratégico de estas plataformas en la nube actúa como un puente directo hacia la orquestación local y avanzada mediante interfaces modulares como ComfyUI.

---

### 3. Configuración de Interfaces y Workflows Profesionales en ComfyUI

ComfyUI se ha consolidado como el estándar de programación visual para la inteligencia artificial generativa. Su arquitectura basada en grafos direccionados permite a los directores técnicos ensamblar pipelines complejos de video e imagen, optimizando el uso de VRAM mediante la modularidad de componentes y la aceleración por nodos.

#### 3.1 Estructura Básica y Modelos de Carga en ComfyUI

*   **Pipeline Esencial para Flux.1:**
    1.  `DualCLIPLoader`: Carga los codificadores de texto. El puerto `clip_name1` se conecta al modelo T5 (`t5xxl_fp16.safetensors` o `t5xxl_fp8_e4m3fn.safetensors` en `ComfyUI/models/text_encoders/`), y `clip_name2` al modelo CLIP (`clip_l.safetensors`).
    2.  `Load Diffusion Model`: Carga el modelo de difusión principal (`flux1-dev.safetensors` o `flux1-schnell.safetensors`) ubicado en `ComfyUI/models/diffusion_models/`.
    3.  `Load VAE`: Carga el autoencoder VAE (`ae.safetensors`) ubicado en `ComfyUI/models/vae/`.
    4.  *Esquema Checkpoint FP8:* Al utilizar versiones integradas (`flux1-dev-fp8.safetensors` en `ComfyUI/models/checkpoints/`), un solo nodo `Load Checkpoint` suministra las salidas MODEL, CLIP y VAE al grafo.

```
Diagrama de Nodos para Flux.1 en ComfyUI:
┌──────────────────┐
│  DualCLIPLoader  ├─(CLIP)─┐
└──────────────────┘        │
┌──────────────────┐        ├─>┌──────────┐    ┌────────────┐    ┌────────────┐
│LoadDiffModel     ├─(MODEL)┼─>│ KSampler ├───>│ VAE Decode ├───>│ Save Image │
└──────────────────┘        │  └──────────┘    └────────────┘    └────────────┘
┌──────────────────┐        │                        ▲
│    Load VAE      ├─(VAE)──┘────────────────────────┘
└──────────────────┘
```

*   **Configuración para HunyuanVideo:**
    *   Puede desplegarse mediante soporte nativo o utilizando el wrapper especializado `ComfyUI-HunyuanVideoWrapper` desarrollado por Kijai.
    *   Requiere la carga del codificador de texto multimodal MLLM alojado en el directorio `ComfyUI/models/LLM/llava-llama-3-8b-text-encoder-tokenizer`.
    *   **Inyección de Prompts de Imagen a Video (IP2V):** La integración del codificador visual de `llava-llama-3-8b` permite inyectar imágenes conceptuales directamente en la fase de prompting del MLLM. La imagen se conecta al nodo de codificación y se referencia en el prompt textual mediante la etiqueta `<image>`. La cantidad de *tokens* visuales transferidos al modelo de difusión se controla mediante el parámetro `image_token_selection_expression`. El modelo genera 576 *tokens* por imagen; una expresión como `::4` selecciona 1 de cada 4 *tokens* (144 *tokens* en total). Superar los 256 *tokens* visuales degrada la calidad de la generación, por lo que se recomienda no utilizar expresiones con menor nivel de submuestreo que `::2`.
    *   **Extensiones de Aceleración:** Soporta el nodo *Enhance-A-Video* para incrementar la fidelidad del movimiento sin consumo adicional de memoria, así como motores de caché de bloques como *TeaCache* y *FirstBlockCache* (integrado en `Comfy-WaveSpeed`). Estos sistemas permiten saltear cálculos en bloques redundantes mediante la configuración de rangos de pasos (`start_step`/`end_step`), optimizando la velocidad de muestreo. La aceleración se complementa activando la atención eficiente mediante el parámetro de inicio `--use-sage-attention`.

```
Flujo de Inferencia de HunyuanVideo en ComfyUI:
[llava-llama-3-8b MLLM] ──┐
                          ├─> [Bloques DiT Dual-Stream] ──> [Bloques DiT Single-Stream] ──> [3D VAE Decoder] ──> Archivo MP4
[CLIP-L Text Encoder]  ──┘
```

#### 3.2 Nodos de Control y Consistencia de Personajes

Para garantizar la continuidad estética y la identidad visual a lo largo de un proyecto audiovisual, se emplean nodos de control paramétrico específicos:

*   **IP-Adapter e IP-Adapter Plus SDXL:** Permiten inyectar la identidad visual, vestimenta o estilo de una imagen de referencia directamente en la generación latente de la escena.
*   **PuLID:** Nodo enfocado en mantener la consistencia facial de los personajes sin alterar la iluminación ni el estilo del entorno.
*   **ControlNet Union Pro:** Permite condicionar la composición visual mediante múltiples mapas de control simultáneos (poses de cuerpo OpenPose, profundidad y bordes Canny).
*   **Uni3C ControlNet (Wan 2.1):** Integrado en workflows como `wan21-i2v-uni3c-controlnet-comfylab.json`, habilita un control de cámara paramétrico exacto en 3D sobre la animación I2V de Wan 2.1. Expone parámetros ajustables de órbita de cámara, trayectorias de acimut (*azimuth*), elevación (*elevation*), distancia focal/zoom y desplazamientos de panorámica y titulación (*pan/tilt offsets*).
*   **SCAIL-2:** Nodo especializado en la sustitución y reemplazo de personajes dentro de secuencias de video preexistentes.
*   **LoRAs Cinemáticos:** Destaca el uso de adaptadores como `IC-LoRA Cameraman v2` en LTX-2.3, diseñado para aplicar transferencias de movimiento de cámara desde un video de origen hacia un video sintético (*Video-to-Video*).

#### 3.3 Catálogo de Workflows JSON Descargables y Verificados

A continuación, se compilan los workflows de ComfyUI verificados (pertenecientes al repositorio `comfylab-es/comfylab-workflows`), detallando sus requisitos operativos e infraestructura de modelos:

| Archivo JSON | Propósito del Workflow | VRAM Mínima Requerida | Modelos Clave Asociados |
| :--- | :--- | :--- | :--- |
| `controlnet-union-workflow.json` | Control preciso de poses, bordes y composición de escena. | 4 - 8 GB | ControlNet Union Pro, SDXL / Flux |
| `flux-kontext-character-edit-comfylab.json` | Edición y modificación de personajes manteniendo consistencia. | 8 GB+ | Flux Kontext |
| `hunyuanvideo-t2v-cinematic-comfylab.json` | Generación de video cinemático mediante texto a video (T2V). | 8 - 24 GB (Probado en RTX 3090) | HunyuanVideo (Base / FP8) |
| `ltx-2-3-uncensored-workflow.json` / `ltxv-2.3-t2v-comfylab.json` | Generación de video con pista de audio sincrónica integrada. | 8 GB+ | LTX-2.3 Distilled |
| `wan-21-i2v-cinematic-comfylab.json` | Animación cinematográfica de imagen estática a video (I2V). | 8 GB+ | Wan 2.1 |
| `wan22-i2v-boxer-replication-comfylab.json` | Animación I2V con arquitectura MoE (*HighNoise* + *LowNoise*). | 8 GB+ (24 GB recomendado) | Wan 2.2 MoE |
| `wan21-i2v-uni3c-controlnet-comfylab.json` | Control de cámara paramétrico (órbita, ángulo, distancia) sobre video. | 8 GB+ | Wan 2.1 + Uni3C ControlNet |
| `ic-lora-cameraman-v2-ltx23-comfylab.json` | Transferencia de movimiento de cámara entre videos (*Video-to-Video*). | 8 GB+ | LTX-2.3 + IC-LoRA Cameraman v2 |
| `scail2-character-replacement-comfylab.json` | Reemplazo automatizado de personajes en secuencias de video. | 8 GB+ | SCAIL-2 |
| `rtx-super-resolution-upscaler-comfylab.json` | *Upscaling* de video a resolución 4K con nitidez profesional. | 4 - 8 GB | RTX Super Resolution |

Esta arquitectura modular en ComfyUI proporciona la flexibilidad requerida para desplegar metodologías complejas de producción cinematográfica y la creación de cortometrajes continuos.

---

### 4. Guía Metodológica para la Producción de Cortometrajes y Repositorios Clave

Para lograr resultados cinematográficos de alta calidad sin incurrir en costes de software comercial, se requiere la adopción de una metodología de producción estructurada que vincule la planificación narrativa con la ejecución técnica.

#### 4.1 Flujo Metodológico de Producción Audiovisual Paso a Paso

*   **Paso 1: Investigación Visual Previa y Concepto:**
    Antes de redactar prompts para ideas complejas o producciones de época, es indispensable realizar una investigación sobre referencias visuales reales, dirección de fotografía, paletas de colores e iluminación histórica.
*   **Paso 2: Guion Gráfico y Reglas de Idioma:**
    Se deben segmentar las escenas estableciendo dos conjuntos de instrucciones con reglas idiomáticas estrictas:
    *   **Guion Gráfico (Narrativa y Escena en Español 100%):** Define el número de toma (#), encuadre, movimiento de cámara, descripción dramática de la acción, diálogo y locución.
    *   **Prompts Técnicos (IAs de Imagen y Video en Inglés 100%):** Especifican de forma explícita los parámetros ópticos y fotográficos: óptica exacta (ej. *35mm anamorphic lens, f/1.8 aperture*), esquema de iluminación (ej. *volumetric chiaroscuro, Rembrandt lighting, 5600K color temperature*), trayectoria de cámara (ej. *dolly push-in, low-angle pedestal up, tracking shot*), relación de aspecto y tasa de fotogramas (ej. `--ar 16:9`, `1280x720`, `24 fps`).

```
Ejemplo de Estructura de Prompt Técnico Profesional (En Inglés):

[Visual Prompt / Base Image - Flux.1]
"Cinematic medium shot of an astronaut standing on the dusty surface of Mars, 35mm anamorphic lens, f/1.8 aperture, shallow depth of field, dramatic volumetric chiaroscuro lighting, Rembrandt lighting setup, 5600K daylight color temperature, fine red dust particles suspended in air, hyperrealistic, 8k resolution, photorealistic film grain, --ar 16:9"

[Motion & Camera Prompt / Video Generator - Wan 2.1 / LTX-2.3 / HunyuanVideo]
"Slow forward camera dolly push-in towards the astronaut's reflective visor, subtle low-angle pedestal up, gentle wind blowing Martian dust horizontally past the helmet, smooth organic motion, 24 fps, cinematic shutter speed"
```

*   **Paso 3: Integración de Prompts de Imagen y Movimiento:**
    *   *Visual Prompt:* Se envía a modelos generadores de imagen estática (Flux.1) para crear el fotograma maestro (*keyframe*) con precisión fotográfica.
    *   *Motion & Camera Prompt:* Se introduce en los modelos de video (Wan 2.1, LTX-2.3, HunyuanVideo) utilizando el fotograma maestro como entrada I2V para dictar la velocidad, la dinámica de los elementos y la trayectoria de la cámara.

#### 4.2 Repositorios Oficiales y Comunidades de Cine IA Open-Source

A continuación, se enumeran los repositorios centrales de código abierto y sus comunidades oficiales asociadas para la consulta de documentación y actualización de modelos:

*   **`Tencent-Hunyuan/HunyuanVideo` (GitHub):**
    *   *Recurso Principal:* Repositorio oficial del modelo HunyuanVideo (13B). Incluye scripts de inferencia, pesos cuantizados en FP8, código para servidor Gradio e inferencia paralela multi-GPU vía xDiT.
    *   *Comunidades:* Canales oficiales en WeChat y servidor oficial en Discord (`tv7FkG4Nwf`).
*   **`Lightricks/LTX-2` (GitHub):**
    *   *Recurso Principal:* Monorepo en PyTorch que abarca los paquetes `ltx-core`, `ltx-pipelines` y `ltx-trainer` para el modelo unificado de video y audio LTX-2.3.
    *   *Comunidades:* Espacios en Hugging Face y servidor oficial de Discord de Lightricks.
*   **`comfyanonymous/ComfyUI_examples` (GitHub):**
    *   *Recurso Principal:* Colección oficial de flujos de trabajo de ComfyUI. Contiene imágenes con metadatos JSON integrados listos para arrastrar a la interfaz, cubriendo HunyuanVideo, Wan 2.1/2.2, LTX-Video, Flux.1 y SDXL.
    *   *Comunidades:* Servidor de Discord de ComfyOrg y foros de desarrollo de ComfyUI.
*   **`comfylab-es/comfylab-workflows` (GitHub):**
    *   *Recurso Principal:* Repositorio de workflows de ComfyUI orientados a la producción cinematográfica, optimizados para GPUs de 4 GB a 8 GB de VRAM y probados en tarjetas RTX 3090 (24 GB).
    *   *Comunidades:* Portales educativos y guías en `comfylab.es` (Español) y `comfylab.dev` (Inglés).
*   **`kijai/ComfyUI-HunyuanVideoWrapper` (GitHub):**
    *   *Recurso Principal:* Wrapper desarrollado por Kijai para integrar HunyuanVideo en ComfyUI, ofreciendo soporte experimental para prompting de imagen a video (*IP2V*), *Enhance-A-Video*, modelos I2V y gestión optimizada de VRAM.
    *   *Comunidades:* Comunidad de desarrolladores en GitHub y X (Twitter).

La constante evolución y accesibilidad de estos modelos de código abierto han democratizado los recursos de la producción audiovisual, permitiendo que cineastas independientes y directores técnicos desarrollen piezas de nivel cinematográfico con un control técnico absoluto y a coste cero.