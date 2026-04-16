# NVIDIA Ecosystem Crawler

A comprehensive web crawler and analyzer for mapping NVIDIA's complete ecosystem including hardware, software, developer tools, business solutions, and technology platforms.

## Features

- **Deep Web Crawling**: Uses `crawl4ai` for efficient async crawling of NVIDIA's website (English and Chinese: `*.nvidia.com`, `*.nvidia.cn`, and paths `/en-us/`, `/zh-cn/`, `/zh-tw/`; other locale paths such as `/ja-jp/` are excluded)
- **Ecosystem Classification**: Automatically categorizes pages into 5 major ecosystems:
  - Hardware Ecosystem (GPUs, DGX, Jetson, DRIVE, Networking)
  - Software Ecosystem (CUDA, TensorRT, Omniverse, Clara, Isaac)
  - Developer Ecosystem (SDKs, NGC, Documentation, Tools)
  - Business Ecosystem (Enterprise, Partners, Industries, Cloud)
  - Technology Ecosystem (AI/ML, HPC, Data Center, Edge Computing)
- **Product & Technology Extraction**: Identifies NVIDIA products and technologies mentioned on pages
- **Multi-format Output**: Generates reports in Markdown, JSON, and Mermaid diagrams

## Installation

Use a virtual environment if your Python is **PEP 668** “externally managed” (common with Homebrew):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Otherwise:

```bash
pip install -r requirements.txt
```

Then install crawl4ai browser dependencies:

```bash
crawl4ai-setup
```

## Usage

### 1. Full Ecosystem Pipeline (Crawl + Analyze + Report)

```bash
# Default settings (5 layers deep, up to 10000 pages)
python main.py

# Traverse ALL sub-pages (no include-pattern filtering)
python main.py --crawl-all

# Custom settings
python main.py --max-depth 3 --max-pages 500 --concurrent 10 --delay 1.0

# Custom output directory
python main.py --output-dir ./my_output
```

### Process Existing Data

If you have previously crawled data:

```bash
python main.py --load-data output/crawl_data.json
```

### Command Line Options


| Option         | Default  | Description                                  |
| -------------- | -------- | -------------------------------------------- |
| `--max-depth`  | 5        | Maximum crawl depth                          |
| `--max-pages`  | 10000    | Maximum pages to crawl                       |
| `--concurrent` | 5        | Maximum concurrent requests                  |
| `--delay`      | 1.5      | Delay between requests (seconds)             |
| `--output-dir` | ./output | Output directory                             |
| `--load-data`  | -        | Load existing crawl data instead of crawling |
| `--seed-urls`  | -        | Custom seed URLs to start crawling           |
| `--crawl-all`  | False    | Traverse ALL sub-pages (skip include-pattern filter) |


### 2. PDF Document Crawler

Specialized crawler for extracting all PDF documents from NVIDIA website:

```bash
# Basic PDF crawl (catalog only)
python -m crawler.pdf_crawler --max-depth 4 --max-pages 2000

# Deep PDF crawl with more pages
python -m crawler.pdf_crawler --max-depth 5 --max-pages 5000 --concurrent 5

# Download PDFs to local folder
python -m crawler.pdf_crawler --max-pages 1000 --download
```

#### PDF Crawler Options


| Option         | Default  | Description                   |
| -------------- | -------- | ----------------------------- |
| `--max-depth`  | 4        | Maximum crawl depth           |
| `--max-pages`  | 2000     | Maximum pages to crawl        |
| `--concurrent` | 5        | Concurrent requests           |
| `--delay`      | 1.5      | Request delay (seconds)       |
| `--download`   | False    | Download PDFs to local folder |
| `--output-dir` | ./output | Output directory              |


#### PDF Crawler Output

- `nvidia_pdf_catalog.json` - Complete PDF catalog with metadata
- `nvidia_pdf_urls.txt` - Plain text list of all PDF URLs
- `nvidia_pdf_report.md` - Markdown report organized by category
- `pdfs/` - Downloaded PDFs (if `--download` flag is used)

## Output Files

After running the ecosystem crawler, you'll find these files in the output directory:


| File                           | Description                       |
| ------------------------------ | --------------------------------- |
| `nvidia_ecosystem_report.md`   | Comprehensive Markdown report     |
| `nvidia_ecosystem.json`        | Full ecosystem data in JSON       |
| `nvidia_products.json`         | Product catalog JSON              |
| `nvidia_technologies.json`     | Technology stack JSON             |
| `nvidia_ecosystem_diagrams.md` | Mermaid diagrams document         |
| `classified_pages.json`        | All classified page data          |
| `crawl_data.json`              | Raw crawl data (for reprocessing) |
| `crawl.log`                    | Crawl log file                    |

`crawl_data.json` and `classified_pages.json` can be very large; they are listed in `.gitignore` so they are not committed by default. The PDF crawler adds `nvidia_pdf_catalog.json`, `nvidia_pdf_urls.txt`, and `nvidia_pdf_report.md` (see above). You may also have extra Markdown under `output/` from past runs or manual notes; only the files in this table are produced by `main.py` in one pass.

## Project Structure

```
nvidia-ecosystem/
├── crawler/
│   ├── __init__.py
│   ├── nvidia_crawler.py      # Main crawler using crawl4ai
│   ├── pdf_crawler.py         # PDF link discovery and optional download
│   ├── url_manager.py         # URL queue and filtering
│   └── rate_limiter.py        # Request rate limiting
├── processors/
│   ├── __init__.py
│   ├── classifier.py          # Ecosystem classifier
│   └── data_extractor.py      # Product/technology extraction
├── generators/
│   ├── __init__.py
│   ├── markdown_gen.py        # Markdown report generator
│   ├── json_gen.py            # JSON data generator
│   └── mermaid_gen.py         # Mermaid diagram generator
├── output/                    # Output directory
├── config.py                  # Configuration settings
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Ecosystem Classification

The classifier uses URL patterns and content keywords to categorize pages:

### Hardware Ecosystem

- GPU product lines (GeForce, Quadro, Tesla, A100, H100, B100)
- DGX systems and HGX platforms
- Jetson embedded platforms
- DRIVE automotive platforms
- Networking (Mellanox, InfiniBand, BlueField)

### Software Ecosystem

- CUDA platform and libraries (cuDNN, cuBLAS, NCCL)
- TensorRT and Triton Inference Server
- Omniverse platform
- Clara (Healthcare), Isaac (Robotics)
- RAPIDS, NeMo, Merlin, Morpheus

### Developer Ecosystem

- SDKs and APIs
- NGC (NVIDIA GPU Cloud)
- Documentation and tutorials
- Developer tools (Nsight, profilers)
- Open source projects

### Business Ecosystem

- Enterprise solutions (AI Enterprise)
- Cloud partnerships (AWS, Azure, GCP)
- Industry solutions (Gaming, Automotive, Healthcare)
- Partner programs

### Technology Ecosystem

- AI/Deep Learning technologies
- High Performance Computing (HPC)
- Computer Vision and NLP
- Graphics technologies (Ray Tracing, DLSS)

## License

MIT License