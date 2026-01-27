"""JSON data generator for NVIDIA ecosystem."""
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import ECOSYSTEM_NAMES, ECOSYSTEM_NAMES_CN


class JSONGenerator:
    """Generate JSON structured data for NVIDIA ecosystem."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize JSON generator.

        Args:
            output_dir: Directory to save output files.
        """
        self.output_dir = output_dir or Path("output")
        self.ecosystem_names = ECOSYSTEM_NAMES
        self.ecosystem_names_cn = ECOSYSTEM_NAMES_CN

    def generate_ecosystem_json(
        self,
        classified_pages: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate ecosystem JSON structure.

        Args:
            classified_pages: List of classified page data.
            metadata: Crawl metadata.

        Returns:
            Structured JSON data.
        """
        # Initialize ecosystem structure
        ecosystems: Dict[str, Dict[str, Any]] = {}
        
        for eco_id in ["hardware", "software", "developer", "business", "technology"]:
            ecosystems[eco_id] = {
                "name": self.ecosystem_names.get(eco_id, eco_id),
                "name_cn": self.ecosystem_names_cn.get(eco_id, eco_id),
                "total_pages": 0,
                "subcategories": {},
                "products": {},
                "technologies": {},
                "keywords": {},
                "urls": [],
            }
        
        # Process pages
        for page in classified_pages:
            eco = page.get("ecosystem", "technology")
            if eco not in ecosystems:
                eco = "technology"
            
            eco_entry = ecosystems[eco]
            eco_entry["total_pages"] += 1
            
            # Subcategory
            subcat = page.get("subcategory")
            if subcat:
                eco_entry["subcategories"][subcat] = (
                    eco_entry["subcategories"].get(subcat, 0) + 1
                )
            
            # Products
            for product in page.get("products", []):
                if isinstance(product, dict):
                    name = product.get("name", "")
                    category = product.get("category", "Other")
                else:
                    name = str(product)
                    category = "Other"
                
                if name:
                    if category not in eco_entry["products"]:
                        eco_entry["products"][category] = []
                    if name not in eco_entry["products"][category]:
                        eco_entry["products"][category].append(name)
            
            # Technologies
            for tech in page.get("technologies", []):
                if isinstance(tech, dict):
                    name = tech.get("name", "")
                    category = tech.get("category", "Other")
                else:
                    name = str(tech)
                    category = "Other"
                
                if name:
                    if category not in eco_entry["technologies"]:
                        eco_entry["technologies"][category] = []
                    if name not in eco_entry["technologies"][category]:
                        eco_entry["technologies"][category].append(name)
            
            # Keywords
            for keyword in page.get("keywords", []):
                eco_entry["keywords"][keyword] = (
                    eco_entry["keywords"].get(keyword, 0) + 1
                )
            
            # Sample URLs (limit to 20)
            url = page.get("url", "")
            if url and len(eco_entry["urls"]) < 20:
                eco_entry["urls"].append(url)
        
        # Sort keywords by count
        for eco_entry in ecosystems.values():
            eco_entry["keywords"] = dict(
                sorted(
                    eco_entry["keywords"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:30]
            )
        
        # Build final structure
        result = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "crawl_start": metadata.get("start_time"),
                "crawl_end": metadata.get("end_time"),
                "total_pages": metadata.get("total_pages", 0),
                "elapsed_seconds": metadata.get("elapsed_seconds", 0),
            },
            "summary": {
                "total_ecosystems": len(ecosystems),
                "ecosystem_distribution": {
                    eco: data["total_pages"]
                    for eco, data in ecosystems.items()
                },
            },
            "ecosystems": ecosystems,
        }
        
        return result

    def generate_product_json(
        self,
        classified_pages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate product-focused JSON.

        Args:
            classified_pages: List of classified page data.

        Returns:
            Product catalog JSON.
        """
        products: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        
        for page in classified_pages:
            for product in page.get("products", []):
                if isinstance(product, dict):
                    name = product.get("name", "")
                    category = product.get("category", "Other")
                else:
                    name = str(product)
                    category = "Other"
                
                if name:
                    products[category][name].add(page.get("url", ""))
        
        # Convert sets to lists for JSON serialization
        result = {
            "generated_at": datetime.now().isoformat(),
            "total_products": sum(
                len(prods) for prods in products.values()
            ),
            "categories": {},
        }
        
        for category, prods in sorted(products.items()):
            result["categories"][category] = {
                "count": len(prods),
                "products": [
                    {"name": name, "urls": list(urls)[:5]}
                    for name, urls in sorted(prods.items())
                ],
            }
        
        return result

    def generate_technology_json(
        self,
        classified_pages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate technology-focused JSON.

        Args:
            classified_pages: List of classified page data.

        Returns:
            Technology stack JSON.
        """
        technologies: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        
        for page in classified_pages:
            for tech in page.get("technologies", []):
                if isinstance(tech, dict):
                    name = tech.get("name", "")
                    category = tech.get("category", "Other")
                else:
                    name = str(tech)
                    category = "Other"
                
                if name:
                    technologies[category][name].add(page.get("url", ""))
        
        result = {
            "generated_at": datetime.now().isoformat(),
            "total_technologies": sum(
                len(techs) for techs in technologies.values()
            ),
            "categories": {},
        }
        
        for category, techs in sorted(technologies.items()):
            result["categories"][category] = {
                "count": len(techs),
                "technologies": [
                    {"name": name, "urls": list(urls)[:5]}
                    for name, urls in sorted(techs.items())
                ],
            }
        
        return result

    def save_json(
        self,
        data: Dict[str, Any],
        filename: str,
    ) -> Path:
        """
        Save JSON data to file.

        Args:
            data: JSON data.
            filename: Output filename.

        Returns:
            Path to saved file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path

    def generate_all(
        self,
        classified_pages: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> Dict[str, Path]:
        """
        Generate all JSON outputs.

        Args:
            classified_pages: List of classified page data.
            metadata: Crawl metadata.

        Returns:
            Dict mapping output type to file path.
        """
        outputs = {}
        
        # Main ecosystem JSON
        ecosystem_json = self.generate_ecosystem_json(classified_pages, metadata)
        outputs["ecosystem"] = self.save_json(
            ecosystem_json, "nvidia_ecosystem.json"
        )
        
        # Product catalog
        product_json = self.generate_product_json(classified_pages)
        outputs["products"] = self.save_json(
            product_json, "nvidia_products.json"
        )
        
        # Technology stack
        tech_json = self.generate_technology_json(classified_pages)
        outputs["technologies"] = self.save_json(
            tech_json, "nvidia_technologies.json"
        )
        
        return outputs
