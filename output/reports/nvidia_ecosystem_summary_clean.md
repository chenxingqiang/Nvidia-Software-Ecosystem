# NVIDIA Ecosystem Summary (noise-filtered)

> Generated: 2026-04-15 02:40 UTC
> Source crawl: 2026-01-23T16:27:35.560600 → 2026-01-26T16:38:28.501775
> Pages in aggregate: **10000**

## Source of truth (recommended)

| Role | File |
|------|------|
| Raw pages | `raw/crawl_data.json` (large; gitignored by default) |
| Per-page classification | `raw/classified_pages.json` (large; gitignored) |
| **Aggregated ecosystems** | **`indices/nvidia_ecosystem.json`** |
| Product index | `indices/nvidia_products.json` |
| Technology index | `indices/nvidia_technologies.json` |
| PDF inventory | `pdf/nvidia_pdf_catalog.json` + `pdf/nvidia_pdf_urls.txt` |
| Human narrative | `reports/*.md` (ecosystem, software trees, summaries) |

## Five-ecosystem distribution

- **Hardware Ecosystem** (`hardware`): 4732 pages (47.3%)
- **Software Ecosystem** (`software`): 812 pages (8.1%)
- **Developer Ecosystem** (`developer`): 1017 pages (10.2%)
- **Business Ecosystem** (`business`): 1836 pages (18.4%)
- **Technology Ecosystem** (`technology`): 1603 pages (16.0%)

## Clean subcategories (top per ecosystem)

*Subcategories matching locale-like tokens (`En Gb`, `Zh Cn`, `En Us …`) or generic junk (`Object`, `Tag`, …) are dropped.*

### Hardware Ecosystem

- **Networking**: 190 pages
- **Geforce**: 117 pages
- **Contact**: 53 pages
- **Courses**: 45 pages
- **Design Visualization**: 41 pages
- **Drive**: 38 pages
- **Products**: 38 pages
- **Dgx**: 36 pages
- **Jetson**: 23 pages
- **Content**: 19 pages
- **Embedded**: 16 pages
- **Autonomous Machines**: 15 pages
- **Rtx**: 13 pages
- **Learning Library**: 12 pages
- **Use Cases**: 12 pages

### Software Ecosystem

- **C**: 102 pages
- **Cuda**: 70 pages
- **Orgs**: 57 pages
- **Clara**: 43 pages
- **Omniverse**: 23 pages
- **Deeplearning**: 17 pages
- **Isaac**: 12 pages
- **Courses**: 11 pages
- **Ai Data Science**: 9 pages
- **Nvidia**: 8 pages
- **Ai Enterprise**: 4 pages
- **Nsight Compute**: 4 pages
- **Base Command Manager**: 3 pages
- **Compute**: 3 pages
- **Data Center**: 3 pages

### Developer Ecosystem

- **Docs**: 44 pages
- **Nvidia**: 33 pages
- **Downloads**: 32 pages
- **Ngc**: 25 pages
- **Nsight Compute**: 24 pages
- **Nsight Visual Studio Edition**: 16 pages
- **Embedded**: 12 pages
- **Ai Data Science**: 10 pages
- **Launchable**: 9 pages
- **Meta**: 7 pages
- **Products**: 7 pages
- **Blog**: 6 pages
- **Models**: 6 pages
- **Collections**: 5 pages
- **Blueprints**: 4 pages

### Business Ecosystem

- **Industries**: 102 pages
- **Solutions**: 64 pages
- **Deep Learning Ai**: 27 pages
- **Design Visualization**: 20 pages
- **Self Driving Cars**: 17 pages
- **Enterprise**: 14 pages
- **Case Studies**: 10 pages
- **Multimedia**: 9 pages
- **Lp**: 8 pages
- **Support**: 8 pages
- **Bios**: 7 pages
- **News**: 7 pages
- **Ai Data Science**: 6 pages
- **Embedded**: 6 pages
- **Explore**: 6 pages

### Technology Ecosystem

- **Data Center**: 260 pages
- **Topics**: 22 pages
- **Ai**: 17 pages
- **C**: 10 pages
- **Launchpad**: 9 pages
- **Blog**: 6 pages
- **Orgs**: 6 pages
- **On Demand**: 5 pages
- **Graduate Fellowships**: 4 pages
- **High Performance Computing**: 4 pages
- **Solutions**: 4 pages
- **Containers**: 3 pages
- **Dgx Cloud**: 3 pages
- **T**: 3 pages
- **Autonomous Machines**: 2 pages

## Top products (mentions across pages, top 40)

- DGX Cloud (5×)
- DGX Station (5×)
- DGX SuperPOD (5×)
- DRIVE AGX (5×)
- DRIVE Sim (5×)
- L4 (5×)
- B200 (5×)
- b200 (5×)
- H200 (5×)
- h200 (5×)
- l4 (5×)
- RTX 50 (5×)
- RTX 5080 (5×)
- RTX 6000 (5×)
- Grace CPU (5×)
- Grace Hopper (5×)
- BlueField (5×)
- Spectrum (5×)
- spectrum (5×)
- bluefield-4 (5×)
- bluefield (5×)
- BlueField-4 (5×)
- ConnectX (5×)
- BlueField-3 (5×)
- BlueField-2 (5×)
- A100 (5×)
- H100 (5×)
- L40 (5×)
- DGX A100 (5×)
- a100 (5×)
- l40 (5×)
- h100 (5×)
- Tesla V100 (5×)
- Jetson Orin (5×)
- Jetson Xavier (5×)
- Jetson TX2 (5×)
- Jetson Nano (5×)
- Jetson AGX Orin (5×)
- Jetson AGX Xavier (5×)
- jetson nano (5×)

## Top technologies (mentions across pages, top 40)

- CUDA (5×)
- cuda (5×)
- cuDNN (5×)
- cudnn (5×)
- CUDA 13.0 (5×)
- NVIDIA AI Enterprise (5×)
- Base Command (5×)
- NVIDIA Enterprise (5×)
- Fleet Command (5×)
- TAO Toolkit (5×)
- NVIDIA enterprise (5×)
- canvas (5×)
- Omniverse Cloud (5×)
- omniverse (5×)
- Omniverse (5×)
- Omniverse Libraries (5×)
- Omniverse Enterprise (5×)
- Omniverse Community (5×)
- Omniverse Digital (5×)
- Omniverse and (5×)
- Omniverse Blueprint (5×)
- Omniverse is (5×)
- Omniverse Kit (5×)
- Omniverse forum (5×)
- Omniverse on (5×)
- Omniverse Platform (5×)
- Omniverse Nucleus (5×)
- Omniverse Launcher (5×)
- clara (5×)
- Clara AGX (5×)
- Clara (5×)
- Isaac (5×)
- isaac (5×)
- Isaac Lab (5×)
- Isaac Sim (5×)
- Isaac ROS (5×)
- Isaac GR00T (5×)
- RAPIDS (5×)
- rapids (5×)
- Nemo (5×)

## Regenerate

```bash
python scripts/summarize_ecosystem.py --input output/indices/nvidia_ecosystem.json
```
