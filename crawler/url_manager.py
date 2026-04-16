"""URL Manager for handling URL queue, deduplication, and filtering."""
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urlunparse

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import (
    ALLOWED_DOMAINS,
    URL_EXCLUDE_PATTERNS,
    URL_INCLUDE_PATTERNS,
)


@dataclass
class URLItem:
    """Represents a URL item in the queue."""
    url: str
    depth: int
    parent_url: Optional[str] = None
    discovered_at: float = 0


class URLManager:
    """Manages URL queue, deduplication, and filtering."""

    def __init__(
        self,
        max_depth: int = 5,
        allowed_domains: Optional[Set[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        crawl_all: bool = False,
    ):
        """
        Initialize URL manager.

        Args:
            max_depth: Maximum crawl depth.
            allowed_domains: Set of allowed domains.
            include_patterns: URL patterns to include.
            exclude_patterns: URL patterns to exclude.
            crawl_all: When True, skip include-pattern filtering and
                       traverse ALL sub-pages under allowed domains.
        """
        self.max_depth = max_depth
        self.allowed_domains = allowed_domains or ALLOWED_DOMAINS
        self.include_patterns = include_patterns or URL_INCLUDE_PATTERNS
        self.exclude_patterns = exclude_patterns or URL_EXCLUDE_PATTERNS
        self.crawl_all = crawl_all
        
        self._queue: Deque[URLItem] = deque()
        self._visited: Set[str] = set()
        self._discovered: Set[str] = set()
        self._failed: Dict[str, str] = {}  # url -> error message

    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and trailing slashes.

        Args:
            url: URL to normalize.

        Returns:
            Normalized URL string.
        """
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/") if parsed.path != "/" else "/",
            parsed.params,
            parsed.query,
            "",  # Remove fragment
        ))
        return normalized

    def is_valid_url(self, url: str) -> bool:
        """
        Check if URL is valid for crawling.

        Args:
            url: URL to validate.

        Returns:
            True if URL should be crawled.
        """
        try:
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must be http or https
            if parsed.scheme not in ("http", "https"):
                return False
            
            # Check domain
            domain = parsed.netloc.lower()
            if not any(domain.endswith(d) for d in self.allowed_domains):
                return False
            
            # Check exclude patterns
            url_lower = url.lower()
            for pattern in self.exclude_patterns:
                if pattern.lower() in url_lower:
                    return False
            
            return True
            
        except Exception:
            return False

    def should_include(self, url: str) -> bool:
        """
        Check if URL matches include patterns or is a base page.

        Args:
            url: URL to check.

        Returns:
            True if URL should be included.
        """
        # When crawl_all is enabled, include every valid URL under
        # allowed domains (is_valid_url already handles domain and
        # exclude-pattern checks).
        if self.crawl_all:
            return True

        url_lower = url.lower()
        
        # Always include main pages
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Include root and main locale entry paths
        if path in (
            "/",
            "/en-us/",
            "/en-us",
            "/zh-cn/",
            "/zh-cn",
            "/zh-tw/",
            "/zh-tw",
        ):
            return True
        
        # Check include patterns
        for pattern in self.include_patterns:
            if pattern.lower() in url_lower:
                return True
        
        # Include pages that are direct children of main site
        path_parts = [p for p in path.split("/") if p]
        if len(path_parts) <= 2:
            return True
        
        return False

    def add_url(
        self,
        url: str,
        depth: int,
        parent_url: Optional[str] = None,
    ) -> bool:
        """
        Add URL to queue if valid and not seen before.

        Args:
            url: URL to add.
            depth: Current crawl depth.
            parent_url: Parent URL that discovered this URL.

        Returns:
            True if URL was added to queue.
        """
        if depth > self.max_depth:
            return False
        
        normalized = self.normalize_url(url)
        
        if normalized in self._discovered:
            return False
        
        if not self.is_valid_url(normalized):
            return False
        
        if not self.should_include(normalized):
            return False
        
        self._discovered.add(normalized)
        
        import time
        item = URLItem(
            url=normalized,
            depth=depth,
            parent_url=parent_url,
            discovered_at=time.time(),
        )
        self._queue.append(item)
        return True

    def add_urls(
        self,
        urls: List[str],
        depth: int,
        parent_url: Optional[str] = None,
    ) -> int:
        """
        Add multiple URLs to queue.

        Args:
            urls: List of URLs to add.
            depth: Current crawl depth.
            parent_url: Parent URL.

        Returns:
            Number of URLs added.
        """
        added = 0
        for url in urls:
            if self.add_url(url, depth, parent_url):
                added += 1
        return added

    def get_next(self) -> Optional[URLItem]:
        """
        Get next URL from queue.

        Returns:
            Next URLItem or None if queue is empty.
        """
        while self._queue:
            item = self._queue.popleft()
            if item.url not in self._visited:
                return item
        return None

    def mark_visited(self, url: str) -> None:
        """Mark URL as visited."""
        normalized = self.normalize_url(url)
        self._visited.add(normalized)

    def mark_failed(self, url: str, error: str) -> None:
        """Mark URL as failed with error message."""
        normalized = self.normalize_url(url)
        self._visited.add(normalized)
        self._failed[normalized] = error

    def is_visited(self, url: str) -> bool:
        """Check if URL has been visited."""
        return self.normalize_url(url) in self._visited

    def extract_links(self, base_url: str, html_content: str) -> List[str]:
        """
        Extract all links from HTML content.

        Args:
            base_url: Base URL for resolving relative links.
            html_content: HTML content to parse.

        Returns:
            List of absolute URLs.
        """
        links = []
        
        # Find all href attributes
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        
        for match in href_pattern.finditer(html_content):
            href = match.group(1)
            
            # Skip javascript, mailto, tel links
            if href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue
            
            # Convert relative to absolute
            absolute_url = urljoin(base_url, href)
            links.append(absolute_url)
        
        return links

    @property
    def queue_size(self) -> int:
        """Get current queue size."""
        return len(self._queue)

    @property
    def visited_count(self) -> int:
        """Get number of visited URLs."""
        return len(self._visited)

    @property
    def discovered_count(self) -> int:
        """Get number of discovered URLs."""
        return len(self._discovered)

    @property
    def failed_count(self) -> int:
        """Get number of failed URLs."""
        return len(self._failed)

    def get_stats(self) -> Dict[str, int]:
        """Get URL manager statistics."""
        return {
            "queue_size": self.queue_size,
            "visited": self.visited_count,
            "discovered": self.discovered_count,
            "failed": self.failed_count,
        }
