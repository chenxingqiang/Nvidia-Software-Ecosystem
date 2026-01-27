#!/usr/bin/env python3
"""Specialized crawler for extracting all PDF documents from NVIDIA website."""
import asyncio
import aiohttp
import json
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, unquote

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import BROWSER_CONFIG, OUTPUT_DIR, SEED_URLS
from crawler.rate_limiter import RateLimiter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class PDFDocument:
    """Represents a discovered PDF document."""
    url: str
    filename: str
    title: str
    source_page: str
    category: str
    file_size: Optional[int] = None
    discovered_at: str = ""
    downloaded: bool = False
    local_path: Optional[str] = None


class NvidiaPDFCrawler:
    """Specialized crawler for extracting PDF documents from NVIDIA website."""

    # PDF-rich seed URLs
    PDF_SEED_URLS = [
        "https://www.nvidia.com/en-us/",
        "https://www.nvidia.com/en-us/data-center/",
        "https://www.nvidia.com/en-us/geforce/",
        "https://www.nvidia.com/en-us/deep-learning-ai/",
        "https://developer.nvidia.com/",
        "https://developer.nvidia.com/cuda-downloads",
        "https://developer.nvidia.com/cudnn",
        "https://developer.nvidia.com/tensorrt",
        "https://www.nvidia.com/en-us/autonomous-machines/",
        "https://www.nvidia.com/en-us/self-driving-cars/",
        "https://www.nvidia.com/en-us/high-performance-computing/",
        "https://www.nvidia.com/en-us/design-visualization/",
        "https://www.nvidia.com/en-us/industries/",
        "https://www.nvidia.com/en-us/solutions/",
        "https://www.nvidia.com/en-us/networking/",
        "https://resources.nvidia.com/",
        "https://www.nvidia.com/content/dam/",
        "https://images.nvidia.com/",
    ]

    # Patterns to identify PDF links
    PDF_PATTERNS = [
        r'href=["\']([^"\']*\.pdf)["\']',
        r'href=["\']([^"\']*\.PDF)["\']',
        r'data-pdf=["\']([^"\']+)["\']',
        r'download=["\']([^"\']*\.pdf)["\']',
    ]

    # Categories based on URL patterns
    CATEGORY_PATTERNS = {
        "whitepaper": ["whitepaper", "white-paper", "wp-"],
        "datasheet": ["datasheet", "data-sheet", "spec", "specification"],
        "guide": ["guide", "manual", "handbook", "tutorial"],
        "technical": ["technical", "tech-brief", "architecture"],
        "solution": ["solution", "case-study", "success-story"],
        "product": ["product", "brochure", "overview"],
        "developer": ["developer", "programming", "sdk", "api"],
        "research": ["research", "paper", "publication"],
    }

    def __init__(
        self,
        max_depth: int = 4,
        max_pages: int = 5000,
        max_concurrent: int = 5,
        request_delay: float = 1.5,
        download_pdfs: bool = False,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize PDF crawler.

        Args:
            max_depth: Maximum crawl depth.
            max_pages: Maximum pages to crawl.
            max_concurrent: Maximum concurrent requests.
            request_delay: Delay between requests.
            download_pdfs: Whether to download PDFs.
            output_dir: Output directory.
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.download_pdfs = download_pdfs
        self.output_dir = output_dir or OUTPUT_DIR
        self.pdf_dir = self.output_dir / "pdfs"
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            delay=request_delay,
            max_concurrent=max_concurrent,
        )
        
        # Browser config
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
        )
        
        # Crawler config
        self.run_config = CrawlerRunConfig(
            word_count_threshold=10,
            remove_overlay_elements=True,
        )
        
        # Storage
        self.discovered_pdfs: Dict[str, PDFDocument] = {}
        self.visited_pages: Set[str] = set()
        self.page_queue: List[tuple] = []  # (url, depth)
        self.metadata: Dict[str, Any] = {}
        
        # Compile regex patterns
        self._pdf_regex = [re.compile(p, re.IGNORECASE) for p in self.PDF_PATTERNS]

    def _normalize_url(self, url: str) -> str:
        """Normalize URL."""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.rstrip("/")

    def _is_nvidia_domain(self, url: str) -> bool:
        """Check if URL is from NVIDIA domain."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(d in domain for d in [
            "nvidia.com", "nvidia.cn", "nvidianews.nvidia.com"
        ])

    def _extract_pdf_links(self, html: str, base_url: str) -> List[str]:
        """Extract PDF links from HTML content."""
        pdf_urls = set()
        
        for regex in self._pdf_regex:
            matches = regex.findall(html)
            for match in matches:
                # Convert relative to absolute URL
                absolute_url = urljoin(base_url, match)
                
                # Only include NVIDIA PDFs
                if self._is_nvidia_domain(absolute_url):
                    pdf_urls.add(absolute_url)
        
        # Also look for common PDF URL patterns
        pdf_pattern = re.compile(
            r'https?://[^\s"\'<>]*nvidia[^\s"\'<>]*\.pdf',
            re.IGNORECASE
        )
        for match in pdf_pattern.findall(html):
            pdf_urls.add(match)
        
        return list(pdf_urls)

    def _extract_page_links(self, html: str, base_url: str) -> List[str]:
        """Extract page links for further crawling."""
        links = set()
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        
        for match in href_pattern.findall(html):
            if match.startswith("#") or match.startswith("javascript:"):
                continue
            if match.lower().endswith(".pdf"):
                continue
            
            absolute_url = urljoin(base_url, match)
            
            if self._is_nvidia_domain(absolute_url):
                # Filter out unwanted pages
                url_lower = absolute_url.lower()
                if any(x in url_lower for x in [
                    "/login", "/signin", "/cart", "/checkout",
                    ".jpg", ".png", ".gif", ".mp4", ".zip",
                    "/zh-cn/", "/zh-tw/", "/ja-jp/", "/ko-kr/",
                ]):
                    continue
                links.add(self._normalize_url(absolute_url))
        
        return list(links)

    def _categorize_pdf(self, url: str, title: str) -> str:
        """Categorize PDF based on URL and title."""
        combined = f"{url} {title}".lower()
        
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in combined:
                    return category
        
        return "other"

    def _extract_filename(self, url: str) -> str:
        """Extract filename from PDF URL."""
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path)
        
        if not filename or not filename.lower().endswith(".pdf"):
            # Generate filename from URL
            clean_path = path.replace("/", "_").strip("_")
            filename = f"{clean_path}.pdf" if clean_path else "document.pdf"
        
        return filename

    def _extract_title(self, url: str, html: str = "") -> str:
        """Extract title for PDF from context."""
        filename = self._extract_filename(url)
        # Clean up filename as title
        title = filename.replace(".pdf", "").replace("-", " ").replace("_", " ")
        title = " ".join(word.capitalize() for word in title.split())
        return title

    async def _crawl_page(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        depth: int,
    ) -> tuple:
        """
        Crawl a page and extract PDF links.

        Returns:
            Tuple of (pdf_urls, page_links)
        """
        try:
            async with self.rate_limiter:
                result = await crawler.arun(url=url, config=self.run_config)
                
                if not result.success:
                    logger.warning(f"Failed to crawl {url}")
                    return [], []
                
                # Get HTML content
                html = result.html or ""
                
                # Extract PDF links
                pdf_urls = self._extract_pdf_links(html, url)
                
                # Extract page links for further crawling
                page_links = []
                if depth < self.max_depth:
                    page_links = self._extract_page_links(html, url)
                
                return pdf_urls, page_links
                
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return [], []

    async def _get_pdf_size(self, session: aiohttp.ClientSession, url: str) -> Optional[int]:
        """Get PDF file size via HEAD request."""
        try:
            async with session.head(url, timeout=10) as response:
                if response.status == 200:
                    content_length = response.headers.get("Content-Length")
                    if content_length:
                        return int(content_length)
        except Exception:
            pass
        return None

    async def _download_pdf(
        self,
        session: aiohttp.ClientSession,
        pdf: PDFDocument,
    ) -> bool:
        """Download a PDF file."""
        try:
            # Create category directory
            category_dir = self.pdf_dir / pdf.category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique filename
            local_path = category_dir / pdf.filename
            counter = 1
            while local_path.exists():
                name, ext = os.path.splitext(pdf.filename)
                local_path = category_dir / f"{name}_{counter}{ext}"
                counter += 1
            
            async with session.get(pdf.url, timeout=60) as response:
                if response.status == 200:
                    with open(local_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    pdf.downloaded = True
                    pdf.local_path = str(local_path)
                    pdf.file_size = local_path.stat().st_size
                    logger.info(f"Downloaded: {pdf.filename}")
                    return True
                    
        except Exception as e:
            logger.error(f"Failed to download {pdf.url}: {e}")
        
        return False

    async def run(
        self,
        seed_urls: Optional[List[str]] = None,
    ) -> Dict[str, PDFDocument]:
        """
        Run the PDF crawler.

        Args:
            seed_urls: Initial URLs to start crawling.

        Returns:
            Dict of discovered PDFs.
        """
        seed_urls = seed_urls or self.PDF_SEED_URLS
        
        # Initialize queue
        for url in seed_urls:
            self.page_queue.append((url, 0))
        
        logger.info(f"Starting PDF crawler with {len(seed_urls)} seed URLs")
        logger.info(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        start_time = time.time()
        self.metadata = {
            "start_time": datetime.now().isoformat(),
            "seed_urls": seed_urls,
            "max_depth": self.max_depth,
            "download_pdfs": self.download_pdfs,
        }
        
        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.download_pdfs:
            self.pdf_dir.mkdir(parents=True, exist_ok=True)
        
        pages_crawled = 0
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            while self.page_queue and pages_crawled < self.max_pages:
                url, depth = self.page_queue.pop(0)
                
                normalized_url = self._normalize_url(url)
                if normalized_url in self.visited_pages:
                    continue
                
                self.visited_pages.add(normalized_url)
                pages_crawled += 1
                
                logger.info(
                    f"[{pages_crawled}/{self.max_pages}] "
                    f"Depth={depth} PDFs={len(self.discovered_pdfs)} "
                    f"Crawling: {url[:80]}..."
                )
                
                pdf_urls, page_links = await self._crawl_page(crawler, url, depth)
                
                # Process discovered PDFs
                for pdf_url in pdf_urls:
                    if pdf_url not in self.discovered_pdfs:
                        pdf_doc = PDFDocument(
                            url=pdf_url,
                            filename=self._extract_filename(pdf_url),
                            title=self._extract_title(pdf_url),
                            source_page=url,
                            category=self._categorize_pdf(pdf_url, ""),
                            discovered_at=datetime.now().isoformat(),
                        )
                        self.discovered_pdfs[pdf_url] = pdf_doc
                        logger.info(f"  Found PDF: {pdf_doc.filename}")
                
                # Add new pages to queue
                for link in page_links:
                    if link not in self.visited_pages:
                        self.page_queue.append((link, depth + 1))
                
                # Save progress periodically
                if pages_crawled % 50 == 0:
                    await self._save_progress()
        
        # Get PDF sizes and optionally download
        if self.discovered_pdfs:
            logger.info(f"Processing {len(self.discovered_pdfs)} discovered PDFs...")
            
            async with aiohttp.ClientSession() as session:
                for pdf in self.discovered_pdfs.values():
                    # Get file size
                    pdf.file_size = await self._get_pdf_size(session, pdf.url)
                    
                    # Download if requested
                    if self.download_pdfs:
                        await self._download_pdf(session, pdf)
                        await asyncio.sleep(0.5)  # Rate limit downloads
        
        # Final save
        elapsed = time.time() - start_time
        self.metadata.update({
            "end_time": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "pages_crawled": pages_crawled,
            "pdfs_found": len(self.discovered_pdfs),
        })
        
        await self._save_progress()
        
        logger.info(f"PDF crawl completed: {len(self.discovered_pdfs)} PDFs found in {elapsed:.1f}s")
        
        return self.discovered_pdfs

    async def _save_progress(self) -> None:
        """Save current progress."""
        # Save PDF catalog
        catalog_file = self.output_dir / "nvidia_pdf_catalog.json"
        
        # Organize by category
        by_category = defaultdict(list)
        for pdf in self.discovered_pdfs.values():
            by_category[pdf.category].append(asdict(pdf))
        
        data = {
            "metadata": self.metadata,
            "summary": {
                "total_pdfs": len(self.discovered_pdfs),
                "by_category": {cat: len(pdfs) for cat, pdfs in by_category.items()},
            },
            "pdfs_by_category": dict(by_category),
            "all_pdfs": [asdict(pdf) for pdf in self.discovered_pdfs.values()],
        }
        
        with open(catalog_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save simple URL list
        url_list_file = self.output_dir / "nvidia_pdf_urls.txt"
        with open(url_list_file, "w", encoding="utf-8") as f:
            for url in sorted(self.discovered_pdfs.keys()):
                f.write(f"{url}\n")
        
        # Save markdown report
        report_file = self.output_dir / "nvidia_pdf_report.md"
        self._generate_report(report_file, by_category)
        
        logger.info(f"Progress saved to {self.output_dir}")

    def _generate_report(
        self,
        output_file: Path,
        by_category: Dict[str, List[Dict]],
    ) -> None:
        """Generate markdown report."""
        lines = []
        
        lines.append("# NVIDIA PDF Document Catalog")
        lines.append("")
        lines.append(f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"> Total PDFs: {len(self.discovered_pdfs)}")
        lines.append("")
        
        # Summary table
        lines.append("## Summary by Category")
        lines.append("")
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        
        for category in sorted(by_category.keys()):
            count = len(by_category[category])
            lines.append(f"| {category.title()} | {count} |")
        
        lines.append("")
        
        # PDFs by category
        for category in sorted(by_category.keys()):
            pdfs = by_category[category]
            lines.append(f"## {category.title()} ({len(pdfs)} documents)")
            lines.append("")
            
            for pdf in pdfs[:50]:  # Limit to 50 per category
                filename = pdf.get("filename", "Unknown")
                url = pdf.get("url", "")
                size = pdf.get("file_size")
                size_str = f" ({size / 1024 / 1024:.1f} MB)" if size else ""
                
                lines.append(f"- [{filename}]({url}){size_str}")
            
            if len(pdfs) > 50:
                lines.append(f"- ... and {len(pdfs) - 50} more")
            
            lines.append("")
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="NVIDIA PDF Crawler")
    parser.add_argument("--max-depth", type=int, default=4, help="Max crawl depth")
    parser.add_argument("--max-pages", type=int, default=2000, help="Max pages to crawl")
    parser.add_argument("--concurrent", type=int, default=5, help="Concurrent requests")
    parser.add_argument("--delay", type=float, default=1.5, help="Request delay")
    parser.add_argument("--download", action="store_true", help="Download PDFs")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="Output directory")
    
    args = parser.parse_args()
    
    crawler = NvidiaPDFCrawler(
        max_depth=args.max_depth,
        max_pages=args.max_pages,
        max_concurrent=args.concurrent,
        request_delay=args.delay,
        download_pdfs=args.download,
        output_dir=args.output_dir,
    )
    
    pdfs = await crawler.run()
    
    print(f"\nFound {len(pdfs)} PDF documents")
    print(f"Results saved to: {args.output_dir}")
    print(f"  - nvidia_pdf_catalog.json")
    print(f"  - nvidia_pdf_urls.txt")
    print(f"  - nvidia_pdf_report.md")


if __name__ == "__main__":
    asyncio.run(main())
