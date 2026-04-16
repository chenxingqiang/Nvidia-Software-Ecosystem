"""Main NVIDIA Ecosystem Crawler using crawl4ai."""
import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import (
    BROWSER_CONFIG,
    CRAWLER_CONFIG,
    OUTPUT_DIR,
    SEED_URLS,
)
from crawler.rate_limiter import RateLimiter
from crawler.url_manager import URLManager, URLItem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class PageData:
    """Data extracted from a crawled page."""
    url: str
    title: str
    description: str
    content: str
    links: List[str]
    depth: int
    parent_url: Optional[str]
    crawled_at: str
    ecosystem: Optional[str] = None
    subcategory: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


class NvidiaEcosystemCrawler:
    """Async crawler for NVIDIA ecosystem."""

    def __init__(
        self,
        max_depth: int = 5,
        max_concurrent: int = 5,
        request_delay: float = 1.5,
        max_pages: int = 10000,
        save_interval: int = 100,
        output_dir: Optional[Path] = None,
        crawl_all: bool = False,
    ):
        """
        Initialize the NVIDIA ecosystem crawler.

        Args:
            max_depth: Maximum crawl depth.
            max_concurrent: Maximum concurrent requests.
            request_delay: Delay between requests in seconds.
            max_pages: Maximum pages to crawl.
            save_interval: Save progress every N pages.
            output_dir: Directory to save output files.
            crawl_all: When True, traverse ALL sub-pages (no include-pattern filter).
        """
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.max_pages = max_pages
        self.save_interval = save_interval
        self.output_dir = output_dir or OUTPUT_DIR
        
        # Initialize components
        self.url_manager = URLManager(max_depth=max_depth, crawl_all=crawl_all)
        self.rate_limiter = RateLimiter(
            delay=request_delay,
            max_concurrent=max_concurrent,
        )
        
        # Results storage
        self.pages: List[PageData] = []
        self.crawl_metadata: Dict[str, Any] = {}
        
        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=BROWSER_CONFIG["headless"],
            verbose=False,
        )
        
        # Crawler run configuration
        self.run_config = CrawlerRunConfig(
            word_count_threshold=10,
            remove_overlay_elements=True,
            process_iframes=False,
        )

    async def crawl_page(
        self,
        crawler: AsyncWebCrawler,
        url_item: URLItem,
    ) -> Optional[PageData]:
        """
        Crawl a single page.

        Args:
            crawler: AsyncWebCrawler instance.
            url_item: URL item to crawl.

        Returns:
            PageData if successful, None otherwise.
        """
        url = url_item.url
        
        try:
            async with self.rate_limiter:
                result = await crawler.arun(
                    url=url,
                    config=self.run_config,
                )
                
                if not result.success:
                    logger.warning(f"Failed to crawl {url}: {result.error_message}")
                    self.url_manager.mark_failed(url, result.error_message or "Unknown error")
                    return None
                
                # Extract page data
                title = result.metadata.get("title", "") if result.metadata else ""
                description = result.metadata.get("description", "") if result.metadata else ""
                
                # Get clean content - ensure it's a string
                raw_content = result.markdown
                if raw_content is None:
                    content = ""
                elif isinstance(raw_content, str):
                    content = raw_content
                else:
                    # Handle MarkdownGenerationResult or other objects
                    # Try common attributes first
                    if hasattr(raw_content, 'raw_markdown'):
                        content = raw_content.raw_markdown or ""
                    elif hasattr(raw_content, 'fit_markdown'):
                        content = raw_content.fit_markdown or ""
                    elif hasattr(raw_content, 'markdown_with_citations'):
                        content = raw_content.markdown_with_citations or ""
                    else:
                        content = str(raw_content) if raw_content else ""
                
                # Ensure content is string
                if not isinstance(content, str):
                    content = str(content) if content else ""
                
                if len(content) > 50000:
                    content = content[:50000]  # Limit content size
                
                # Extract links for further crawling
                links = []
                if result.links:
                    internal_links = result.links.get("internal", [])
                    if isinstance(internal_links, list):
                        for link in internal_links:
                            if isinstance(link, dict):
                                href = link.get("href", "")
                            else:
                                href = str(link)
                            if href:
                                links.append(href)
                
                page_data = PageData(
                    url=url,
                    title=title,
                    description=description,
                    content=content,
                    links=links,
                    depth=url_item.depth,
                    parent_url=url_item.parent_url,
                    crawled_at=datetime.now().isoformat(),
                )
                
                self.url_manager.mark_visited(url)
                
                # Add discovered links to queue
                if links:
                    added = self.url_manager.add_urls(
                        links,
                        depth=url_item.depth + 1,
                        parent_url=url,
                    )
                    logger.debug(f"Added {added} new URLs from {url}")
                
                return page_data
                
        except Exception as e:
            logger.error(f"Error crawling {url}: {str(e)}")
            self.url_manager.mark_failed(url, str(e))
            return None

    async def run(self, seed_urls: Optional[List[str]] = None) -> List[PageData]:
        """
        Run the crawler.

        Args:
            seed_urls: Initial URLs to start crawling from.

        Returns:
            List of crawled page data.
        """
        seed_urls = seed_urls or SEED_URLS
        
        # Initialize seed URLs
        for url in seed_urls:
            self.url_manager.add_url(url, depth=0)
        
        logger.info(f"Starting crawl with {len(seed_urls)} seed URLs")
        logger.info(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}")
        
        start_time = time.time()
        self.crawl_metadata = {
            "start_time": datetime.now().isoformat(),
            "seed_urls": seed_urls,
            "max_depth": self.max_depth,
            "max_pages": self.max_pages,
        }
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            pages_crawled = 0
            
            while pages_crawled < self.max_pages:
                url_item = self.url_manager.get_next()
                
                if url_item is None:
                    logger.info("No more URLs to crawl")
                    break
                
                logger.info(
                    f"[{pages_crawled + 1}/{self.max_pages}] "
                    f"Crawling (depth={url_item.depth}): {url_item.url}"
                )
                
                page_data = await self.crawl_page(crawler, url_item)
                
                if page_data:
                    self.pages.append(page_data)
                    pages_crawled += 1
                    
                    # Periodic save
                    if pages_crawled % self.save_interval == 0:
                        await self.save_progress()
                        stats = self.url_manager.get_stats()
                        logger.info(
                            f"Progress: {pages_crawled} pages, "
                            f"Queue: {stats['queue_size']}, "
                            f"Discovered: {stats['discovered']}"
                        )
        
        # Final save
        elapsed = time.time() - start_time
        self.crawl_metadata.update({
            "end_time": datetime.now().isoformat(),
            "elapsed_seconds": elapsed,
            "total_pages": len(self.pages),
            "url_stats": self.url_manager.get_stats(),
        })
        
        await self.save_progress()
        
        logger.info(f"Crawl completed: {len(self.pages)} pages in {elapsed:.1f}s")
        
        return self.pages

    def _make_json_serializable(self, obj):
        """Convert object to JSON-serializable format."""
        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            # Handle objects with __dict__ - try to get useful attributes
            if hasattr(obj, 'raw_markdown'):
                return str(obj.raw_markdown) if obj.raw_markdown else ""
            elif hasattr(obj, 'fit_markdown'):
                return str(obj.fit_markdown) if obj.fit_markdown else ""
            return str(obj)
        else:
            return str(obj)

    async def save_progress(self) -> None:
        """Save current progress to files."""
        # Save raw data as JSON
        output_file = self.output_dir / "crawl_data.json"
        
        # Convert pages to dicts with JSON-serializable values
        pages_data = []
        for p in self.pages:
            page_dict = asdict(p)
            page_dict = self._make_json_serializable(page_dict)
            pages_data.append(page_dict)
        
        data = {
            "metadata": self._make_json_serializable(self.crawl_metadata),
            "pages": pages_data,
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Progress saved to {output_file}")

    def get_pages(self) -> List[PageData]:
        """Get all crawled pages."""
        return self.pages

    def get_metadata(self) -> Dict[str, Any]:
        """Get crawl metadata."""
        return self.crawl_metadata


async def main():
    """Main entry point for testing the crawler."""
    crawler = NvidiaEcosystemCrawler(
        max_depth=CRAWLER_CONFIG["max_depth"],
        max_concurrent=CRAWLER_CONFIG["max_concurrent"],
        request_delay=CRAWLER_CONFIG["request_delay"],
        max_pages=CRAWLER_CONFIG["max_pages"],
        save_interval=CRAWLER_CONFIG["save_interval"],
        crawl_all=CRAWLER_CONFIG.get("crawl_all", False),
    )
    
    pages = await crawler.run()
    print(f"Crawled {len(pages)} pages")


if __name__ == "__main__":
    asyncio.run(main())
