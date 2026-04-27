"""Comprehensive pytest suite for software ecosystem report generator functions.

Covers: generators/software_ecosystem_report.py — _noise_subcat, _norm_tech_name,
_dedupe_tech_names, _top_subcategories, _flatten_tech_bucket,
build_software_ecosystem_markdown, and write_software_ecosystem_report.
"""

import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generators.software_ecosystem_report import (
    build_software_ecosystem_markdown,
    write_software_ecosystem_report,
    _noise_subcat,
    _norm_tech_name,
    _dedupe_tech_names,
    _top_subcategories,
    _flatten_tech_bucket,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_ecosystem(**kwargs):
    """Construct a minimal ecosystem dict for `build_software_ecosystem_markdown`."""
    return {
        "metadata": kwargs.get("metadata", {}),
        "summary": kwargs.get("summary", {}),
        "ecosystems": kwargs.get("ecosystems", {}),
    }


def make_tech_catalog():
    """Minimal technology catalog matching expected structure."""
    return {
        "categories": {
            "CUDA Platform": {"count": 2, "technologies": [{"name": "CUDA"}, {"name": "cuDNN"}]},
            "AI Frameworks": {"count": 1, "technologies": [{"name": "NeMo"}]},
        }
    }


# ---------------------------------------------------------------------------
# _noise_subcat
# ---------------------------------------------------------------------------

class TestNoiseSubcat:
    """Cover _noise_subcat: same patterns as other noise filters, None/empty, junk tokens."""

    def test_empty_string(self):
        assert _noise_subcat("") is True

    def test_none_input(self):
        assert _noise_subcat(None) is True

    def test_whitespace_only(self):
        assert _noise_subcat("   ") is True

    def test_junk_token_object(self):
        assert _noise_subcat("object") is True

    def test_junk_token_l(self):
        assert _noise_subcat("l") is True

    def test_junk_token_en(self):
        assert _noise_subcat("en") is True

    def test_junk_token_images(self):
        assert _noise_subcat("images") is True

    def test_junk_token_search(self):
        assert _noise_subcat("search") is True

    def test_junk_token_categories(self):
        assert _noise_subcat("categories") is True

    def test_junk_token_kb(self):
        assert _noise_subcat("kb") is True

    def test_junk_token_shop(self):
        assert _noise_subcat("shop") is True

    def test_junk_token_help(self):
        assert _noise_subcat("help") is True

    def test_junk_token_login(self):
        assert _noise_subcat("login") is True

    def test_junk_token_account(self):
        assert _noise_subcat("account") is True

    def test_junk_token_download(self):
        assert _noise_subcat("download") is True

    def test_junk_token_join(self):
        assert _noise_subcat("join") is True

    def test_junk_token_dashboard(self):
        assert _noise_subcat("dashboard") is True

    def test_junk_token_gtc(self):
        assert _noise_subcat("gtc") is True

    def test_junk_token_catalog(self):
        assert _noise_subcat("catalog") is True

    def test_junk_token_faq(self):
        assert _noise_subcat("faq") is True

    def test_junk_token_forums(self):
        assert _noise_subcat("forums") is True

    def test_junk_token_home(self):
        assert _noise_subcat("home") is True

    def test_junk_token_nvidia_com(self):
        assert _noise_subcat("nvidia.com") is True

    def test_junk_token_c(self):
        assert _noise_subcat("c") is True

    def test_junk_token_orgs(self):
        assert _noise_subcat("orgs") is True

    def test_junk_token_percent_20(self):
        assert _noise_subcat("%20") is True

    def test_junk_token_tag(self):
        assert _noise_subcat("tag") is True

    def test_junk_token_hot(self):
        assert _noise_subcat("hot") is True

    def test_junk_token_case_insensitive(self):
        assert _noise_subcat("En") is True
        assert _noise_subcat("IMAGES") is True
        assert _noise_subcat("Object") is True
        assert _noise_subcat("Help") is True

    def test_locale_pair_en_us(self):
        assert _noise_subcat("En Us") is True
        assert _noise_subcat("en us") is True

    def test_locale_pair_zh_cn(self):
        assert _noise_subcat("zh cn") is True

    def test_locale_pair_ja_jp(self):
        assert _noise_subcat("ja JP") is True

    def test_locale_pair_ko_kr(self):
        assert _noise_subcat("ko kr") is True

    def test_misc_slug_prefix_es_mx(self):
        assert _noise_subcat("Es Mx") is True

    def test_misc_slug_prefix_fr_ca(self):
        assert _noise_subcat("fr ca") is True

    def test_misc_slug_prefix_de_de(self):
        assert _noise_subcat("De DE") is True

    def test_misc_slug_prefix_it_it(self):
        assert _noise_subcat("it it") is True  # "It It" — case insensitive

    def test_valid_subcategory(self):
        assert _noise_subcat("CUDA") is False
        assert _noise_subcat("Geforce") is False
        assert _noise_subcat("Deep Learning") is False
        assert _noise_subcat("AI Platform") is False

    def test_non_ascii_not_locale_pattern(self):
        # Not caught by locale regex → False (regex is ASCII-only)
        assert _noise_subcat("你好") is False


# ---------------------------------------------------------------------------
# _norm_tech_name
# ---------------------------------------------------------------------------

class TestNormTechName:
    """Cover _norm_tech_name: whitespace collapse, newlines removed, empty string."""

    def test_whitespace_collapse(self):
        assert _norm_tech_name("hello   world") == "hello world"

    def test_trailing_whitespace(self):
        assert _norm_tech_name("hello  ") == "hello"

    def test_leading_whitespace(self):
        assert _norm_tech_name("  hello") == "hello"

    def test_newlines_replaced_with_space(self):
        assert _norm_tech_name("hello\nworld") == "hello world"

    def test_multiple_newlines(self):
        assert _norm_tech_name("hello\n\nworld") == "hello world"

    def test_mixed_whitespace(self):
        assert _norm_tech_name(" \t hello \n world \r ") == "hello world"

    def test_empty_string(self):
        assert _norm_tech_name("") == ""

    def test_none_input(self):
        assert _norm_tech_name(None) == ""

    def test_only_whitespace(self):
        assert _norm_tech_name(" \n \t ") == ""

    def test_single_word(self):
        assert _norm_tech_name("CUDA") == "CUDA"

    def test_preserve_internal_casing(self):
        assert _norm_tech_name("cuDNN") == "cuDNN"

    def test_carriage_return(self):
        assert _norm_tech_name("a\r\nb") == "a b"


# ---------------------------------------------------------------------------
# _dedupe_tech_names
# ---------------------------------------------------------------------------

class TestDedupeTechNames:
    """Cover _dedupe_tech_names: case-insensitive merge, whitespace variants,
    names >120 chars skipped, limit applied."""

    def test_case_insensitive_merge(self):
        result = _dedupe_tech_names(["CUDA", "cuda", "Cuda"], 10)
        # "CUDA" is longest, so it's kept
        assert "CUDA" in result
        assert len(result) == 1

    def test_whitespace_variants_merged(self):
        result = _dedupe_tech_names(["hello   world", "hello world", "hello  world"], 10)
        # All normalize to "hello world" via _norm_tech_name, so only one kept
        assert len(result) == 1
        assert result[0] == "hello world"

    def test_longest_variant_kept(self):
        # "abc", "ab", "a" normalize to distinct keys — all kept, sorted by length desc
        result = _dedupe_tech_names(["abc", "ab", "a"], 10)
        assert len(result) == 3
        assert result[0] == "abc"
        assert result[1] == "ab"
        assert result[2] == "a"

    def test_long_name_skipped(self):
        long_name = "x" * 121
        result = _dedupe_tech_names([long_name, "ok"], 10)
        assert long_name not in result
        assert "ok" in result

    def test_name_exactly_120_chars_kept(self):
        name_120 = "x" * 120
        result = _dedupe_tech_names([name_120], 10)
        assert name_120 in result

    def test_limit_applied(self):
        result = _dedupe_tech_names([f"tech-{i}" for i in range(20)], 5)
        assert len(result) == 5

    def test_empty_string_filtered(self):
        result = _dedupe_tech_names(["", "valid"], 10)
        assert "" not in result
        assert "valid" in result

    def test_whitespace_only_filtered(self):
        result = _dedupe_tech_names(["   ", "valid"], 10)
        assert "   " not in result
        assert "valid" in result

    def test_sorted_by_length_desc_then_alphabetical(self):
        result = _dedupe_tech_names(["a", "bb", "ccc", "dd", "eee"], 10)
        lengths = [len(n) for n in result]
        assert lengths == sorted(lengths, reverse=True)
        # When lengths equal, alphabetical applies
        for i in range(len(result) - 1):
            if len(result[i]) == len(result[i + 1]):
                assert result[i].lower() < result[i + 1].lower()

    def test_all_candidates_skipped_returns_empty(self):
        result = _dedupe_tech_names(["", " "], 10)
        assert result == []

    def test_single_valid_item(self):
        result = _dedupe_tech_names(["only"], 10)
        assert result == ["only"]

    def test_empty_input(self):
        result = _dedupe_tech_names([], 10)
        assert result == []

    def test_leading_trailing_whitespace_stripped_before_check(self):
        # "  a  " → _norm_tech_name → "a" → but "b" is longer
        result = _dedupe_tech_names(["  a  ", "b"], 10)
        assert "b" in result


# ---------------------------------------------------------------------------
# _top_subcategories
# ---------------------------------------------------------------------------

class TestTopSubcategories:
    """Cover _top_subcategories: noise filtered, sorted by count desc, limit applied."""

    def test_basic_extraction(self):
        sub = {"CUDA": 5, "Geforce": 3}
        result = _top_subcategories(sub, 10)
        assert len(result) == 2
        assert result[0] == ("CUDA", 5)
        assert result[1] == ("Geforce", 3)

    def test_sorted_by_count_desc(self):
        sub = {"A": 1, "B": 5, "D": 3}
        result = _top_subcategories(sub, 10)
        assert result[0][1] == 5
        assert result[1][1] == 3
        assert result[2][1] == 1

    def test_tie_broken_by_lowercase_alpha(self):
        sub = {"B_alpha": 5, "A_alpha": 5}
        result = _top_subcategories(sub, 10)
        assert result[0][0].lower() < result[1][0].lower()

    def test_noise_filtered(self):
        sub = {"object": 10, "CUDA": 5, "en": 3}
        result = _top_subcategories(sub, 10)
        names = [r[0] for r in result]
        assert "object" not in names
        assert "en" not in names
        assert "CUDA" in names

    def test_limit_applied(self):
        sub = {f"cat-{i}": i for i in range(20)}
        result = _top_subcategories(sub, 5)
        assert len(result) == 5

    def test_none_input(self):
        result = _top_subcategories(None, 10)
        assert result == []

    def test_empty_dict(self):
        result = _top_subcategories({}, 10)
        assert result == []

    def test_zero_limit(self):
        sub = {"CUDA": 5}
        result = _top_subcategories(sub, 0)
        assert result == []

    def test_non_int_values(self):
        sub = {"CUDA": "3", "Geforce": 2}
        result = _top_subcategories(sub, 10)
        # int("3") = 3
        assert ("CUDA", 3) in result

    def test_string_keys(self):
        sub = {"CUDA": 5}
        result = _top_subcategories(sub, 10)
        assert isinstance(result[0][0], str)


# ---------------------------------------------------------------------------
# _flatten_tech_bucket
# ---------------------------------------------------------------------------

class TestFlattenTechBucket:
    """Cover _flatten_tech_bucket: counter from category->names dict, case-insensitive
    counting."""

    def test_basic_flattening(self):
        bucket = {
            "CUDA Platform": ["CUDA", "cuDNN"],
            "AI": ["NeMo", "CUDA"],
        }
        result = _flatten_tech_bucket(bucket)
        assert isinstance(result, Counter)
        assert result["CUDA"] == 2
        assert result["cuDNN"] == 1
        assert result["NeMo"] == 1

    def test_whitespace_normalization(self):
        bucket = {"Cat": ["hello   world"]}
        result = _flatten_tech_bucket(bucket)
        assert result["hello world"] == 1

    def test_newline_normalization(self):
        bucket = {"Cat": ["hello\nworld"]}
        result = _flatten_tech_bucket(bucket)
        assert result["hello world"] == 1

    def test_empty_categories_ignored(self):
        bucket = {"Cat": []}
        result = _flatten_tech_bucket(bucket)
        assert len(result) == 0

    def test_non_list_values_ignored(self):
        bucket = {"Cat": "not a list"}
        result = _flatten_tech_bucket(bucket)
        assert len(result) == 0

    def test_none_input(self):
        result = _flatten_tech_bucket(None)
        assert isinstance(result, Counter)
        assert len(result) == 0

    def test_empty_dict(self):
        result = _flatten_tech_bucket({})
        assert len(result) == 0

    def test_non_string_items_converted(self):
        bucket = {"Cat": [123]}
        result = _flatten_tech_bucket(bucket)
        assert result["123"] == 1

    def test_single_category(self):
        bucket = {"Cat": ["A", "A", "B"]}
        result = _flatten_tech_bucket(bucket)
        assert result["A"] == 2
        assert result["B"] == 1

    def test_empty_names_filtered(self):
        bucket = {"Cat": ["valid", "", "   "]}
        result = _flatten_tech_bucket(bucket)
        assert "valid" in result
        assert "" not in result
        assert len(result) == 1

    def test_name_newline_only_results_empty(self):
        bucket = {"Cat": ["\n"]}
        result = _flatten_tech_bucket(bucket)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# build_software_ecosystem_markdown
# ---------------------------------------------------------------------------

class TestBuildSoftwareEcosystemMarkdown:
    """Cover build_software_ecosystem_markdown: sections present, distribution stats,
    technology categories table, noise filtering."""

    def test_main_heading(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "2024-01-01", "crawl_end": "2024-01-02",
                       "total_pages": 100},
            summary={"ecosystem_distribution": {"software": 30, "developer": 20}},
            ecosystems={
                "software": {"subcategories": {"CUDA": 5, "cuDNN": 3}},
                "developer": {"subcategories": {"SDK": 4}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "# NVIDIA Software Ecosystem Report" in result

    def test_generated_timestamp(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "", "crawl_end": "", "total_pages": 0},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "Generated:" in result
        assert "UTC" in result

    def test_purpose_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 1. Purpose and data sources" in result

    def test_classifier_snapshot_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            summary={"ecosystem_distribution": {"software": 30, "developer": 20}},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 2. Classifier snapshot: Software vs Developer" in result
        assert "30" in result
        assert "20" in result

    def test_software_subcategories_listed(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            summary={"ecosystem_distribution": {"software": 30, "developer": 0}},
            ecosystems={
                "software": {"subcategories": {"CUDA": 5, "cuDNN": 3}},
                "developer": {"subcategories": {}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "CUDA" in result
        assert "cuDNN" in result

    def test_no_subcategories_message(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            summary={"ecosystem_distribution": {"software": 30, "developer": 0}},
            ecosystems={
                "software": {"subcategories": {}},
                "developer": {"subcategories": {}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "no subcategories after filter" in result.lower()

    def test_developer_subcategories_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            summary={"ecosystem_distribution": {"software": 30, "developer": 20}},
            ecosystems={
                "software": {"subcategories": {"CUDA": 5}},
                "developer": {"subcategories": {"SDK": 4}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "2.2 Developer ecosystem" in result
        assert "SDK" in result

    def test_noise_subcategories_filtered(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            summary={"ecosystem_distribution": {"software": 30, "developer": 0}},
            ecosystems={
                "software": {"subcategories": {"object": 5, "CUDA": 3, "en": 2}},
                "developer": {"subcategories": {}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "object" not in result
        # "en" is a substring of "Generated" — check it doesn't appear as a subcategory item
        assert "- **en**:" not in result
        assert "CUDA" in result

    def test_technology_stack_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 3. Global software technology stack" in result

    def test_categories_table(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "CUDA Platform" in result
        assert "AI Frameworks" in result

    def test_technology_dedup_samples(self):
        catalog = {
            "categories": {
                "AI Frameworks": {"count": 3, "technologies": [
                    {"name": "NeMo"}, {"name": "NeMo"}, {"name": "Triton"},
                ]},
            }
        }
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, catalog)
        # NeMo should appear only once (deduped)
        assert result.count("NeMo") <= 2  # once in list, possibly once in section heading text

    def test_associated_technologies_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            ecosystems={
                "software": {
                    "subcategories": {"CUDA": 5},
                    "technologies": {"Cat": ["CUDA", "cuDNN"]},
                },
                "developer": {"subcategories": {}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 4. Technologies most associated" in result
        # CUDA and cuDNN flattened and displayed
        assert "CUDA" in result

    def test_limitations_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 6. Limitations" in result

    def test_related_reports_section(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 5. Related reports in `reports/`" in result

    def test_empty_metadata_handled_gracefully(self):
        eco = make_ecosystem()
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "# NVIDIA Software Ecosystem Report" in result
        assert "---" in result  # empty values replaced with dashes

    def test_none_summary_handled(self):
        eco = {"metadata": {"crawl_start": "", "crawl_end": "", "total_pages": 0},
               "summary": None, "ecosystems": None}
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "# NVIDIA Software Ecosystem Report" in result

    def test_empty_categories_catalog(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 0},
        )
        result = build_software_ecosystem_markdown(eco, {"categories": {}})
        assert "## 3. Global software technology stack" in result

    def test_categories_sorted_by_count_desc(self):
        catalog = {
            "categories": {
                "Small": {"count": 1, "technologies": [{"name": "A"}]},
                "Big": {"count": 10, "technologies": [{"name": "B"}]},
                "Medium": {"count": 5, "technologies": [{"name": "C"}]},
            },
        }
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, catalog)
        # Find table rows: "| Big | 10 |" should appear before "| Medium | 5 |"
        big_pos = result.index("| Big |")
        medium_pos = result.index("| Medium |")
        small_pos = result.index("| Small |")
        assert big_pos < medium_pos < small_pos

    def test_non_dict_technologies_handled(self):
        catalog = {
            "categories": {
                "Mixed": {"count": 3, "technologies": [
                    {"name": "Good"}, "raw_string", 42,
                ]},
            },
        }
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, catalog)
        # "Good" is a dict with name, "raw_string" and 42 are not dicts → skipped
        assert "Good" in result

    def test_sw_technologies_missing_handled(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            ecosystems={
                "software": {"subcategories": {}, "technologies": {}},
                "developer": {"subcategories": {}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 4. Technologies most associated" in result

    def test_sw_technologies_none_handled(self):
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
            ecosystems={
                "software": {"subcategories": {}, "technologies": None},
                "developer": {"subcategories": {}},
            },
        )
        result = build_software_ecosystem_markdown(eco, make_tech_catalog())
        assert "## 4. Technologies most associated" in result

    def test_payload_without_count(self):
        catalog = {
            "categories": {
                "Cat": {"technologies": [{"name": "X"}]},
            },
        }
        eco = make_ecosystem(
            metadata={"crawl_start": "A", "crawl_end": "B", "total_pages": 50},
        )
        result = build_software_ecosystem_markdown(eco, catalog)
        # {(payload or {}).get("count", 0)} → 0
        assert "Cat" in result


# ---------------------------------------------------------------------------
# write_software_ecosystem_report
# ---------------------------------------------------------------------------

class TestWriteSoftwareEcosystemReport:
    """Cover write_software_ecosystem_report: file written, FileNotFoundError when
    indices missing."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.tmp = tempfile.TemporaryDirectory()
        yield
        self.tmp.cleanup()

    def _write_indices(self, indices_dir):
        eco_path = indices_dir / "nvidia_ecosystem.json"
        tech_path = indices_dir / "nvidia_technologies.json"

        eco_path.write_text(json.dumps({
            "metadata": {"crawl_start": "2024-01-01", "crawl_end": "2024-01-02",
                          "total_pages": 100},
            "summary": {"ecosystem_distribution": {"software": 30, "developer": 20}},
            "ecosystems": {
                "software": {"subcategories": {"CUDA": 5, "cuDNN": 3}},
                "developer": {"subcategories": {"SDK": 4}},
            },
        }), encoding="utf-8")

        tech_path.write_text(json.dumps(make_tech_catalog()), encoding="utf-8")

    def test_writes_report_file(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)
        self._write_indices(indices)

        path = write_software_ecosystem_report(indices, reports)
        assert path.exists()
        assert path.suffix == ".md"

    def test_creates_reports_directory(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "nested" / "reports"
        indices.mkdir(parents=True)
        self._write_indices(indices)

        path = write_software_ecosystem_report(indices, reports)
        assert path.exists()

    def test_returns_path_object(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)
        self._write_indices(indices)

        path = write_software_ecosystem_report(indices, reports)
        assert isinstance(path, Path)

    def test_file_content_is_markdown(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)
        self._write_indices(indices)

        path = write_software_ecosystem_report(indices, reports)
        content = path.read_text(encoding="utf-8")
        assert "# NVIDIA Software Ecosystem Report" in content

    def test_missing_ecosystem_json_raises_file_not_found(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)

        # Only write technologies, not ecosystem
        tech_path = indices / "nvidia_technologies.json"
        tech_path.write_text(json.dumps(make_tech_catalog()), encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="nvidia_ecosystem.json"):
            write_software_ecosystem_report(indices, reports)

    def test_missing_technologies_json_raises_file_not_found(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)

        eco_path = indices / "nvidia_ecosystem.json"
        eco_path.write_text(json.dumps({
            "metadata": {}, "summary": {}, "ecosystems": {},
        }), encoding="utf-8")

        with pytest.raises(FileNotFoundError, match="nvidia_technologies.json"):
            write_software_ecosystem_report(indices, reports)

    def test_indices_dir_dne(self):
        indices = Path(self.tmp.name) / "nonexistent_dir"
        reports = Path(self.tmp.name) / "reports"

        with pytest.raises(FileNotFoundError):
            write_software_ecosystem_report(indices, reports)

    def test_overwrites_existing_report(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)
        reports.mkdir(parents=True)
        self._write_indices(indices)

        # Write a placeholder
        (reports / "nvidia_software_ecosystem_report.md").write_text("old", encoding="utf-8")

        path = write_software_ecosystem_report(indices, reports)
        content = path.read_text(encoding="utf-8")
        assert "NVIDIA Software Ecosystem Report" in content
        assert content != "old"

    def test_actual_output_file_name(self):
        indices = Path(self.tmp.name) / "indices"
        reports = Path(self.tmp.name) / "reports"
        indices.mkdir(parents=True)
        self._write_indices(indices)

        path = write_software_ecosystem_report(indices, reports)
        assert path.name == "nvidia_software_ecosystem_report.md"
