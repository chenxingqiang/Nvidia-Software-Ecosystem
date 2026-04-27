"""Markdown report generator for NVIDIA ecosystem."""
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import ECOSYSTEM_NAMES, ECOSYSTEM_NAMES_CN

# Noise filters (same logic as scripts/summarize_ecosystem.py)
_LOCALE_PAIR = re.compile(r"^[A-Za-z]{2}\s+[A-Za-z]{2,3}$")
_EN_US_SLUG = re.compile(r"^En\s+Us\b", re.I)
_MISC_SLUG_PREFIX = re.compile(
    r"^(Es|Fr|De|It|Pt|Nl|Pl|Ro|Fi|Sv|Nb|Da|Cs|Tr)\s+[A-Za-z]{2,3}\b",
    re.I,
)
_JUNK_TOKENS = frozenset({
    "object", "l", "%20", "tag", "en", "hot", "images", "search",
    "categories", "kb", "shop", "help", "login", "account", "download",
    "join", "dashboard", "gtc", "catalog", "faq", "forums", "home", "nvidia.com",
    "c", "orgs",
})


def _is_noise_subcategory(name: str) -> bool:
    """Check if a subcategory name is locale noise or junk."""
    s = (name or "").strip()
    if not s:
        return True
    if s.lower() in _JUNK_TOKENS:
        return True
    if _LOCALE_PAIR.match(s):
        return True
    if _EN_US_SLUG.match(s):
        return True
    if _MISC_SLUG_PREFIX.match(s):
        return True
    return False


class MarkdownGenerator:
    """Generate Markdown reports for NVIDIA ecosystem data."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize Markdown generator.

        Args:
            output_dir: Directory to save output files.
        """
        self.output_dir = output_dir or Path("output")
        self.ecosystem_names = ECOSYSTEM_NAMES
        self.ecosystem_names_cn = ECOSYSTEM_NAMES_CN

    def generate_ecosystem_report(
        self,
        ecosystem_data: Dict[str, Any],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate comprehensive ecosystem report.

        Args:
            ecosystem_data: Organized ecosystem data.
            metadata: Crawl metadata.

        Returns:
            Markdown string.
        """
        lines = []
        
        # Header
        lines.append("# NVIDIA Ecosystem Landscape / NVIDIA 生态系统全景图")
        lines.append("")
        lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary statistics
        lines.append("## Overview / 概览")
        lines.append("")
        total_pages = metadata.get("total_pages", 0)
        lines.append(f"- **Total Pages Analyzed / 分析页面总数**: {total_pages}")
        lines.append(f"- **Crawl Duration / 爬取时长**: {metadata.get('elapsed_seconds', 0):.1f}s")
        lines.append("")
        
        # Ecosystem distribution
        lines.append("### Ecosystem Distribution / 生态分布")
        lines.append("")
        lines.append("| Ecosystem | 生态 | Pages | Percentage |")
        lines.append("|-----------|------|-------|------------|")
        
        for eco_id, eco_data in ecosystem_data.items():
            name_en = self.ecosystem_names.get(eco_id, eco_id)
            name_cn = self.ecosystem_names_cn.get(eco_id, eco_id)
            count = eco_data.get("total_pages", 0)
            pct = (count / total_pages * 100) if total_pages > 0 else 0
            lines.append(f"| {name_en} | {name_cn} | {count} | {pct:.1f}% |")
        
        lines.append("")
        
        # Detailed sections for each ecosystem
        eco_order = ["hardware", "software", "developer", "business", "technology"]
        
        for idx, eco_id in enumerate(eco_order, 1):
            if eco_id not in ecosystem_data:
                continue
            
            eco_data = ecosystem_data[eco_id]
            name_en = self.ecosystem_names.get(eco_id, eco_id)
            name_cn = self.ecosystem_names_cn.get(eco_id, eco_id)
            
            lines.append(f"## {idx}. {name_en} / {name_cn}")
            lines.append("")
            
            # Subcategories (noise filtered)
            subcategories = eco_data.get("subcategories", {})
            if subcategories:
                lines.append("### Categories / 分类")
                lines.append("")

                clean_subcats = [
                    (k, v) for k, v in subcategories.items()
                    if not _is_noise_subcategory(str(k))
                ]
                for subcat, count in sorted(
                    clean_subcats, key=lambda x: x[1], reverse=True
                )[:15]:
                    lines.append(f"- **{subcat}**: {count} pages")

                lines.append("")
            
            # Products (for hardware)
            products = eco_data.get("products", {})
            if products:
                lines.append("### Products / 产品")
                lines.append("")
                
                for category, items in products.items():
                    lines.append(f"#### {category}")
                    lines.append("")
                    for item in items[:10]:
                        lines.append(f"- {item}")
                    lines.append("")
            
            # Technologies (for software)
            technologies = eco_data.get("technologies", {})
            if technologies:
                lines.append("### Technologies / 技术")
                lines.append("")
                
                for category, items in technologies.items():
                    lines.append(f"#### {category}")
                    lines.append("")
                    for item in items[:10]:
                        lines.append(f"- {item}")
                    lines.append("")
            
            # Keywords
            keywords = eco_data.get("top_keywords", [])
            if keywords:
                lines.append("### Key Topics / 关键主题")
                lines.append("")
                keyword_list = [f"`{kw}`" for kw, _ in keywords[:10]]
                lines.append(", ".join(keyword_list))
                lines.append("")
            
            # Sample URLs
            sample_urls = eco_data.get("sample_urls", [])
            if sample_urls:
                lines.append("### Sample Resources / 示例资源")
                lines.append("")
                for url in sample_urls[:5]:
                    lines.append(f"- [{url}]({url})")
                lines.append("")
        
        return "\n".join(lines)

    def generate_product_catalog(
        self,
        products: Dict[str, List[str]],
    ) -> str:
        """
        Generate product catalog.

        Args:
            products: Dict mapping category to product list.

        Returns:
            Markdown string.
        """
        lines = []
        
        lines.append("# NVIDIA Product Catalog / NVIDIA 产品目录")
        lines.append("")
        
        for category, items in sorted(products.items()):
            lines.append(f"## {category}")
            lines.append("")
            
            for item in sorted(set(items)):
                lines.append(f"- {item}")
            
            lines.append("")
        
        return "\n".join(lines)

    def generate_technology_stack(
        self,
        technologies: Dict[str, List[str]],
    ) -> str:
        """
        Generate technology stack overview.

        Args:
            technologies: Dict mapping category to technology list.

        Returns:
            Markdown string.
        """
        lines = []
        
        lines.append("# NVIDIA Technology Stack / NVIDIA 技术栈")
        lines.append("")
        
        for category, items in sorted(technologies.items()):
            lines.append(f"## {category}")
            lines.append("")
            
            for item in sorted(set(items)):
                lines.append(f"- {item}")
            
            lines.append("")
        
        return "\n".join(lines)

    def save_report(
        self,
        content: str,
        filename: str = "nvidia_ecosystem_report.md",
    ) -> Path:
        """
        Save report to file.

        Args:
            content: Markdown content.
            filename: Output filename.

        Returns:
            Path to saved file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return output_path

    def generate_full_report(
        self,
        classified_pages: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate full report from classified pages.

        Args:
            classified_pages: List of classified page data.
            metadata: Crawl metadata.

        Returns:
            Markdown string.
        """
        # Organize data by ecosystem
        ecosystem_data: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "total_pages": 0,
                "subcategories": defaultdict(int),
                "products": defaultdict(dict),       # cat -> {name_lower: display_name}
                "technologies": defaultdict(dict),    # cat -> {name_lower: display_name}
                "top_keywords": [],
                "sample_urls": [],
            }
        )

        all_products: Dict[str, Dict[str, str]] = defaultdict(dict)
        all_technologies: Dict[str, Dict[str, str]] = defaultdict(dict)
        keyword_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        seen_urls: Set[str] = set()

        for page in classified_pages:
            url = page.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)

            eco = page.get("ecosystem", "technology")
            eco_entry = ecosystem_data[eco]

            eco_entry["total_pages"] += 1

            subcat = page.get("subcategory")
            if subcat:
                eco_entry["subcategories"][subcat] += 1

            # Collect products (case-insensitive dedup)
            for product in page.get("products", []):
                if isinstance(product, dict):
                    name = product.get("name", "")
                    category = product.get("category", "Other")
                else:
                    name = str(product)
                    category = "Other"

                if name:
                    key = name.lower()
                    if key not in eco_entry["products"][category]:
                        eco_entry["products"][category][key] = name
                    if key not in all_products[category]:
                        all_products[category][key] = name

            # Collect technologies (case-insensitive dedup)
            for tech in page.get("technologies", []):
                if isinstance(tech, dict):
                    name = tech.get("name", "")
                    category = tech.get("category", "Other")
                else:
                    name = str(tech)
                    category = "Other"

                if name:
                    key = name.lower()
                    if key not in eco_entry["technologies"][category]:
                        eco_entry["technologies"][category][key] = name
                    if key not in all_technologies[category]:
                        all_technologies[category][key] = name

            # Track keywords
            for keyword in page.get("keywords", []):
                keyword_counts[eco][keyword] += 1

            # Sample URLs
            if len(eco_entry["sample_urls"]) < 10:
                eco_entry["sample_urls"].append(url)

        # Convert dicts to sorted lists for report generation
        for eco in ecosystem_data:
            eco_entry = ecosystem_data[eco]
            eco_entry["products"] = {
                cat: sorted(names.values(), key=str.lower)
                for cat, names in eco_entry["products"].items()
            }
            eco_entry["technologies"] = {
                cat: sorted(names.values(), key=str.lower)
                for cat, names in eco_entry["technologies"].items()
            }
        
        # Sort keywords
        for eco in ecosystem_data:
            kw_counts = keyword_counts[eco]
            ecosystem_data[eco]["top_keywords"] = sorted(
                kw_counts.items(), key=lambda x: x[1], reverse=True
            )[:20]
        
        return self.generate_ecosystem_report(dict(ecosystem_data), metadata)
