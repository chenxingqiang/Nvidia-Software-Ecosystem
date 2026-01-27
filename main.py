#!/usr/bin/env python3
"""Main entry point for NVIDIA Ecosystem Crawler."""
import argparse
import asyncio
import json
import logging
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import CRAWLER_CONFIG, OUTPUT_DIR, SEED_URLS
from crawler.nvidia_crawler import NvidiaEcosystemCrawler, PageData
from processors.classifier import EcosystemClassifier
from processors.data_extractor import DataExtractor
from generators.markdown_gen import MarkdownGenerator
from generators.json_gen import JSONGenerator
from generators.mermaid_gen import MermaidGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(OUTPUT_DIR / "crawl.log", mode="w"),
    ],
)
logger = logging.getLogger(__name__)


class NvidiaEcosystemPipeline:
    """Complete pipeline for crawling and analyzing NVIDIA ecosystem."""

    def __init__(
        self,
        max_depth: int = 5,
        max_pages: int = 10000,
        max_concurrent: int = 5,
        request_delay: float = 1.5,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize the pipeline.

        Args:
            max_depth: Maximum crawl depth.
            max_pages: Maximum pages to crawl.
            max_concurrent: Maximum concurrent requests.
            request_delay: Delay between requests.
            output_dir: Directory for output files.
        """
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.crawler = NvidiaEcosystemCrawler(
            max_depth=max_depth,
            max_pages=max_pages,
            max_concurrent=max_concurrent,
            request_delay=request_delay,
            output_dir=self.output_dir,
        )
        self.classifier = EcosystemClassifier()
        self.extractor = DataExtractor()
        self.markdown_gen = MarkdownGenerator(self.output_dir)
        self.json_gen = JSONGenerator(self.output_dir)
        self.mermaid_gen = MermaidGenerator(self.output_dir)
        
        # Results
        self.pages: List[PageData] = []
        self.classified_pages: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    async def run_crawler(
        self,
        seed_urls: Optional[List[str]] = None,
    ) -> List[PageData]:
        """
        Run the web crawler.

        Args:
            seed_urls: Initial URLs to start crawling.

        Returns:
            List of crawled pages.
        """
        logger.info("Starting NVIDIA ecosystem crawler...")
        
        self.pages = await self.crawler.run(seed_urls or SEED_URLS)
        self.metadata = self.crawler.get_metadata()
        
        logger.info(f"Crawled {len(self.pages)} pages")
        
        return self.pages

    def classify_pages(self) -> List[Dict[str, Any]]:
        """
        Classify all crawled pages into ecosystems.

        Returns:
            List of classified page data.
        """
        logger.info("Classifying pages into ecosystems...")
        
        self.classified_pages = []
        
        for page in self.pages:
            # Ensure values are not None
            url = page.url or ""
            title = page.title or ""
            description = page.description or ""
            content = page.content or ""
            links = page.links or []
            
            # Classify
            classification = self.classifier.classify(
                url=url,
                title=title,
                description=description,
                content=content,
            )
            
            # Extract structured data
            extracted = self.extractor.extract_page(
                url=url,
                title=title,
                description=description,
                content=content,
                ecosystem=classification.ecosystem,
                subcategory=classification.subcategory,
                links=links,
            )
            
            # Combine data
            page_data = {
                "url": url,
                "title": title,
                "description": description,
                "depth": page.depth,
                "ecosystem": classification.ecosystem,
                "confidence": classification.confidence,
                "subcategory": classification.subcategory,
                "matched_patterns": classification.matched_patterns,
                "matched_keywords": classification.matched_keywords,
                "products": [asdict(p) for p in extracted.products],
                "technologies": [asdict(t) for t in extracted.technologies],
                "keywords": extracted.keywords,
            }
            
            self.classified_pages.append(page_data)
        
        # Log classification summary
        summary = self.classifier.get_summary()
        logger.info(f"Classification summary: {summary['total_pages']} pages classified")
        
        for eco, eco_data in summary["ecosystems"].items():
            logger.info(f"  {eco_data['name']}: {eco_data['total_pages']} pages")
        
        return self.classified_pages

    def generate_reports(self) -> Dict[str, Path]:
        """
        Generate all output reports.

        Returns:
            Dict mapping report type to file path.
        """
        logger.info("Generating reports...")
        outputs = {}
        
        # Markdown report
        md_content = self.markdown_gen.generate_full_report(
            self.classified_pages, self.metadata
        )
        outputs["markdown"] = self.markdown_gen.save_report(
            md_content, "nvidia_ecosystem_report.md"
        )
        logger.info(f"Generated Markdown report: {outputs['markdown']}")
        
        # JSON outputs
        json_outputs = self.json_gen.generate_all(
            self.classified_pages, self.metadata
        )
        outputs.update(json_outputs)
        for name, path in json_outputs.items():
            logger.info(f"Generated JSON {name}: {path}")
        
        # Mermaid diagrams
        mermaid_content = self.mermaid_gen.generate_full_diagram_doc(
            self.classified_pages, self.metadata
        )
        outputs["mermaid"] = self.mermaid_gen.save_diagram(
            mermaid_content, "nvidia_ecosystem_diagrams.md"
        )
        logger.info(f"Generated Mermaid diagrams: {outputs['mermaid']}")
        
        # Save classified data for reference
        classified_output = self.output_dir / "classified_pages.json"
        with open(classified_output, "w", encoding="utf-8") as f:
            json.dump(self.classified_pages, f, ensure_ascii=False, indent=2)
        outputs["classified_data"] = classified_output
        
        return outputs

    async def run_full_pipeline(
        self,
        seed_urls: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """
        Run the complete pipeline: crawl -> classify -> generate reports.

        Args:
            seed_urls: Initial URLs to start crawling.

        Returns:
            Dict mapping output type to file path.
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("NVIDIA Ecosystem Crawler - Full Pipeline")
        logger.info("=" * 60)
        
        # Step 1: Crawl
        await self.run_crawler(seed_urls)
        
        # Step 2: Classify
        self.classify_pages()
        
        # Step 3: Generate reports
        outputs = self.generate_reports()
        
        # Summary
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info("Pipeline completed!")
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Pages crawled: {len(self.pages)}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("Generated files:")
        for name, path in outputs.items():
            logger.info(f"  - {name}: {path.name}")
        logger.info("=" * 60)
        
        return outputs

    def load_existing_data(self, data_file: Path) -> bool:
        """
        Load existing crawl data from file.

        Args:
            data_file: Path to crawl_data.json file.

        Returns:
            True if data was loaded successfully.
        """
        if not data_file.exists():
            logger.warning(f"Data file not found: {data_file}")
            return False
        
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.metadata = data.get("metadata", {})
            pages_data = data.get("pages", [])
            
            # Convert to PageData objects
            self.pages = []
            for p in pages_data:
                self.pages.append(PageData(
                    url=p.get("url", ""),
                    title=p.get("title", ""),
                    description=p.get("description", ""),
                    content=p.get("content", ""),
                    links=p.get("links", []),
                    depth=p.get("depth", 0),
                    parent_url=p.get("parent_url"),
                    crawled_at=p.get("crawled_at", ""),
                ))
            
            logger.info(f"Loaded {len(self.pages)} pages from {data_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False

    def process_existing_data(self) -> Dict[str, Path]:
        """
        Process already crawled data and generate reports.

        Returns:
            Dict mapping output type to file path.
        """
        if not self.pages:
            logger.error("No pages to process. Load or crawl data first.")
            return {}
        
        self.classify_pages()
        return self.generate_reports()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="NVIDIA Ecosystem Crawler - Crawl and analyze NVIDIA's ecosystem"
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=CRAWLER_CONFIG["max_depth"],
        help="Maximum crawl depth (default: %(default)s)",
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=CRAWLER_CONFIG["max_pages"],
        help="Maximum pages to crawl (default: %(default)s)",
    )
    
    parser.add_argument(
        "--concurrent",
        type=int,
        default=CRAWLER_CONFIG["max_concurrent"],
        help="Maximum concurrent requests (default: %(default)s)",
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=CRAWLER_CONFIG["request_delay"],
        help="Delay between requests in seconds (default: %(default)s)",
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory (default: %(default)s)",
    )
    
    parser.add_argument(
        "--load-data",
        type=Path,
        help="Load existing crawl data from file instead of crawling",
    )
    
    parser.add_argument(
        "--seed-urls",
        type=str,
        nargs="+",
        help="Custom seed URLs to start crawling",
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Update file handler path
    for handler in logging.root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logging.root.removeHandler(handler)
    
    file_handler = logging.FileHandler(args.output_dir / "crawl.log", mode="w")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.root.addHandler(file_handler)
    
    pipeline = NvidiaEcosystemPipeline(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        max_concurrent=args.concurrent,
        request_delay=args.delay,
        output_dir=args.output_dir,
    )
    
    if args.load_data:
        # Process existing data
        if pipeline.load_existing_data(args.load_data):
            outputs = pipeline.process_existing_data()
        else:
            logger.error("Failed to load existing data")
            sys.exit(1)
    else:
        # Run full pipeline
        outputs = await pipeline.run_full_pipeline(args.seed_urls)
    
    # Print output locations
    print("\nGenerated files:")
    for name, path in outputs.items():
        print(f"  {name}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
