"""Comprehensive tests for the JSONGenerator in generators/json_gen.py."""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from generators.json_gen import JSONGenerator


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
    """Fresh JSONGenerator writing into a temporary directory."""
    return JSONGenerator(output_dir=tmp_path)


# ---------------------------------------------------------------------------
# generate_ecosystem_json
# ---------------------------------------------------------------------------

class TestEcosystemJson:
    """Tests for JSONGenerator.generate_ecosystem_json()."""

    # -- Structure ----------------------------------------------------------

    def test_structure_has_required_top_level_keys(self, generator):
        """Output contains 'metadata', 'summary', and 'ecosystems' keys."""
        result = generator.generate_ecosystem_json([], make_metadata())
        assert "metadata" in result
        assert "summary" in result
        assert "ecosystems" in result

    def test_metadata_copies_crawl_fields(self, generator):
        """Metadata section reflects the crawl metadata passed in."""
        meta = make_metadata(
            start_time="2025-06-01T10:00:00",
            end_time="2025-06-01T11:30:00",
            total_pages=42,
            elapsed_seconds=5400.0,
        )
        result = generator.generate_ecosystem_json([], meta)
        m = result["metadata"]
        assert m["crawl_start"] == "2025-06-01T10:00:00"
        assert m["crawl_end"] == "2025-06-01T11:30:00"
        assert m["total_pages"] == 42
        assert m["elapsed_seconds"] == 5400.0
        assert "generated_at" in m
        # generated_at should be an ISO 8601 string
        assert isinstance(m["generated_at"], str)
        assert "T" in m["generated_at"]

    def test_summary_has_total_ecosystems_and_distribution(self, generator):
        """Summary counts ecosystems and breaks down page counts."""
        result = generator.generate_ecosystem_json([], make_metadata())
        s = result["summary"]
        assert "total_ecosystems" in s
        assert "ecosystem_distribution" in s
        # Five fixed ecosystem IDs always present
        assert s["total_ecosystems"] == 5
        assert isinstance(s["ecosystem_distribution"], dict)

    def test_all_five_ecosystem_ids_present(self, generator):
        """The ecosystems dict always contains all five expected IDs."""
        result = generator.generate_ecosystem_json([], make_metadata())
        eco = result["ecosystems"]
        for eid in ("hardware", "software", "developer", "business", "technology"):
            assert eid in eco

    def test_each_ecosystem_entry_has_required_keys(self, generator):
        """Every ecosystem entry includes name, name_cn, counters, and
        collections."""
        result = generator.generate_ecosystem_json([], make_metadata())
        for eco_entry in result["ecosystems"].values():
            for key in ("name", "name_cn", "total_pages", "subcategories",
                        "products", "technologies", "keywords", "urls"):
                assert key in eco_entry

    # -- Ecosystem distribution --------------------------------------------

    def test_ecosystem_distribution_counts(self, generator):
        """Pages classified to each ecosystem are counted correctly."""
        pages = [
            make_page(ecosystem="hardware", url="https://example.com/1"),
            make_page(ecosystem="hardware", url="https://example.com/2"),
            make_page(ecosystem="software", url="https://example.com/3"),
            make_page(ecosystem="business", url="https://example.com/4"),
            make_page(ecosystem="technology", url="https://example.com/5"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        dist = result["summary"]["ecosystem_distribution"]
        assert dist["hardware"] == 2
        assert dist["software"] == 1
        assert dist["business"] == 1
        assert dist["technology"] == 1
        assert dist["developer"] == 0

    def test_total_pages_per_ecosystem(self, generator):
        """Each ecosystem entry's total_pages matches distribution."""
        pages = [
            make_page(ecosystem="hardware", url="https://example.com/hw1"),
            make_page(ecosystem="software", url="https://example.com/sw1"),
            make_page(ecosystem="software", url="https://example.com/sw2"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        assert result["ecosystems"]["hardware"]["total_pages"] == 1
        assert result["ecosystems"]["software"]["total_pages"] == 2

    # -- Unknown ecosystem fallback ----------------------------------------

    def test_unknown_ecosystem_falls_to_technology(self, generator):
        """Pages with unrecognised ecosystem IDs are assigned to 'technology'."""
        pages = [
            make_page(ecosystem="nonexistent", url="https://example.com/1"),
            make_page(ecosystem="garbage", url="https://example.com/2"),
            make_page(ecosystem="hardware", url="https://example.com/3"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        assert result["ecosystems"]["technology"]["total_pages"] == 2
        assert result["ecosystems"]["hardware"]["total_pages"] == 1

    # -- URL deduplication -------------------------------------------------

    def test_url_deduplication_across_pages(self, generator):
        """Duplicate URLs are counted once and the duplicate is skipped."""
        pages = [
            make_page(url="https://example.com/a", ecosystem="hardware"),
            make_page(url="https://example.com/a", ecosystem="hardware"),
            make_page(url="https://example.com/b", ecosystem="hardware"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        assert result["ecosystems"]["hardware"]["total_pages"] == 2
        assert result["summary"]["ecosystem_distribution"]["hardware"] == 2

    def test_empty_url_pages_still_counted(self, generator):
        """Pages with empty URLs are counted (not deduplicated as they are all '')."""
        pages = [
            make_page(url="", ecosystem="hardware"),
            make_page(url="", ecosystem="hardware"),
        ]
        # Second '' is not added to seen_urls (condition: "if url and url in
        # seen_urls"), and also not added to seen_urls (condition: "if url").
        # Both go through — total_pages == 2.
        result = generator.generate_ecosystem_json(pages, make_metadata())
        assert result["ecosystems"]["hardware"]["total_pages"] == 2

    # -- Subcategory counting -----------------------------------------------

    def test_subcategory_counting(self, generator):
        """Subcategory counts are aggregated per-ecosystem."""
        pages = [
            make_page(ecosystem="hardware", subcategory="Geforce", url="https://example.com/a"),
            make_page(ecosystem="hardware", subcategory="Geforce", url="https://example.com/b"),
            make_page(ecosystem="hardware", subcategory="DGX", url="https://example.com/c"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        subs = result["ecosystems"]["hardware"]["subcategories"]
        assert subs["Geforce"] == 2
        assert subs["DGX"] == 1

    def test_none_subcategory_not_counted(self, generator):
        """None subcategory is ignored in counting."""
        pages = [
            make_page(ecosystem="hardware", subcategory=None, url="https://example.com/a"),
            make_page(ecosystem="hardware", subcategory="GPU", url="https://example.com/b"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        subs = result["ecosystems"]["hardware"]["subcategories"]
        assert "GPU" in subs
        assert None not in subs

    # -- Product grouping by category with dedup ---------------------------

    def test_product_grouping_by_category(self, generator):
        """Products are grouped under their category key."""
        pages = [
            make_page(ecosystem="hardware", products=[
                {"name": "RTX 4090", "category": "GPU"},
                {"name": "H100", "category": "Data Center"},
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        prods = result["ecosystems"]["hardware"]["products"]
        assert "GPU" in prods
        assert "Data Center" in prods
        assert "RTX 4090" in prods["GPU"]
        assert "H100" in prods["Data Center"]

    def test_product_dedup_case_insensitive(self, generator):
        """Products with the same name in different casing are deduplicated."""
        pages = [
            make_page(ecosystem="hardware", products=[
                {"name": "RTX 4090", "category": "GPU"},
            ]),
            make_page(ecosystem="hardware", products=[
                {"name": "rtx 4090", "category": "GPU"},
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        prods = result["ecosystems"]["hardware"]["products"]["GPU"]
        # Only one entry, in the casing of the first occurrence
        assert len(prods) == 1

    def test_products_as_plain_strings(self, generator):
        """Plain-string products default to category 'Other'."""
        pages = [
            make_page(ecosystem="hardware", products=["GeForce", "CUDA"]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        prods = result["ecosystems"]["hardware"]["products"]
        assert "Other" in prods
        assert "GeForce" in prods["Other"]
        assert "CUDA" in prods["Other"]
        assert len(prods["Other"]) == 2

    def test_products_mixed_dict_and_string(self, generator):
        """Mixed product types (dict and string) are handled together."""
        pages = [
            make_page(ecosystem="hardware", products=[
                {"name": "RTX 4090", "category": "GPU"},
                "CUDA",
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        prods = result["ecosystems"]["hardware"]["products"]
        assert "GPU" in prods
        assert "Other" in prods

    def test_product_empty_name_skipped(self, generator):
        """Products with empty names are not added."""
        pages = [
            make_page(ecosystem="hardware", products=[
                {"name": "", "category": "GPU"},
                {"name": "H100", "category": "Data Center"},
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        prods = result["ecosystems"]["hardware"]["products"]
        # Empty name should be skipped
        assert "GPU" not in prods
        assert "Data Center" in prods

    # -- Technology grouping by category with dedup ------------------------

    def test_technology_grouping_by_category(self, generator):
        """Technologies are grouped under their category key."""
        pages = [
            make_page(ecosystem="software", technologies=[
                {"name": "CUDA", "category": "Platform"},
                {"name": "TensorRT", "category": "Inference"},
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        techs = result["ecosystems"]["software"]["technologies"]
        assert "Platform" in techs
        assert "Inference" in techs
        assert "CUDA" in techs["Platform"]
        assert "TensorRT" in techs["Inference"]

    def test_technology_dedup_case_insensitive(self, generator):
        """Technologies with same name in different casing are deduplicated."""
        pages = [
            make_page(ecosystem="software", technologies=[
                {"name": "CUDA", "category": "Platform"},
            ]),
            make_page(ecosystem="software", technologies=[
                {"name": "cuda", "category": "Platform"},
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        techs = result["ecosystems"]["software"]["technologies"]["Platform"]
        assert len(techs) == 1

    def test_technologies_as_plain_strings(self, generator):
        """Plain-string technologies default to category 'Other'."""
        pages = [
            make_page(ecosystem="software", technologies=["CUDA", "TensorRT"]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        techs = result["ecosystems"]["software"]["technologies"]
        assert "Other" in techs
        assert len(techs["Other"]) == 2

    def test_technology_empty_name_skipped(self, generator):
        """Technologies with empty names are not added."""
        pages = [
            make_page(ecosystem="software", technologies=[
                {"name": "", "category": "Platform"},
                {"name": "TensorRT", "category": "Inference"},
            ]),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        techs = result["ecosystems"]["software"]["technologies"]
        assert "Platform" not in techs
        assert "Inference" in techs

    # -- Keyword counting --------------------------------------------------

    def test_keyword_counting(self, generator):
        """Keywords are counted across pages in each ecosystem."""
        pages = [
            make_page(ecosystem="hardware", keywords=["GPU", "GeForce", "GPU"], url="https://example.com/a"),
            make_page(ecosystem="hardware", keywords=["GPU", "RTX"], url="https://example.com/b"),
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        kw = result["ecosystems"]["hardware"]["keywords"]
        assert kw["GPU"] == 3
        assert kw["GeForce"] == 1
        assert kw["RTX"] == 1

    def test_keywords_top_30_limit(self, generator):
        """Only the top 30 keywords (by count) are retained, sorted descending."""
        pages = []
        for i in range(50):
            pages.append(
                make_page(ecosystem="hardware", keywords=[f"kw_{i}"] * (50 - i))
            )
        result = generator.generate_ecosystem_json(pages, make_metadata())
        kw = result["ecosystems"]["hardware"]["keywords"]
        assert len(kw) <= 30
        # Verify descending order
        counts = list(kw.values())
        assert counts == sorted(counts, reverse=True)

    # -- Sample URLs -------------------------------------------------------

    def test_sample_url_limit_20(self, generator):
        """At most 20 sample URLs are retained per ecosystem."""
        pages = [
            make_page(url=f"https://example.com/page_{i}", ecosystem="hardware")
            for i in range(25)
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        urls = result["ecosystems"]["hardware"]["urls"]
        assert len(urls) == 20

    def test_url_list_preserves_order(self, generator):
        """Sample URLs appear in the order pages were processed."""
        pages = [
            make_page(url=f"https://example.com/page_{i}", ecosystem="hardware")
            for i in range(5)
        ]
        result = generator.generate_ecosystem_json(pages, make_metadata())
        urls = result["ecosystems"]["hardware"]["urls"]
        assert urls[0] == "https://example.com/page_0"
        assert urls[4] == "https://example.com/page_4"


# ---------------------------------------------------------------------------
# generate_product_json
# ---------------------------------------------------------------------------

class TestProductJson:
    """Tests for JSONGenerator.generate_product_json()."""

    def test_structure_has_required_keys(self, generator):
        """Output has 'generated_at', 'total_products', and 'categories'."""
        result = generator.generate_product_json([])
        assert "generated_at" in result
        assert "total_products" in result
        assert "categories" in result
        assert isinstance(result["generated_at"], str)
        assert "T" in result["generated_at"]

    def test_category_grouping(self, generator):
        """Products are grouped by category."""
        pages = [
            make_page(products=[
                {"name": "RTX 4090", "category": "GPU"},
                {"name": "H100", "category": "Data Center"},
            ]),
        ]
        result = generator.generate_product_json(pages)
        cats = result["categories"]
        assert "GPU" in cats
        assert "Data Center" in cats
        assert cats["GPU"]["count"] == 1
        assert cats["Data Center"]["count"] == 1

    def test_product_dedup_by_lowercase_key(self, generator):
        """Products with same lowercased name are deduplicated across pages."""
        pages = [
            make_page(products=[{"name": "RTX 4090", "category": "GPU"}]),
            make_page(products=[{"name": "rtx 4090", "category": "GPU"}]),
        ]
        result = generator.generate_product_json(pages)
        cats = result["categories"]
        assert cats["GPU"]["count"] == 1
        assert len(cats["GPU"]["products"]) == 1

    def test_url_tracking_per_product_limit_5(self, generator):
        """Each product records at most 5 URLs."""
        pages = [
            make_page(url=f"https://example.com/page_{i}",
                      products=[{"name": "RTX 4090", "category": "GPU"}])
            for i in range(10)
        ]
        result = generator.generate_product_json(pages)
        prod = result["categories"]["GPU"]["products"][0]
        assert len(prod["urls"]) == 5

    def test_product_sorting_by_name(self, generator):
        """Products are sorted alphabetically by name within their category."""
        pages = [
            make_page(products=[{"name": "H100", "category": "GPU"}]),
            make_page(products=[{"name": "A100", "category": "GPU"}]),
            make_page(products=[{"name": "B100", "category": "GPU"}]),
        ]
        result = generator.generate_product_json(pages)
        names = [p["name"] for p in result["categories"]["GPU"]["products"]]
        assert names == sorted(names, key=str.lower)

    def test_total_products_reflects_unique_count(self, generator):
        """total_products is the sum of unique products across categories."""
        pages = [
            make_page(products=[
                {"name": "RTX 4090", "category": "GPU"},
                {"name": "H100", "category": "Data Center"},
                {"name": "RTX 4090", "category": "GPU"},  # duplicate
            ]),
        ]
        result = generator.generate_product_json(pages)
        assert result["total_products"] == 2

    def test_empty_pages_list(self, generator):
        """An empty page list produces a valid but empty result."""
        result = generator.generate_product_json([])
        assert result["total_products"] == 0
        assert result["categories"] == {}

    def test_products_as_dict_with_name_category(self, generator):
        """Dict-style products use their name and category keys."""
        pages = [
            make_page(products=[
                {"name": "DGX Station", "category": "Systems"},
            ]),
        ]
        result = generator.generate_product_json(pages)
        cats = result["categories"]
        assert "Systems" in cats
        assert cats["Systems"]["products"][0]["name"] == "DGX Station"

    def test_products_as_plain_string(self, generator):
        """Plain-string products default to category 'Other'."""
        pages = [
            make_page(products=["RTX 4090"]),
        ]
        result = generator.generate_product_json(pages)
        assert "Other" in result["categories"]
        assert result["categories"]["Other"]["products"][0]["name"] == "RTX 4090"

    def test_url_deduplication_in_product_json(self, generator):
        """Duplicate page URLs are skipped during product collection."""
        pages = [
            make_page(url="https://example.com/a",
                      products=[{"name": "H100", "category": "GPU"}]),
            make_page(url="https://example.com/a",
                      products=[{"name": "A100", "category": "GPU"}]),
        ]
        result = generator.generate_product_json(pages)
        # Only first page was processed; A100 is not collected
        names = [p["name"] for p in result["categories"]["GPU"]["products"]]
        assert "H100" in names
        assert "A100" not in names

    def test_categories_sorted_alphabetically(self, generator):
        """Category keys in the result are sorted alphabetically."""
        pages = [
            make_page(products=[{"name": "X", "category": "Data Center"}]),
            make_page(products=[{"name": "Y", "category": "GPU"}]),
        ]
        result = generator.generate_product_json(pages)
        cat_names = list(result["categories"].keys())
        assert cat_names == sorted(cat_names)


# ---------------------------------------------------------------------------
# generate_technology_json
# ---------------------------------------------------------------------------

class TestTechnologyJson:
    """Tests for JSONGenerator.generate_technology_json()."""

    def test_structure_has_required_keys(self, generator):
        """Output has 'generated_at', 'total_technologies', and 'categories'."""
        result = generator.generate_technology_json([])
        assert "generated_at" in result
        assert "total_technologies" in result
        assert "categories" in result

    def test_category_grouping_with_lowercase_dedup(self, generator):
        """Technologies grouped by category, lowercase-deduplicated."""
        pages = [
            make_page(technologies=[
                {"name": "CUDA", "category": "Platform"}],
                url="https://example.com/a"),
            make_page(technologies=[
                {"name": "cuda", "category": "Platform"},
                {"name": "TensorRT", "category": "Inference"}],
                url="https://example.com/b"),
        ]
        result = generator.generate_technology_json(pages)
        cats = result["categories"]
        assert cats["Platform"]["count"] == 1
        assert cats["Inference"]["count"] == 1

    def test_empty_pages_list(self, generator):
        """An empty page list gives total_technologies=0 and empty categories."""
        result = generator.generate_technology_json([])
        assert result["total_technologies"] == 0
        assert result["categories"] == {}

    def test_technologies_sorted_by_name(self, generator):
        """Technologies within a category are sorted by lowercase name."""
        pages = [
            make_page(technologies=[
                {"name": "TensorRT", "category": "AI"},
                {"name": "CUDA", "category": "AI"},
            ]),
        ]
        result = generator.generate_technology_json(pages)
        techs = result["categories"]["AI"]["technologies"]
        names = [t["name"] for t in techs]
        assert names == sorted(names, key=str.lower)

    def test_technologies_as_plain_string(self, generator):
        """Plain-string technologies default to category 'Other'."""
        pages = [
            make_page(technologies=["CUDA"]),
        ]
        result = generator.generate_technology_json(pages)
        assert "Other" in result["categories"]
        assert result["categories"]["Other"]["technologies"][0]["name"] == "CUDA"

    def test_empty_name_skipped(self, generator):
        """Technologies with empty names are skipped."""
        pages = [
            make_page(technologies=[
                {"name": "", "category": "Platform"},
                {"name": "CUDA", "category": "Platform"},
            ]),
        ]
        result = generator.generate_technology_json(pages)
        assert result["categories"]["Platform"]["count"] == 1

    def test_url_limit_5_per_technology(self, generator):
        """Each technology records at most 5 URLs."""
        pages = [
            make_page(url=f"https://example.com/page_{i}",
                      technologies=[{"name": "CUDA", "category": "Platform"}])
            for i in range(10)
        ]
        result = generator.generate_technology_json(pages)
        tech = result["categories"]["Platform"]["technologies"][0]
        assert len(tech["urls"]) == 5


# ---------------------------------------------------------------------------
# save_json
# ---------------------------------------------------------------------------

class TestSaveJson:
    """Tests for JSONGenerator.save_json()."""

    def test_file_creation(self, generator, tmp_path):
        """save_json creates the file at the expected path."""
        data = {"key": "value"}
        path = generator.save_json(data, "test_output.json")
        assert path.exists()
        assert path.parent == tmp_path

    def test_content_roundtrip(self, generator):
        """Data written with save_json can be read back equivalently."""
        data = {
            "string": "hello",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"deep": True},
            "unicode": "\u4e2d\u6587",
        }
        path = generator.save_json(data, "roundtrip.json")
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_creates_parent_directories(self, tmp_path):
        """save_json creates intermediate directories if needed."""
        subdir = tmp_path / "deeply" / "nested"
        gen = JSONGenerator(output_dir=subdir)
        path = gen.save_json({"a": 1}, "data.json")
        assert path.exists()
        assert path.parent == subdir

    def test_ensure_ascii_false(self, generator):
        """Non-ASCII characters are written literally (as UTF-8 bytes), not
        escaped as \\uXXXX sequences."""
        data = {"name": "\u4e2d\u6587"}  # Chinese: 中文
        path = generator.save_json(data, "unicode.json")
        raw = path.read_text(encoding="utf-8")
        # ensure_ascii=False writes literal characters
        assert "\u4e2d\u6587" in raw  # 中文 in raw bytes
        # When ensure_ascii=True (the json.dumps default) they ARE escaped
        escaped = json.dumps(data)  # ensure_ascii=True by default
        assert "\\u4e2d\\u6587" in escaped

    def test_pretty_print_indentation(self, generator):
        """Output JSON uses 2-space indentation."""
        data = {"a": {"b": [1, 2, 3]}}
        path = generator.save_json(data, "indent.json")
        raw = path.read_text(encoding="utf-8")
        assert "  " in raw  # indentation spaces present


# ---------------------------------------------------------------------------
# generate_all
# ---------------------------------------------------------------------------

class TestGenerateAll:
    """Tests for JSONGenerator.generate_all()."""

    _ECO_FILE = "nvidia_ecosystem.json"
    _PROD_FILE = "nvidia_products.json"
    _TECH_FILE = "nvidia_technologies.json"

    def test_all_three_files_created(self, generator, tmp_path):
        """generate_all creates exactly the three expected JSON files."""
        pages = [
            make_page(ecosystem="hardware",
                      products=[{"name": "H100", "category": "GPU"}],
                      technologies=[{"name": "CUDA", "category": "Platform"}]),
        ]
        outputs = generator.generate_all(pages, make_metadata())
        assert (tmp_path / self._ECO_FILE).exists()
        assert (tmp_path / self._PROD_FILE).exists()
        assert (tmp_path / self._TECH_FILE).exists()

    def test_paths_returned_in_dict(self, generator):
        """The returned dict maps 'ecosystem', 'products', 'technologies'
        to Path objects."""
        outputs = generator.generate_all(
            [make_page()], make_metadata()
        )
        assert "ecosystem" in outputs
        assert "products" in outputs
        assert "technologies" in outputs
        assert outputs["ecosystem"].name == self._ECO_FILE
        assert outputs["products"].name == self._PROD_FILE
        assert outputs["technologies"].name == self._TECH_FILE

    def test_output_files_are_valid_json(self, generator, tmp_path):
        """All three generated files contain valid, parseable JSON."""
        generator.generate_all([make_page()], make_metadata())
        for filename in (self._ECO_FILE, self._PROD_FILE, self._TECH_FILE):
            with open(tmp_path / filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, dict)

    def test_outputs_share_data_source(self, generator, tmp_path):
        """Ecosystem and product JSONs reflect the same page data."""
        pages = [
            make_page(ecosystem="hardware",
                      products=[{"name": "H100", "category": "GPU"}],
                      technologies=[{"name": "CUDA", "category": "Platform"}]),
        ]
        generator.generate_all(pages, make_metadata())

        with open(tmp_path / self._ECO_FILE, "r", encoding="utf-8") as f:
            eco = json.load(f)
        with open(tmp_path / self._PROD_FILE, "r", encoding="utf-8") as f:
            prod = json.load(f)
        with open(tmp_path / self._TECH_FILE, "r", encoding="utf-8") as f:
            tech = json.load(f)

        assert eco["ecosystems"]["hardware"]["total_pages"] == 1
        assert prod["total_products"] == 1
        assert tech["total_technologies"] == 1


# ---------------------------------------------------------------------------
# Default output_dir
# ---------------------------------------------------------------------------

class TestDefaultOutputDir:
    """Tests covering the default (no output_dir argument) behaviour."""

    def test_default_output_dir_is_output(self):
        """When no output_dir is given, it defaults to Path('output')."""
        gen = JSONGenerator()
        assert gen.output_dir == __import__("pathlib").Path("output")
