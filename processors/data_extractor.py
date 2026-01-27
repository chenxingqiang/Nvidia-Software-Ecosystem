"""Data extractor for processing crawled page content."""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse


@dataclass
class ExtractedProduct:
    """Extracted product information."""
    name: str
    category: str
    description: str
    url: str
    features: List[str] = field(default_factory=list)
    specifications: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractedTechnology:
    """Extracted technology information."""
    name: str
    category: str
    description: str
    url: str
    related_products: List[str] = field(default_factory=list)


@dataclass
class ExtractedPage:
    """Extracted and processed page data."""
    url: str
    title: str
    description: str
    ecosystem: str
    subcategory: Optional[str]
    products: List[ExtractedProduct] = field(default_factory=list)
    technologies: List[ExtractedTechnology] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)


class DataExtractor:
    """Extract structured data from crawled pages."""

    # Known NVIDIA product patterns
    PRODUCT_PATTERNS = [
        r"GeForce\s+(?:RTX|GTX)?\s*\d+(?:\s*Ti)?",
        r"Quadro\s+(?:RTX|P|K)?\s*\d+",
        r"Tesla\s+(?:V|A|H|K)\d+",
        r"DGX\s+(?:A100|H100|Station|Cloud|SuperPOD)",
        r"Jetson\s+(?:AGX\s+)?(?:Orin|Xavier|Nano|TX\d)",
        r"DRIVE\s+(?:AGX|Orin|Thor|Hyperion|Sim)",
        r"A100|H100|H200|B100|B200|L40|L4",
        r"RTX\s+\d+(?:\s*Ti|\s*Super)?",
        r"Grace\s+(?:Hopper|CPU)",
        r"BlueField(?:-\d)?",
        r"ConnectX(?:-\d)?",
        r"Spectrum(?:-\d)?",
    ]

    # Known NVIDIA technology/software patterns
    TECH_PATTERNS = [
        r"CUDA(?:\s+\d+(?:\.\d+)?)?",
        r"cuDNN(?:\s+\d+(?:\.\d+)?)?",
        r"TensorRT(?:\s+\d+(?:\.\d+)?)?",
        r"Triton\s+(?:Inference\s+)?Server",
        r"NVIDIA\s+(?:AI\s+)?Enterprise",
        r"Omniverse(?:\s+\w+)?",
        r"Clara(?:\s+\w+)?",
        r"Isaac(?:\s+\w+)?",
        r"RAPIDS(?:\s+\w+)?",
        r"NeMo(?:\s+\w+)?",
        r"Merlin(?:\s+\w+)?",
        r"Morpheus(?:\s+\w+)?",
        r"DeepStream(?:\s+\w+)?",
        r"Metropolis(?:\s+\w+)?",
        r"Maxine(?:\s+\w+)?",
        r"Riva(?:\s+\w+)?",
        r"TAO\s+Toolkit",
        r"NGC(?:\s+\w+)?",
        r"Base\s+Command",
        r"Fleet\s+Command",
        r"DLSS(?:\s+\d+)?",
        r"Ray\s+Tracing",
        r"Reflex",
        r"Broadcast",
        r"Canvas",
        r"NVLink",
        r"NVSwitch",
    ]

    def __init__(self):
        """Initialize data extractor."""
        self._product_regex = [
            re.compile(p, re.IGNORECASE) for p in self.PRODUCT_PATTERNS
        ]
        self._tech_regex = [
            re.compile(p, re.IGNORECASE) for p in self.TECH_PATTERNS
        ]

    def extract_products(self, content: str, url: str) -> List[ExtractedProduct]:
        """
        Extract product mentions from content.

        Args:
            content: Page content.
            url: Page URL.

        Returns:
            List of extracted products.
        """
        products = []
        seen_names: Set[str] = set()
        
        for regex in self._product_regex:
            matches = regex.findall(content)
            for match in matches:
                name = match.strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    
                    # Determine category from product name
                    category = self._categorize_product(name)
                    
                    products.append(ExtractedProduct(
                        name=name,
                        category=category,
                        description="",
                        url=url,
                    ))
        
        return products

    def _categorize_product(self, name: str) -> str:
        """Categorize product by name."""
        name_lower = name.lower()
        
        if any(x in name_lower for x in ["geforce", "rtx", "gtx"]):
            return "Consumer GPU"
        elif "quadro" in name_lower:
            return "Professional GPU"
        elif any(x in name_lower for x in ["tesla", "a100", "h100", "b100", "l40"]):
            return "Data Center GPU"
        elif "dgx" in name_lower:
            return "DGX Systems"
        elif "jetson" in name_lower:
            return "Edge AI / Embedded"
        elif "drive" in name_lower:
            return "Automotive"
        elif any(x in name_lower for x in ["grace", "hopper", "blackwell"]):
            return "Data Center Platform"
        elif any(x in name_lower for x in ["bluefield", "connectx", "spectrum"]):
            return "Networking"
        else:
            return "Other Hardware"

    def extract_technologies(
        self,
        content: str,
        url: str,
    ) -> List[ExtractedTechnology]:
        """
        Extract technology/software mentions from content.

        Args:
            content: Page content.
            url: Page URL.

        Returns:
            List of extracted technologies.
        """
        technologies = []
        seen_names: Set[str] = set()
        
        for regex in self._tech_regex:
            matches = regex.findall(content)
            for match in matches:
                name = match.strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    
                    category = self._categorize_technology(name)
                    
                    technologies.append(ExtractedTechnology(
                        name=name,
                        category=category,
                        description="",
                        url=url,
                    ))
        
        return technologies

    def _categorize_technology(self, name: str) -> str:
        """Categorize technology by name."""
        name_lower = name.lower()
        
        if any(x in name_lower for x in ["cuda", "cudnn", "cublas"]):
            return "CUDA Platform"
        elif any(x in name_lower for x in ["tensorrt", "triton"]):
            return "AI Inference"
        elif any(x in name_lower for x in ["nemo", "merlin", "morpheus", "rapids"]):
            return "AI Frameworks"
        elif "omniverse" in name_lower:
            return "Omniverse Platform"
        elif "clara" in name_lower:
            return "Healthcare AI"
        elif "isaac" in name_lower:
            return "Robotics"
        elif any(x in name_lower for x in ["deepstream", "metropolis"]):
            return "Computer Vision"
        elif any(x in name_lower for x in ["maxine", "riva", "broadcast"]):
            return "Speech & Audio AI"
        elif any(x in name_lower for x in ["dlss", "ray tracing", "reflex"]):
            return "Graphics Technology"
        elif "ngc" in name_lower:
            return "Cloud & Containers"
        elif any(x in name_lower for x in ["nvlink", "nvswitch"]):
            return "Interconnect Technology"
        else:
            return "Other Software"

    def extract_keywords(self, content: str, top_n: int = 20) -> List[str]:
        """
        Extract important keywords from content.

        Args:
            content: Page content.
            top_n: Number of top keywords to return.

        Returns:
            List of keywords.
        """
        # NVIDIA-specific important terms
        important_terms = {
            "ai", "gpu", "cuda", "deep learning", "machine learning",
            "neural network", "inference", "training", "hpc",
            "data center", "cloud", "edge", "automotive", "robotics",
            "healthcare", "gaming", "professional visualization",
            "accelerated computing", "generative ai", "llm",
        }
        
        content_lower = content.lower()
        found_keywords = []
        
        for term in important_terms:
            if term in content_lower:
                found_keywords.append(term)
        
        return found_keywords[:top_n]

    def extract_page(
        self,
        url: str,
        title: str,
        description: str,
        content: str,
        ecosystem: str,
        subcategory: Optional[str] = None,
        links: Optional[List[str]] = None,
    ) -> ExtractedPage:
        """
        Extract all structured data from a page.

        Args:
            url: Page URL.
            title: Page title.
            description: Page description.
            content: Page content.
            ecosystem: Classified ecosystem.
            subcategory: Page subcategory.
            links: Page links.

        Returns:
            ExtractedPage with all structured data.
        """
        combined_content = f"{title} {description} {content}"
        
        return ExtractedPage(
            url=url,
            title=title,
            description=description,
            ecosystem=ecosystem,
            subcategory=subcategory,
            products=self.extract_products(combined_content, url),
            technologies=self.extract_technologies(combined_content, url),
            keywords=self.extract_keywords(combined_content),
            links=links or [],
        )

    def extract_batch(
        self,
        pages: List[Dict[str, Any]],
    ) -> List[ExtractedPage]:
        """
        Extract data from a batch of pages.

        Args:
            pages: List of page dicts.

        Returns:
            List of ExtractedPage objects.
        """
        return [
            self.extract_page(
                url=p.get("url", ""),
                title=p.get("title", ""),
                description=p.get("description", ""),
                content=p.get("content", ""),
                ecosystem=p.get("ecosystem", "technology"),
                subcategory=p.get("subcategory"),
                links=p.get("links", []),
            )
            for p in pages
        ]
