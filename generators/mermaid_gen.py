"""Mermaid diagram generator for NVIDIA ecosystem."""
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


def _is_noise_name(name: str) -> bool:
    """Check if an extracted product/tech name is noise."""
    s = (name or "").strip()
    if not s or len(s) < 2:
        return True
    # Filter non-ASCII
    if not all(ord(c) < 128 for c in s):
        return True
    # Filter names with excessive internal whitespace (artifacts)
    if re.search(r'\s{2,}', s):
        return True
    return False


class MermaidGenerator:
    """Generate Mermaid diagrams for NVIDIA ecosystem visualization."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize Mermaid generator.

        Args:
            output_dir: Directory to save output files.
        """
        self.output_dir = output_dir or Path("output")
        self.ecosystem_names = ECOSYSTEM_NAMES
        self.ecosystem_names_cn = ECOSYSTEM_NAMES_CN

    def _sanitize_id(self, text: str) -> str:
        """Sanitize text for use as Mermaid node ID."""
        # Replace spaces and special chars with underscores
        sanitized = "".join(
            c if c.isalnum() else "_"
            for c in text
        )
        return sanitized[:30]  # Limit length

    def _sanitize_label(self, text: str) -> str:
        """Sanitize text for use as Mermaid label."""
        # Remove/escape problematic characters
        text = text.replace('"', "'")
        text = text.replace("<", "")
        text = text.replace(">", "")
        text = text.replace("[", "(")
        text = text.replace("]", ")")
        # Word-boundary-aware truncation: avoid cutting mid-word
        if len(text) > 40:
            # Find last space before position 37
            last_space = text.rfind(" ", 0, 37)
            if last_space > 0:
                text = text[:last_space] + "..."
            else:
                text = text[:37] + "..."
        return text

    def generate_ecosystem_mindmap(
        self,
        ecosystem_data: Dict[str, Any],
    ) -> str:
        """
        Generate mindmap diagram for ecosystem overview.

        Args:
            ecosystem_data: Organized ecosystem data.

        Returns:
            Mermaid mindmap syntax.
        """
        lines = ["mindmap"]
        lines.append("  root((NVIDIA Ecosystem))")
        
        eco_order = ["hardware", "software", "developer", "business", "technology"]
        
        for eco_id in eco_order:
            if eco_id not in ecosystem_data:
                continue
            
            eco_data = ecosystem_data[eco_id]
            name = self.ecosystem_names.get(eco_id, eco_id)
            count = eco_data.get("total_pages", 0)
            
            # Second level: ecosystem
            lines.append(f"    {name}")
            
            # Third level: top subcategories (noise filtered)
            subcategories = eco_data.get("subcategories", {})
            # Filter noise subcategories
            clean_subcats = [
                (k, v) for k, v in subcategories.items()
                if not _is_noise_subcategory(str(k))
            ]
            sorted_subcats = sorted(
                clean_subcats,
                key=lambda x: x[1],
                reverse=True,
            )[:5]

            for subcat, _ in sorted_subcats:
                subcat_clean = self._sanitize_label(subcat)
                lines.append(f"      {subcat_clean}")
        
        return "\n".join(lines)

    def generate_flowchart(
        self,
        ecosystem_data: Dict[str, Any],
    ) -> str:
        """
        Generate flowchart showing ecosystem relationships.

        Args:
            ecosystem_data: Organized ecosystem data.

        Returns:
            Mermaid flowchart syntax.
        """
        lines = ["flowchart TD"]
        
        # Central NVIDIA node
        lines.append('    NVIDIA["NVIDIA Platform"]')
        
        # Add ecosystem nodes
        eco_order = ["hardware", "software", "developer", "business", "technology"]
        eco_nodes = {}
        
        for eco_id in eco_order:
            if eco_id not in ecosystem_data:
                continue
            
            eco_data = ecosystem_data[eco_id]
            name = self.ecosystem_names.get(eco_id, eco_id)
            node_id = self._sanitize_id(eco_id)
            eco_nodes[eco_id] = node_id
            
            count = eco_data.get("total_pages", 0)
            lines.append(f'    {node_id}["{name}"]')
            lines.append(f"    NVIDIA --> {node_id}")
        
        # Add cross-connections based on ecosystem relationships
        connections = [
            ("hardware", "software", "powers"),
            ("software", "developer", "enables"),
            ("developer", "technology", "implements"),
            ("technology", "business", "drives"),
            ("hardware", "technology", "accelerates"),
        ]
        
        for src, dst, label in connections:
            if src in eco_nodes and dst in eco_nodes:
                lines.append(
                    f'    {eco_nodes[src]} -.->|"{label}"| {eco_nodes[dst]}'
                )
        
        return "\n".join(lines)

    @staticmethod
    def _dedupe_case_insensitive(items: List[str]) -> List[str]:
        """Deduplicate a list case-insensitively, keeping first occurrence."""
        seen: Set[str] = set()
        result: List[str] = []
        for item in items:
            key = str(item).lower()
            if key not in seen:
                seen.add(key)
                result.append(str(item))
        return result

    def generate_product_tree(
        self,
        products: Dict[str, List[str]],
    ) -> str:
        """
        Generate tree diagram for products.

        Args:
            products: Dict mapping category to product list.

        Returns:
            Mermaid mindmap syntax.
        """
        lines = ["mindmap"]
        lines.append("  root((NVIDIA Products))")
        
        for category, items in sorted(products.items()):
            if not items:
                continue

            cat_clean = self._sanitize_label(category)
            lines.append(f"    {cat_clean}")

            # Add unique products (limit to 8 per category, noise + case filtered)
            clean_items = [i for i in items if not _is_noise_name(str(i))]
            unique_items = self._dedupe_case_insensitive(clean_items)[:8]
            for item in unique_items:
                item_clean = self._sanitize_label(item)
                lines.append(f"      {item_clean}")

        return "\n".join(lines)

    def generate_technology_tree(
        self,
        technologies: Dict[str, List[str]],
    ) -> str:
        """
        Generate tree diagram for technologies.

        Args:
            technologies: Dict mapping category to technology list.

        Returns:
            Mermaid mindmap syntax.
        """
        lines = ["mindmap"]
        lines.append("  root((NVIDIA Software))")

        for category, items in sorted(technologies.items()):
            if not items:
                continue

            cat_clean = self._sanitize_label(category)
            lines.append(f"    {cat_clean}")

            clean_items = [i for i in items if not _is_noise_name(str(i))]
            unique_items = self._dedupe_case_insensitive(clean_items)[:8]
            for item in unique_items:
                item_clean = self._sanitize_label(item)
                lines.append(f"      {item_clean}")

        return "\n".join(lines)

    def generate_ecosystem_pie(
        self,
        ecosystem_data: Dict[str, Any],
    ) -> str:
        """
        Generate pie chart for ecosystem distribution.

        Args:
            ecosystem_data: Organized ecosystem data.

        Returns:
            Mermaid pie chart syntax.
        """
        lines = ['pie title "NVIDIA Ecosystem Distribution"']
        
        for eco_id, eco_data in ecosystem_data.items():
            name = self.ecosystem_names.get(eco_id, eco_id)
            count = eco_data.get("total_pages", 0)
            if count > 0:
                lines.append(f'    "{name}" : {count}')
        
        return "\n".join(lines)

    def generate_full_diagram_doc(
        self,
        classified_pages: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> str:
        """
        Generate complete Markdown document with all diagrams.

        Args:
            classified_pages: List of classified page data.
            metadata: Crawl metadata.

        Returns:
            Markdown with embedded Mermaid diagrams.
        """
        # Organize data
        ecosystem_data: Dict[str, Dict[str, Any]] = {}
        products: Dict[str, Set[str]] = defaultdict(set)
        technologies: Dict[str, Set[str]] = defaultdict(set)
        
        for eco_id in ["hardware", "software", "developer", "business", "technology"]:
            ecosystem_data[eco_id] = {
                "total_pages": 0,
                "subcategories": defaultdict(int),
            }
        
        seen_urls: Set[str] = set()
        for page in classified_pages:
            url = page.get("url", "")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            
            eco = page.get("ecosystem", "technology")
            if eco not in ecosystem_data:
                eco = "technology"
            
            ecosystem_data[eco]["total_pages"] += 1
            
            subcat = page.get("subcategory")
            if subcat:
                ecosystem_data[eco]["subcategories"][subcat] += 1
            
            for product in page.get("products", []):
                if isinstance(product, dict):
                    name = product.get("name", "")
                    category = product.get("category", "Other")
                else:
                    name = str(product)
                    category = "Other"
                if name:
                    products[category].add(name)
            
            for tech in page.get("technologies", []):
                if isinstance(tech, dict):
                    name = tech.get("name", "")
                    category = tech.get("category", "Other")
                else:
                    name = str(tech)
                    category = "Other"
                if name:
                    technologies[category].add(name)
        
        # Generate document
        lines = []
        
        lines.append("# NVIDIA Ecosystem Diagrams / NVIDIA 生态系统图表")
        lines.append("")
        lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Ecosystem mindmap
        lines.append("## Ecosystem Overview / 生态系统概览")
        lines.append("")
        lines.append("```mermaid")
        lines.append(self.generate_ecosystem_mindmap(ecosystem_data))
        lines.append("```")
        lines.append("")
        
        # Flowchart
        lines.append("## Ecosystem Relationships / 生态系统关系")
        lines.append("")
        lines.append("```mermaid")
        lines.append(self.generate_flowchart(ecosystem_data))
        lines.append("```")
        lines.append("")
        
        # Pie chart
        lines.append("## Distribution / 分布")
        lines.append("")
        lines.append("```mermaid")
        lines.append(self.generate_ecosystem_pie(ecosystem_data))
        lines.append("```")
        lines.append("")
        
        # Product tree (convert sets to sorted lists)
        if products:
            lines.append("## Product Hierarchy / 产品层级")
            lines.append("")
            lines.append("```mermaid")
            products_list = {cat: sorted(names) for cat, names in products.items()}
            lines.append(self.generate_product_tree(products_list))
            lines.append("```")
            lines.append("")
        
        # Technology tree (convert sets to sorted lists)
        if technologies:
            lines.append("## Technology Stack / 技术栈")
            lines.append("")
            lines.append("```mermaid")
            tech_list = {cat: sorted(names) for cat, names in technologies.items()}
            lines.append(self.generate_technology_tree(tech_list))
            lines.append("```")
            lines.append("")
        
        return "\n".join(lines)

    def save_diagram(
        self,
        content: str,
        filename: str = "nvidia_ecosystem_diagrams.md",
    ) -> Path:
        """
        Save diagram document to file.

        Args:
            content: Markdown content with Mermaid diagrams.
            filename: Output filename.

        Returns:
            Path to saved file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return output_path
