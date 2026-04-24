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
        r"\bGeForce\s+(?:RTX|GTX)?\s*\d+(?:\s*Ti)?\b",
        r"\bQuadro\s+(?:RTX|P|K)?\s*\d+\b",
        r"\bTesla\s+(?:V|A|H|K)\d+\b",
        r"\bDGX\s+(?:A100|H100|Station|Cloud|SuperPOD)\b",
        r"\bJetson\s+(?:AGX\s+)?(?:Orin|Xavier|Nano|TX\d)\b",
        r"\bDRIVE\s+(?:AGX|Orin|Thor|Hyperion|Sim)\b",
        r"\b(?:A100|H100|H200|B100|B200|L40S?|L4)\b",
        r"\bRTX\s+\d+(?:\s*Ti|\s*Super)?\b",
        r"\bGrace\s+(?:Hopper|CPU)\b",
        r"\bBlueField(?:-\d+)?\b",
        r"\bConnectX(?:-\d+)?\b",
        r"\bSpectrum(?:-\d+)?\b",
    ]

    # Known NVIDIA technology/software patterns
    TECH_PATTERNS = [
        r"\bCUDA(?:\s+\d+(?:\.\d+)?)?\b",
        r"\bcuDNN(?:\s+\d+(?:\.\d+)?)?\b",
        r"\bTensorRT(?:\s+\d+(?:\.\d+)?)?\b",
        r"\bTriton\s+(?:Inference\s+)?Server\b",
        r"\bNVIDIA\s+(?:AI\s+)?Enterprise\b",
        r"\bOmniverse(?:\s+\w+)*\b",
        r"\bClara(?:\s+\w+)*\b",
        r"\bIsaac(?:\s+\w+)*\b",
        r"\bRAPIDS(?:\s+\w+)*\b",
        r"\bNeMo(?:\s+\w+)*\b",
        r"\bMerlin(?:\s+\w+)*\b",
        r"\bMorpheus(?:\s+\w+)*\b",
        r"\bDeepStream(?:\s+\w+)*\b",
        r"\bMetropolis(?:\s+\w+)*\b",
        r"\bMaxine(?:\s+\w+)*\b",
        r"\bRiva(?:\s+\w+)*\b",
        r"\bTAO\s+Toolkit\b",
        r"\bNGC(?:\s+\w+)*\b",
        r"\bBase\s+Command\b",
        r"\bFleet\s+Command\b",
        r"\bDLSS(?:\s+\d+)?\b",
        r"\bRay\s+Tracing\b",
        r"\bReflex\b",
        r"\bBroadcast\b",
        r"\bCanvas\b",
        r"\bNVLink\b",
        r"\bNVSwitch\b",
    ]

    @staticmethod
    def _clean_name(name: str) -> Optional[str]:
        """Normalize and validate an extracted name.

        Returns None if the name is noise (non-ASCII, empty, too short).
        """
        if not name:
            return None
        # Collapse internal whitespace and strip
        cleaned = re.sub(r'\s+', ' ', name).strip()
        if not cleaned:
            return None
        # Filter out non-ASCII fragments (Japanese, Chinese, Turkish, etc.)
        if not all(ord(c) < 128 for c in cleaned):
            return None
        # Filter names that are too short to be meaningful (single letter, bare number)
        if len(cleaned) < 2:
            return None
        # Filter names that are clearly garbage (e.g., concatenated URL fragments)
        if len(cleaned) > 60:
            return None
        return cleaned

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
                name = self._clean_name(match)
                if not name:
                    continue
                # Case-insensitive deduplication
                key = name.lower()
                if key in seen_names:
                    continue
                seen_names.add(key)

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
                name = self._clean_name(match)
                if not name:
                    continue
                # Case-insensitive deduplication
                key = name.lower()
                if key in seen_names:
                    continue
                seen_names.add(key)

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
