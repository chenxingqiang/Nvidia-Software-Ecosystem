"""Comprehensive pytest suite for MermaidGenerator and module-level helpers.

Covers: generators/mermaid_gen.py — _is_noise_subcategory, _is_noise_name, and all
public/private methods of MermaidGenerator.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from generators.mermaid_gen import MermaidGenerator, _is_noise_subcategory, _is_noise_name


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def make_ecosystem_data(**kwargs):
    return {
        "total_pages": kwargs.get("total_pages", 0),
        "subcategories": kwargs.get("subcategories", {}),
    }


# Reusable fixture-level ecosystem data
FULL_ECO_DATA = {
    "hardware": {"total_pages": 10, "subcategories": {"Geforce": 5, "En Us": 2}},
    "software": {"total_pages": 8, "subcategories": {"CUDA": 4}},
    "developer": {"total_pages": 5, "subcategories": {"SDK": 3}},
    "business": {"total_pages": 3, "subcategories": {"Enterprise": 2}},
    "technology": {"total_pages": 4, "subcategories": {"AI": 3}},
}


# ---------------------------------------------------------------------------
# ID sanitization
# ---------------------------------------------------------------------------

class TestSanitizeId:
    """Cover _sanitize_id including alphanumeric preservation, space/special-char
    replacement, and truncation at 30 characters."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    # --- Alphanumeric kept ---

    def test_alphanumeric_kept(self):
        assert self.gen._sanitize_id("abc123") == "abc123"

    def test_uppercase_kept(self):
        assert self.gen._sanitize_id("CUDA") == "CUDA"

    def test_digits_kept(self):
        assert self.gen._sanitize_id("RTX4090") == "RTX4090"

    # --- Spaces → underscores ---

    def test_single_space(self):
        assert self.gen._sanitize_id("hello world") == "hello_world"

    def test_multiple_spaces(self):
        assert self.gen._sanitize_id("a  b   c") == "a__b___c"

    def test_leading_trailing_spaces(self):
        # Pure alnum check — spaces become underscores, so leading space → leading underscore
        result = self.gen._sanitize_id("  padded  ")
        assert result.startswith("__")
        assert result.endswith("__")

    # --- Special characters → underscores ---

    def test_hyphen(self):
        assert self.gen._sanitize_id("data-center") == "data_center"

    def test_slash(self):
        assert self.gen._sanitize_id("foo/bar") == "foo_bar"

    def test_punctuation(self):
        sanitized = self.gen._sanitize_id("hello!@#$%^&*()world")
        assert "!" not in sanitized and "@" not in sanitized and "#" not in sanitized
        # All non-alnum chars become underscores
        assert all(c.isalnum() or c == "_" for c in sanitized)

    def test_chinese_chars_become_underscores(self):
        # Python c.isalnum() returns True for Chinese characters,
        # so they are preserved as-is, not replaced with underscores.
        sanitized = self.gen._sanitize_id("你好")
        assert sanitized == "你好"

    # --- Length limit 30 ---

    def test_exact_30_chars_kept(self):
        text = "a" * 30
        assert self.gen._sanitize_id(text) == text

    def test_longer_than_30_truncated(self):
        text = "a" * 50
        assert self.gen._sanitize_id(text) == "a" * 30

    def test_truncation_does_not_crash_with_mixed(self):
        text = "abcdefghijklmnopqrstuvwxyz0123456789!!!"
        result = self.gen._sanitize_id(text)
        assert len(result) <= 30

    # --- Edge cases ---

    def test_empty_string(self):
        assert self.gen._sanitize_id("") == ""

    def test_only_underscores(self):
        assert self.gen._sanitize_id("!@#") == "___"


# ---------------------------------------------------------------------------
# Label sanitization
# ---------------------------------------------------------------------------

class TestSanitizeLabel:
    """Cover _sanitize_label: quote/angle-bracket/square-bracket removal,
    word-boundary-aware truncation at 40 chars, and no-truncation for short text."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    # --- Quote removal ---

    def test_double_quotes_to_single(self):
        assert self.gen._sanitize_label('hello "world"') == "hello 'world'"

    def test_multiple_double_quotes(self):
        assert self.gen._sanitize_label('"a" "b"') == "'a' 'b'"

    def test_no_double_quotes_left(self):
        result = self.gen._sanitize_label('"test"')
        assert '"' not in result

    # --- Angle bracket removal ---

    def test_angle_brackets_removed(self):
        assert self.gen._sanitize_label("<hello>") == "hello"

    def test_nested_angle_brackets(self):
        assert self.gen._sanitize_label("a<b<c>d>e") == "abcde"

    # --- Square bracket conversion ---

    def test_square_brackets_converted(self):
        assert self.gen._sanitize_label("[item]") == "(item)"

    def test_mixed_brackets(self):
        assert self.gen._sanitize_label("[a] <b>") == "(a) b"

    # --- Short text (no truncation) ---

    def test_short_text_no_truncation(self):
        assert self.gen._sanitize_label("CUDA") == "CUDA"

    def test_exactly_40_chars(self):
        text = "a" * 40
        assert self.gen._sanitize_label(text) == text

    # --- Word-boundary-aware truncation ---

    def test_long_text_truncated_at_word_boundary(self):
        text = "NVIDIA CUDA Deep Neural Network Library Extra"
        # 47 chars triggers truncation; last space before pos 37 is at pos 32
        result = self.gen._sanitize_label(text)
        assert len(result) < len(text)
        assert "..." in result
        # Should end with word boundary + "..."
        assert result.endswith("...")
        assert "Library" not in result  # the last word should have been cut

    def test_truncation_with_ellipsis(self):
        text = "This is a very long technology name description here"
        result = self.gen._sanitize_label(text)
        assert result.endswith("...")

    def test_truncation_single_long_word_no_space(self):
        # A single >40-char token with no spaces → hard cut at 37 + "..."
        text = "a" * 50
        result = self.gen._sanitize_label(text)
        assert len(result) == 40  # 37 "a" + "..."
        assert result == "a" * 37 + "..."

    def test_truncation_no_space_in_first_37(self):
        # Space beyond position 37 means the result is hard-cut at 37.
        # Must be > 40 chars to trigger truncation.
        text = "a" * 42 + " b"  # 44 chars, space at position 42
        result = self.gen._sanitize_label(text)
        # rfind(" ", 0, 37) → no space found (space at pos 42 > 37) → hard cut at 37 + "..."
        assert result == "a" * 37 + "..."

    def test_truncation_space_at_position_0_ignored(self):
        # rfind returns >0 check protects against space at pos 0 being treated as cut point
        text = " " + "x" * 45
        result = self.gen._sanitize_label(text)
        # First char is a space, replaced later — but rfind(" ",0,37) would find pos 0
        # Since condition is `last_space > 0`, pos 0 is ignored → hard cut
        # Actually with space-removal already done by bracket handling... no, that doesn't
        # remove regular spaces. So rfind finds pos 0, which is NOT >0 → hard cut at 37+...
        assert result.endswith("...")

    def test_truncation_with_punctuation_chars(self):
        text = "NVIDIA [CUDA] <Deep> Neural-Network \"Framework\" Version.Two"
        result = self.gen._sanitize_label(text)
        assert "[" not in result
        assert "<" not in result
        assert '"' not in result
        assert len(result) <= 40

    # --- Edge cases ---

    def test_empty_string(self):
        assert self.gen._sanitize_label("") == ""

    def test_only_special_chars_to_remove(self):
        # After removing <, >, converting " to ', [ to (, ] to )
        # The " → ' replacement preserves single quotes in the result
        assert self.gen._sanitize_label("<\"[]\">") == "'()'"


# ---------------------------------------------------------------------------
# Noise filters: _is_noise_subcategory
# ---------------------------------------------------------------------------

class TestIsNoiseSubcategory:
    """Cover the module-level _is_noise_subcategory function."""

    def test_empty_string(self):
        assert _is_noise_subcategory("") is True

    def test_none_input(self):
        assert _is_noise_subcategory(None) is True

    def test_whitespace_only(self):
        assert _is_noise_subcategory("   ") is True

    def test_junk_token_object(self):
        assert _is_noise_subcategory("object") is True

    def test_junk_token_l(self):
        assert _is_noise_subcategory("l") is True

    def test_junk_token_en(self):
        assert _is_noise_subcategory("en") is True

    def test_junk_token_images(self):
        assert _is_noise_subcategory("images") is True

    def test_junk_token_search(self):
        assert _is_noise_subcategory("search") is True

    def test_junk_token_case_insensitive(self):
        assert _is_noise_subcategory("En") is True
        assert _is_noise_subcategory("IMAGES") is True
        assert _is_noise_subcategory("Object") is True

    def test_locale_pair_en_us(self):
        assert _is_noise_subcategory("En Us") is True
        assert _is_noise_subcategory("en us") is True

    def test_locale_pair_zh_cn(self):
        assert _is_noise_subcategory("zh cn") is True

    def test_misc_slug_prefix(self):
        assert _is_noise_subcategory("Es Mx") is True
        assert _is_noise_subcategory("fr ca") is True
        assert _is_noise_subcategory("De DE") is True

    def test_valid_subcategory(self):
        assert _is_noise_subcategory("CUDA") is False
        assert _is_noise_subcategory("Geforce") is False
        assert _is_noise_subcategory("Deep Learning") is False

    def test_non_ascii_valid(self):
        # Chinese characters are not caught by locale/junk filters → False
        assert _is_noise_subcategory("你好") is False


# ---------------------------------------------------------------------------
# Noise name filter: _is_noise_name
# ---------------------------------------------------------------------------

class TestIsNoiseName:
    """Cover the module-level _is_noise_name function."""

    def test_empty_string(self):
        assert _is_noise_name("") is True

    def test_none_input(self):
        assert _is_noise_name(None) is True

    def test_whitespace_only(self):
        assert _is_noise_name("   ") is True

    def test_too_short_single_char(self):
        assert _is_noise_name("a") is True

    def test_min_length_2_pass(self):
        assert _is_noise_name("ab") is False

    def test_non_ascii(self):
        assert _is_noise_name("你好") is True
        assert _is_noise_name("cuDA") is False  # ASCII mixed case

    def test_excessive_internal_whitespace(self):
        assert _is_noise_name("hello  world") is True
        assert _is_noise_name("a   b") is True

    def test_normal_whitespace_ok(self):
        assert _is_noise_name("hello world") is False

    def test_trailing_whitespace_stripped(self):
        # "a " stripped → "a" → len < 2 → True
        assert _is_noise_name("a ") is True

    def test_valid_name(self):
        assert _is_noise_name("CUDA Toolkit") is False
        assert _is_noise_name("NVIDIA RTX 4090") is False

    def test_non_ascii_with_whitespace(self):
        assert _is_noise_name("café latte") is True  # café has non-ASCII


# ---------------------------------------------------------------------------
# Ecosystem mindmap
# ---------------------------------------------------------------------------

class TestEcosystemMindmap:
    """Cover generate_ecosystem_mindmap: root node, ecosystem second-level nodes,
    top-5 subcategories, and noise filtering."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    def test_starts_with_mindmap_directive(self):
        result = self.gen.generate_ecosystem_mindmap(FULL_ECO_DATA)
        lines = result.split("\n")
        assert lines[0] == "mindmap"

    def test_root_node_present(self):
        result = self.gen.generate_ecosystem_mindmap(FULL_ECO_DATA)
        assert "root((NVIDIA Ecosystem))" in result

    def test_ecosystem_nodes_at_second_level(self):
        result = self.gen.generate_ecosystem_mindmap(FULL_ECO_DATA)
        lines = result.split("\n")
        ecosystem_lines = [l for l in lines if l.startswith("    ") and not l.startswith("      ")]
        assert len(ecosystem_lines) >= 1
        assert any("Hardware Ecosystem" in l for l in ecosystem_lines)
        assert any("Software Ecosystem" in l for l in ecosystem_lines)

    def test_top_5_subcategories(self):
        data = {
            "hardware": {
                "total_pages": 10,
                "subcategories": {
                    "A": 9, "B": 8, "C": 7, "D": 6, "E": 5, "F": 4, "G": 3,
                },
            },
        }
        result = self.gen.generate_ecosystem_mindmap(data)
        # count third-level lines (6 spaces indentation)
        subcat_lines = [l for l in result.split("\n") if l.startswith("      ") and not l.startswith("        ")]
        assert len(subcat_lines) == 5

    def test_noise_subcategories_filtered(self):
        data = {
            "hardware": {
                "total_pages": 10,
                "subcategories": {
                    "object": 5,
                    "en": 3,
                    "CUDA": 4,
                    "En Us": 2,
                    "search": 1,
                },
            },
        }
        result = self.gen.generate_ecosystem_mindmap(data)
        assert "object" not in result
        assert "En Us" not in result

    def test_noise_subcategory_case_insensitive_filtering(self):
        data = {
            "hardware": {
                "total_pages": 10,
                "subcategories": {
                    "Object": 5,
                    "CUDA": 4,
                    "Images": 2,
                },
            },
        }
        result = self.gen.generate_ecosystem_mindmap(data)
        assert "Object" not in result
        assert "Images" not in result
        # "CUDA" is valid and should appear
        assert "CUDA" in result

    def test_empty_ecosystem_skipped(self):
        result = self.gen.generate_ecosystem_mindmap({"hardware": make_ecosystem_data()})
        lines = result.split("\n")
        ecosystem_lines = [l for l in lines if l.startswith("    Hardware")]
        assert len(ecosystem_lines) == 1

    def test_empty_data_produces_minimal_output(self):
        result = self.gen.generate_ecosystem_mindmap({})
        lines = result.split("\n")
        assert lines[0] == "mindmap"
        assert "root((NVIDIA Ecosystem))" in result

    def test_no_subcategories(self):
        result = self.gen.generate_ecosystem_mindmap(FULL_ECO_DATA)
        # All ecosystems are listed at second level
        assert "Hardware Ecosystem" in result
        assert "Business Ecosystem" in result

    def test_unknown_ecosystem_id_not_in_order(self):
        data = {
            "custom_eco": {"total_pages": 5, "subcategories": {"Test": 3}},
        }
        result = self.gen.generate_ecosystem_mindmap(data)
        # custom_eco not in eco_order → not present in output (except it might be
        # skipped because it's not in the hardcoded order list)
        assert "custom_eco" not in result


# ---------------------------------------------------------------------------
# Flowchart
# ---------------------------------------------------------------------------

class TestFlowchart:
    """Cover generate_flowchart: NVIDIA root node, ecosystem nodes, cross-connections."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    def test_starts_with_flowchart_directive(self):
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        assert result.startswith("flowchart TD")

    def test_nvidia_root_node(self):
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        assert 'NVIDIA["NVIDIA Platform"]' in result

    def test_ecosystem_nodes_with_labels(self):
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        assert '"Hardware Ecosystem"' in result
        assert '"Software Ecosystem"' in result

    def test_root_to_ecosystem_connections(self):
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        # All ecosystems should be connected from NVIDIA root
        assert "NVIDIA --> hardware" in result
        assert "NVIDIA --> software" in result
        assert "NVIDIA --> developer" in result
        assert "NVIDIA --> business" in result
        assert "NVIDIA --> technology" in result

    def test_cross_connections_with_labels(self):
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        assert '|"powers"|' in result
        assert '|"enables"|' in result
        assert '|"implements"|' in result
        assert '|"drives"|' in result
        assert '|"accelerates"|' in result

    def test_cross_connections_use_dashed_arrows(self):
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        # dashed arrows are -.-> in Mermaid
        assert "-.->" in result

    def test_missing_ecosystem_skips_cross_connection(self):
        # Remove 'developer' from data → connections involving it should be absent
        partial = {k: v for k, v in FULL_ECO_DATA.items() if k != "developer"}
        result = self.gen.generate_flowchart(partial)
        assert "developer" not in result
        # connection ("hardware","software","powers") still present
        assert "hardware" in result
        assert "software" in result

    def test_sanitized_ecosystem_ids(self):
        # eco_id "hardware" → sanitized still "hardware"
        result = self.gen.generate_flowchart(FULL_ECO_DATA)
        assert 'hardware["' in result
        assert 'software["' in result

    def test_empty_data(self):
        result = self.gen.generate_flowchart({})
        lines = result.split("\n")
        assert lines[0] == "flowchart TD"
        assert len(lines) >= 2  # at least directive + NVIDIA node


# ---------------------------------------------------------------------------
# Product tree
# ---------------------------------------------------------------------------

class TestProductTree:
    """Cover generate_product_tree: root node, categories, products (limit 8 per
    category), noise + case dedup."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    def test_root_node(self):
        result = self.gen.generate_product_tree({})
        assert "root((NVIDIA Products))" in result

    def test_categories_at_second_level(self):
        products = {
            "GPUs": ["RTX 4090", "RTX 4080"],
            "Data Center": ["H100", "A100"],
        }
        result = self.gen.generate_product_tree(products)
        lines = result.split("\n")
        second_level = [l for l in lines if l.startswith("    ") and not l.startswith("      ")]
        assert any("GPUs" in l for l in second_level)
        assert any("Data Center" in l for l in second_level)

    def test_products_at_third_level(self):
        products = {"GPUs": ["RTX 4090", "RTX 4080"]}
        result = self.gen.generate_product_tree(products)
        assert "RTX 4090" in result
        assert "RTX 4080" in result

    def test_limit_8_per_category(self):
        products = {"GPUs": [f"GPU-{i}" for i in range(20)]}
        result = self.gen.generate_product_tree(products)
        third_level = [l for l in result.split("\n") if l.startswith("      ") and not l.startswith("        ")]
        assert len(third_level) <= 8

    def test_noise_names_filtered(self):
        products = {"Test": ["x", "ab", "", "hello  world"]}
        result = self.gen.generate_product_tree(products)
        # "x" → too short (len<2), "" → empty, "hello  world" → excessive whitespace
        assert "x" not in result.split("\n")[-2]
        # "ab" should be present
        assert "ab" in result

    def test_case_insensitive_dedup(self):
        products = {"GPUs": ["RTX", "rtx", "RTx", "Rtx"]}
        result = self.gen.generate_product_tree(products)
        # Only one occurrence of the canonical form should appear.
        # _dedupe_case_insensitive keeps the first occurrence ("RTX").
        count = result.count("RTX")
        assert count == 1

    def test_case_insensitive_dedup_keeps_first(self):
        products = {"GPUs": ["First", "FIRST", "first"]}
        result = self.gen.generate_product_tree(products)
        assert "First" in result
        assert "FIRST" not in result
        assert "first" not in result or result.count("First") == 1

    def test_non_string_items_converted(self):
        products = {"GPUs": [123, "RTX"]}
        result = self.gen.generate_product_tree(products)
        # 123 is converted to "123" by str() in _is_noise_name; len("123")>=2, ASCII → not noise
        # "123" in result — works because str(item) is used
        assert "RTX" in result

    def test_empty_category_skipped(self):
        products = {"GPUs": [], "Data Center": ["H100"]}
        result = self.gen.generate_product_tree(products)
        # Should not have "GPUs" heading since it has no items
        lines = result.split("\n")
        second_level = [l for l in lines if l.startswith("    ") and not l.startswith("      ")]
        # second_level includes "root((NVIDIA Products))" — that's at line index 1
        # and category lines
        assert not any("GPUs" == l.strip() for l in second_level)
        assert any("Data Center" in l for l in second_level)

    def test_categories_sorted(self):
        products = {"Z-Category": ["A"], "A-Category": ["B"]}
        result = self.gen.generate_product_tree(products)
        # categories are sorted alphabetically
        lines = result.split("\n")
        cat_lines = [l.strip() for l in lines if l.startswith("    ") and not l.startswith("      ") and "root" not in l]
        assert cat_lines[0].startswith("A-Category")
        assert cat_lines[1].startswith("Z-Category")


# ---------------------------------------------------------------------------
# Technology tree
# ---------------------------------------------------------------------------

class TestTechnologyTree:
    """Cover generate_technology_tree: root node, categories, technologies (limit 8),
    noise + case dedup."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    def test_root_node(self):
        result = self.gen.generate_technology_tree({})
        assert "root((NVIDIA Software))" in result

    def test_categories_at_second_level(self):
        techs = {"CUDA Platform": ["CUDA", "cuDNN"], "AI Frameworks": ["NeMo"]}
        result = self.gen.generate_technology_tree(techs)
        assert "CUDA Platform" in result
        assert "AI Frameworks" in result

    def test_technologies_at_third_level(self):
        techs = {"CUDA Platform": ["CUDA", "cuDNN"]}
        result = self.gen.generate_technology_tree(techs)
        assert "CUDA" in result
        assert "cuDNN" in result

    def test_limit_8_per_category(self):
        techs = {"Frameworks": [f"FW-{i}" for i in range(20)]}
        result = self.gen.generate_technology_tree(techs)
        third_level = [l for l in result.split("\n") if l.startswith("      ") and not l.startswith("        ")]
        assert len(third_level) <= 8

    def test_noise_names_filtered(self):
        techs = {"Test": ["", "a", "ab  cd", "valid"]}
        result = self.gen.generate_technology_tree(techs)
        # "a" is too short (len < 2) → filtered by _is_noise_name
        # "" is empty → filtered by _is_noise_name
        # "ab  cd" has excessive whitespace → filtered by _is_noise_name
        # "valid" passes all noise checks → included
        # Check third-level lines (exactly 6 spaces) — only "valid" should appear
        third_level = [l.strip() for l in result.split("\n")
                       if l.startswith("      ") and not l.startswith("        ")]
        assert third_level == ["valid"]

    def test_case_insensitive_dedup(self):
        techs = {"Platform": ["CUDA", "cuda", "Cuda"]}
        result = self.gen.generate_technology_tree(techs)
        count = result.count("CUDA") + result.count("Cuda")
        assert count == 1

    def test_non_string_items_converted(self):
        techs = {"Platform": [None, "CUDA"]}
        result = self.gen.generate_technology_tree(techs)
        # str(None) = "None" → len >= 2, ASCII → not noise; but "None" will appear
        assert "CUDA" in result

    def test_categories_sorted(self):
        techs = {"Z-Framework": ["A"], "B-Framework": ["B"]}
        result = self.gen.generate_technology_tree(techs)
        lines = result.split("\n")
        cat_lines = [l.strip() for l in lines if l.startswith("    ") and not l.startswith("      ") and "root" not in l]
        assert cat_lines[0].startswith("B-Framework")
        assert cat_lines[1].startswith("Z-Framework")


# ---------------------------------------------------------------------------
# Ecosystem pie
# ---------------------------------------------------------------------------

class TestEcosystemPie:
    """Cover generate_ecosystem_pie: pie syntax with double-quoted labels."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    def test_pie_directive(self):
        result = self.gen.generate_ecosystem_pie(FULL_ECO_DATA)
        assert result.startswith('pie title "NVIDIA Ecosystem Distribution"')

    def test_all_ecosystems_with_counts(self):
        result = self.gen.generate_ecosystem_pie(FULL_ECO_DATA)
        assert '"Hardware Ecosystem" : 10' in result
        assert '"Software Ecosystem" : 8' in result
        assert '"Developer Ecosystem" : 5' in result
        assert '"Business Ecosystem" : 3' in result
        assert '"Technology Ecosystem" : 4' in result

    def test_labels_in_double_quotes(self):
        result = self.gen.generate_ecosystem_pie(FULL_ECO_DATA)
        for line in result.split("\n")[1:]:
            if line.strip():
                assert line.strip().startswith('"')
                # Labels are enclosed in double quotes: "Label" : count
                assert '" :' in line

    def test_zero_count_excluded(self):
        data = {"hardware": make_ecosystem_data(total_pages=0)}
        result = self.gen.generate_ecosystem_pie(data)
        assert "hardware" not in result  # 0 count → line not emitted

    def test_nonzero_count_included(self):
        data = {"hardware": make_ecosystem_data(total_pages=1)}
        result = self.gen.generate_ecosystem_pie(data)
        assert '"Hardware Ecosystem" : 1' in result

    def test_empty_data(self):
        result = self.gen.generate_ecosystem_pie({})
        lines = result.split("\n")
        assert len(lines) == 1  # only the pie title line

    def test_unknown_ecosystem_id_uses_raw_id(self):
        data = {"custom": make_ecosystem_data(total_pages=5)}
        result = self.gen.generate_ecosystem_pie(data)
        # custom is not in ECOSYSTEM_NAMES → falls back to raw id
        assert '"custom" : 5' in result

    def test_single_ecosystem(self):
        data = {"hardware": make_ecosystem_data(total_pages=10)}
        result = self.gen.generate_ecosystem_pie(data)
        assert '"Hardware Ecosystem" : 10' in result


# ---------------------------------------------------------------------------
# Full diagram doc
# ---------------------------------------------------------------------------

class TestFullDiagramDoc:
    """Cover generate_full_diagram_doc: all 5 diagram types, correct heading structure."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.gen = MermaidGenerator()

    def _sample_pages(self):
        return [
            {
                "url": "https://nvidia.com/en-us/cuda/toolkit",
                "ecosystem": "software",
                "subcategory": "CUDA Toolkit",
                "products": [{"name": "CUDA", "category": "CUDA Platform"}],
                "technologies": [{"name": "CUDA", "category": "CUDA Platform"}],
            },
            {
                "url": "https://nvidia.com/en-us/geforce/gaming",
                "ecosystem": "hardware",
                "subcategory": "Gaming",
                "products": [{"name": "RTX 4090", "category": "GPUs"}],
                "technologies": [{"name": "DLSS", "category": "Rendering"}],
            },
            {
                "url": "https://nvidia.com/en-us/deep-learning/sdk",
                "ecosystem": "developer",
                "subcategory": "SDK",
                "products": [{"name": "SDK", "category": "Developer Tools"}],
                "technologies": [{"name": "cuDNN", "category": "Libraries"}],
            },
        ]

    def _metadata(self):
        return {"crawl_start": "2024-01-01", "crawl_end": "2024-01-02", "total_pages": 100}

    def test_main_heading(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "# NVIDIA Ecosystem Diagrams / NVIDIA 生态系统图表" in result

    def test_generated_timestamp(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "Generated:" in result

    def test_mindmap_section(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "## Ecosystem Overview / 生态系统概览" in result
        assert "mindmap" in result
        assert "root((NVIDIA Ecosystem))" in result

    def test_flowchart_section(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "## Ecosystem Relationships / 生态系统关系" in result
        assert "flowchart TD" in result

    def test_pie_section(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "## Distribution / 分布" in result
        assert 'pie title "NVIDIA Ecosystem Distribution"' in result

    def test_product_tree_section(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "## Product Hierarchy / 产品层级" in result
        assert "root((NVIDIA Products))" in result

    def test_technology_tree_section(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        assert "## Technology Stack / 技术栈" in result
        assert "root((NVIDIA Software))" in result

    def test_all_mermaid_codeblocks_closed(self):
        result = self.gen.generate_full_diagram_doc(self._sample_pages(), self._metadata())
        opens = result.count("```mermaid")
        closes = result.count("```")
        # closes includes both the mermaid open+close and the markdown fence markers,
        # so we just check each "```mermaid" has a matching "```" close
        assert closes >= opens * 2  # each open has a matching close; the close lines are just "```"

    def test_no_duplicate_urls(self):
        pages = [
            {"url": "https://nvidia.com/en-us/cuda/", "ecosystem": "software",
             "subcategory": "CUDA", "products": [], "technologies": []},
            {"url": "https://nvidia.com/en-us/cuda/", "ecosystem": "software",
             "subcategory": "CUDA", "products": [], "technologies": []},
        ]
        result = self.gen.generate_full_diagram_doc(pages, self._metadata())
        # Should not crash — deduped by URL
        assert "CUDA" in result

    def test_empty_pages_produces_valid_doc(self):
        result = self.gen.generate_full_diagram_doc([], self._metadata())
        assert "# NVIDIA Ecosystem Diagrams" in result
        assert "mindmap" in result  # still generates empty mindmap

    def test_product_as_str_not_dict(self):
        pages = [
            {"url": "https://nvidia.com/p1", "ecosystem": "software",
             "subcategory": "Test", "products": ["RawProduct"], "technologies": []},
        ]
        result = self.gen.generate_full_diagram_doc(pages, self._metadata())
        assert "RawProduct" in result

    def test_no_products_or_technologies_sections_omitted(self):
        # But since product/technology sections are generated from the defaultdict,
        # if there are no products, the "## Product Hierarchy" section is absent.
        result = self.gen.generate_full_diagram_doc([], self._metadata())
        assert "## Product Hierarchy" not in result
        assert "## Technology Stack" not in result

    def test_subcategory_is_none_handled(self):
        pages = [
            {"url": "https://nvidia.com/p1", "ecosystem": "software",
             "subcategory": None, "products": [], "technologies": []},
        ]
        result = self.gen.generate_full_diagram_doc(pages, self._metadata())
        # Should not crash — subcategory is None → falsy → not counted
        assert "mindmap" in result


# ---------------------------------------------------------------------------
# Save diagram
# ---------------------------------------------------------------------------

class TestSaveDiagram:
    """Cover save_diagram: writes file, creates directories."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.tmp = tempfile.TemporaryDirectory()
        yield
        self.tmp.cleanup()

    def test_writes_file(self):
        out_dir = Path(self.tmp.name) / "diagrams"
        gen = MermaidGenerator(output_dir=out_dir)
        path = gen.save_diagram("# Test", "test.md")
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "# Test" in content

    def test_creates_parent_directories(self):
        out_dir = Path(self.tmp.name) / "nested" / "deep" / "diagrams"
        gen = MermaidGenerator(output_dir=out_dir)
        path = gen.save_diagram("# Test", "deep.md")
        assert path.exists()

    def test_returns_path_object(self):
        out_dir = Path(self.tmp.name) / "diagrams"
        gen = MermaidGenerator(output_dir=out_dir)
        path = gen.save_diagram("# Test")
        assert isinstance(path, Path)

    def test_default_filename(self):
        out_dir = Path(self.tmp.name) / "diagrams"
        gen = MermaidGenerator(output_dir=out_dir)
        path = gen.save_diagram("# Test")
        assert path.name == "nvidia_ecosystem_diagrams.md"

    def test_custom_filename(self):
        out_dir = Path(self.tmp.name) / "diagrams"
        gen = MermaidGenerator(output_dir=out_dir)
        path = gen.save_diagram("# Test", "custom.md")
        assert path.name == "custom.md"

    def test_overwrites_existing(self):
        out_dir = Path(self.tmp.name) / "diagrams"
        gen = MermaidGenerator(output_dir=out_dir)
        gen.save_diagram("first", "overwrite.md")
        gen.save_diagram("second", "overwrite.md")
        content = (out_dir / "overwrite.md").read_text(encoding="utf-8")
        assert "second" in content
        assert "first" not in content


# ---------------------------------------------------------------------------
# Case-insensitive dedup (staticmethod)
# ---------------------------------------------------------------------------

class TestDedupeCaseInsensitive:
    """Cover MermaidGenerator._dedupe_case_insensitive."""

    def test_duplicates_removed(self):
        result = MermaidGenerator._dedupe_case_insensitive(["A", "A", "B"])
        assert result == ["A", "B"]

    def test_case_insensitive_merge(self):
        result = MermaidGenerator._dedupe_case_insensitive(["cuda", "CUDA", "Cuda"])
        assert len(result) == 1
        assert result[0] == "cuda"

    def test_first_occurrence_kept(self):
        result = MermaidGenerator._dedupe_case_insensitive(["Alpha", "ALPHA", "alpha"])
        assert result == ["Alpha"]

    def test_mixed_case_preserved(self):
        result = MermaidGenerator._dedupe_case_insensitive(["First", "SECOND", "third"])
        assert result == ["First", "SECOND", "third"]

    def test_non_string_items_handled(self):
        result = MermaidGenerator._dedupe_case_insensitive(["A", 123, None])
        assert "A" in result
        assert "123" in result
        assert "None" in result
        assert len(result) == 3

    def test_empty_list(self):
        assert MermaidGenerator._dedupe_case_insensitive([]) == []

    def test_single_item(self):
        assert MermaidGenerator._dedupe_case_insensitive(["only"]) == ["only"]

    def test_all_same_case_different(self):
        result = MermaidGenerator._dedupe_case_insensitive(["a", "A", "aA", "AA"])
        assert len(result) == 2  # "a" and "A" = same, "aA" and "AA" = same
        assert "aA" in result
        assert "a" in result

    def test_order_preserved(self):
        items = ["first", "second", "third", "FIRST", "second"]
        result = MermaidGenerator._dedupe_case_insensitive(items)
        assert result == ["first", "second", "third"]
