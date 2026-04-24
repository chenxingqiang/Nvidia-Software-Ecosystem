"""Ecosystem classifier for categorizing NVIDIA pages."""
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import sys
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])
from config import ECOSYSTEM_PATTERNS, ECOSYSTEM_NAMES, ECOSYSTEM_NAMES_CN


@dataclass
class ClassificationResult:
    """Result of ecosystem classification."""
    ecosystem: str
    confidence: float
    subcategory: Optional[str] = None
    matched_patterns: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)


@dataclass
class EcosystemStats:
    """Statistics for an ecosystem category."""
    total_pages: int = 0
    subcategories: Dict[str, int] = field(default_factory=dict)
    top_keywords: List[Tuple[str, int]] = field(default_factory=list)
    sample_urls: List[str] = field(default_factory=list)


class EcosystemClassifier:
    """Classifier for categorizing pages into NVIDIA ecosystems."""

    def __init__(self, patterns: Optional[Dict] = None):
        """
        Initialize classifier.

        Args:
            patterns: Custom ecosystem patterns. Uses default if not provided.
        """
        self.patterns = patterns or ECOSYSTEM_PATTERNS
        self.ecosystem_names = ECOSYSTEM_NAMES
        self.ecosystem_names_cn = ECOSYSTEM_NAMES_CN
        
        # Compile regex patterns for efficiency
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        self._compile_patterns()
        
        # Statistics
        self.stats: Dict[str, EcosystemStats] = {
            eco: EcosystemStats() for eco in self.patterns
        }
        self._keyword_counts: Dict[str, Counter] = {
            eco: Counter() for eco in self.patterns
        }

    def _compile_patterns(self) -> None:
        """Compile URL patterns to regex for faster matching."""
        for ecosystem, config in self.patterns.items():
            patterns = []
            for pattern in config.get("url_patterns", []):
                # Escape special regex chars except *
                escaped = re.escape(pattern).replace(r"\*", ".*")
                patterns.append(re.compile(escaped, re.IGNORECASE))
            self._compiled_patterns[ecosystem] = patterns

    def _score_url(self, url: str, ecosystem: str) -> float:
        """
        Score URL match for an ecosystem.

        Args:
            url: URL to score.
            ecosystem: Ecosystem to match against.

        Returns:
            Match score (0.0 to 1.0).
        """
        patterns = self._compiled_patterns.get(ecosystem, [])
        
        for pattern in patterns:
            if pattern.search(url):
                return 1.0
        
        return 0.0

    def _score_content(
        self,
        title: str,
        description: str,
        content: str,
        ecosystem: str,
    ) -> Tuple[float, List[str]]:
        """
        Score content match for an ecosystem.

        Args:
            title: Page title.
            description: Page description.
            content: Page content.
            ecosystem: Ecosystem to match against.

        Returns:
            Tuple of (score, matched_keywords).
        """
        keywords = self.patterns.get(ecosystem, {}).get("keywords", [])
        if not keywords:
            return 0.0, []
        
        # Ensure inputs are strings (handle None values)
        title = title or ""
        description = description or ""
        content = content or ""
        
        # Combine all text, weighted by importance
        content_slice = content[:5000] if len(content) > 5000 else content
        combined = f"{title} {title} {description} {content_slice}".lower()
        
        matched = []
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in combined:
                matched.append(keyword)
        
        if not matched:
            return 0.0, []
        
        # Score based on number of matches and keyword importance
        score = min(len(matched) / 5.0, 1.0)  # Cap at 1.0
        
        # Boost score if keyword is in title
        title_lower = title.lower()
        for keyword in matched[:3]:
            if keyword.lower() in title_lower:
                score = min(score + 0.2, 1.0)
        
        return score, matched

    def classify(
        self,
        url: str,
        title: str = "",
        description: str = "",
        content: str = "",
    ) -> ClassificationResult:
        """
        Classify a page into an ecosystem.

        Args:
            url: Page URL.
            title: Page title.
            description: Page description.
            content: Page content (markdown or text).

        Returns:
            ClassificationResult with ecosystem and confidence.
        """
        # Ensure all inputs are strings (handle None values)
        url = url or ""
        title = title or ""
        description = description or ""
        content = content or ""
        
        scores: Dict[str, Dict[str, Any]] = {}
        
        for ecosystem in self.patterns:
            url_score = self._score_url(url, ecosystem)
            content_score, matched_keywords = self._score_content(
                title, description, content, ecosystem
            )
            
            # Combined score (URL patterns weighted more heavily)
            combined = url_score * 0.6 + content_score * 0.4
            
            scores[ecosystem] = {
                "score": combined,
                "url_score": url_score,
                "content_score": content_score,
                "matched_keywords": matched_keywords,
            }
        
        # Find best match
        best_ecosystem = max(scores, key=lambda e: scores[e]["score"])
        best_data = scores[best_ecosystem]
        
        # Determine subcategory based on URL path
        subcategory = self._extract_subcategory(url, best_ecosystem)
        
        # Get matched URL patterns
        matched_patterns = []
        for pattern in self.patterns.get(best_ecosystem, {}).get("url_patterns", []):
            if pattern.lower() in url.lower():
                matched_patterns.append(pattern)
        
        result = ClassificationResult(
            ecosystem=best_ecosystem,
            confidence=best_data["score"],
            subcategory=subcategory,
            matched_patterns=matched_patterns,
            matched_keywords=best_data["matched_keywords"],
        )
        
        # Update statistics
        self._update_stats(url, result)
        
        return result

    def _extract_subcategory(self, url: str, ecosystem: str) -> Optional[str]:
        """
        Extract subcategory from URL.

        Args:
            url: Page URL.
            ecosystem: Classified ecosystem.

        Returns:
            Subcategory string or None.
        """
        parsed = urlparse(url)
        skip_locales = frozenset({
            "en-us", "zh-cn", "zh-tw",
            "en-gb", "en-au", "en-in", "en-sg", "en-eu",
            "es-la", "es-mx", "fr-ca", "fr-be", "pt-pt",
            "sv-se", "nb-no", "da-dk", "tr-tr", "pl-pl",
            "nl-nl", "nl-be", "fi-fi", "cs-cz", "ro-ro",
        })
        path_parts = [p for p in parsed.path.split("/") if p and p not in skip_locales]
        
        if len(path_parts) >= 1:
            # Return first meaningful path segment as subcategory
            subcategory = path_parts[0].replace("-", " ").title()
            return subcategory
        
        return None

    def _update_stats(self, url: str, result: ClassificationResult) -> None:
        """Update classification statistics."""
        stats = self.stats[result.ecosystem]
        stats.total_pages += 1
        
        if result.subcategory:
            stats.subcategories[result.subcategory] = (
                stats.subcategories.get(result.subcategory, 0) + 1
            )
        
        # Track keywords
        for keyword in result.matched_keywords:
            self._keyword_counts[result.ecosystem][keyword] += 1
        
        # Keep sample URLs (max 10)
        if len(stats.sample_urls) < 10:
            stats.sample_urls.append(url)

    def get_stats(self) -> Dict[str, EcosystemStats]:
        """
        Get classification statistics.

        Returns:
            Dict mapping ecosystem names to stats.
        """
        # Update top keywords before returning
        for ecosystem, counter in self._keyword_counts.items():
            self.stats[ecosystem].top_keywords = counter.most_common(20)
        
        return self.stats

    def get_summary(self) -> Dict[str, Any]:
        """
        Get classification summary.

        Returns:
            Summary dict with ecosystem breakdowns.
        """
        stats = self.get_stats()
        
        summary = {
            "total_pages": sum(s.total_pages for s in stats.values()),
            "ecosystems": {},
        }
        
        for ecosystem, eco_stats in stats.items():
            summary["ecosystems"][ecosystem] = {
                "name": self.ecosystem_names.get(ecosystem, ecosystem),
                "name_cn": self.ecosystem_names_cn.get(ecosystem, ecosystem),
                "total_pages": eco_stats.total_pages,
                "subcategories": dict(
                    sorted(
                        eco_stats.subcategories.items(),
                        key=lambda x: x[1],
                        reverse=True,
                    )[:20]
                ),
                "top_keywords": eco_stats.top_keywords[:10],
                "sample_urls": eco_stats.sample_urls[:5],
            }
        
        return summary

    def classify_batch(
        self,
        pages: List[Dict[str, Any]],
    ) -> List[Tuple[Dict[str, Any], ClassificationResult]]:
        """
        Classify a batch of pages.

        Args:
            pages: List of page dicts with url, title, description, content.

        Returns:
            List of (page, classification) tuples.
        """
        results = []
        
        for page in pages:
            classification = self.classify(
                url=page.get("url", ""),
                title=page.get("title", ""),
                description=page.get("description", ""),
                content=page.get("content", ""),
            )
            results.append((page, classification))
        
        return results
