"""Configuration for NVIDIA Ecosystem Crawler."""
from pathlib import Path
from typing import Dict, List, Set

# Base directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"

# Crawler settings
CRAWLER_CONFIG = {
    "base_url": "https://www.nvidia.com/en-us/",
    "max_depth": 5,
    "max_concurrent": 5,
    "request_delay": 1.5,  # seconds between requests
    "timeout": 30,  # seconds
    "max_pages": 10000,  # maximum pages to crawl
    "save_interval": 100,  # save progress every N pages
}

# Browser configuration
BROWSER_CONFIG = {
    "headless": True,
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# Seed URLs - main entry points for crawling
SEED_URLS: List[str] = [
    "https://www.nvidia.com/en-us/",
    "https://www.nvidia.com/en-us/geforce/",
    "https://www.nvidia.com/en-us/data-center/",
    "https://www.nvidia.com/en-us/deep-learning-ai/",
    "https://www.nvidia.com/en-us/autonomous-machines/",
    "https://www.nvidia.com/en-us/omniverse/",
    "https://www.nvidia.com/en-us/solutions/",
    "https://www.nvidia.com/en-us/industries/",
    "https://developer.nvidia.com/",
    "https://www.nvidia.com/en-us/networking/",
    "https://www.nvidia.com/en-us/design-visualization/",
    "https://www.nvidia.com/en-us/self-driving-cars/",
    "https://www.nvidia.com/en-us/high-performance-computing/",
]

# URL filtering patterns
URL_INCLUDE_PATTERNS: List[str] = [
    "/products/",
    "/solutions/",
    "/developer/",
    "/data-center/",
    "/ai/",
    "/deep-learning/",
    "/geforce/",
    "/quadro/",
    "/dgx/",
    "/jetson/",
    "/drive/",
    "/omniverse/",
    "/clara/",
    "/isaac/",
    "/cuda/",
    "/tensorrt/",
    "/ngc/",
    "/enterprise/",
    "/partners/",
    "/industries/",
    "/cloud/",
    "/hpc/",
    "/networking/",
    "/autonomous-machines/",
    "/design-visualization/",
    "/self-driving-cars/",
    "/high-performance-computing/",
]

URL_EXCLUDE_PATTERNS: List[str] = [
    "/blog/",
    "/news/",
    "/press/",
    "/login/",
    "/signin/",
    "/signup/",
    "/cart/",
    "/checkout/",
    "/account/",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".exe",
    ".dmg",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    "/zh-cn/",
    "/zh-tw/",
    "/ja-jp/",
    "/ko-kr/",
    "/de-de/",
    "/fr-fr/",
    "/es-es/",
    "/it-it/",
    "/pt-br/",
    "/ru-ru/",
]

# Allowed domains for crawling
ALLOWED_DOMAINS: Set[str] = {
    "nvidia.com",
    "www.nvidia.com",
    "developer.nvidia.com",
    "docs.nvidia.com",
    "ngc.nvidia.com",
}

# Ecosystem classification patterns
ECOSYSTEM_PATTERNS: Dict[str, Dict[str, List[str]]] = {
    "hardware": {
        "url_patterns": [
            "/geforce/",
            "/quadro/",
            "/dgx/",
            "/jetson/",
            "/drive/",
            "/networking/",
            "/mellanox/",
            "/infiniband/",
            "/gpu/",
            "/a100/",
            "/h100/",
            "/b100/",
            "/l40/",
            "/rtx/",
            "/titan/",
            "/hgx/",
            "/egx/",
        ],
        "keywords": [
            "gpu", "graphics card", "geforce", "quadro", "dgx", "jetson",
            "drive", "a100", "h100", "b100", "rtx", "titan", "hgx", "egx",
            "mellanox", "infiniband", "connectx", "bluefield", "spectrum",
            "nvlink", "nvswitch", "grace", "hopper", "blackwell", "ampere",
            "ada lovelace", "turing", "volta", "pascal",
        ],
    },
    "software": {
        "url_patterns": [
            "/cuda/",
            "/tensorrt/",
            "/omniverse/",
            "/clara/",
            "/isaac/",
            "/cudnn/",
            "/cublas/",
            "/nccl/",
            "/triton/",
            "/riva/",
            "/maxine/",
            "/broadcast/",
            "/ai-enterprise/",
        ],
        "keywords": [
            "cuda", "cudnn", "cublas", "tensorrt", "omniverse", "clara",
            "isaac", "nccl", "triton", "riva", "maxine", "broadcast",
            "deepstream", "metropolis", "fleet command", "ai enterprise",
            "base command", "nemo", "merlin", "morpheus", "rapids",
            "tao toolkit", "dali", "nvjpeg", "video codec",
        ],
    },
    "developer": {
        "url_patterns": [
            "/developer/",
            "/sdk/",
            "/ngc/",
            "/docs/",
            "/tools/",
            "/libraries/",
            "/samples/",
            "/tutorials/",
        ],
        "keywords": [
            "sdk", "api", "developer", "documentation", "tutorial",
            "sample code", "github", "open source", "ngc", "container",
            "docker", "kubernetes", "helm", "nsight", "profiler",
            "debugger", "compiler", "nvcc", "ptx",
        ],
    },
    "business": {
        "url_patterns": [
            "/enterprise/",
            "/partners/",
            "/industries/",
            "/cloud/",
            "/solutions/",
            "/professional/",
            "/workstation/",
        ],
        "keywords": [
            "enterprise", "business", "partner", "industry", "solution",
            "cloud", "aws", "azure", "gcp", "oracle", "alibaba",
            "gaming", "automotive", "healthcare", "finance", "retail",
            "manufacturing", "media", "entertainment", "education",
            "government", "research", "startup", "inception program",
        ],
    },
    "technology": {
        "url_patterns": [
            "/ai/",
            "/hpc/",
            "/deep-learning/",
            "/data-center/",
            "/machine-learning/",
            "/computer-vision/",
            "/nlp/",
            "/recommender/",
        ],
        "keywords": [
            "artificial intelligence", "machine learning", "deep learning",
            "neural network", "transformer", "llm", "large language model",
            "computer vision", "natural language processing", "nlp",
            "recommendation system", "reinforcement learning", "generative ai",
            "hpc", "high performance computing", "supercomputer",
            "data center", "inference", "training", "ray tracing",
            "dlss", "reflex", "broadcast", "canvas", "gaugan",
        ],
    },
}

# Ecosystem display names
ECOSYSTEM_NAMES: Dict[str, str] = {
    "hardware": "Hardware Ecosystem",
    "software": "Software Ecosystem",
    "developer": "Developer Ecosystem",
    "business": "Business Ecosystem",
    "technology": "Technology Ecosystem",
}

# Ecosystem Chinese names
ECOSYSTEM_NAMES_CN: Dict[str, str] = {
    "hardware": "硬件生态",
    "software": "软件生态",
    "developer": "开发者生态",
    "business": "商业生态",
    "technology": "技术生态",
}
