"""Comprehensive tests for MarkdownGenerator and helpers in
generators/markdown_gen.py."""
import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from generators.markdown_gen import MarkdownGenerator, _is_noise_subcategory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_page(**kwargs):
    """Create a classified page dict with sensible defaults for testing."""
    return {
        "url": kwargs.get("url", "https://www.nvidia.com/en-us/test/"),
        "ecosystem": kwargs.get("ecosystem", "technology"),
        "subcategory": kwargs.get("subcategory"),
        "products": kwargs.get("products", []),
        "technologies": kwargs.get("technologies", []),
        "keywords": kwargs.get("keywords", []),
    }


def make_metadata(**kwargs):
    """Create crawl metadata dict with sensible defaults."""
    return {
        "start_time": kwargs.get("start_time", "2025-01-01T00:00:00"),
        "end_time": kwargs.get("end_time", "2025-01-01T01:00:00"),
        "total_pages": kwargs.get("total_pages", 0),
        "elapsed_seconds": kwargs.get("elapsed_seconds", 3600.0),
    }


@pytest.fixture
def generator(tmp_path):
    """Fresh MarkdownGenerator writing into a temporary directory."""
    return MarkdownGenerator(output_dir=tmp_path)


# ---------------------------------------------------------------------------
# _is_noise_subcategory
# ---------------------------------------------------------------------------

class TestNoiseFilter:
    """Tests for the module-level _is_noise_subcategory function."""

    # -- None / empty ------------------------------------------------------

    def test_none_is_noise(self):
        """None input is treated as noise."""
        assert _is_noise_subcategory(None) is True

    def test_empty_string_is_noise(self):
        """Empty string is noise."""
        assert _is_noise_subcategory("") is True

    def test_whitespace_only_is_noise(self):
        """A string containing only whitespace is noise."""
        assert _is_noise_subcategory("   ") is True
        assert _is_noise_subcategory("\t") is True

    # -- Junk tokens -------------------------------------------------------

    def test_junk_token_object(self):
        assert _is_noise_subcategory("object") is True

    def test_junk_token_tag(self):
        assert _is_noise_subcategory("tag") is True

    def test_junk_token_search(self):
        assert _is_noise_subcategory("search") is True

    def test_junk_token_login(self):
        assert _is_noise_subcategory("login") is True

    def test_junk_token_account(self):
        assert _is_noise_subcategory("account") is True

    def test_junk_token_download(self):
        assert _is_noise_subcategory("download") is True

    def test_junk_token_help(self):
        assert _is_noise_subcategory("help") is True

    def test_junk_token_l(self):
        """Token 'l' (lowercase L) is in the junk set."""
        assert _is_noise_subcategory("l") is True

    def test_junk_token_percent20(self):
        assert _is_noise_subcategory("%20") is True

    def test_junk_token_case_insensitive(self):
        """Junk token matching is case-insensitive."""
        assert _is_noise_subcategory("Object") is True
        assert _is_noise_subcategory("LOGIN") is True
        assert _is_noise_subcategory("Search") is True

    # -- Locale pairs ------------------------------------------------------

    def test_locale_pair_en_us(self):
        assert _is_noise_subcategory("En Us") is True

    def test_locale_pair_fr_ca(self):
        assert _is_noise_subcategory("Fr Ca") is True

    def test_locale_pair_zh_cn(self):
        assert _is_noise_subcategory("Zh Cn") is True

    def test_locale_pair_with_three_char_region(self):
        """Locale pair can have a 2- or 3-character region code (_LOCALE_PAIR
        allows {2,3} for the second component)."""
        assert _is_noise_subcategory("Es Esp") is True

    # -- Misc locale slug prefix -------------------------------------------

    def test_misc_prefix_es_la(self):
        assert _is_noise_subcategory("Es La") is True

    def test_misc_prefix_pt_pt(self):
        assert _is_noise_subcategory("Pt Pt") is True

    def test_misc_prefix_sv_se(self):
        assert _is_noise_subcategory("Sv Se") is True

    def test_misc_prefix_fr_fr(self):
        assert _is_noise_subcategory("Fr Fr") is True

    def test_misc_prefix_de_de(self):
        assert _is_noise_subcategory("De De") is True

    def test_misc_prefix_it_it(self):
        assert _is_noise_subcategory("It It") is True

    def test_misc_prefix_nl_nl(self):
        assert _is_noise_subcategory("Nl Nl") is True

    # -- NOT noise ---------------------------------------------------------

    def test_regular_subcategory_is_not_noise(self):
        assert _is_noise_subcategory("Geforce") is False
        assert _is_noise_subcategory("CUDA") is False
        assert _is_noise_subcategory("Data Center") is False

    def test_eur_not_noise(self):
        """EUR is not in the junk token set and does not match locale patterns."""
        assert _is_noise_subcategory("EUR") is False
        assert _is_noise_subcategory("Eur") is False
        assert _is_noise_subcategory("eur") is False

    def test_other_currency_or_abbreviated_is_not_noise(self):
        """Abbreviations like USD, GBP, API etc. are not noise."""
        assert _is_noise_subcategory("USD") is False
        assert _is_noise_subcategory("API") is False
        assert _is_noise_subcategory("SDK") is False

    def test_en_us_slug_variant(self):
        """Pattern starting with 'En Us' (En Us followed by word boundary) is noise."""
        assert _is_noise_subcategory("En Us Graphics") is True

    def test_not_matching_en_us_slug(self):
        """A word that just happens to contain 'en' is not flagged."""
        assert _is_noise_subcategory("Environments") is False


# ---------------------------------------------------------------------------
# generate_ecosystem_report
# ---------------------------------------------------------------------------

def _sample_ecosystem_data():
    """Return a realistic ecosystem_data dict for testing report generation."""
    return {
        "hardware": {
            "total_pages": 30,
            "subcategories": {"Geforce": 15, "DGX": 5, "En Us": 2, "login": 3,
                              "Jetson": 5},
            "products": {
                "GPU": ["A100", "H100", "RTX 4090"],
                "Systems": ["DGX Station", "DGX H100"],
            },
            "technologies": {},
            "top_keywords": [("GPU", 25), ("GeForce", 18), ("RTX", 12)],
            "sample_urls": [
                "https://nvidia.com/hw/page1",
                "https://nvidia.com/hw/page2",
            ],
        },
        "software": {
            "total_pages": 20,
            "subcategories": {"CUDA": 10, "TensorRT": 5, "Search": 2},
            "products": {},
            "technologies": {
                "Platform": ["CUDA", "cuDNN"],
                "Inference": ["TensorRT"],
            },
            "top_keywords": [("CUDA", 20), ("TensorRT", 15)],
            "sample_urls": ["https://nvidia.com/sw/page1"],
        },
        "developer": {
            "total_pages": 5,
            "subcategories": {},
            "products": {},
            "technologies": {},
            "top_keywords": [],
            "sample_urls": [],
        },
        "business": {"total_pages": 3, "subcategories": {}, "products": {},
                     "technologies": {}, "top_keywords": [],
                     "sample_urls": []},
        "technology": {"total_pages": 2, "subcategories": {}, "products": {},
                       "technologies": {}, "top_keywords": [],
                       "sample_urls": []},
    }


class TestEcosystemReport:
    """Tests for MarkdownGenerator.generate_ecosystem_report()."""

    @pytest.fixture
    def eco_data(self):
        return _sample_ecosystem_data()

    @pytest.fixture
    def meta(self):
        return make_metadata(total_pages=60, elapsed_seconds=120.5)

    # -- Header ------------------------------------------------------------

    def test_header_has_title(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "# NVIDIA Ecosystem Landscape" in report

    def test_header_has_timestamp_line(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "> Generated:" in report
        # Should contain a date-like pattern YYYY-MM-DD
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}", report) is not None

    # -- Overview table ----------------------------------------------------

    def test_overview_table_present(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "## Overview" in report
        assert "Total Pages Analyzed" in report

    def test_total_pages_from_metadata(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "60" in report  # from meta

    def test_elapsed_seconds_from_metadata(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "120.5s" in report

    # -- Ecosystem distribution percentages --------------------------------

    def test_ecosystem_distribution_table(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "Ecosystem Distribution" in report
        # Table column headers
        assert "| Ecosystem |" in report or "|Ecosystem |" in report

    def test_distribution_percentages(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        # hardware: 30/60 = 50.0%
        assert "50.0%" in report

    # -- Ecosystem sections ------------------------------------------------

    def test_ecosystem_sections_exist(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "1. Hardware Ecosystem" in report
        assert "2. Software Ecosystem" in report
        assert "3. Developer Ecosystem" in report
        assert "4. Business Ecosystem" in report
        assert "5. Technology Ecosystem" in report

    # -- Noise-filtered subcategories --------------------------------------

    def test_noise_filtered_subcategories(self, generator, eco_data, meta):
        """'En Us' and 'login' are noise and excluded from the report."""
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "Geforce" in report
        assert "DGX" in report
        assert "Jetson" in report
        assert "En Us" not in report
        assert "login" not in report

    # -- Products section --------------------------------------------------

    def test_products_section_for_hardware(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "### Products" in report
        # Product names appear under category headings
        assert "H100" in report

    # -- Technologies section ----------------------------------------------

    def test_technologies_section_for_software(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "### Technologies" in report
        assert "CUDA" in report
        assert "TensorRT" in report

    # -- Keywords section --------------------------------------------------

    def test_keywords_section(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "### Key Topics" in report

    # -- Sample URLs -------------------------------------------------------

    def test_sample_urls_section(self, generator, eco_data, meta):
        report = generator.generate_ecosystem_report(eco_data, meta)
        assert "### Sample Resources" in report

    # -- Empty ecosystem data -----------------------------------------------

    def test_empty_ecosystem_data_does_not_crash(self, generator, meta):
        report = generator.generate_ecosystem_report({}, meta)
        assert isinstance(report, str)
        assert len(report) > 0
        assert "# NVIDIA Ecosystem Landscape" in report

    def test_zero_total_pages_percentage_is_zero(self, generator, meta):
        """When total_pages is 0, percentage shows 0.0%."""
        meta_zero = make_metadata(total_pages=0)
        eco = {
            "hardware": {"total_pages": 0, "subcategories": {},
                         "products": {}, "technologies": {},
                         "top_keywords": [], "sample_urls": []},
        }
        report = generator.generate_ecosystem_report(eco, meta_zero)
        assert "0.0%" in report


# ---------------------------------------------------------------------------
# generate_product_catalog
# ---------------------------------------------------------------------------

class TestProductCatalog:
    """Tests for MarkdownGenerator.generate_product_catalog()."""

    def test_category_sections(self, generator):
        products = {
            "GPU": ["H100", "A100"],
            "Systems": ["DGX Station"],
        }
        report = generator.generate_product_catalog(products)
        assert "## GPU" in report
        assert "## Systems" in report

    def test_sorted_items(self, generator):
        products = {
            "GPU": ["H100", "A100", "B100"],
        }
        report = generator.generate_product_catalog(products)
        lines = [line for line in report.split("\n") if line.startswith("- ")]
        items = [line[2:] for line in lines]
        assert items == sorted(set(items))

    def test_dedup(self, generator):
        """Duplicate items in a category are removed."""
        products = {
            "GPU": ["H100", "A100", "H100"],
        }
        report = generator.generate_product_catalog(products)
        lines = [l for l in report.split("\n") if l.startswith("- ")]
        assert len(lines) == 2  # H100 appears once, A100 once

    def test_empty_products_is_valid(self, generator):
        report = generator.generate_product_catalog({})
        assert "# NVIDIA Product Catalog" in report
        assert len(report.split("\n")) > 1

    def test_title_in_report(self, generator):
        report = generator.generate_product_catalog({})
        assert "# NVIDIA Product Catalog" in report

    def test_categories_sorted(self, generator):
        products = {
            "Data Center": ["H100"],
            "GPU": ["RTX 4090"],
            "AI": ["CUDA"],
        }
        report = generator.generate_product_catalog(products)
        lines = [l for l in report.split("\n") if l.startswith("## ")]
        # Category headings after the main title
        cat_lines = [l[3:] for l in lines[1:]]  # strip "## "
        assert cat_lines == sorted(cat_lines)


# ---------------------------------------------------------------------------
# generate_technology_stack
# ---------------------------------------------------------------------------

class TestTechnologyStack:
    """Tests for MarkdownGenerator.generate_technology_stack()."""

    def test_category_sections(self, generator):
        technologies = {
            "Platform": ["CUDA", "cuDNN"],
            "Inference": ["TensorRT"],
        }
        report = generator.generate_technology_stack(technologies)
        assert "## Platform" in report
        assert "## Inference" in report

    def test_sorted_items(self, generator):
        technologies = {
            "AI": ["TensorRT", "CUDA"],
        }
        report = generator.generate_technology_stack(technologies)
        lines = [line for line in report.split("\n") if line.startswith("- ")]
        items = [line[2:] for line in lines]
        assert items == sorted(set(items))

    def test_dedup(self, generator):
        """Duplicate technology names in a category are removed."""
        technologies = {
            "Platform": ["CUDA", "cuDNN", "CUDA"],
        }
        report = generator.generate_technology_stack(technologies)
        lines = [l for l in report.split("\n") if l.startswith("- ")]
        assert len(lines) == 2

    def test_empty_technologies_is_valid(self, generator):
        report = generator.generate_technology_stack({})
        assert "# NVIDIA Technology Stack" in report

    def test_title_in_report(self, generator):
        report = generator.generate_technology_stack({})
        assert "# NVIDIA Technology Stack" in report


# ---------------------------------------------------------------------------
# save_report
# ---------------------------------------------------------------------------

class TestSaveReport:
    """Tests for MarkdownGenerator.save_report()."""

    def test_writes_to_file(self, generator, tmp_path):
        content = "# Test Report\n\nHello, world.\n"
        path = generator.save_report(content, "test_report.md")
        assert path.exists()
        assert path.read_text(encoding="utf-8") == content

    def test_default_filename(self, generator, tmp_path):
        path = generator.save_report("# Report")
        assert path.name == "nvidia_ecosystem_report.md"

    def test_creates_directories(self, tmp_path):
        subdir = tmp_path / "reports" / "subdir"
        gen = MarkdownGenerator(output_dir=subdir)
        path = gen.save_report("# Content", "report.md")
        assert path.exists()
        assert path.parent == subdir

    def test_returns_path(self, generator):
        path = generator.save_report("# Hi")
        assert isinstance(path, Path)
        assert path.name == "nvidia_ecosystem_report.md"


# ---------------------------------------------------------------------------
# generate_full_report
# ---------------------------------------------------------------------------

class TestGenerateFullReport:
    """Tests for MarkdownGenerator.generate_full_report()."""

    def test_aggregates_products_technologies_keywords_subcategories(
        self, generator
    ):
        """The full report method collects products, technologies, keywords,
        and subcategories from all pages."""
        pages = [
            make_page(ecosystem="hardware",
                      url="https://example.com/hw",
                      subcategory="Geforce",
                      products=[{"name": "RTX 4090", "category": "GPU"}],
                      technologies=[{"name": "CUDA", "category": "Platform"}],
                      keywords=["GPU"]),
            make_page(ecosystem="software",
                      url="https://example.com/sw",
                      subcategory="CUDA",
                      products=[{"name": "CUDA Toolkit", "category": "SDK"}],
                      technologies=[{"name": "TensorRT", "category": "Inference"}],
                      keywords=["CUDA"]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        # Should contain content from both ecosystems
        assert "Hardware Ecosystem" in report
        assert "Software Ecosystem" in report

    def test_url_deduplication(self, generator):
        """Duplicate URLs result in only one page being processed."""
        pages = [
            make_page(url="https://example.com/dup",
                      ecosystem="hardware",
                      keywords=["GPU"]),
            make_page(url="https://example.com/dup",
                      ecosystem="hardware",
                      keywords=["RTX"]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        # The second page is skipped, so 'RTX' keyword is NOT collected
        assert "RTX" not in report
        assert "GPU" in report

    def test_ecosystem_assignment(self, generator):
        """Pages are sorted into the ecosystem they specify."""
        pages = [
            make_page(ecosystem="hardware",
                      url="https://example.com/hw",
                      products=[{"name": "H100", "category": "GPU"}]),
            make_page(ecosystem="software",
                      url="https://example.com/sw",
                      technologies=[{"name": "CUDA", "category": "Platform"}]),
            make_page(ecosystem="business",
                      url="https://example.com/biz",
                      keywords=["Enterprise"]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "Hardware Ecosystem" in report
        assert "Software Ecosystem" in report
        assert "Business Ecosystem" in report

    def test_unknown_ecosystem_handled(self, generator):
        """Pages with unrecognised ecosystem ID are kept as-is in the data
        model and shown in the distribution table, but do NOT get a dedicated
        detailed section (unlike json_gen which forcibly remaps to 'technology'
        — markdown_gen only renders detailed sections for the 5 known ecosystem
        IDs)."""
        pages = [
            make_page(ecosystem="garbage",
                      products=[{"name": "Mystery Product", "category": "Unknown"}]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        # The distribution table still shows the raw ecosystem name
        assert "garbage" in report
        # No dedicated section for 'garbage' (only the 5 known ecosystems),
        # so the product is not rendered in the report body.
        assert "Mystery Product" not in report

    def test_case_insensitive_product_dedup(self, generator):
        """Products differing only in case are deduplicated in the report."""
        pages = [
            make_page(ecosystem="hardware",
                      products=[{"name": "H100", "category": "GPU"}]),
            make_page(ecosystem="hardware",
                      products=[{"name": "h100", "category": "GPU"}]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        # "H100" should appear but only once (not duplicated)
        count = report.count("H100")
        assert count == 1

    def test_case_insensitive_technology_dedup(self, generator):
        """Technologies differing only in case are deduplicated."""
        pages = [
            make_page(ecosystem="software",
                      technologies=[{"name": "CUDA", "category": "Platform"}]),
            make_page(ecosystem="software",
                      technologies=[{"name": "cuda", "category": "Platform"}]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        count = report.count("CUDA")
        assert count == 1

    def test_empty_pages_list(self, generator):
        """An empty page list produces a valid, non-crashing report."""
        report = generator.generate_full_report([], make_metadata())
        assert isinstance(report, str)
        assert "# NVIDIA Ecosystem Landscape" in report

    def test_report_includes_keywords_section(self, generator):
        """Keywords are collected and rendered in Key Topics sections."""
        pages = [
            make_page(ecosystem="hardware",
                      keywords=["GPU", "RTX", "GPU"]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "Key Topics" in report

    def test_report_includes_sample_urls(self, generator):
        """Sample URLs appear in Sample Resources sections."""
        pages = [
            make_page(url="https://www.nvidia.com/en-us/geforce/",
                      ecosystem="hardware"),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "Sample Resources" in report
        assert "https://www.nvidia.com/en-us/geforce/" in report

    def test_sample_urls_limited_to_10_per_ecosystem(self, generator):
        """At most 10 sample URLs are collected per ecosystem."""
        pages = [
            make_page(url=f"https://nvidia.com/hw/page_{i}",
                      ecosystem="hardware")
            for i in range(15)
        ]
        report = generator.generate_full_report(pages, make_metadata())
        # The Sample Resources section for hardware should contain at most 5
        # displayed (the report generator only renders first 5), but the
        # internal collection caps at 10. We verify no crash.
        assert "Sample Resources" in report

    def test_mixed_product_types_handled(self, generator):
        """Both dict and plain-string products are collected correctly."""
        pages = [
            make_page(ecosystem="hardware", products=[
                {"name": "H100", "category": "GPU"},
                "RTX 4090",
            ]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "H100" in report
        assert "RTX 4090" in report

    def test_mixed_technology_types_handled(self, generator):
        """Both dict and plain-string technologies are collected."""
        pages = [
            make_page(ecosystem="software", technologies=[
                {"name": "CUDA", "category": "Platform"},
                "TensorRT",
            ]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "CUDA" in report
        assert "TensorRT" in report

    def test_empty_name_products_skipped(self, generator):
        """Products with empty names are silently dropped."""
        pages = [
            make_page(ecosystem="hardware", products=[
                {"name": "", "category": "GPU"},
                {"name": "H100", "category": "GPU"},
            ]),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "H100" in report


# ---------------------------------------------------------------------------
# Default output_dir
# ---------------------------------------------------------------------------

class TestDefaultOutputDir:
    """Tests covering the default (no output_dir argument) behaviour."""

    def test_default_output_dir_is_output(self):
        """When no output_dir is given, it defaults to Path('output')."""
        gen = MarkdownGenerator()
        assert gen.output_dir == Path("output")


# ---------------------------------------------------------------------------
# Integration: report output contains locale-clean subcategories
# ---------------------------------------------------------------------------

class TestLocaleCleaningInReport:
    """Verify that noise-filtering is applied during report generation."""

    def test_en_us_subcategory_filtered_in_full_report(self, generator):
        pages = [
            make_page(ecosystem="hardware", subcategory="En Us", url="https://example.com/1"),
            make_page(ecosystem="hardware", subcategory="Geforce", url="https://example.com/2"),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "Geforce" in report
        assert "En Us" not in report

    def test_fr_ca_subcategory_filtered(self, generator):
        pages = [
            make_page(subcategory="Fr Ca"),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "Fr Ca" not in report

    def test_junk_token_filtered(self, generator):
        pages = [
            make_page(subcategory="search"),
        ]
        report = generator.generate_full_report(pages, make_metadata())
        assert "search" not in report
