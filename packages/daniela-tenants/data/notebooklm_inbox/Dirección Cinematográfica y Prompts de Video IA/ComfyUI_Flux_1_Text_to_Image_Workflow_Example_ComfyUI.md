ComfyUI Flux.1 Text-to-Image Workflow Example - ComfyUI

#### Documentation Index

Fetch the complete documentation index at: [/llms.txt](https://docs.comfy.org/llms.txt)
Use this file to discover all available pages before exploring further.
[Skip to main content](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#content-area)
[ComfyUI home pagelight logodark logo](https://docs.comfy.org/)
[Get Started](https://docs.comfy.org/)
[Built-in Nodes](https://docs.comfy.org/built-in-nodes/overview)
[Developers](https://docs.comfy.org/development/overview)
[Custom Nodes](https://docs.comfy.org/custom-nodes/intro)
[Support](https://docs.comfy.org/support/contact-support)
\* [Download](https://comfy.org/download?utm_source=docs)
\* [Comfy Cloud](https://comfy.org/cloud?utm_source=docs)
\* [Comfy Cloud](https://comfy.org/cloud?utm_source=docs)
Search...
Navigation
Flux
ComfyUI Flux.1 Text-to-Image Workflow Example
Search...
Ctrl K

##### Get Started

```
*  [Home](https://docs.comfy.org/)
*  Local (Self-Hosted)
*  [Comfy Cloud](https://docs.comfy.org/get_started/cloud)
*  Install Custom Nodes
*  [First Generation](https://docs.comfy.org/get_started/first_generation)
```

##### Agent Tools

```
*  [Overview](https://docs.comfy.org/agent-tools)
*  [Comfy MCP](https://docs.comfy.org/agent-tools/mcp)
*  [Comfy CLI](https://docs.comfy.org/agent-tools/cli)
*  Comfy Agent
*  [Skills for coding agents](https://docs.comfy.org/agent-tools/skills)
```

##### Basic Concepts

```
*  [ComfyUI Workflows: Nodes, Links, and Visual Programming](https://docs.comfy.org/basic-concepts/workflow)
*  [Nodes](https://docs.comfy.org/basic-concepts/nodes)
*  [Custom Nodes](https://docs.comfy.org/basic-concepts/custom-nodes)
*  [Properties](https://docs.comfy.org/basic-concepts/properties)
*  [ComfyUI Links: How Node Connections Work](https://docs.comfy.org/basic-concepts/links)
*  [Models](https://docs.comfy.org/basic-concepts/models)
*  [Dependencies](https://docs.comfy.org/basic-concepts/dependencies)
```

##### Interface Guide

```
*  [Interface Overview](https://docs.comfy.org/interface/overview)
*  [APP mode](https://docs.comfy.org/interface/app-mode)
*  [Nodes 2.0](https://docs.comfy.org/interface/nodes-2)
*  [Mask Editor](https://docs.comfy.org/interface/maskeditor)
*  [Workflow Templates](https://docs.comfy.org/interface/features/template)
*  [Subgraph](https://docs.comfy.org/interface/features/subgraph)
*  [Partial Execution](https://docs.comfy.org/interface/features/partial-execution)
*  [Node docs](https://docs.comfy.org/interface/features/node-docs)
*  ComfyUI Settings
*  Cloud Exclusive
```

##### Tutorials

```
*  Basic Examples
*  ControlNet
*  Image
    *  Flux
        *  [Flux.2 Dev](https://docs.comfy.org/tutorials/flux/flux-2-dev)
        *  [Flux.2 Klein](https://docs.comfy.org/tutorials/flux/flux-2-klein)
        *  [Flux.1 Krea Dev](https://docs.comfy.org/tutorials/flux/flux1-krea-dev)
        *  [Flux.1 Kontext Dev](https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev)
        *  [Flux.1 Text-to-Image](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image)
        *  [ByteDance USO](https://docs.comfy.org/tutorials/flux/flux-1-uso)
        *  [Flux.1 fill dev](https://docs.comfy.org/tutorials/flux/flux-1-fill-dev)
        *  [Flux.1 ControlNet](https://docs.comfy.org/tutorials/flux/flux-1-controlnet)
    *  Qwen
    *  Z-Image
    *  Boogu
    *  HiDream
    *  Ovis
    *  NewBie-image
    *  ERNIE-Image
    *  Anima
    *  Lens
    *  PixelDiT
    *  Krea 2
    *  Ideogram
    *  Mage-Flow
    *  [Cosmos-Predict2](https://docs.comfy.org/tutorials/image/cosmos/cosmos-predict2-t2i)
    *  [OmniGen2](https://docs.comfy.org/tutorials/image/omnigen/omnigen2)
*  3D
*  LLM
*  Video
*  Audio
*  Utility
```

##### Comfy Cloud Nodes

```
*  [Overview](https://docs.comfy.org/cloud-nodes/overview)
```

##### Partner Nodes

```
*  [Overview](https://docs.comfy.org/tutorials/partner-nodes/overview)
*  [Pricing](https://docs.comfy.org/tutorials/partner-nodes/pricing)
*  [Concurrency Limits](https://docs.comfy.org/tutorials/partner-nodes/concurrency-limits)
*  [FAQs](https://docs.comfy.org/tutorials/partner-nodes/faq)
*  [Data Retention](https://docs.comfy.org/tutorials/partner-nodes/data-retention)
*  [Model Providers](https://docs.comfy.org/tutorials/partner-nodes/model-providers)
*  Partner Models
*  [Changelog](https://docs.comfy.org/changelog)
```

English

#### On this page

```
*  [Flux.1 Full Version Text-to-Image Example](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux-1-full-version-text-to-image-example)
    *  [Flux.1 Dev](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux-1-dev)
    *  [Flux.1 Dev fp8: Text to Image](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux_dev_checkpoint_example)
    *  [1. Workflow File](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#1-workflow-file)
    *  [2. Manual Model Installation](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#2-manual-model-installation)
    *  [3. Steps to Run the Workflow](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#3-steps-to-run-the-workflow)
    *  [Flux.1 Schnell](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux-1-schnell)
    *  [Flux.1 Schnell FP8](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux_schnell)
    *  [1. Workflow File](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#1-workflow-file-2)
    *  [2. Manual Models Installation](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#2-manual-models-installation)
    *  [3. Steps to Run the Workflow](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#3-steps-to-run-the-workflow-2)
*  [Flux.1 FP8 Checkpoint Version Text-to-Image Example](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux-1-fp8-checkpoint-version-text-to-image-example)
    *  [Flux.1 Dev](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux-1-dev-2)
    *  [Flux.1 Dev: Text to Image](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux_dev_full_text_to_image)
    *  [Flux.1 Schnell](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux-1-schnell-2)
    *  [Flux.1 Schnell FP8](https://docs.comfy.org/tutorials/flux/flux-1-text-to-image#flux_schnell-2)
```

Flux

### ComfyUI Flux.1 Text-to-Image Workflow Example

Copy page Copy page
Generate text-to-image with the open-source Flux.1 model in ComfyUI, including full and FP8 checkpoint versions, with step-by-step workflow setup.
Copy page Copy page
Flux is one of the largest open-source text-to-image generation models, with 12B parameters and an original file size of approximately 23GB. It was developed by [Black Forest Labs](https://blackforestlabs.ai/), a team founded by former Stable Diffusion team members. Flux is known for its excellent image quality and flexibility, capable of generating high-quality, diverse images. Currently, the Flux.1 model has several main versions:
\* **Flux.1 Pro:** The best performing model, closed-source, only available through API calls.
\* **Flux.1 [dev]：** Open-source but limited to non-commercial use, distilled from the Pro version, with performance close to the Pro version.
\* **Flux.1 [schnell]：** Uses the Apache2.0 license, requires only 4 steps to generate images, suitable for low-spec hardware.
**Flux.1 Model Features**
\* **Hybrid Architecture:** Combines the advantages of Transformer networks and diffusion models, effectively integrating text and image information, improving the alignment accuracy between generated images and prompts, with excellent fidelity to complex prompts.
\* **Parameter Scale:** Flux has 12B parameters, capturing more complex pattern relationships and generating more realistic, diverse images.
\* **Supports Multiple Styles:** Supports diverse styles, with excellent performance for various types of images.
In this example, we'll introduce text-to-image examples using both Flux.1 Dev and Flux.1 Schnell versions, including the full version model and the simplified FP8 Checkpoint version.
\* **Flux Full Version:** Best performance, but requires larger VRAM resources and installation of multiple model files.
\* **Flux FP8 Checkpoint:** Requires only one fp8 version of the model, but quality is slightly reduced compared to the full version.
All workflow images's Metadata contains the corresponding model download information. You can load the workflows by:
\* Dragging them directly into ComfyUI
\* Or using the menu Workflows -> Open（ctrl+o）
If you're not using the Desktop Version or some models can't be downloaded automatically, please refer to the manual installation sections to save the model files to the corresponding folder. Make sure your ComfyUI is updated to the latest version before starting.

#### Flux.1 Full Version Text-to-Image Example

If you can't download models from [black-forest-labs/FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev), make sure you've logged into Huggingface and agreed to the corresponding repository's license agreement.

##### Flux.1 Dev

##### Flux.1 Dev fp8: Text to Image

Generate images using Flux.1 Dev fp8 quantized version. Suitable for devices with limited VRAM, requires only one model file, but image quality is slightly reduced compared to the full version.
[

#### Run on Comfy Cloud

Run this workflow on Comfy Cloud](https://cloud.comfy.org/?template=flux\_dev\_checkpoint\_example&utm\_source=docs&utm\_medium=referral&utm\_campaign=flux-1-text-to-image)
[

#### Download Workflow

Download JSON or search “Flux.1 Dev fp8” in Template Library](https://github.com/Comfy-Org/workflow\_templates/blob/main/templates/flux\_dev\_checkpoint\_example.json)
**Example output**

###### 1. Workflow File

###### 2. Manual Model Installation

```
*  The flux1-dev.safetensors file requires agreeing to the [black-forest-labs/FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev) agreement before downloading via browser.
*  If your VRAM is low, you can try using [t5xxl_fp8_e4m3fn.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors?download=true) to replace the t5xxl_fp16.safetensors file.
```

Please download the following model files:
\* [clip\_l.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/clip_l.safetensors?download=true)
\* [t5xxl\_fp16.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp16.safetensors?download=true) Recommended when your VRAM is greater than 32GB.
\* [ae.safetensors](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/ae.safetensors?download=true)
\* [flux1-dev.safetensors](https://huggingface.co/black-forest-labs/FLUX.1-dev/blob/main/flux1-dev.safetensors)
Storage location:

```
ComfyUI/
├── models/
│   ├── text_encoders/
│   │   ├── clip_l.safetensors
│   │   └── t5xxl_fp16.safetensors
│   ├── vae/
│   │   └── ae.safetensors
│   └── diffusion_models/
│       └── flux1-dev.safetensors
```

###### 3. Steps to Run the Workflow

Please refer to the image below to ensure all model files are loaded correctly
1. Ensure the DualCLIPLoader node has the following models loaded:
\* clip\_name1: t5xxl\_fp16.safetensors
\* clip\_name2: clip\_l.safetensors
1. Ensure the Load Diffusion Model node has flux1-dev.safetensors loaded
1. Make sure the Load VAE node has ae.safetensors loaded
1. Click the Queue button, or use the shortcut Ctrl(cmd) + Enter to run the workflow
Thanks to Flux's excellent prompt following capability, we don't need any negative prompts

##### Flux.1 Schnell

##### Flux.1 Schnell FP8

Quickly generate images with Flux.1 Schnell fp8 quantized version. Ideal for low-end hardware, requires only 4 steps to generate images.
[

#### Run on Comfy Cloud

Run this workflow on Comfy Cloud](https://cloud.comfy.org/?template=flux\_schnell&utm\_source=docs&utm\_medium=referral&utm\_campaign=flux-1-text-to-image)
[

#### Download Workflow

Download JSON or search “Flux.1 Schnell” in Template Library](https://github.com/Comfy-Org/workflow\_templates/blob/main/templates/flux\_schnell\_full\_text\_to\_image.json)

###### 1. Workflow File

###### 2. Manual Models Installation

In this workflow, only two model files are different from the Flux1 Dev version workflow. For t5xxl, you can still use the fp16 version for better results.
\* **t5xxl\_fp16.safetensors** -> **t5xxl\_fp8.safetensors**
\* **flux1-dev.safetensors** -> **flux1-schnell.safetensors**
Complete model file list:
\* [clip\_l.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/clip_l.safetensors?download=true)
\* [t5xxl\_fp8\_e4m3fn.safetensors](https://huggingface.co/comfyanonymous/flux_text_encoders/blob/main/t5xxl_fp8_e4m3fn.safetensors?download=true)
\* [ae.safetensors](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/ae.safetensors?download=true)
\* [flux1-schnell.safetensors](https://huggingface.co/black-forest-labs/FLUX.1-schnell/blob/main/flux1-schnell.safetensors)
File storage location:

```
ComfyUI/
├── models/
│   ├── text_encoders/
│   │   ├── clip_l.safetensors
│   │   └── t5xxl_fp8_e4m3fn.safetensors
│   ├── vae/
│   │   └── ae.safetensors
│   └── diffusion_models/
│       └── flux1-schnell.safetensors
```

###### 3. Steps to Run the Workflow

```
1. Ensure the DualCLIPLoader node has the following models loaded:
*  clip_name1: t5xxl_fp8_e4m3fn.safetensors
    *  clip_name2: clip_l.safetensors
1. Ensure the Load Diffusion Model node has flux1-schnell.safetensors loaded
1. Ensure the Load VAE node has ae.safetensors loaded
1. Click the Queue button, or use the shortcut Ctrl(cmd) + Enter to run the workflow
```

#### Flux.1 FP8 Checkpoint Version Text-to-Image Example

The fp8 version is a quantized version of the original Flux.1 fp16 version. To some extent, the quality of this version will be lower than that of the fp16 version, but it also requires less VRAM, and you only need to install one model file to try running it.

##### Flux.1 Dev

##### Flux.1 Dev: Text to Image

Generate high-quality images with Flux Dev full version. Requires larger VRAM and multiple model files, but provides the best prompt following capability.
[

#### Run on Comfy Cloud

Run this workflow on Comfy Cloud](https://cloud.comfy.org/?template=flux\_dev\_full\_text\_to\_image&utm\_source=docs&utm\_medium=referral&utm\_campaign=flux-1-text-to-image)
[

#### Download Workflow

Download JSON or search “Flux.1 Dev FP8” in Template Library](https://github.com/Comfy-Org/workflow\_templates/blob/main/templates/flux\_dev\_full\_text\_to\_image.json)
**Example output**
Please download the image below and drag it into ComfyUI to load the workflow. Please download [flux1-dev-fp8.safetensors](https://huggingface.co/Comfy-Org/flux1-dev/blob/main/flux1-dev-fp8.safetensors?download=true) and save it to the ComfyUI/models/checkpoints/ directory. Ensure that the corresponding Load Checkpoint node loads flux1-dev-fp8.safetensors , and you can try to run the workflow.

##### Flux.1 Schnell

##### Flux.1 Schnell FP8

Quickly generate images with Flux.1 Schnell fp8 quantized version. Ideal for low-end hardware, requires only 4 steps to generate images.
[

#### Run on Comfy Cloud

Run this workflow on Comfy Cloud](https://cloud.comfy.org/?template=flux\_schnell&utm\_source=docs&utm\_medium=referral&utm\_campaign=flux-1-text-to-image)
[

#### Download Workflow

Download JSON or search “Flux.1 Schnell FP8” in Template Library](https://github.com/Comfy-Org/workflow\_templates/blob/main/templates/flux\_schnell.json)
Please download the image below and drag it into ComfyUI to load the workflow. Please download [flux1-schnell-fp8.safetensors](https://huggingface.co/Comfy-Org/flux1-schnell/blob/main/flux1-schnell-fp8.safetensors?download=true) and save it to the ComfyUI/models/checkpoints/ directory. Ensure that the corresponding Load Checkpoint node loads flux1-schnell-fp8.safetensors , and you can try to run the workflow.
💬
💬 Click or scroll here to load comments
Was this page helpful?
Yes No
[Suggest edits](https://github.com/comfy-org/docs/edit/main/tutorials/flux/flux-1-text-to-image.mdx) [Raise issue](https://github.com/comfy-org/docs/issues/new?title=Issue on docs&body=Path: /tutorials/flux/flux-1-text-to-image)
[ComfyUI Flux Kontext Dev Native Workflow Example Previous](https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev)
[ByteDance USO ComfyUI Native Workflow example Next](https://docs.comfy.org/tutorials/flux/flux-1-uso)
Ctrl+I
[ComfyUI home pagelight logodark logo](https://docs.comfy.org/)
[github](https://github.com/Comfy-Org/ComfyUI) [x](https://x.com/ComfyUI) [discord](https://discord.com/invite/comfyorg) [youtube](https://www.youtube.com/@comfyorg)
Resources
[installation](https://docs.comfy.org/installation/system_requirements) [Tutorials](https://docs.comfy.org/tutorials/basic/text-to-image) [Development](https://docs.comfy.org/development/overview)
Products
[Features](https://www.comfy.org/?utm_source=docs) [Gallery](https://www.comfy.org/gallery?utm_source=docs) [Download](https://www.comfy.org/download?utm_source=docs)
Company
[About](https://www.comfy.org/about?utm_source=docs) [Careers](https://www.comfy.org/careers?utm_source=docs) [Terms of Service](https://www.comfy.org/terms-of-service?utm_source=docs) [Privacy Policy](https://www.comfy.org/privacy-policy?utm_source=docs)
[github](https://github.com/Comfy-Org/ComfyUI) [x](https://x.com/ComfyUI) [discord](https://discord.com/invite/comfyorg) [youtube](https://www.youtube.com/@comfyorg)
[Powered by This documentation is built and hosted on Mintlify, a developer documentation platform](https://www.mintlify.com?utm_campaign=poweredBy&utm_medium=referral&utm_source=dripart)
x