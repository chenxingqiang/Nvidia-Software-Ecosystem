"""Tests for URLManager in crawler/url_manager.py."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from crawler.url_manager import URLManager, URLItem

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager():
    """Fresh URLManager with default NVIDIA config."""
    return URLManager()


@pytest.fixture
def crawl_all_manager():
    """URLManager in crawl_all mode."""
    return URLManager(crawl_all=True)


# ============================================================================
# 1. URL Normalization (normalize_url)
# ============================================================================


class TestNormalizeURL:
    """Tests for URLManager.normalize_url()."""

    def test_removes_fragment(self, manager):
        """Fragment identifiers after # are stripped."""
        assert manager.normalize_url(
            "https://www.nvidia.com/en-us/page#section"
        ) == "https://www.nvidia.com/en-us/page"

    def test_removes_fragment_with_query(self, manager):
        """Query string is preserved, fragment is removed."""
        assert manager.normalize_url(
            "https://www.nvidia.com/en-us/page?q=1#section"
        ) == "https://www.nvidia.com/en-us/page?q=1"

    def test_removes_trailing_slash(self, manager):
        """Trailing slash on non-root path is removed."""
        assert manager.normalize_url(
            "https://www.nvidia.com/en-us/geforce/"
        ) == "https://www.nvidia.com/en-us/geforce"

    def test_preserves_root_path_slash(self, manager):
        """Root path '/' is preserved (not stripped to empty).
        URL with no path (empty string) remains unchanged because the
        guard only applies when parsed.path == '/', not when it is ''."""
        assert manager.normalize_url(
            "https://www.nvidia.com/"
        ) == "https://www.nvidia.com/"
        # Bare domain with no path produces '' from urlparse;
        # this is not the same as '/' so the rstrip guard does not fire.
        assert manager.normalize_url(
            "https://www.nvidia.com"
        ) == "https://www.nvidia.com"

    def test_lowercases_netloc(self, manager):
        """Netloc (domain) is lowercased."""
        assert manager.normalize_url(
            "https://WWW.NVIDIA.COM/en-us/GeForce"
        ) == "https://www.nvidia.com/en-us/GeForce"

    def test_preserves_query_params(self, manager):
        """Query parameters are preserved unchanged."""
        assert manager.normalize_url(
            "https://www.nvidia.com/en-us/page?key=value&other=1"
        ) == "https://www.nvidia.com/en-us/page?key=value&other=1"

    def test_preserves_semicolon_params(self, manager):
        """URL params (via semicolon) are preserved."""
        assert manager.normalize_url(
            "https://www.nvidia.com/en-us/page;param=value"
        ) == "https://www.nvidia.com/en-us/page;param=value"

    def test_preserves_port_in_netloc(self, manager):
        """Port number is preserved in the netloc (normalize does not strip it)."""
        assert manager.normalize_url(
            "http://localhost:8000/en-us/geforce/"
        ) == "http://localhost:8000/en-us/geforce"


# ============================================================================
# 2. URL Validation (is_valid_url)
# ============================================================================


class TestIsValidURL:
    """Tests for URLManager.is_valid_url()."""

    # -- Valid NVIDIA URLs ---------------------------------------------------

    def test_valid_nvidia_main_site(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/en-us/geforce/") is True

    def test_valid_developer_subdomain(self, manager):
        assert manager.is_valid_url("https://developer.nvidia.com/cuda/") is True

    def test_valid_docs_subdomain(self, manager):
        assert manager.is_valid_url("https://docs.nvidia.com/deeplearning/") is True

    def test_valid_ngc_subdomain(self, manager):
        assert manager.is_valid_url("https://ngc.nvidia.com/catalog/") is True

    def test_valid_nvidia_cn(self, manager):
        assert manager.is_valid_url("https://www.nvidia.cn/products/") is True

    def test_valid_root_nvidia_cn(self, manager):
        assert manager.is_valid_url("https://nvidia.cn/") is True

    def test_valid_root_nvidia_com(self, manager):
        assert manager.is_valid_url("https://nvidia.com/") is True

    # -- Missing scheme ------------------------------------------------------

    def test_missing_scheme_rejected(self, manager):
        assert manager.is_valid_url("www.nvidia.com/en-us/geforce/") is False

    def test_empty_string_rejected(self, manager):
        assert manager.is_valid_url("") is False

    # -- Non-HTTP scheme -----------------------------------------------------

    def test_ftp_scheme_rejected(self, manager):
        assert manager.is_valid_url("ftp://www.nvidia.com/drivers/") is False

    def test_mailto_scheme_rejected(self, manager):
        assert manager.is_valid_url("mailto:support@nvidia.com") is False

    def test_javascript_scheme_rejected(self, manager):
        assert manager.is_valid_url("javascript:void(0)") is False

    # -- Blocked domain (not in ALLOWED_DOMAINS) -----------------------------

    def test_google_blocked(self, manager):
        assert manager.is_valid_url("https://www.google.com/") is False

    def test_amd_blocked(self, manager):
        assert manager.is_valid_url("https://www.amd.com/") is False

    def test_intel_blocked(self, manager):
        assert manager.is_valid_url("https://www.intel.com/") is False

    # -- Subdomain matching (endswith semantics) -----------------------------

    def test_subdomain_passes_domain_check(self, manager):
        """A subdomain of nvidia.com passes via endswith match."""
        assert manager.is_valid_url("https://store.nvidia.com/") is True

    def test_deep_subdomain_passes(self, manager):
        """Any subdomain ending with an allowed domain passes."""
        assert manager.is_valid_url("https://a.b.c.developer.nvidia.com/") is True

    def test_false_friend_domain_passes(self, manager):
        """endswith check matches strings that accidentally end with nvidia.com.
        This is a known looseness in the current domain-check logic."""
        assert manager.is_valid_url("https://not-nvidia.com/") is True

    # -- Exclude patterns ----------------------------------------------------

    def test_blog_excluded(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/en-us/blog/post123/") is False

    def test_news_excluded(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/en-us/news/article/") is False

    def test_pdf_excluded(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/docs/report.pdf") is False

    def test_zip_excluded(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/drivers/driver.zip") is False

    def test_login_excluded(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/login/") is False

    def test_locale_excluded_ja_jp(self, manager):
        """Non-target locale path markers are in the exclude list."""
        assert manager.is_valid_url("https://www.nvidia.com/ja-jp/products/") is False

    def test_locale_excluded_de_de(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/de-de/products/") is False

    def test_locale_excluded_ko_kr(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/ko-kr/products/") is False

    # -- Case-insensitive matching -------------------------------------------

    def test_valid_url_case_insensitive_path(self, manager):
        assert manager.is_valid_url("https://www.nvidia.com/EN-US/GeForce/") is True

    def test_exclude_pattern_case_insensitive(self, manager):
        """Exclude pattern matching is case-insensitive."""
        assert manager.is_valid_url("https://www.nvidia.com/en-us/BLOG/post/") is False
        assert manager.is_valid_url("https://www.nvidia.com/en-us/News/article/") is False

    # -- Exception handling --------------------------------------------------

    def test_malformed_url_returns_false(self, manager):
        """Malformed or unparseable URLs are gracefully rejected."""
        assert manager.is_valid_url("://") is False


# ============================================================================
# 3. Include Filtering (should_include)
# ============================================================================


class TestShouldInclude:
    """Tests for URLManager.should_include()."""

    # -- Include pattern matching --------------------------------------------

    def test_products_pattern_match(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us/products/geforce/") is True

    def test_solutions_pattern_match(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us/solutions/healthcare/") is True

    def test_cuda_pattern_match(self, manager):
        assert manager.should_include("https://developer.nvidia.com/cuda-toolkit") is True

    def test_geforce_pattern_match(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us/geforce/graphics-cards/") is True

    def test_data_center_pattern_match(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us/data-center/a100/") is True

    def test_deep_learning_pattern_match(self, manager):
        """URL containing /deep-learning/ matches the include pattern.
        Note: the pattern is /deep-learning/ which is a substring match,
        so it only matches URLs that literally contain /deep-learning/."""
        assert manager.should_include(
            "https://www.nvidia.com/en-us/deep-learning/courses/"
        ) is True

    def test_omniverse_pattern_match(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us/omniverse/platform/") is True

    def test_developer_nvidia_com_path(self, manager):
        """developer.nvidia.com paths matching /developer/ pattern are included."""
        assert manager.should_include("https://developer.nvidia.com/developer/tools/") is True

    # -- Root / main locale paths always included ----------------------------

    def test_root_path_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/") is True

    def test_en_us_path_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us/") is True

    def test_en_us_no_trailing_slash_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/en-us") is True

    def test_zh_cn_path_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/zh-cn/") is True

    def test_zh_cn_no_trailing_slash_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/zh-cn") is True

    def test_zh_tw_path_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/zh-tw/") is True

    def test_zh_tw_no_trailing_slash_included(self, manager):
        assert manager.should_include("https://www.nvidia.com/zh-tw") is True

    def test_locale_paths_case_insensitive(self, manager):
        """Locale path checks are case-insensitive."""
        assert manager.should_include("https://www.nvidia.com/EN-US/") is True
        assert manager.should_include("https://www.nvidia.com/ZH-CN/") is True

    # -- crawl_all mode skips include filtering ------------------------------

    def test_crawl_all_includes_everything(self, crawl_all_manager):
        """In crawl_all mode, should_include always returns True."""
        assert crawl_all_manager.should_include(
            "https://www.nvidia.com/en-us/random-page/"
        ) is True
        assert crawl_all_manager.should_include(
            "https://www.nvidia.com/en-us/anything/deep/nested/"
        ) is True

    # -- Shallow paths (<= 2 parts) always included --------------------------

    def test_single_path_part_included(self, manager):
        """A path with one meaningful segment (e.g. /en-us/geforce) has
        path_parts=['en-us', 'geforce'] => 2 parts => included."""
        assert manager.should_include("https://www.nvidia.com/en-us/geforce") is True

    def test_two_path_parts_included(self, manager):
        """path_parts=['en-us', 'hardware', 'rtx-4090'] => 3 parts => NOT included
        unless a pattern matches.  Two-or-fewer parts are included."""
        assert manager.should_include("https://www.nvidia.com/en-us/rtx-4090") is True

    def test_root_no_locale_two_parts_included(self, manager):
        """path_parts=['about', 'careers'] => 2 parts => included even without
        a matching include pattern."""
        assert manager.should_include("https://www.nvidia.com/about/careers") is True

    # -- Deep paths without matching pattern are excluded --------------------

    def test_deep_unmatched_path_excluded(self, manager):
        """3+ path segments with no include-pattern match => excluded."""
        assert manager.should_include(
            "https://www.nvidia.com/en-us/support/contact/drivers/windows"
        ) is False

    def test_four_level_path_excluded(self, manager):
        assert manager.should_include(
            "https://www.nvidia.com/en-us/company/executives/management/office"
        ) is False


# ============================================================================
# 4. URL Queuing (add_url)
# ============================================================================


class TestAddURL:
    """Tests for URLManager.add_url()."""

    def test_adds_valid_url(self, manager):
        result = manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        assert result is True
        assert manager.queue_size == 1
        assert manager.discovered_count == 1

    def test_rejects_exceeded_depth(self, manager):
        """Depth > max_depth is rejected. Default max_depth is 5, so 6 exceeds."""
        result = manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=6)
        assert result is False
        assert manager.queue_size == 0

    def test_accepts_boundary_depth(self, manager):
        """depth == max_depth is accepted."""
        result = manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=5)
        assert result is True
        assert manager.queue_size == 1

    def test_rejects_duplicate_normalized_url(self, manager):
        """Same URL after normalization was already discovered; rejected."""
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        result = manager.add_url(
            "https://www.nvidia.com/en-us/geforce#frag", depth=1
        )
        assert result is False
        assert manager.queue_size == 1  # only first was added

    def test_rejects_duplicate_exact_url(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)
        result = manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)
        assert result is False

    def test_rejects_invalid_url(self, manager):
        result = manager.add_url("https://www.google.com/", depth=0)
        assert result is False
        assert manager.queue_size == 0

    def test_rejects_not_include_url(self, manager):
        """URL is valid but does not match include filters => rejected."""
        result = manager.add_url(
            "https://www.nvidia.com/en-us/support/contact/drivers", depth=0
        )
        assert result is False
        assert manager.queue_size == 0

    def test_created_item_has_correct_fields(self, manager):
        manager.add_url(
            "https://www.nvidia.com/en-us/geforce/",
            depth=2,
            parent_url="https://www.nvidia.com/en-us/",
        )
        item = manager.get_next()
        assert item is not None
        assert item.url == "https://www.nvidia.com/en-us/geforce"
        assert item.depth == 2
        assert item.parent_url == "https://www.nvidia.com/en-us/"
        assert item.discovered_at > 0


# ============================================================================
# 5. Batch URL Adding (add_urls)
# ============================================================================


class TestAddURLs:
    """Tests for URLManager.add_urls()."""

    URLS = [
        "https://www.nvidia.com/en-us/geforce/",
        "https://www.nvidia.com/en-us/products/",
        "https://www.nvidia.com/en-us/cuda/",
        "https://www.google.com/",                  # invalid domain
        "https://www.nvidia.com/en-us/blog/post1/",  # excluded pattern
        "https://www.nvidia.com/en-us/support/contact/drivers/windows",  # not included
        "https://www.nvidia.com/en-us/geforce/#frag",  # duplicate after normalize
    ]

    def test_returns_count_of_added_urls(self, manager):
        added = manager.add_urls(self.URLS, depth=0)
        assert added == 3  # geforce, products, cuda

    def test_queue_size_matches_added_count(self, manager):
        manager.add_urls(self.URLS, depth=0)
        assert manager.queue_size == 3

    def test_batch_with_different_depths(self, manager):
        added = manager.add_urls(
            [
                "https://www.nvidia.com/en-us/geforce/",
                "https://www.nvidia.com/en-us/products/",
            ],
            depth=6,  # exceeds max_depth=5
        )
        assert added == 0

    def test_empty_list_returns_zero(self, manager):
        assert manager.add_urls([], depth=0) == 0

    def test_all_duplicates_returns_zero(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)
        added = manager.add_urls(
            [
                "https://www.nvidia.com/en-us/geforce/",
                "https://www.nvidia.com/en-us/products/",
            ],
            depth=1,
        )
        assert added == 0


# ============================================================================
# 6. Queue Management (get_next, mark_visited, mark_failed, is_visited)
# ============================================================================


class TestQueueManagement:
    """Tests for get_next, mark_visited, mark_failed, is_visited."""

    def test_get_next_returns_none_when_empty(self, manager):
        assert manager.get_next() is None

    def test_get_next_returns_first_item(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        item = manager.get_next()
        assert item is not None
        assert item.url == "https://www.nvidia.com/en-us/geforce"

    def test_get_next_skips_visited_urls(self, manager):
        """When an item was visited between being queued and popped,
        get_next skips it and returns the next unvisited item."""
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)

        # Mark geforce as visited before it is popped
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/")

        item = manager.get_next()
        assert item is not None
        # products should be returned because geforce was skipped
        assert item.url == "https://www.nvidia.com/en-us/products"

    def test_get_next_returns_none_when_all_visited(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/")
        assert manager.get_next() is None

    def test_order_is_fifo(self, manager):
        """Queue preserves insertion order (FIFO)."""
        urls = [
            "https://www.nvidia.com/en-us/geforce/",
            "https://www.nvidia.com/en-us/products/",
            "https://www.nvidia.com/en-us/cuda/",
        ]
        for url in urls:
            manager.add_url(url, depth=0)

        popped = []
        while (item := manager.get_next()) is not None:
            popped.append(item.url)

        assert popped == [
            "https://www.nvidia.com/en-us/geforce",
            "https://www.nvidia.com/en-us/products",
            "https://www.nvidia.com/en-us/cuda",
        ]

    def test_mark_visited_normalizes_before_storing(self, manager):
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/#frag")
        assert manager.is_visited("https://www.nvidia.com/en-us/geforce/") is True

    def test_is_visited_not_yet_visited(self, manager):
        assert manager.is_visited("https://www.nvidia.com/en-us/geforce/") is False

    def test_mark_visited_updates_count(self, manager):
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/")
        assert manager.visited_count == 1

    def test_mark_failed_stores_error_and_marks_visited(self, manager):
        manager.mark_failed("https://www.nvidia.com/en-us/geforce/", "Timeout")
        assert manager.is_visited("https://www.nvidia.com/en-us/geforce/") is True
        assert manager.failed_count == 1

    def test_mark_failed_does_not_double_count_visited(self, manager):
        """When already visited and then marked failed, visited_count
        should remain 1 (the URL is added to _visited via both paths
        but it is a set, so count stays 1)."""
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/")
        manager.mark_failed("https://www.nvidia.com/en-us/geforce/", "Error")
        assert manager.visited_count == 1
        assert manager.failed_count == 1

    def test_mark_failed_updates_error_on_second_call(self, manager):
        manager.mark_failed("https://www.nvidia.com/en-us/geforce/", "Timeout")
        manager.mark_failed("https://www.nvidia.com/en-us/geforce/", "ConnectionRefused")
        # same normalized key, dict entry is overwritten
        assert manager.failed_count == 1

    def test_get_next_after_mark_failed_does_not_return_again(self, manager):
        """A marked-failed URL is in _visited; if it is still in the queue,
        get_next skips it."""
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.mark_failed("https://www.nvidia.com/en-us/geforce/", "Timeout")
        assert manager.get_next() is None


# ============================================================================
# 7. Link Extraction (extract_links)
# ============================================================================


class TestExtractLinks:
    """Tests for URLManager.extract_links()."""

    HTML_SAMPLE = """
    <html>
    <body>
        <a href="https://www.nvidia.com/en-us/geforce/graphics-cards/">GeForce</a>
        <a href='/en-us/products/'>Products</a>
        <a href="products/nvidia-rtx-6000/">RTX</a>
        <a href="javascript:void(0)">JS Link</a>
        <a href="mailto:support@nvidia.com">Email</a>
        <a href="tel:+1234567890">Phone</a>
        <a href="#top">Anchor</a>
        <a href="https://developer.nvidia.com/cuda-downloads">CUDA</a>
    </body>
    </html>
    """

    def test_extracts_href_attributes(self, manager):
        base = "https://www.nvidia.com/en-us/geforce/"
        links = manager.extract_links(base, self.HTML_SAMPLE)
        assert len(links) == 4  # 4 non-skipped links

    def test_skips_javascript_links(self, manager):
        base = "https://www.nvidia.com/en-us/"
        links = manager.extract_links(base, '<a href="javascript:void(0)">x</a>')
        assert len(links) == 0

    def test_skips_mailto_links(self, manager):
        base = "https://www.nvidia.com/en-us/"
        links = manager.extract_links(base, '<a href="mailto:a@b.com">x</a>')
        assert len(links) == 0

    def test_skips_tel_links(self, manager):
        base = "https://www.nvidia.com/en-us/"
        links = manager.extract_links(base, '<a href="tel:12345">x</a>')
        assert len(links) == 0

    def test_skips_hash_links(self, manager):
        base = "https://www.nvidia.com/en-us/"
        links = manager.extract_links(base, '<a href="#top">x</a>')
        assert len(links) == 0

    def test_converts_relative_to_absolute(self, manager):
        """Relative paths are resolved against the base URL."""
        base = "https://www.nvidia.com/en-us/geforce/"
        links = manager.extract_links(
            base, '<a href="products/graphics-cards/">Cards</a>'
        )
        assert links == ["https://www.nvidia.com/en-us/geforce/products/graphics-cards/"]

    def test_converts_root_relative_to_absolute(self, manager):
        """Root-relative paths (starting with /) are resolved against base origin."""
        base = "https://www.nvidia.com/en-us/geforce/"
        links = manager.extract_links(base, '<a href="/en-us/products/">Products</a>')
        assert links == ["https://www.nvidia.com/en-us/products/"]

    def test_preserves_absolute_urls(self, manager):
        base = "https://www.nvidia.com/en-us/"
        links = manager.extract_links(
            base,
            '<a href="https://developer.nvidia.com/cuda/">CUDA</a>',
        )
        assert links == ["https://developer.nvidia.com/cuda/"]

    def test_handles_empty_html(self, manager):
        assert manager.extract_links("https://www.nvidia.com/", "") == []

    def test_handles_no_links_html(self, manager):
        links = manager.extract_links(
            "https://www.nvidia.com/", "<html><body><p>No links</p></body></html>"
        )
        assert links == []

    def test_extracts_single_quoted_href(self, manager):
        links = manager.extract_links(
            "https://www.nvidia.com/",
            "<a href='/en-us/geforce/'>GeForce</a>",
        )
        assert links == ["https://www.nvidia.com/en-us/geforce/"]

    def test_extracts_multiple_links_with_duplicates(self, manager):
        html = """
        <a href="/en-us/products/">Products</a>
        <a href="/en-us/products/">Products again</a>
        <a href="/en-us/geforce/">GeForce</a>
        """
        links = manager.extract_links("https://www.nvidia.com", html)
        assert len(links) == 3
        assert links[0] == "https://www.nvidia.com/en-us/products/"


# ============================================================================
# 8. Properties and Stats
# ============================================================================


class TestPropertiesAndStats:
    """Tests for queue_size, visited_count, discovered_count, failed_count, get_stats."""

    def test_initial_queue_size_zero(self, manager):
        assert manager.queue_size == 0

    def test_initial_visited_count_zero(self, manager):
        assert manager.visited_count == 0

    def test_initial_discovered_count_zero(self, manager):
        assert manager.discovered_count == 0

    def test_initial_failed_count_zero(self, manager):
        assert manager.failed_count == 0

    def test_queue_size_increments_on_add(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        assert manager.queue_size == 1

    def test_queue_size_decrements_on_pop(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.get_next()
        assert manager.queue_size == 0

    def test_discovered_count_tracks_unique_added_urls(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)  # duplicate
        assert manager.discovered_count == 2

    def test_get_stats_returns_dict(self, manager):
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/")
        manager.mark_failed("https://www.nvidia.com/en-us/geforce/", "error")

        stats = manager.get_stats()
        assert stats == {
            "queue_size": 2,       # products still in queue; geforce was visited but still in queue
            "visited": 1,          # geforce marked as visited
            "discovered": 2,       # both geforce and products discovered
            "failed": 1,           # geforce marked as failed
        }

    def test_get_stats_comprehensive(self, manager):
        """End-to-end flow: add several URLs, visit some, fail some, check stats."""
        manager.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/products/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/cuda/", depth=0)
        manager.add_url("https://www.nvidia.com/en-us/dgx/", depth=0)

        # Simulate crawl progress
        item1 = manager.get_next()
        manager.mark_visited(item1.url)

        item2 = manager.get_next()
        manager.mark_failed(item2.url, "Timeout")

        item3 = manager.get_next()
        manager.mark_visited(item3.url)

        stats = manager.get_stats()
        assert stats["queue_size"] == 1  # one left
        assert stats["visited"] == 3     # two visited + one failed
        assert stats["discovered"] == 4  # all discovered
        assert stats["failed"] == 1      # one failed


# ============================================================================
# 9. Custom Configuration
# ============================================================================


class TestCustomConfig:
    """Tests for custom constructor parameters."""

    def test_custom_max_depth_shallow(self):
        mgr = URLManager(max_depth=1)
        assert mgr.add_url("https://www.nvidia.com/en-us/geforce/", depth=1) is True
        assert mgr.add_url("https://www.nvidia.com/en-us/products/", depth=2) is False

    def test_custom_max_depth_deep(self):
        mgr = URLManager(max_depth=10)
        assert mgr.add_url("https://www.nvidia.com/en-us/geforce/", depth=10) is True
        assert mgr.add_url("https://www.nvidia.com/en-us/products/", depth=11) is False

    def test_custom_allowed_domains_adds_new_domain(self):
        mgr = URLManager(allowed_domains={"nvidia.com", "test.domain.com"})
        assert mgr.is_valid_url("https://test.domain.com/page/") is True
        assert mgr.is_valid_url("https://www.nvidia.com/") is True
        assert mgr.is_valid_url("https://other.com/") is False

    def test_custom_allowed_domains_restricts(self):
        mgr = URLManager(allowed_domains={"nvidia.com"})
        assert mgr.is_valid_url("https://nvidia.com/") is True
        # Only "nvidia.com" in allowed_domains; this may still match via endswith
        # since "www.nvidia.com".endswith("nvidia.com") is True
        assert mgr.is_valid_url("https://www.nvidia.com/") is True

    def test_custom_include_patterns(self):
        mgr = URLManager(include_patterns=["/custom-path/"])
        assert mgr.should_include(
            "https://www.nvidia.com/en-us/custom-path/page/"
        ) is True
        # A deep path (3+ parts) without a matching pattern is excluded.
        assert mgr.should_include(
            "https://www.nvidia.com/en-us/geforce/graphics/rtx"
        ) is False
        # Shallow paths (<=2 parts) are still included regardless of patterns.
        assert mgr.should_include("https://www.nvidia.com/en-us/geforce") is True

    def test_custom_include_patterns_overrides_shallow(self):
        """Custom include pattern alone decides deep-path inclusion."""
        mgr = URLManager(include_patterns=["/custom-path/"])
        # Deep path without custom pattern match
        assert mgr.should_include(
            "https://www.nvidia.com/en-us/geforce/graphics/rtx"
        ) is False
        # Deep path with custom pattern match
        assert mgr.should_include(
            "https://www.nvidia.com/en-us/custom-path/whatever/deep"
        ) is True

    def test_custom_exclude_patterns(self):
        mgr = URLManager(exclude_patterns=["/blocked/", ".custom-ext"])
        assert mgr.is_valid_url("https://www.nvidia.com/en-us/blocked/page/") is False
        assert mgr.is_valid_url("https://www.nvidia.com/file.custom-ext") is False
        assert mgr.is_valid_url("https://www.nvidia.com/en-us/geforce/") is True

    def test_crawl_all_mode(self):
        mgr = URLManager(crawl_all=True)
        # should_include always returns True
        assert mgr.should_include("https://www.nvidia.com/en-us/any/deep/path/here") is True
        # add_url still filters by is_valid and depth
        mgr.add_url("https://www.nvidia.com/en-us/geforce/", depth=0)
        assert mgr.queue_size == 1
        # invalid domain still rejected
        assert mgr.add_url("https://www.google.com/", depth=0) is False

    def test_crawl_all_without_include_patterns(self):
        """In crawl_all mode, include_patterns are irrelevant."""
        mgr = URLManager(crawl_all=True, include_patterns=[])
        assert mgr.should_include("https://www.nvidia.com/en-us/deep/nested") is True

    def test_combined_custom_config(self):
        """Multiple custom settings together."""
        mgr = URLManager(
            max_depth=3,
            allowed_domains={"docs.nvidia.com"},
            include_patterns=["/cuda/", "/deeplearning/"],
            exclude_patterns=["/legacy/"],
        )
        # Correct domain and include pattern
        assert mgr.add_url("https://docs.nvidia.com/cuda/release-notes/", depth=1) is True
        # Wrong domain
        assert mgr.add_url("https://www.nvidia.com/en-us/geforce/", depth=0) is False
        # Excluded pattern
        assert mgr.add_url("https://docs.nvidia.com/legacy/old-page/", depth=0) is False
        # Depth exceeded
        assert mgr.add_url("https://docs.nvidia.com/cuda/new/", depth=4) is False


# ============================================================================
# Edge Cases and Integration Scenarios
# ============================================================================


class TestEdgeCases:
    """Boundary conditions and integration tests."""

    def test_normalize_then_validate_roundtrip(self, manager):
        """Normalizing then validating should be idempotent for valid URLs."""
        url = "https://www.nvidia.com/en-us/geforce/#frag"
        n1 = manager.normalize_url(url)
        n2 = manager.normalize_url(n1)
        assert n1 == n2  # idempotent

    def test_add_url_with_fragment_is_deduped(self, manager):
        """Adding the same URL with and without a fragment is deduplicated."""
        assert manager.add_url("https://www.nvidia.com/en-us/products/", depth=0) is True
        assert manager.add_url(
            "https://www.nvidia.com/en-us/products/#section", depth=0
        ) is False

    def test_add_url_with_and_without_trailing_slash(self, manager):
        """Trailing slash differences are normalized away."""
        assert manager.add_url("https://www.nvidia.com/en-us/products/", depth=0) is True
        assert manager.add_url("https://www.nvidia.com/en-us/products", depth=0) is False

    def test_many_urls_crawl_flow(self, manager):
        """Simulate a small crawl: add, pop, visit, fail in sequence."""
        seed_urls = [
            "https://www.nvidia.com/en-us/",
            "https://www.nvidia.com/en-us/products/",
            "https://www.nvidia.com/en-us/cuda/",
            "https://www.nvidia.com/en-us/dgx/",
        ]
        manager.add_urls(seed_urls, depth=0)

        visited_urls = []
        for _ in range(len(seed_urls)):
            item = manager.get_next()
            if item is None:
                break
            if "products" in item.url:
                manager.mark_failed(item.url, "Timeout")
            else:
                manager.mark_visited(item.url)
                visited_urls.append(item.url)

        assert len(visited_urls) == 3  # 3 visited, 1 failed
        assert manager.get_next() is None  # queue exhausted
        assert manager.discovered_count == 4
        assert manager.failed_count == 1
        assert manager.visited_count == 4  # failed also counts as visited

    def test_is_visited_case_insensitive_domain(self, manager):
        """is_visited normalizes the URL before checking."""
        manager.mark_visited("https://WWW.NVIDIA.COM/en-us/geforce/")
        assert manager.is_visited("https://www.nvidia.com/en-us/geforce") is True

    def test_is_visited_with_trailing_slash(self, manager):
        """Trailing slash difference is normalized."""
        manager.mark_visited("https://www.nvidia.com/en-us/geforce/")
        assert manager.is_visited("https://www.nvidia.com/en-us/geforce") is True

    def test_urlitem_dataclass_creation(self):
        """URLItem can be created directly with all fields."""
        item = URLItem(
            url="https://www.nvidia.com/en-us/geforce",
            depth=2,
            parent_url="https://www.nvidia.com/en-us/",
            discovered_at=1234567890.0,
        )
        assert item.url == "https://www.nvidia.com/en-us/geforce"
        assert item.depth == 2
        assert item.parent_url == "https://www.nvidia.com/en-us/"
        assert item.discovered_at == 1234567890.0

    def test_urlitem_defaults(self):
        """URLItem default values for optional fields."""
        item = URLItem(url="https://www.nvidia.com/", depth=0)
        assert item.parent_url is None
        assert item.discovered_at == 0
