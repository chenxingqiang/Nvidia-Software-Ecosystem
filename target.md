# NVIDIA Software & Hardware Ecosystem — Complete System Specification

## Objective

Build a complete system to **crawl, classify, extract, and generate** comprehensive reports on NVIDIA's software and hardware ecosystem layout. The output must include specific introductions and clear attribution (which software/hardware belongs to which category/ecosystem).

## Source

- Primary: `https://www.nvidia.com/en-us/` (English)
- Secondary: `https://www.nvidia.com/zh-cn/`, `https://www.nvidia.cn/` (Chinese locales)
- All sub-pages reachable via internal links within the allowed domain scope.

## 5 Target Ecosystems

Every crawled page must be classified into one of the following ecosystems:

| # | Ecosystem | Scope |
|---|-----------|-------|
| 1 | **Data Center & AI** | DGX, HGX, Grace Hopper, networking (Spectrum/Quantum/ConnectX), NVIDIA AI Enterprise, Base Command, DGX Cloud |
| 2 | **Professional Visualization** | RTX workstations, Omniverse, Quadro/RTX professional GPUs, vGPU, CloudXR |
| 3 | **Gaming & GeForce** | GeForce RTX GPUs, GeForce NOW, NVIDIA App, DLSS, Reflex, Broadcast, Ansel |
| 4 | **Automotive & Robotics** | DRIVE platform (Orin, Thor, Hyperion), Jetson edge AI, Isaac platform, Metropolis, DeepStream |
| 5 | **Developer Ecosystem** | CUDA Toolkit, cuDNN, TensorRT, cuBLAS, NCCL, RAPIDS, NGC Catalog, NIM, AI Blueprints |

## Crawler Requirements

- Use `crawl4ai` (async) for high-concurrency crawling.
- Respect `robots.txt` and implement rate limiting (configurable delay + concurrency).
- URL management: normalize (strip fragments/trailing slashes), deduplicate, filter by include/exclude patterns.
- Save raw crawl data periodically (checkpointing) to `output/raw/`.
- PDF sub-crawler: discover and optionally download PDF documents (whitepapers, datasheets, guides).
- Support both English and Chinese URL paths.

## Classification & Extraction

### Page Classification
- Score each page against 5 ecosystems using:
  - **URL pattern matching** (60% weight) — e.g., URLs containing `/dgx/`, `/geforce/`, `/drive/`, `/cuda/`
  - **Content keyword matching** (40% weight) — e.g., page text mentioning "CUDA cores", "tensor core", "ray tracing"
- Assign primary ecosystem (highest score) + secondary affiliations.

### Hardware Extraction
Identify and categorize NVIDIA hardware products:
- **Consumer GPUs**: GeForce RTX 50/40/30 series
- **Data Center GPUs**: H100, H200, B100, B200, L40S, A100
- **Workstation GPUs**: RTX A-series, RTX PRO
- **DPUs & NICs**: BlueField, ConnectX
- **Automotive SoCs**: DRIVE Orin, DRIVE Thor, DRIVE AGX
- **Edge AI**: Jetson Orin (Nano/NX/AGX), Jetson AGX Orin
- **DGX Systems**: DGX H100, DGX B200, DGX Station, DGX Spark
- **HGX Platforms**: HGX H100, HGX B200
- **Networking**: Spectrum switches, Quantum InfiniBand
- **Grace CPU**: Grace Hopper Superchip, Grace CPU

### Software Extraction
Identify and categorize NVIDIA software/technology:
- **CUDA Platform**: CUDA Toolkit, cuDNN, cuBLAS, cuFFT, cuSPARSE
- **AI Training**: NeMo Framework, NeMo Curator, TAO Toolkit
- **AI Inference**: TensorRT, TensorRT-LLM, Triton Inference Server
- **AI Microservices (NIM)**: Llama NIM, Nemotron NIM, etc.
- **Data Science**: RAPIDS (cuDF, cuML, cuGraph), cuOpt
- **Digital Twins**: Omniverse, Omniverse Kit, USD
- **Robotics**: Isaac Sim, Isaac ROS, Isaac Lab, GR00T
- **Automotive**: DRIVE OS, DRIVE Sim, DRIVE Concierge
- **Rendering**: RTXGI, DLSS, Reflex, RTX Remix
- **Cloud Gaming**: GeForce NOW
- **Health & Life Sciences**: Clara, MONAI, BioNeMo
- **Telecom**: Aerial, DOCA, Morpheus

## Output Deliverables

All output is organized under `output/` with this subdirectory layout:

```
output/
├── raw/               ← raw crawl data (classified_pages.json, crawl_data.json)
├── indices/           ← structured JSON indexes (ecosystem, products, technologies)
├── reports/           ← human-readable reports (Markdown + Mermaid diagrams)
├── pdf/               ← downloaded PDF documents
└── README.md          ← output directory reference
```

### Required Reports
1. **Main Ecosystem Report** (`nvidia_ecosystem_report.md`): Bilingual (EN/CN) organized by ecosystem with distribution tables, subcategories, products, technologies, keywords, and sample URLs.
2. **Software Ecosystem Report** (`nvidia_software_ecosystem_report.md`): Noise-filtered narrative focused on the software stack, with theme analysis and deduplication.
3. **Ecosystem Summary** (`nvidia_ecosystem_summary_clean.md`): Compact overview filtering out locale-pair and junk subcategories.
4. **Mermaid Diagrams** (`nvidia_ecosystem_diagrams.md`): Mindmap, flowchart, pie chart, product tree, and technology tree diagrams.
5. **JSON Indices**: `nvidia_ecosystem.json`, `nvidia_products.json`, `nvidia_technologies.json` for programmatic consumption.

## Pipeline Flow

```
crawl4ai (AsyncWebCrawler)
  │
  ├── nvidia.com/en-us/ + zh-cn/ + nvidia.cn/
  │
  ▼
URLManager (normalize → validate → deduplicate → enqueue)
  │
  ▼
EcosystemClassifier (URL pattern 60% + content keyword 40%)
  │
  ▼
DataExtractor (regex: products, technologies, keywords)
  │
  ▼
Generators
  ├── JSONGenerator    → output/indices/*.json
  ├── MarkdownGenerator → output/reports/*.md
  ├── MermaidGenerator  → output/reports/nvidia_ecosystem_diagrams.md
  └── SoftwareEcosystemReport → output/reports/nvidia_software_ecosystem_report.md

Scripts
  └── summarize_ecosystem.py → output/reports/nvidia_ecosystem_summary_clean.md
```

## Success Criteria

- All 5 ecosystems are covered with meaningful page counts per ecosystem.
- Hardware products and software technologies are correctly attributed to their ecosystem(s).
- Reports are readable, well-structured, bilingual, and free of noise (duplicates, navigation pages, locale mirrors).
- The pipeline can run from scratch (full crawl) or resume from saved data (`--load-data`).
- Output directory structure is clean and predictable (raw/indices/reports/pdf/).
