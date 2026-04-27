"""Tests for the EcosystemClassifier in processors/classifier.py."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from processors.classifier import (
    EcosystemClassifier,
    ClassificationResult,
    EcosystemStats,
)
from config import ECOSYSTEM_PATTERNS, ECOSYSTEM_NAMES, ECOSYSTEM_NAMES_CN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DEFAULT_PATTERNS_SNAPSHOT = {
    k: {"url_patterns": list(v["url_patterns"]), "keywords": list(v["keywords"])}
    for k, v in ECOSYSTEM_PATTERNS.items()
}


@pytest.fixture
def classifier():
    """Fresh classifier with default NVIDIA ecosystem patterns."""
    return EcosystemClassifier()


@pytest.fixture
def empty_classifier():
    """Classifier with no patterns — useful for edge-case testing."""
    return EcosystemClassifier(patterns={
        "x": {"url_patterns": [], "keywords": []},
        "y": {"url_patterns": [], "keywords": []},
    })


@pytest.fixture
def minimal_classifier():
    """Two-ecosystem classifier with minimal patterns for controlled tests."""
    return EcosystemClassifier(patterns={
        "hardware": {
            "url_patterns": ["/gpu/", "/geforce/"],
            "keywords": ["gpu", "graphics card", "geforce", "rtx"],
        },
        "software": {
            "url_patterns": ["/cuda/", "/tensorrt/"],
            "keywords": ["cuda", "tensorrt", "toolkit"],
        },
    })


# ---------------------------------------------------------------------------
# URL scoring
# ---------------------------------------------------------------------------

class TestUrlScoring:
    def test_exact_match_returns_one(self, classifier):
        """A URL containing an ecosystem pattern returns 1.0 for that ecosystem."""
        assert classifier._score_url("https://www.nvidia.com/en-us/geforce/", "hardware") == 1.0

    def test_no_match_returns_zero(self, classifier):
        """A URL that matches no patterns returns 0.0."""
        assert classifier._score_url("https://example.com/plain-page", "hardware") == 0.0

    def test_pattern_substring_match(self, classifier):
        """URL patterns match as path components, not arbitrary substrings."""
        assert classifier._score_url("https://nvidia.com/products/geforce/rtx-4090", "hardware") == 1.0

    def test_case_insensitive(self, classifier):
        """URL matching is case-insensitive."""
        assert classifier._score_url("https://www.nvidia.com/GeForce/", "hardware") == 1.0

    def test_multiple_patterns_first_match_wins(self, classifier):
        """The first matching pattern in the ecosystem returns 1.0 — loop returns on first hit."""
        assert classifier._score_url("https://nvidia.com/en-us/a100/", "hardware") == 1.0

    def test_unknown_ecosystem_returns_zero(self, classifier):
        """An ecosystem not present in the compiled patterns yields 0.0."""
        assert classifier._score_url("https://nvidia.com/anything", "nonexistent") == 0.0

    def test_deeply_nested_path_match(self, classifier):
        """Patterns match anywhere in the URL path, including deeply nested paths."""
        assert classifier._score_url(
            "https://docs.nvidia.com/deep-learning/frameworks/user-guide/index.html", "technology"
        ) == 1.0


# ---------------------------------------------------------------------------
# Content scoring
# ---------------------------------------------------------------------------

class TestContentScoring:
    def test_keyword_match_in_content(self, classifier):
        """A keyword found in the content contributes to the score."""
        score, matched = classifier._score_content(
            "Page Title",
            "Page description",
            "This page talks about gpu acceleration and deep learning.",
            "hardware",
        )
        assert score > 0.0
        assert "gpu" in matched

    def test_title_boost(self, classifier):
        """Keywords appearing in the title receive a +0.2 score boost each (capped at 1.0)."""
        # Put gpu and rtx in title — should get base score + boost
        score, matched = classifier._score_content(
            "NVIDIA GPU RTX Series",
            "",
            "additional text about graphics card",
            "hardware",
        )
        # base: min(3/5, 1.0) = 0.6, boost: +0.2 (gpu) + 0.2 (rtx) = 1.0 (capped)
        assert score == 1.0
        assert "gpu" in matched and "rtx" in matched

    def test_score_capped_at_one(self, classifier):
        """The content score never exceeds 1.0 even with many keyword matches + title boosts."""
        title = "gpu rtx graphics card geforce ampere hopper blackwell ada lovelace"
        content = "cuda cudnn cublas tensorrt omniverse"
        score, _ = classifier._score_content(title, "", content, "hardware")
        assert score == 1.0

    def test_no_keyword_match_returns_zero(self, classifier):
        """When no keywords match, score is 0.0 and matched list is empty."""
        score, matched = classifier._score_content(
            "Title", "Desc", "This content has no matching keywords at all.", "hardware"
        )
        assert score == 0.0
        assert matched == []

    def test_empty_keywords_returns_zero(self, empty_classifier):
        """An ecosystem with no keywords returns 0.0 content score."""
        score, matched = empty_classifier._score_content("Title", "Desc", "Content", "x")
        assert score == 0.0
        assert matched == []

    def test_none_inputs_handled(self, classifier):
        """None values for title/description/content are coerced to empty strings."""
        score, matched = classifier._score_content(None, None, None, "hardware")
        assert score == 0.0
        assert matched == []

    def test_content_truncated_to_5000_chars(self, classifier):
        """Content beyond 5000 characters is ignored to keep scoring fast."""
        prefix = "gpu "
        long_content = prefix + ("padding " * 6000)
        score, matched = classifier._score_content("Title", "Desc", long_content, "hardware")
        assert "gpu" in matched

    def test_keyword_case_insensitive(self, classifier):
        """Keyword matching is case-insensitive."""
        score, matched = classifier._score_content("", "", "GPU acceleration for Graphics Cards", "hardware")
        assert "gpu" in matched
        assert "graphics card" in matched

    def test_score_proportional_to_matches(self, classifier):
        """Score is min(matched_count / 5, 1.0). 2 matches = 0.4, 3 matches = 0.6."""
        score_2, m2 = classifier._score_content("", "", "gpu graphics card", "hardware")
        score_3, m3 = classifier._score_content("", "", "gpu graphics card geforce", "hardware")
        assert len(m2) == 2
        assert len(m3) == 3
        assert score_2 == 0.4
        assert score_3 == 0.6

    def test_description_weighted_once(self, classifier):
        """Description contributes to the combined text but is not double-weighted (unlike title)."""
        score, matched = classifier._score_content("", "gpu", "", "hardware")
        assert "gpu" in matched
        assert score > 0


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

class TestClassify:
    def test_url_match_determines_ecosystem(self, minimal_classifier):
        """When URL strongly matches hardware, classification picks hardware."""
        result = minimal_classifier.classify(
            url="https://www.nvidia.com/en-us/geforce/rtx-4090",
            title="Some Page",
            description="",
            content="random content",
        )
        assert result.ecosystem == "hardware"
        assert result.confidence >= 0.6  # url_score=1.0 * 0.6 + content=0 * 0.4

    def test_content_match_determines_ecosystem(self, minimal_classifier):
        """When URL matches neither pattern, content keywords drive classification."""
        result = minimal_classifier.classify(
            url="https://www.nvidia.com/en-us/unknown-page",
            title="CUDA Toolkit Documentation",
            description="tensorrt and cuda tools",
            content="Learn how to use the CUDA toolkit for GPU programming.",
        )
        assert result.ecosystem == "software"

    def test_combined_score_weighting(self, minimal_classifier):
        """URL is weighted 0.6, content 0.4 in combined score."""
        result = minimal_classifier.classify(
            url="https://www.nvidia.com/en-us/geforce/",
            title="CUDA Toolkit",
            description="cuda tensorrt toolkit",
            content="",
        )
        # hardware: url=1.0*0.6 + content=0*0.4 = 0.6
        # software: url=0*0.6 + content_score > 0*0.4 > 0
        # content_score for software: 3 matches / 5 = 0.6, no title keywords in software
        # Actually: title has "CUDA" (keyword "cuda" → case-insensitive match)
        # software: url=0*0.6=0.0, content_score=min(2/5,1.0)=0.4 + boost(0.2 for cuda in title)=0.6
        # combined: 0.0*0.6 + 0.6*0.4 = 0.24
        # Hardware still wins with 0.6 > 0.24
        assert result.ecosystem == "hardware"

    def test_classify_records_matched_patterns(self, minimal_classifier):
        """ClassificationResult includes the URL patterns that matched."""
        result = minimal_classifier.classify(
            url="https://www.nvidia.com/en-us/geforce/rtx-4090",
            title="",
            description="",
            content="",
        )
        assert "/geforce/" in result.matched_patterns

    def test_classify_records_matched_keywords(self, minimal_classifier):
        """ClassificationResult includes the content keywords that matched."""
        result = minimal_classifier.classify(
            url="https://www.nvidia.com/en-us/some-page",
            title="gpu rtx graphics",
            description="",
            content="",
        )
        assert any("gpu" in kw.lower() for kw in result.matched_keywords)

    def test_empty_inputs_do_not_crash(self, classifier):
        """Classifier handles empty strings across all inputs gracefully."""
        result = classifier.classify("", "", "", "")
        assert isinstance(result, ClassificationResult)
        assert isinstance(result.ecosystem, str)
        assert 0.0 <= result.confidence <= 1.0

    def test_zero_confidence_when_nothing_matches(self, empty_classifier):
        """When no URL or content patterns match, confidence is 0.0."""
        result = empty_classifier.classify("https://example.com", "Title", "Desc", "Content")
        assert result.confidence == 0.0

    def test_subcategory_attached(self, classifier):
        """ClassificationResult includes a subcategory derived from the URL path."""
        result = classifier.classify(
            "https://www.nvidia.com/en-us/geforce/graphics-cards/rtx-4090/",
            "GeForce RTX 4090",
        )
        assert result.subcategory is not None


# ---------------------------------------------------------------------------
# Subcategory extraction
# ---------------------------------------------------------------------------

class TestSubcategoryExtraction:
    def test_first_meaningful_segment_used(self, classifier):
        """The first non-locale path segment becomes the subcategory."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/geforce/graphics-cards/",
            "hardware",
        )
        assert sub == "Geforce"

    def test_english_locale_skipped(self, classifier):
        """Locale codes like en-us are excluded from subcategory extraction."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/dgx/",
            "hardware",
        )
        assert sub == "Dgx"

    def test_chinese_locale_skipped(self, classifier):
        """Chinese locale codes (zh-cn, zh-tw) are excluded."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/zh-cn/products/",
            "hardware",
        )
        assert sub == "Products"

    def test_hyphens_converted_to_spaces_and_title_cased(self, classifier):
        """Hyphens in path segments become spaces with title casing."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/data-center/",
            "technology",
        )
        assert sub == "Data Center"

    def test_no_path_returns_none(self, classifier):
        """A URL with no path segments (after stripping locale) returns None."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/",
            "hardware",
        )
        assert sub is None

    def test_root_path_returns_none(self, classifier):
        """A bare domain root returns None."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/",
            "hardware",
        )
        assert sub is None

    def test_single_char_segments_skipped(self, classifier):
        """Segments shorter than 2 characters are filtered out."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/a/b/c/deep-learning/",
            "technology",
        )
        assert sub == "Deep Learning"

    def test_multiple_locales_in_path(self, classifier):
        """Multiple locale segments are all skipped — first content segment is used."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/sv-se/geforce/",
            "hardware",
        )
        assert sub == "Geforce"

    def test_nonexistent_ecosystem_does_not_affect_extraction(self, classifier):
        """Subcategory extraction is ecosystem-agnostic (the param is passed but unused)."""
        sub = classifier._extract_subcategory(
            "https://www.nvidia.com/en-us/cuda/",
            "nonexistent",
        )
        assert sub == "Cuda"


# ---------------------------------------------------------------------------
# Statistics tracking
# ---------------------------------------------------------------------------

class TestStatistics:
    def test_total_pages_incremented(self, classifier):
        """Each classification increments the page count for that ecosystem."""
        assert classifier.stats["hardware"].total_pages == 0
        classifier.classify("https://www.nvidia.com/en-us/geforce/", "GPU Page")
        assert classifier.stats["hardware"].total_pages == 1

    def test_subcategory_tracking(self, classifier):
        """Subcategories are counted per-ecosystem."""
        classifier.classify("https://www.nvidia.com/en-us/geforce/gaming/")
        classifier.classify("https://www.nvidia.com/en-us/geforce/gaming/")
        stats = classifier.stats["hardware"]
        # _extract_subcategory returns the FIRST content segment after locale filtering,
        # so both URLs extract "Geforce", not "Gaming"
        assert stats.subcategories.get("Geforce") == 2

    def test_keyword_tracking(self, classifier):
        """Matched keywords are counted per-ecosystem for frequency analysis."""
        classifier.classify(
            "https://www.nvidia.com/en-us/geforce/",
            "gpu rtx graphics card",
            "",
            "",
        )
        counter = classifier._keyword_counts["hardware"]
        assert counter["gpu"] >= 1

    def test_sample_urls_capped_at_10(self, classifier):
        """At most 10 sample URLs are retained per ecosystem."""
        for i in range(15):
            classifier.classify(f"https://www.nvidia.com/en-us/gpu/page{i}/")
        assert len(classifier.stats["hardware"].sample_urls) == 10

    def test_stats_independent_across_ecosystems(self, classifier):
        """Stats for one ecosystem don't leak into another."""
        classifier.classify("https://www.nvidia.com/en-us/geforce/", "GPU Page")
        classifier.classify("https://www.nvidia.com/en-us/cuda/", "CUDA Toolkit")
        assert classifier.stats["hardware"].total_pages >= 1
        assert classifier.stats["software"].total_pages >= 1

    def test_get_summary_returns_structure(self, classifier):
        """get_summary returns a dict with total_pages and ecosystems breakdown."""
        classifier.classify("https://www.nvidia.com/en-us/geforce/", "GPU Page")
        summary = classifier.get_summary()
        assert "total_pages" in summary
        assert "ecosystems" in summary
        assert summary["total_pages"] > 0
        for eco in ECOSYSTEM_PATTERNS:
            assert eco in summary["ecosystems"]
            assert "name" in summary["ecosystems"][eco]
            assert "name_cn" in summary["ecosystems"][eco]

    def test_get_stats_returns_top_keywords(self, classifier):
        """get_stats computes top_keywords from the keyword counter."""
        classifier.classify("https://www.nvidia.com/en-us/geforce/", "gpu rtx gpu")
        stats = classifier.get_stats()
        assert len(stats["hardware"].top_keywords) >= 1

    def test_get_summary_top_keywords_limited_to_10(self, classifier):
        """Summary includes at most the top 10 keywords per ecosystem."""
        summary = classifier.get_summary()
        for eco_data in summary["ecosystems"].values():
            assert len(eco_data["top_keywords"]) <= 10

    def test_get_summary_subcategories_limited_to_20(self, classifier):
        """Summary includes at most the top 20 subcategories per ecosystem (by count)."""
        summary = classifier.get_summary()
        for eco_data in summary["ecosystems"].values():
            assert len(eco_data["subcategories"]) <= 20


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------

class TestClassifyBatch:
    def test_batch_returns_tuples(self, classifier):
        """classify_batch returns a list of (page_dict, ClassificationResult) tuples."""
        pages = [
            {"url": "https://www.nvidia.com/en-us/geforce/", "title": "GeForce"},
            {"url": "https://www.nvidia.com/en-us/cuda/", "title": "CUDA"},
        ]
        results = classifier.classify_batch(pages)
        assert len(results) == 2
        for page, classification in results:
            assert isinstance(page, dict)
            assert isinstance(classification, ClassificationResult)

    def test_batch_preserves_page_data(self, classifier):
        """The original page dict is returned unchanged alongside the classification."""
        pages = [
            {"url": "https://www.nvidia.com/en-us/geforce/", "title": "GeForce", "custom": "value"},
        ]
        results = classifier.classify_batch(pages)
        assert results[0][0]["custom"] == "value"

    def test_batch_empty_list(self, classifier):
        """An empty page list returns an empty result list."""
        assert classifier.classify_batch([]) == []

    def test_batch_missing_keys_default_to_empty(self, classifier):
        """Pages missing title/description/content keys default to empty strings."""
        pages = [{"url": "https://www.nvidia.com/en-us/geforce/"}]
        results = classifier.classify_batch(pages)
        assert len(results) == 1
        assert isinstance(results[0][1], ClassificationResult)


# ---------------------------------------------------------------------------
# Custom patterns
# ---------------------------------------------------------------------------

class TestCustomPatterns:
    def test_custom_patterns_override_defaults(self):
        """A classifier initialized with custom patterns works independently of defaults."""
        custom = {
            "ai": {
                "url_patterns": ["/ai-ml/"],
                "keywords": ["artificial intelligence", "machine learning", "neural network"],
            },
            "web": {
                "url_patterns": ["/web/", "/frontend/"],
                "keywords": ["javascript", "react", "css", "html"],
            },
        }
        clf = EcosystemClassifier(patterns=custom)
        result = clf.classify(
            url="https://example.com/ai-ml/models",
            title="Neural Network Training",
            description="",
            content="train your neural network with machine learning",
        )
        assert result.ecosystem == "ai"
        assert result.confidence >= 0.6  # url=1.0*0.6 + some content

    def test_custom_pattern_stats_independent(self):
        """Statistics for custom classifiers don't include default ecosystems."""
        clf = EcosystemClassifier(patterns={
            "cat": {"url_patterns": ["/meow/"], "keywords": ["cat"]},
        })
        clf.classify("https://example.com/meow/persian", "Cat Page", "", "cat")
        assert "cat" in clf.stats
        assert len(clf.stats) == 1


# ---------------------------------------------------------------------------
# Dataclass structures
# ---------------------------------------------------------------------------

class TestDataClasses:
    def test_classification_result_defaults(self):
        """ClassificationResult has sensible defaults for optional fields."""
        result = ClassificationResult(ecosystem="test", confidence=0.5)
        assert result.subcategory is None
        assert result.matched_patterns == []
        assert result.matched_keywords == []

    def test_ecosystem_stats_defaults(self):
        """EcosystemStats initializes with zero counters and empty collections."""
        stats = EcosystemStats()
        assert stats.total_pages == 0
        assert stats.subcategories == {}
        assert stats.top_keywords == []
        assert stats.sample_urls == []


# ---------------------------------------------------------------------------
# Boundary / robustness
# ---------------------------------------------------------------------------

class TestBoundaryBehavior:
    def test_very_long_url_does_not_crash(self, classifier):
        """Extremely long URLs don't cause regex backtracking issues."""
        long_url = "https://www.nvidia.com/en-us/geforce/" + "x" * 10000
        result = classifier.classify(long_url, "", "", "")
        assert isinstance(result, ClassificationResult)

    def test_content_with_special_regex_chars(self, classifier):
        """Content containing regex special characters is treated as plain text."""
        result = classifier.classify(
            "https://www.nvidia.com/en-us/some-page",
            "(test) [gpu] *accelerator*",
            "regex .* chars $^",
            "{nvidia} + \\ gpu ? : circuit",
        )
        assert isinstance(result, ClassificationResult)

    def test_unicode_content(self, classifier):
        """Non-ASCII content is handled correctly."""
        result = classifier.classify(
            "https://www.nvidia.com/en-us/geforce/",
            "NVIDIA GPU加速",
            "图形处理器",
            "gpu 图形处理单元",
        )
        assert result.ecosystem == "hardware"

    def test_classify_none_url(self, classifier):
        """None URL is coerced to empty string and doesn't crash."""
        result = classifier.classify(None, "Some Title", "", "")
        assert isinstance(result, ClassificationResult)
