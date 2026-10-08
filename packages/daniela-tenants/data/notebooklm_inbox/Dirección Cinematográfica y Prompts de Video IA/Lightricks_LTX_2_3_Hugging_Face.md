Lightricks/LTX-2.3 · Hugging Face
[Hugging Face's logo Hugging Face](https://huggingface.co/)
\* [Models](https://huggingface.co/models)
\* [Datasets](https://huggingface.co/datasets)
\* [Spaces](https://huggingface.co/spaces)
\* [Buckets new](https://huggingface.co/storage)
\* [Docs](https://huggingface.co/docs)
\* [Enterprise](https://huggingface.co/enterprise)
\* [Pricing](https://huggingface.co/pricing)
\* Website
\* [Tasks](https://huggingface.co/tasks)
\* [HuggingChat](https://huggingface.co/chat)
\* [Collections](https://huggingface.co/collections)
\* [Languages](https://huggingface.co/languages)
\* [Organizations](https://huggingface.co/organizations)
\* Community
\* [Blog](https://huggingface.co/blog)
\* [Posts](https://huggingface.co/posts)
\* [Daily Papers](https://huggingface.co/papers)
\* [Hardware](https://huggingface.co/hardware)
\* [Learn](https://huggingface.co/learn)
\* [Discord](https://huggingface.co/join/discord)
\* [Forum](https://discuss.huggingface.co/)
\* [GitHub](https://github.com/huggingface)
\* Solutions
\* [Team & Enterprise](https://huggingface.co/enterprise)
\* [Hugging Face PRO](https://huggingface.co/pro)
\* [Enterprise Support](https://huggingface.co/support)
\* [Inference Providers](https://huggingface.co/inference/models)
\* [Inference Endpoints](https://huggingface.co/inference-endpoints)
\* [Storage Buckets](https://huggingface.co/storage)
\* [Log In](https://huggingface.co/login)
\* [Sign Up](https://huggingface.co/join)

### [Lightricks](https://huggingface.co/Lightricks) / [LTX-2.3](https://huggingface.co/Lightricks/LTX-2.3) Like 1.92k Follow

LTX.io 5.57k
[Image-to-Video](https://huggingface.co/models?pipeline_tag=image-to-video)
[Diffusers](https://huggingface.co/models?library=diffusers)
[LTX-2](https://huggingface.co/models?library=ltx)
9 languages
[text-to-video](https://huggingface.co/models?other=text-to-video)
[video-to-video](https://huggingface.co/models?other=video-to-video)
[image-text-to-video](https://huggingface.co/models?other=image-text-to-video)
[audio-to-video](https://huggingface.co/models?other=audio-to-video)
[text-to-audio](https://huggingface.co/models?other=text-to-audio)
[video-to-audio](https://huggingface.co/models?other=video-to-audio)
[audio-to-audio](https://huggingface.co/models?other=audio-to-audio)
[text-to-audio-video](https://huggingface.co/models?other=text-to-audio-video)
[image-to-audio-video](https://huggingface.co/models?other=image-to-audio-video)
[image-text-to-audio-video](https://huggingface.co/models?other=image-text-to-audio-video)
[ltx-2](https://huggingface.co/models?other=ltx-2)
[ltx-video](https://huggingface.co/models?other=ltx-video)
[ltxv](https://huggingface.co/models?other=ltxv)
[lightricks](https://huggingface.co/models?other=lightricks)
[ltx-2.3](https://huggingface.co/models?other=ltx-2.3)
[Eval Results](https://huggingface.co/models?other=eval-results)
arxiv: 2601.03233
License: ltx-2-community-license-agreement
[Model card](https://huggingface.co/Lightricks/LTX-2.3) [Files Files and versions xet](https://huggingface.co/Lightricks/LTX-2.3/tree/main)
[Community 65](https://huggingface.co/Lightricks/LTX-2.3/discussions)
Deploy
Copy to bucket new
Use this model

##### Instructions to use Lightricks/LTX-2.3 with libraries, inference providers, notebooks, and local apps. Follow these links to get started.

```
*  Libraries
*  [Diffusers](https://huggingface.co/Lightricks/LTX-2.3?library=diffusers) How to use Lightricks/LTX-2.3 with Diffusers:
```

```
pip install -U diffusers transformers accelerate
```

```
import torch
from diffusers import DiffusionPipeline
from diffusers.utils import load_image, export_to_video

# switch to "mps" for apple devices
pipe = DiffusionPipeline.from_pretrained("Lightricks/LTX-2.3", dtype=torch.bfloat16, device_map="cuda")
pipe.to("cuda")

prompt = "A man with short gray hair plays a red electric guitar."
image = load_image(
    "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/diffusers/guitar-man.png"
)

output = pipe(image=image, prompt=prompt).frames[0]
export_to_video(output, "output.mp4")
```

```
*  [LTX-2](https://huggingface.co/Lightricks/LTX-2.3?library=ltx) How to use Lightricks/LTX-2.3 with LTX-2:
```

```
# Install the LTX-2 pipelines
git clone https://github.com/Lightricks/LTX-2.git
cd LTX-2
uv sync --frozen
```

```
# Download the weights from this repo, plus the Gemma text encoder
hf download Lightricks/LTX-2.3 --local-dir models/LTX-2.3
hf download google/gemma-3-12b-it-qat-q4_0-unquantized --local-dir models/gemma-3-12b
```

```
# Fast pipeline (distilled model, no distilled LoRA needed)
uv run python -m ltx_pipelines.distilled \
    --distilled-checkpoint-path models/LTX-2.3/<distilled-checkpoint>.safetensors \
    --spatial-upsampler-path models/LTX-2.3/<spatial-upsampler>.safetensors \
    --gemma-root models/gemma-3-12b \
    --prompt "A beautiful sunset over the ocean" \
    --output-path output.mp4
# For image-to-video, add: --image path/to/image.jpg 0 0.8
```

```
# HQ pipeline (two-stage, higher quality)
uv run python -m ltx_pipelines.ti2vid_two_stages_hq \
    --checkpoint-path models/LTX-2.3/<checkpoint>.safetensors \
    --distilled-lora models/LTX-2.3/<distilled-lora>.safetensors 0.8 \
    --spatial-upsampler-path models/LTX-2.3/<spatial-upsampler>.safetensors \
    --gemma-root models/gemma-3-12b \
    --prompt "A beautiful sunset over the ocean" \
    --output-path output.mp4
# For image-to-video, add: --image path/to/image.jpg 0 0.8
```

```
*  Notebooks
*  [Google Colab](https://huggingface.co/Lightricks/LTX-2.3/colab)
*  [Kaggle](https://huggingface.co/Lightricks/LTX-2.3/kaggle)
*  [LTX-2.3 Model Card](https://huggingface.co/Lightricks/LTX-2.3#ltx-23-model-card)
*  [Model Checkpoints](https://huggingface.co/Lightricks/LTX-2.3#model-checkpoints)
    *  [Model Details](https://huggingface.co/Lightricks/LTX-2.3#model-details)
*  [Online demo](https://huggingface.co/Lightricks/LTX-2.3#online-demo)
*  [Run locally](https://huggingface.co/Lightricks/LTX-2.3#run-locally)
    *  [Direct use license](https://huggingface.co/Lightricks/LTX-2.3#direct-use-license)
    *  [ComfyUI](https://huggingface.co/Lightricks/LTX-2.3#comfyui)
    *  [PyTorch codebase](https://huggingface.co/Lightricks/LTX-2.3#pytorch-codebase)
        *  [Installation](https://huggingface.co/Lightricks/LTX-2.3#installation)
        *  [Inference](https://huggingface.co/Lightricks/LTX-2.3#inference)
    *  [Diffusers 🧨](https://huggingface.co/Lightricks/LTX-2.3#diffusers-%F0%9F%A7%A8)
    *  [General tips:](https://huggingface.co/Lightricks/LTX-2.3#general-tips)
        *  [Limitations](https://huggingface.co/Lightricks/LTX-2.3#limitations)
*  [Train the model](https://huggingface.co/Lightricks/LTX-2.3#train-the-model)
    *  [Citation](https://huggingface.co/Lightricks/LTX-2.3#citation)
```

### LTX-2.3 Model Card

This model card focuses on the LTX-2.3 model, which is a significant update to the [LTX-2 model](https://huggingface.co/Lightricks/LTX-2) with improved audio and visual quality as well as enhanced prompt adherence. LTX-2 was presented in the paper [LTX-2: Efficient Joint Audio-Visual Foundation Model](https://huggingface.co/papers/2601.03233).
💻💻 **If you want to dive in right to the code - it is available here.** 💾💾
LTX-2.3 is a DiT-based audio-video foundation model designed to generate synchronized video and audio within a single model. It brings together the core building blocks of modern video generation, with open weights and a focus on practical, local execution.

### Model Checkpoints

| Name | Notes |
| --- | --- |
| ltx-2.3-22b-dev | The full model, flexible and trainable in bf16 |
| ltx-2.3-22b-distilled | The distilled version of the full model, 8 steps, CFG=1 |
| ltx-2.3-22b-distilled-1.1 | The distilled v1.1 version of the full model, 8 steps, CFG=1 - A different aesthetic experience and improved audio compared to v1.0 |
| ltx-2.3-22b-distilled-lora-384 | A LoRA version of the distilled model applicable to the full model |
| ltx-2.3-22b-distilled-lora-384-1.1 | A LoRA version of the v1.1 distilled model applicable to the full model |
| ltx-2.3-spatial-upscaler-x2-1.1 | An x2 spatial upscaler for the ltx-2.3 latents, used in multi stage (multiscale) pipelines for higher resolution |
| ltx-2.3-spatial-upscaler-x1.5-1.0 | An x1.5 spatial upscaler for the ltx-2.3 latents, used in multi stage (multiscale) pipelines for higher resolution |
| ltx-2.3-temporal-upscaler-x2-1.0 | An x2 temporal upscaler for the ltx-2.3 latents, used in multi stage (multiscale) pipelines for higher FPS |

#### Model Details

```
*   **Developed by:**  Lightricks
*   **Model type:**  Diffusion-based audio-video foundation model
*   **Language(s):**  English
```

### Online demo

LTX-2.3 is accessible right away via the [API Playground](https://console.ltx.video/playground/).

### Run locally

#### Direct use license

You can use the models - full, distilled, upscalers and any derivatives of the models - for purposes under the [license](https://github.com/Lightricks/LTX-2/blob/main/LICENSE).

#### ComfyUI

We recommend you use the built-in LTXVideo nodes that can be found in the ComfyUI Manager. For manual installation information, please refer to our [documentation site](https://docs.ltx.video/open-source-model/integration-tools/comfy-ui).

#### PyTorch codebase

The [LTX-2 codebase](https://github.com/Lightricks/LTX-2) is a monorepo with several packages. From model definition in 'ltx-core' to pipelines in 'ltx-pipelines' and training capabilities in 'ltx-trainer'. The codebase was tested with Python >=3.12, CUDA version >12.7, and supports PyTorch ~= 2.7.

##### Installation

```
git clone https://github.com/Lightricks/LTX-2.git
cd LTX-2

# From the repository root
uv sync
source .venv/bin/activate
```

##### Inference

To use our model, please follow the instructions in our [ltx-pipelines](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-pipelines/README.md) package.

#### Diffusers 🧨

LTX-2.3 support in the [Diffusers Python library](https://huggingface.co/docs/diffusers/main/en/index) is coming soon!

#### General tips:

```
*  Width & height settings must be divisible by 32. Frame count must be divisible by 8 + 1.
*  In case the resolution or number of frames are not divisible by 32 or 8 + 1, the input should be padded with -1 and then cropped to the desired resolution and number of frames.
*  For tips on writing effective prompts, please visit our [Prompting guide](https://ltx.video/blog/how-to-prompt-for-ltx-2)
```

##### Limitations

```
*  This model is not intended or able to provide factual information.
*  As a statistical model this checkpoint might amplify existing societal biases.
*  The model may fail to generate videos that matches the prompts perfectly.
*  Prompt following is heavily influenced by the prompting-style.
*  The model may generate content that is inappropriate or offensive.
*  When generating audio without speech, the audio may be of lower quality.
```

### Train the model

The base (dev) model is fully trainable.
It's extremely easy to reproduce the LoRAs and IC-LoRAs we publish with the model by following the instructions on the [LTX-2 Trainer Readme](https://github.com/Lightricks/LTX-2/blob/main/packages/ltx-trainer/README.md).
Training for motion, style or likeness (sound+appearance) can take less than an hour in many settings.

#### Citation

```
@article{hacohen2025ltx2,
  title={LTX-2: Efficient Joint Audio-Visual Foundation Model},
  author={HaCohen, Yoav and Brazowski, Benny and Chiprut, Nisan and Bitterman, Yaki and Kvochko, Andrew and Berkowitz, Avishai and Shalem, Daniel and Lifschitz, Daphna and Moshe, Dudu and Porat, Eitan and Richardson, Eitan and Guy Shiran and Itay Chachy and Jonathan Chetboun and Michael Finkelson and Michael Kupchick and Nir Zabari and Nitzan Guetta and Noa Kotler and Ofir Bibi and Ori Gordon and Poriya Panet and Roi Benita and Shahar Armon and Victor Kulikov and Yaron Inger and Yonatan Shiftan and Zeev Melumian and Zeev Farbman},
  journal={arXiv preprint arXiv:2601.03233},
  year={2025}
}
```

Downloads last month
1,076,038
Inference Providers [NEW](https://huggingface.co/docs/inference-providers)
[Image-to-Video](https://huggingface.co/tasks/image-to-video)
This model isn't deployed by any Inference Provider. [🙋 41 Ask for provider support](https://huggingface.co/spaces/huggingface/InferenceSupport/discussions/8436)

#### Model tree for Lightricks/LTX-2.3

Adapters
[116 models](https://huggingface.co/models?other=base_model:adapter:Lightricks/LTX-2.3)
Finetunes
[122 models](https://huggingface.co/models?other=base_model:finetune:Lightricks/LTX-2.3)
Merges
[3 models](https://huggingface.co/models?other=base_model:merge:Lightricks/LTX-2.3)
Quantizations
[72 models](https://huggingface.co/models?other=base_model:quantized:Lightricks/LTX-2.3)

#### Spaces using Lightricks/LTX-2.3 100

[Lightricks/ltx-2-3-22b-ic-lora-clean-plate](https://huggingface.co/spaces/Lightricks/ltx-2-3-22b-ic-lora-clean-plate)
[Lightricks/ltx2-relight-lora-demo](https://huggingface.co/spaces/Lightricks/ltx2-relight-lora-demo)
[Lightricks/LTX-2-3](https://huggingface.co/spaces/Lightricks/LTX-2-3)
[Lightricks/ltx-2-3-spatial-upscaler](https://huggingface.co/spaces/Lightricks/ltx-2-3-spatial-upscaler)
[Lightricks/LTX-2-3-hdr](https://huggingface.co/spaces/Lightricks/LTX-2-3-hdr)
[🟩 embedl/hfviewer](https://huggingface.co/spaces/embedl/hfviewer)
[🎬 techfreakworm/LTX2.3-Studio](https://huggingface.co/spaces/techfreakworm/LTX2.3-Studio)
[🕺 linoyts/LTX-2-3-sync](https://huggingface.co/spaces/linoyts/LTX-2-3-sync)
\* 95 Spaces + 92 Spaces

#### Collection including Lightricks/LTX-2.3

[

###### LTX-2.3

Collection LTX-2.3 base models, quantized models and accompanying LoRAs and IC-LoRAs • 10 items • Updated 22 days ago • 72](https://huggingface.co/collections/Lightricks/ltx-23)

#### Paper for Lightricks/LTX-2.3

[

###### LTX-2: Efficient Joint Audio-Visual Foundation Model

Paper • 2601.03233 • Published Jan 6 • 197](https://huggingface.co/papers/2601.03233)

#### Evaluation results

```
*  [meituan-longcat/WBench](https://huggingface.co/datasets/meituan-longcat/WBench) [leaderboard](https://huggingface.co/datasets/meituan-longcat/WBench?eval_result=Lightricks/LTX-2.3)
*  Wbench Navi [View evaluation results](https://huggingface.co/Lightricks/LTX-2.3/discussions/56) [source](https://meituan-longcat.github.io/WBench/) 74.4
*  Wbench Full [View evaluation results](https://huggingface.co/Lightricks/LTX-2.3/discussions/56) [source](https://meituan-longcat.github.io/WBench/) [](https://huggingface.co/datasets/meituan-longcat/WBench?eval_result=Lightricks%2FLTX-2.3&leaderboard_task_id=wbench_full) 70.9
```

System theme
Company
[TOS](https://huggingface.co/terms-of-service) [Privacy](https://huggingface.co/privacy) [About](https://huggingface.co/huggingface) [Careers](https://apply.workable.com/huggingface/) 
Website
[Models](https://huggingface.co/models) [Datasets](https://huggingface.co/datasets) [Spaces](https://huggingface.co/spaces) [Pricing](https://huggingface.co/pricing) [Docs](https://huggingface.co/docs)
Inference providers allow you to run inference using different serverless providers.
View evaluation results shared by the community
Source: WBench Leaderboard
View evaluation results shared by the community
Source: WBench Leaderboard
Ranked #2 overall