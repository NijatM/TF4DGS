# Gaussian splat repair research

Reviewed 2026-10-12 for Temporal Fields 4D Gaussian Splatting (TF4DGS).
Primary sources: author project pages, papers, official repositories and model
cards. Code availability means a public release was found, not that TF4DGS
compatibility or output quality has been tested. This is research only; the
rejected full-duration training attempt remains ended.

## Likely NVIDIA presentation matches

- **Difix3D+ (CVPR 2025)**: a single-step diffusion enhancer, progressive
  refinement of an existing representation, and an additional rendering-time
  enhancer. Public code and weights. Its gsplat example consumes a training
  checkpoint and calibrated images; it is not a universal PLY repair command.
  [Project](https://research.nvidia.com/labs/toronto-ai/difix3d/),
  [code](https://github.com/nv-tlabs/Difix3D),
  [paper, arXiv:2503.01774](https://arxiv.org/abs/2503.01774).
- **NuRec Fixer / Harmonizer**: NVIDIA currently labels the enhancement link
  Harmonizer on its NuRec page, but that link leads to the model card named
  Fixer. The card describes Cosmos-Predict-0.6B, offline 3D distillation and
  online image enhancement, with 1024x576 input/output and Linux support.
  This is a strong match if the presentation showed driving simulation.
  [NuRec](https://developer.nvidia.com/omniverse/nurec),
  [model](https://huggingface.co/nvidia/Fixer),
  [NVIDIA demonstration](https://developer.nvidia.com/blog/accelerating-av-simulation-with-neural-reconstruction-and-world-foundation-models/).
- **ArtiFixer (SIGGRAPH 2026)**: autoregressive repair/extension of long
  camera trajectories. ArtiFixer outputs images; ArtiFixer3D distills generated
  views into 3DGRUT; ArtiFixer3D+ adds image enhancement afterward. Public
  source and checkpoints. Likely match if the talk showed long orbit videos
  and completion of largely unobserved areas.
  [Project](https://research.nvidia.com/labs/sil/projects/artifixer/),
  [code](https://github.com/nv-tlabs/ArtiFixer),
  [weights](https://huggingface.co/nvidia/ArtiFixer).
- **Kaolin / ArtisanGS**: strongest match if the speaker explicitly called
  it a library and demonstrated a browser editor. NVIDIA's SIGGRAPH 2026
  documentation links a public prerelease branch with splat segmentation
  and a toy inpainter that bakes 2D diffusion edits into the 3D scene.
  [Conference documentation](https://kaolin.readthedocs.io/en/latest/notes/siggraph2026.html),
  [apps](https://github.com/NVIDIAGameWorks/kaolin/tree/web_framework_prerelease/kaolin/app),
  [ArtisanGS paper/project](https://research.nvidia.com/labs/sil/projects/ArtisanGS/).

These are candidates; the exact presentation has not been identified.

## Existing Gaussian cleanup and direct refinement

| Method | What it changes | Availability and boundary |
| --- | --- | --- |
| [PointNuker](https://github.com/Dymensium/PointNuker) | Deletes isolated clusters/outliers using DBSCAN, radius/statistical filters and cropping. | Public Python GUI, MIT. GS-safe export preserves attributes. Cannot fill holes. A largest-cluster rule can delete valid detached room objects. |
| [Clean-GS](https://github.com/smlab-niser/clean-gs) / [paper](https://arxiv.org/abs/2601.00913) | Prunes trained PLY using sparse masks, depth-buffered color checks and neighbor filtering. | Public MIT implementation, 2026 preprint. Designed to isolate targets; keeping a complete room requires adapting mask policy. |
| [SplatFormer](https://sergeyprokudin.github.io/splatformer/) / [code](https://github.com/ChenYutongTHU/SplatFormer) | Predicts residual changes directly to Gaussian attributes in a feed-forward point transformer. | ICLR 2025; code/checkpoints. Trained on object datasets; not demonstrated as a universal whole-room or 4D repair model. |
| [ArtisanGS](https://research.nvidia.com/labs/sil/projects/ArtisanGS/) | User-correctable AI/manual selection and localized editing. | 2026 research; Kaolin prerelease apps. Helps target unwanted regions; selection alone does not recover lost geometry. |

## Repairing rendered views and refining the representation

| Method | Repair strategy | Release status |
| --- | --- | --- |
| [Difix3D+](https://github.com/nv-tlabs/Difix3D) | Correct novel-view images, refine the 3D representation with them, optionally enhance final renders. | CVPR 2025; code and models, NVIDIA terms. Static reconstruction adapters. |
| [NuRec Fixer](https://huggingface.co/nvidia/Fixer) | Cosmos image repair; offline distillation or online enhancement. | Released model, NVIDIA Open Model License. AV training domain; textile transfer is untested. |
| [ArtiFixer](https://github.com/nv-tlabs/ArtiFixer) | Reference-, opacity- and camera-conditioned video repair, followed optionally by 3DGRUT reconstruction. | SIGGRAPH 2026; Apache-2.0 source, separately governed NVIDIA weights. Static scene pipeline. |
| [GSFix3D](https://gsfix3d.github.io/) / [code](https://github.com/GSFix3D/GSFix3D) | Scene-adapted diffusion repairs novel views and holes, then optimizes Gaussian data from the repaired images. Optional mesh conditioning. | 3DV 2026; code and pretrained models. Dataset-format adaptation needed; noncommercial reconstruction component. |
| [GSFixer, Yin et al.](https://github.com/GVCLab/GSFixer) | Video restoration guided by original-image VGGT geometry and DINOv2 semantics, then 3D optimization. | ICML 2026; code/models. CogVideoX-5B workflow tested on H20/H100. Different project from GSFix3D's internal model also named GSFixer. |
| [RI3D](https://people.engr.tamu.edu/nimak/Papers/RI3D/index.html) / [code](https://github.com/avinashpaliwal/RI3D) | Separate repair and inpainting priors; optimize observed regions, then missing regions. | ICCV 2025; released implementation. Ubuntu/2080 Ti test configuration makes it worth considering for a bounded local static test. |
| [3DGS-Enhancer](https://github.com/xiliu8006/3DGS-Enhancer) | Video diffusion provides consistent novel views for Gaussian refinement. | NeurIPS 2024. Partial release: README still lists spatial-temporal decoder and confidence-aware 3DGS as unavailable. |
| [GenFusion](https://github.com/Inception3D/GenFusion) | Cyclic reconstruction and generation conditioned on degraded RGB-D renders. | CVPR 2025; official code. Reconstruction uses a surfel rasterizer; not a direct replacement for our 4C4D decoder. |

For these methods, a good-looking enhanced PNG/video does not establish that
the exported PLY improved. Inspect the raw Gaussian rendering after the
distillation/reconstruction stage, with image enhancement disabled.

## Missing-region completion

| Method | Focus | Availability and limitations |
| --- | --- | --- |
| [GSComplete](https://arxiv.org/abs/2609.08449) | Preserve original splats and add new splats to incomplete objects using diffusion guidance and a preservation loss. | September 2026 preprint; paper says code/data upon acceptance. Static objects; completed regions are plausible rather than measured. |
| [Fillerbuster](https://ethanweber.me/fillerbuster/) / [code](https://github.com/facebookresearch/fillerbuster) | Multi-view scene completion, including masked regions and casual captures. | 2025 research; inference/training code and weights, primarily CC BY-NC. Reconstructs using generated supervision rather than simply filtering a PLY. |
| [3DGIC](https://github.com/peterjohnsonhuang/3dgic) | Depth-guided cross-view inpainting, especially holes after object removal. | CVPR 2025. Author explicitly describes public release as a suboptimal version; full implementation belongs to sponsor. |
| [SplatFill](https://mahtaabdn.github.io/SplatFill/) | Depth-guided, selective correction of inconsistent masked regions. | ICPR 2026; project lists code TBD. Relevant research, not a verified installable tool. |
| [GaussFiller](https://yhpffy.github.io/GaussFiller/) / [paper](https://openaccess.thecvf.com/content/CVPR2026F/papers/Ping_GaussFiller_Unleashing_VLM-Expert_Guidance_for_3D_Scene_Completion_with_3D_CVPRF_2026_paper.pdf) | VLM-guided choice of completion viewpoints and inpainted candidates from sparse RGB-D captures. | CVPR Findings 2026. Public implementation not verified in this review. Intended for plausible scene completion. |

## Preventing or correcting floaters during optimization

- [StableGS: A Floater-Free Framework](https://arxiv.org/abs/2503.18458):
  dual-opacity paths separate geometry regularization and appearance, with
  depth consistency and external priors. This is a training change, not a
  post-export filter. [Author organization code](https://github.com/MooreThreads/StableGS)
  is sparsely documented; current issues report missing modules. Do not confuse
  it with another repository named StableGS about geometric probing.
- [TIDI-GS](https://arxiv.org/abs/2601.09291): multi-view evidence, learned
  importance, isolation checks and detail guards drive periodic pruning with
  depth guidance. 2026 preprint, reportedly tested on a 16 GB RTX 4080.
  Public author implementation not located. Training statistics are needed;
  cannot reproduce the full method from a bare PLY.

## Dynamic repair most relevant to TF4DGS

**[4DGS-Fixer, arXiv:2609.21176](https://arxiv.org/abs/2609.21176)**
is a September 18, 2026 preprint specifically for four fixed cameras. It fuses
MVSAnywhere depths for initialization, restores novel camera paths at selected
times using a reference-guided video model, caches pseudo-targets, then refines
the dynamic field. Its Neural3DV table reports PSNR 24.18 versus 22.29 for
4C4D, a 1.89 dB gain; those are author-reported benchmark results, not our data.
Public code was not located. It uses STGS rather than our exact 4C4D adapter.
Our three heterogeneous cameras and thin textile are an untested transfer case.

[Splat4D](https://visual-ai.github.io/splat4d/) is related generative work on
monocular video with uncertainty masking and video-guided refinement. It is
not an established postprocessor for an arbitrary continuous 4C4D checkpoint.

Video-based consistency in static-scene repair means consistency across camera
views. It does not automatically enforce the physical-time consistency of
cloth deformation. Independently repairing each timestamp can alter patterns,
create flicker or erase legitimate hands and motion.

## Hardware and project recommendation

Recorded local hardware: NVIDIA RTX A4000, approximately 16 GB VRAM, Windows.
No tools in this review were installed or benchmarked locally.

1. Start an eventual static repair comparison with **PointNuker / carefully
   adapted Clean-GS**, **Difix3D reference-guided repair**, and **RI3D or
   GSFix3D**. These test cleanup versus learned repair on a small scene.
   This is a feasibility shortlist, not a promise that every model fits.
2. Treat **ArtiFixer** as a leading recent visual-repair candidate, but not a
   ready local installation: official instructions use Linux containers and
   large-memory test GPUs. The 1.3B variant is lighter, but README's comfortable
   all-workflows example is an 80 GB GPU. No verified 16 GB configuration was
   found. GSFixer's H20/H100 workflow also needs a memory audit first.
3. For dynamic reconstruction, study **4DGS-Fixer** before adapting static
   repair across time. Audit calibration, synchronization, initialization and
   the long-duration adapter independently. The failed cloth result does not
   establish which of these was the cause.
4. Preserve an evidence-based reconstruction for deformation/color analysis.
   Label any generatively completed geometry or changed colors separately.
   Missing surfaces cannot be verified as measured merely because they look
   plausible. Deleting a true yarn, hand or suspension cable is also a failure.

An eventual comparison should keep the same input images, camera poses, action
interval and orbit; render before/after with enhancement disabled; inspect
silhouettes, pattern retention, hands, novel-view depth and temporal flicker;
and validate scale/displacement against known measurements. Do not select
methods by a visually enhanced demo alone. The original failed experiment
remains stopped until the user chooses a new experiment.
