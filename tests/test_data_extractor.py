"""Comprehensive tests for DataExtractor in processors/data_extractor.py."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from processors.data_extractor import (
    DataExtractor,
    ExtractedProduct,
    ExtractedTechnology,
    ExtractedPage,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def extractor():
    """Fresh DataExtractor instance."""
    return DataExtractor()


# ---------------------------------------------------------------------------
# _clean_name — static method
# ---------------------------------------------------------------------------


class TestCleanName:
    """Tests for DataExtractor._clean_name()."""

    # -- valid names ----------------------------------------------------------

    def test_short_name_passes(self):
        """Names with 2+ ASCII chars, no stop words, fewer than 5 words."""
        assert DataExtractor._clean_name("CUDA") == "CUDA"

    def test_name_with_spaces_passes(self):
        """Multi-word name (fewer than 5 words) passes."""
        assert DataExtractor._clean_name("GeForce RTX 4090") == "GeForce RTX 4090"

    def test_name_with_leading_trailing_whitespace(self):
        """Leading and trailing whitespace is stripped."""
        assert DataExtractor._clean_name("  TensorRT  ") == "TensorRT"

    def test_name_with_internal_whitespace_collapsed(self):
        """Multiple internal spaces/tabs collapse to single space."""
        assert DataExtractor._clean_name("DGX   A100") == "DGX A100"
        assert DataExtractor._clean_name("CUDA\t12.0") == "CUDA 12.0"

    def test_name_with_newline_collapsed(self):
        """Newlines collapse to single space."""
        result = DataExtractor._clean_name("NVIDIA\nAI\nEnterprise")
        assert result == "NVIDIA AI Enterprise"

    def test_four_word_name_passes(self):
        """A name with exactly 4 words is allowed (upper bound before rejection)."""
        assert DataExtractor._clean_name("NVIDIA AI Enterprise 5.0") == "NVIDIA AI Enterprise 5.0"

    def test_nvidia_pattern_name_passes(self):
        """Representative NVIDIA product/tech names all pass."""
        names = [
            "A100",
            "H100",
            "B200",
            "L40S",
            "L4",
            "ConnectX-7",
            "Spectrum-4",
            "BlueField-3",
            "Grace Hopper",
            "DGX Station",
            "DRIVE Orin",
            "Jetson AGX Orin",
            "Quadro RTX 8000",
            "Tesla V100",
            "DLSS 3",
            "Ray Tracing",
            "TAO Toolkit",
            "Base Command",
            "Fleet Command",
        ]
        for name in names:
            assert DataExtractor._clean_name(name) is not None, f"Expected {name!r} to pass"

    # -- None / empty input ---------------------------------------------------

    def test_none_returns_none(self):
        """None input returns None."""
        assert DataExtractor._clean_name(None) is None

    def test_empty_string_returns_none(self):
        """Empty string returns None."""
        assert DataExtractor._clean_name("") is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only string returns None."""
        assert DataExtractor._clean_name("   \t\n  ") is None

    def test_falsy_zero_int_returns_none(self):
        """Numeric 0 (falsy) returns None when passed — not name is True."""
        assert DataExtractor._clean_name(0) is None  # type: ignore[arg-type]

    # -- non-ASCII rejection --------------------------------------------------

    def test_chinese_characters_rejected(self):
        """Names containing Chinese characters are rejected."""
        assert DataExtractor._clean_name("中文字符") is None

    def test_japanese_characters_rejected(self):
        """Names containing Japanese characters are rejected."""
        assert DataExtractor._clean_name("日本語テキスト") is None

    def test_accented_latin_rejected(self):
        """Names with accented Latin characters (e.g., e-acute) are rejected."""
        assert DataExtractor._clean_name("NVIDIA\xe9") is None

    def test_mixed_ascii_and_non_ascii_rejected(self):
        """Even one non-ASCII character in the name causes rejection."""
        assert DataExtractor._clean_name("CUDA \u00e9dition") is None

    def test_emoji_rejected(self):
        """Names containing emoji are rejected."""
        assert DataExtractor._clean_name("GPU \U0001f680") is None

    # -- too short (<2 chars) -------------------------------------------------

    def test_single_letter_rejected(self):
        """Single letter is too short."""
        assert DataExtractor._clean_name("A") is None

    def test_single_digit_rejected(self):
        """Bare number of length 1 is too short."""
        assert DataExtractor._clean_name("1") is None

    def test_single_char_punctuation_rejected(self):
        """Single punctuation character is too short."""
        assert DataExtractor._clean_name("-") is None

    def test_minimum_length_two_passes(self):
        """Exactly 2 characters passes the length check."""
        assert DataExtractor._clean_name("L4") == "L4"

    # -- too long (>60 chars) -------------------------------------------------

    def test_exactly_60_chars_passes(self):
        """A name with exactly 60 characters is still valid."""
        name = "A" * 60
        assert len(name) == 60
        assert DataExtractor._clean_name(name) == name

    def test_61_chars_rejected(self):
        """A name longer than 60 characters is rejected."""
        name = "A" * 61
        assert DataExtractor._clean_name(name) is None

    def test_very_long_name_rejected(self):
        """Extremely long strings are rejected."""
        assert DataExtractor._clean_name("A" * 200) is None

    # -- stop words -----------------------------------------------------------

    def test_common_article_stop_word_rejected(self):
        """Name containing 'the' is rejected (article stop word)."""
        assert DataExtractor._clean_name("the GPU") is None

    def test_preposition_stop_word_rejected(self):
        """Name containing 'for' is rejected (preposition stop word)."""
        assert DataExtractor._clean_name("for developers") is None

    def test_conjunction_stop_word_rejected(self):
        """Name containing 'and' is rejected (conjunction stop word)."""
        assert DataExtractor._clean_name("AI and ML") is None

    def test_verb_stop_word_rejected(self):
        """Name containing 'includes' is rejected (verb stop word)."""
        assert DataExtractor._clean_name("CUDA includes toolkit") is None

    def test_stop_word_as_standalone_rejected(self):
        """A bare stop word is rejected."""
        assert DataExtractor._clean_name("provides") is None

    def test_stop_word_case_insensitive(self):
        """Stop-word check is case-insensitive."""
        assert DataExtractor._clean_name("THE GPU") is None
        assert DataExtractor._clean_name("For You") is None

    def test_legitimate_name_without_stop_words_passes(self):
        """Names without any stop words pass through."""
        assert DataExtractor._clean_name("NVIDIA Enterprise 5.0") is not None
        assert DataExtractor._clean_name("CUDA Toolkit") is not None

    def test_stop_word_substring_not_falsely_rejected(self):
        """The check splits on words, so substring matches are not falsely caught."""
        # "tensor" does not contain any stop word as a whole word; edge-case guard
        assert DataExtractor._clean_name("TensorCore") == "TensorCore"

    # -- 5+ words (sentence fragments) ----------------------------------------

    def test_five_word_sentence_rejected(self):
        """Five words or more are rejected as sentence fragments."""
        assert DataExtractor._clean_name("this is a five word sentence") is None

    def test_six_word_sentence_rejected(self):
        """Six-word sentence fragments are rejected."""
        assert DataExtractor._clean_name("this is a six word sentence extra") is None

    def test_four_words_accepted(self):
        """Four-word names are at the threshold and are accepted."""
        result = DataExtractor._clean_name("NVIDIA GeForce RTX 4090")
        assert result == "NVIDIA GeForce RTX 4090"


# ---------------------------------------------------------------------------
# Product extraction
# ---------------------------------------------------------------------------


class TestExtractProducts:
    """Tests for DataExtractor.extract_products()."""

    URL = "https://nvidia.com/test"

    def test_extracts_geforce_rtx_pattern(self, extractor):
        """GeForce RTX 4090 is extracted from content."""
        content = "The new GeForce RTX 4090 offers incredible performance."
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        assert "geforce rtx 4090" in names

    def test_extracts_rtx_ti_pattern(self, extractor):
        """RTX 4090 Ti is extracted via the RTX pattern."""
        content = "Introducing the RTX 4090 Ti."
        products = extractor.extract_products(content, self.URL)

        assert any("rtx 4090 ti" in p.name.lower() for p in products)

    def test_extracts_dgx_systems(self, extractor):
        """DGX A100 and DGX H100 are extracted."""
        content = "DGX A100 and DGX H100 power modern data centers."
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        assert "dgx a100" in names
        assert "dgx h100" in names

    def test_extracts_jetson_devices(self, extractor):
        """Jetson Orin and Jetson Nano are extracted."""
        content = "Jetson AGX Orin and Jetson Nano support edge AI workloads."
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        assert any("jetson" in n for n in names)
        # Jetson AGX Orin specifically
        assert "jetson agx orin" in names

    def test_extracts_datacenter_gpu_codes(self, extractor):
        """A100, H100, B200, L40S are extracted via the code-name pattern."""
        content = "We benchmarked A100, H100, B200, and L40S GPUs."
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        for expected in ["a100", "h100", "b200", "l40s"]:
            assert expected in names, f"Expected {expected!r} in {names}"

    def test_extracts_grace_hopper(self, extractor):
        """Grace Hopper platform is extracted."""
        content = "The Grace Hopper superchip combines CPU and GPU."
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        assert "grace hopper" in names

    def test_extracts_networking_products(self, extractor):
        """BlueField, ConnectX, Spectrum devices are extracted."""
        content = "BlueField-3 DPUs, ConnectX-7 adapters, and Spectrum-4 switches."
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        assert any("bluefield" in n for n in names)
        assert any("connectx" in n for n in names)
        assert any("spectrum" in n for n in names)

    def test_case_insensitive_extraction(self, extractor):
        """Regex matching is case-insensitive."""
        content = "geforce rtx 4090 and tesla v100 and quadro rtx 8000"
        products = extractor.extract_products(content, self.URL)

        names = {p.name.lower() for p in products}
        assert "geforce rtx 4090" in names

    def test_deduplication_by_lowercase_key(self, extractor):
        """Duplicates are removed based on case-insensitive name comparison."""
        content = "RTX 4090 is great. The RTX 4090 is powerful. Use an RTX 4090 today."
        products = extractor.extract_products(content, self.URL)

        rtx_entries = [p for p in products if "rtx 4090" in p.name.lower()]
        assert len(rtx_entries) == 1

    def test_deduplication_case_variant(self, extractor):
        """Mixed-case variants of the same product are deduplicated."""
        content = "RTX 4090 and rtx 4090 and Rtx 4090"
        products = extractor.extract_products(content, self.URL)

        rtx_entries = [p for p in products if "rtx 4090" in p.name.lower()]
        assert len(rtx_entries) == 1

    def test_unrelated_content_returns_empty(self, extractor):
        """Content with no NVIDIA product mentions returns an empty list."""
        content = "This is a page about baking recipes."
        products = extractor.extract_products(content, self.URL)

        assert products == []

    def test_product_has_correct_fields(self, extractor):
        """Extracted products have name, category, description, url, and empty features/specs."""
        products = extractor.extract_products("A100 GPU benchmarks", self.URL)

        assert len(products) >= 1
        product = products[0]
        assert isinstance(product, ExtractedProduct)
        assert product.name == "A100"
        assert product.category == "Data Center GPU"
        assert product.description == ""
        assert product.url == self.URL
        assert product.features == []
        assert product.specifications == {}

    def test_empty_content_returns_empty_list(self, extractor):
        """Empty content string returns an empty list."""
        assert extractor.extract_products("", self.URL) == []

    def test_multiple_pattern_matches_same_line(self, extractor):
        """Multiple product patterns matched in a single line all get extracted, deduped."""
        content = "We offer GeForce RTX 4090, DGX A100, and A100 for various workloads."
        products = extractor.extract_products(content, self.URL)

        # At minimum: GeForce RTX 4090, RTX 4090, DGX A100, A100
        # After dedup, A100 appears once; GeForce RTX 4090 and RTX 4090 are different keys
        assert len(products) >= 3

    def test_each_product_is_extracted_product_instance(self, extractor):
        """Every element in the returned list is an ExtractedProduct dataclass."""
        content = "GeForce RTX 4090 and Jetson Orin"
        products = extractor.extract_products(content, self.URL)

        assert len(products) > 0
        for p in products:
            assert isinstance(p, ExtractedProduct)


# ---------------------------------------------------------------------------
# Product categorization
# ---------------------------------------------------------------------------


class TestCategorizeProduct:
    """Tests for DataExtractor._categorize_product()."""

    def test_consumer_gpu_geforce(self, extractor):
        assert extractor._categorize_product("GeForce RTX 4090") == "Consumer GPU"

    def test_consumer_gpu_rtx(self, extractor):
        assert extractor._categorize_product("RTX 4090 Ti") == "Consumer GPU"

    def test_consumer_gpu_gtx(self, extractor):
        assert extractor._categorize_product("GTX 1660 Super") == "Consumer GPU"

    def test_professional_gpu_quadro(self, extractor):
        assert extractor._categorize_product("Quadro P6000") == "Professional GPU"

    def test_data_center_gpu_tesla(self, extractor):
        assert extractor._categorize_product("Tesla V100") == "Data Center GPU"

    def test_data_center_gpu_a100(self, extractor):
        assert extractor._categorize_product("A100") == "Data Center GPU"

    def test_data_center_gpu_h100(self, extractor):
        assert extractor._categorize_product("H100") == "Data Center GPU"

    def test_data_center_gpu_b100(self, extractor):
        assert extractor._categorize_product("B100") == "Data Center GPU"

    def test_data_center_gpu_l40(self, extractor):
        assert extractor._categorize_product("L40S") == "Data Center GPU"

    def test_dgx_systems(self, extractor):
        # Use DGX names that do not contain overlapping keywords from
        # earlier elif branches (e.g. "a100", "h100" are Data Center GPU).
        assert extractor._categorize_product("DGX Station") == "DGX Systems"
        assert extractor._categorize_product("DGX Cloud") == "DGX Systems"
        assert extractor._categorize_product("DGX SuperPOD") == "DGX Systems"

    def test_edge_ai_jetson(self, extractor):
        assert extractor._categorize_product("Jetson AGX Orin") == "Edge AI / Embedded"
        assert extractor._categorize_product("Jetson Nano") == "Edge AI / Embedded"

    def test_automotive_drive(self, extractor):
        assert extractor._categorize_product("DRIVE Orin") == "Automotive"
        assert extractor._categorize_product("DRIVE Thor") == "Automotive"

    def test_data_center_platform_grace(self, extractor):
        assert extractor._categorize_product("Grace CPU") == "Data Center Platform"

    def test_data_center_platform_hopper(self, extractor):
        assert extractor._categorize_product("Grace Hopper") == "Data Center Platform"

    def test_data_center_platform_blackwell(self, extractor):
        assert extractor._categorize_product("Blackwell B200") == "Data Center Platform"

    def test_networking_bluefield(self, extractor):
        assert extractor._categorize_product("BlueField-3") == "Networking"

    def test_networking_connectx(self, extractor):
        assert extractor._categorize_product("ConnectX-7") == "Networking"

    def test_networking_spectrum(self, extractor):
        assert extractor._categorize_product("Spectrum-4") == "Networking"

    def test_case_insensitive_categorization(self, extractor):
        """Categorization lowercases name before matching."""
        assert extractor._categorize_product("geforce rtx 4090") == "Consumer GPU"
        # Use DGX Station (no overlapping keywords) to avoid earlier-branch capture
        assert extractor._categorize_product("dgx station") == "DGX Systems"

    def test_other_hardware_unknown_name(self, extractor):
        """An unrecognized product name falls through to 'Other Hardware'."""
        assert extractor._categorize_product("UnknownDevice X99") == "Other Hardware"

    def test_empty_string_other_hardware(self, extractor):
        """Empty string maps to 'Other Hardware' (no category match)."""
        assert extractor._categorize_product("") == "Other Hardware"

    def test_category_priority_order(self, extractor):
        """
        Categorization uses elif chain: first matching branch wins.

        For names matching multiple branches, the first checked category applies:
        - "GeForce RTX" matches "rtx" -> Consumer GPU (checked first)
        - "Quadro RTX 8000" contains both "rtx" and "quadro",
          but "rtx" is checked before "quadro" -> Consumer GPU
        - "DGX A100" contains both "a100" and "dgx",
          but "a100" is checked before "dgx" -> Data Center GPU
        """
        assert extractor._categorize_product("GeForce RTX") == "Consumer GPU"
        assert extractor._categorize_product("Quadro RTX 8000") == "Consumer GPU"
        assert extractor._categorize_product("DGX A100") == "Data Center GPU"


# ---------------------------------------------------------------------------
# Technology extraction
# ---------------------------------------------------------------------------


class TestExtractTechnologies:
    """Tests for DataExtractor.extract_technologies()."""

    URL = "https://developer.nvidia.com/test"

    def test_extracts_cuda(self, extractor):
        content = "CUDA enables accelerated computing on NVIDIA GPUs."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "cuda" in names

    def test_extracts_cuda_with_version(self, extractor):
        content = "This application requires CUDA 12.0 or higher."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "cuda 12.0" in names

    def test_extracts_tensorrt(self, extractor):
        content = "TensorRT optimizes deep learning models for inference."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "tensorrt" in names

    def test_extracts_isaac(self, extractor):
        content = "The Isaac Sim platform for robot development."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert any("isaac" in n for n in names)

    def test_extracts_omniverse(self, extractor):
        content = "Omniverse platform engine for real-time 3D collaboration."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert any("omniverse" in n for n in names)

    def test_extracts_rapids(self, extractor):
        content = "RAPIDS accelerates GPU data science frameworks."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert any("rapids" in n for n in names)

    def test_extracts_deepstream(self, extractor):
        content = "DeepStream SDK platform for intelligent video analytics."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert any("deepstream" in n for n in names)

    def test_extracts_dlss(self, extractor):
        content = "DLSS 3 boosts frame rates with AI-powered rendering."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "dlss 3" in names

    def test_extracts_ray_tracing(self, extractor):
        content = "Ray Tracing delivers photorealistic lighting."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "ray tracing" in names

    def test_extracts_nvlink_nvswitch(self, extractor):
        content = "NVLink and NVSwitch provide high-speed GPU interconnect."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "nvlink" in names
        assert "nvswitch" in names

    def test_case_insensitive_extraction_tech(self, extractor):
        """Technology regex matching is case-insensitive."""
        content = "cuda and tensorrt and deepstream"
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "cuda" in names
        assert "tensorrt" in names

    def test_deduplication_tech(self, extractor):
        """Duplicate technology mentions are removed case-insensitively."""
        content = "CUDA 12.0 and cuda 12.0 and CUDA 12.0"
        technologies = extractor.extract_technologies(content, self.URL)

        cuda_versions = [t for t in technologies if "cuda 12.0" in t.name.lower()]
        assert len(cuda_versions) == 1

    def test_unrelated_content_returns_empty_tech(self, extractor):
        """Content with no NVIDIA technology mentions returns empty list."""
        content = "A recipe for chocolate chip cookies."
        technologies = extractor.extract_technologies(content, self.URL)

        assert technologies == []

    def test_technology_has_correct_fields(self, extractor):
        """Extracted technologies have the right fields and types."""
        technologies = extractor.extract_technologies("CUDA is a parallel computing platform.", self.URL)

        assert len(technologies) >= 1
        tech = technologies[0]
        assert isinstance(tech, ExtractedTechnology)
        assert tech.name == "CUDA"
        assert tech.category == "CUDA Platform"
        assert tech.description == ""
        assert tech.url == self.URL
        assert tech.related_products == []

    def test_empty_content_returns_empty_list_tech(self, extractor):
        "Empty content returns empty list for technologies."
        assert extractor.extract_technologies("", self.URL) == []

    def test_broadcast_and_canvas_technologies(self, extractor):
        """Broadcast and Canvas are caught by TECH_PATTERNS."""
        content = "NVIDIA Broadcast and NVIDIA Canvas for creators."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "broadcast" in names
        assert "canvas" in names

    def test_triton_inference_server(self, extractor):
        """Triton Inference Server is extracted."""
        content = "Deploy models with Triton Inference Server."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "triton inference server" in names

    def test_base_command_and_fleet_command(self, extractor):
        """Base Command and Fleet Command are extracted."""
        content = "Manage deployments with Base Command and Fleet Command."
        technologies = extractor.extract_technologies(content, self.URL)

        names = {t.name.lower() for t in technologies}
        assert "base command" in names
        assert "fleet command" in names


# ---------------------------------------------------------------------------
# Technology categorization
# ---------------------------------------------------------------------------


class TestCategorizeTechnology:
    """Tests for DataExtractor._categorize_technology()."""

    def test_cuda_platform(self, extractor):
        assert extractor._categorize_technology("CUDA") == "CUDA Platform"
        assert extractor._categorize_technology("cuDNN") == "CUDA Platform"
        assert extractor._categorize_technology("cuBLAS") == "CUDA Platform"

    def test_ai_inference_tensorrt(self, extractor):
        assert extractor._categorize_technology("TensorRT") == "AI Inference"

    def test_ai_inference_triton(self, extractor):
        assert extractor._categorize_technology("Triton Inference Server") == "AI Inference"

    def test_ai_frameworks_nemo(self, extractor):
        assert extractor._categorize_technology("NeMo") == "AI Frameworks"

    def test_ai_frameworks_merlin(self, extractor):
        assert extractor._categorize_technology("Merlin") == "AI Frameworks"

    def test_ai_frameworks_morpheus(self, extractor):
        assert extractor._categorize_technology("Morpheus") == "AI Frameworks"

    def test_ai_frameworks_rapids(self, extractor):
        assert extractor._categorize_technology("RAPIDS") == "AI Frameworks"

    def test_omniverse_platform(self, extractor):
        assert extractor._categorize_technology("Omniverse") == "Omniverse Platform"

    def test_healthcare_ai_clara(self, extractor):
        assert extractor._categorize_technology("Clara") == "Healthcare AI"

    def test_robotics_isaac(self, extractor):
        assert extractor._categorize_technology("Isaac Sim") == "Robotics"

    def test_computer_vision_deepstream(self, extractor):
        assert extractor._categorize_technology("DeepStream") == "Computer Vision"

    def test_computer_vision_metropolis(self, extractor):
        assert extractor._categorize_technology("Metropolis") == "Computer Vision"

    def test_speech_audio_ai_maxine(self, extractor):
        assert extractor._categorize_technology("Maxine") == "Speech & Audio AI"

    def test_speech_audio_ai_riva(self, extractor):
        assert extractor._categorize_technology("Riva") == "Speech & Audio AI"

    def test_speech_audio_ai_broadcast(self, extractor):
        assert extractor._categorize_technology("Broadcast") == "Speech & Audio AI"

    def test_graphics_technology_dlss(self, extractor):
        assert extractor._categorize_technology("DLSS 3") == "Graphics Technology"

    def test_graphics_technology_ray_tracing(self, extractor):
        assert extractor._categorize_technology("Ray Tracing") == "Graphics Technology"

    def test_graphics_technology_reflex(self, extractor):
        assert extractor._categorize_technology("Reflex") == "Graphics Technology"

    def test_cloud_containers_ngc(self, extractor):
        assert extractor._categorize_technology("NGC") == "Cloud & Containers"

    def test_interconnect_technology_nvlink(self, extractor):
        assert extractor._categorize_technology("NVLink") == "Interconnect Technology"

    def test_interconnect_technology_nvswitch(self, extractor):
        assert extractor._categorize_technology("NVSwitch") == "Interconnect Technology"

    def test_other_software_unknown(self, extractor):
        """Unrecognized technology falls through to 'Other Software'."""
        assert extractor._categorize_technology("UnknownTool 2.0") == "Other Software"

    def test_case_insensitive_categorization_tech(self, extractor):
        """Technology categorization lowercases the name before matching."""
        assert extractor._categorize_technology("cuda") == "CUDA Platform"
        assert extractor._categorize_technology("tensorrt") == "AI Inference"
        assert extractor._categorize_technology("omniverse") == "Omniverse Platform"
        assert extractor._categorize_technology("nvlink") == "Interconnect Technology"

    def test_empty_string_other_software(self, extractor):
        """Empty string yields 'Other Software'."""
        assert extractor._categorize_technology("") == "Other Software"

    def test_category_priority_order_tech(self, extractor):
        """
        Elif chain: the first matching branch wins.
        CUDA is matched by CUDA Platform before later branches.
        """
        # "cuda" is checked first
        assert extractor._categorize_technology("CUDA 12.0") == "CUDA Platform"


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------


class TestExtractKeywords:
    """Tests for DataExtractor.extract_keywords()."""

    def test_known_terms_found(self, extractor):
        """Terms present in important_terms set are returned."""
        content = "This GPU enables AI and deep learning in the data center."
        keywords = extractor.extract_keywords(content)

        assert "gpu" in keywords
        assert "ai" in keywords
        assert "deep learning" in keywords
        assert "data center" in keywords

    def test_term_not_in_content_missing(self, extractor):
        """Terms absent from content are not included."""
        content = "Simple web page about cooking."
        keywords = extractor.extract_keywords(content)

        assert keywords == []

    def test_top_n_limit(self, extractor):
        """Only the first top_n keywords are returned."""
        # Content that would match many terms
        content = (
            "AI gpu cuda deep learning machine learning neural network "
            "inference training hpc data center cloud edge automotive "
            "robotics healthcare gaming professional visualization "
            "accelerated computing generative ai llm"
        )
        keywords = extractor.extract_keywords(content, top_n=5)

        assert len(keywords) <= 5

    def test_default_top_n_is_20(self, extractor):
        """When top_n is not specified, at most 20 keywords are returned."""
        # Content matching all or most terms
        content = (
            "ai gpu cuda deep learning machine learning neural network "
            "inference training hpc data center cloud edge automotive "
            "robotics healthcare gaming professional visualization "
            "accelerated computing generative ai llm"
        )
        keywords = extractor.extract_keywords(content)

        assert len(keywords) <= 20

    def test_matching_is_lowercase(self, extractor):
        """Keyword matching is case-insensitive (content is lowercased)."""
        content = "GPU and AI and Deep Learning in the Cloud"
        keywords = extractor.extract_keywords(content)

        assert "gpu" in keywords
        assert "ai" in keywords
        assert "deep learning" in keywords
        assert "cloud" in keywords

    def test_order_matches_important_terms_iteration(self, extractor):
        """Keywords are returned in the order of the important_terms set iteration."""
        content = "gpu and ai and deep learning and hpc"
        keywords = extractor.extract_keywords(content)

        # All matched terms should be present regardless of order
        for term in ["gpu", "ai", "deep learning", "hpc"]:
            assert term in keywords

    def test_empty_content_returns_empty_keywords(self, extractor):
        """Empty content returns an empty keyword list."""
        assert extractor.extract_keywords("") == []

    def test_top_n_zero_returns_empty(self, extractor):
        """top_n=0 returns an empty list."""
        content = "ai gpu cuda deep learning"
        assert extractor.extract_keywords(content, top_n=0) == []

    def test_top_n_larger_than_matches_returns_all(self, extractor):
        """When top_n exceeds the number of matches, all matches are returned."""
        content = "ai and gpu"
        keywords = extractor.extract_keywords(content, top_n=10)

        assert len(keywords) <= 2


# ---------------------------------------------------------------------------
# Page extraction
# ---------------------------------------------------------------------------


class TestExtractPage:
    """Tests for DataExtractor.extract_page()."""

    def test_combines_products_and_technologies(self, extractor):
        """Title/description/content are combined for extraction."""
        page = extractor.extract_page(
            url="https://nvidia.com/geforce",
            title="GeForce RTX 4090",
            description="CUDA powered consumer GPU",
            content="The GeForce RTX 4090 uses CUDA for accelerated performance.",
            ecosystem="hardware",
        )

        assert isinstance(page, ExtractedPage)
        product_names = {p.name.lower() for p in page.products}
        tech_names = {t.name.lower() for t in page.technologies}

        # Product from title
        assert "geforce rtx 4090" in product_names
        # Technology from description
        assert "cuda" in tech_names

    def test_keywords_extracted_from_combined_content(self, extractor):
        """Keywords come from the combined title + description + content."""
        page = extractor.extract_page(
            url="https://nvidia.com/test",
            title="GPU Accelerated AI",
            description="Deep learning at scale",
            content="Data center ready machine learning solutions.",
            ecosystem="data-center",
        )

        keywords = page.keywords
        assert "gpu" in keywords
        assert "ai" in keywords
        assert "deep learning" in keywords
        assert "data center" in keywords

    def test_links_passed_through(self, extractor):
        """The links argument is passed through to ExtractedPage."""
        links = ["https://nvidia.com/a", "https://nvidia.com/b"]
        page = extractor.extract_page(
            url="https://nvidia.com/test",
            title="Test",
            description="",
            content="",
            ecosystem="technology",
            links=links,
        )

        assert page.links == links

    def test_links_default_to_empty_list(self, extractor):
        """When links is not provided, it defaults to an empty list."""
        page = extractor.extract_page(
            url="https://nvidia.com/test",
            title="Test",
            description="",
            content="",
            ecosystem="technology",
        )

        assert page.links == []

    def test_page_metadata_preserved(self, extractor):
        """URL, title, description, ecosystem, and subcategory are preserved."""
        page = extractor.extract_page(
            url="https://developer.nvidia.com/cuda",
            title="CUDA Toolkit",
            description="Parallel computing platform",
            content="Intro to CUDA programming.",
            ecosystem="developer-tools",
            subcategory="cuda-toolkit",
        )

        assert page.url == "https://developer.nvidia.com/cuda"
        assert page.title == "CUDA Toolkit"
        assert page.description == "Parallel computing platform"
        assert page.ecosystem == "developer-tools"
        assert page.subcategory == "cuda-toolkit"

    def test_subcategory_optional_none(self, extractor):
        """subcategory is Optional[str] — None is valid."""
        page = extractor.extract_page(
            url="https://nvidia.com/test",
            title="Test",
            description="",
            content="",
            ecosystem="technology",
        )

        assert page.subcategory is None


# ---------------------------------------------------------------------------
# Batch extraction
# ---------------------------------------------------------------------------


class TestExtractBatch:
    """Tests for DataExtractor.extract_batch()."""

    def test_multiple_pages_extracted(self, extractor):
        """A batch of multiple pages produces corresponding ExtractedPage objects."""
        pages = [
            {
                "url": "https://nvidia.com/geforce",
                "title": "GeForce RTX 4090",
                "description": "Consumer GPU with CUDA",
                "content": "The GeForce RTX 4090 delivers AI-powered gaming.",
                "ecosystem": "hardware",
            },
            {
                "url": "https://developer.nvidia.com/tensorrt",
                "title": "TensorRT",
                "description": "AI inference optimizer",
                "content": "TensorRT accelerates deep learning inference.",
                "ecosystem": "developer-tools",
            },
        ]

        results = extractor.extract_batch(pages)

        assert len(results) == 2
        assert isinstance(results[0], ExtractedPage)
        assert isinstance(results[1], ExtractedPage)
        assert results[0].url == "https://nvidia.com/geforce"
        assert results[1].url == "https://developer.nvidia.com/tensorrt"

    def test_empty_list_returns_empty_list(self, extractor):
        """An empty page list returns an empty result list."""
        assert extractor.extract_batch([]) == []

    def test_missing_keys_default_to_empty(self, extractor):
        """Missing keys (title, description, content) get default '' values."""
        pages = [{"url": "https://nvidia.com/test"}]

        results = extractor.extract_batch(pages)

        assert len(results) == 1
        page = results[0]
        assert page.url == "https://nvidia.com/test"
        assert page.title == ""
        assert page.description == ""
        # No products/technologies extracted from empty content
        assert page.products == []
        assert page.technologies == []
        assert page.keywords == []

    def test_missing_url_defaults_to_empty_string(self, extractor):
        """When 'url' key is missing, it defaults to ''."""
        pages = [{"title": "Test"}]

        results = extractor.extract_batch(pages)

        assert results[0].url == ""

    def test_missing_ecosystem_defaults_to_technology(self, extractor):
        """When 'ecosystem' is missing, it defaults to 'technology'."""
        pages = [{"url": "https://nvidia.com/test"}]

        results = extractor.extract_batch(pages)

        assert results[0].ecosystem == "technology"

    def test_missing_links_defaults_to_empty_list(self, extractor):
        """When 'links' is missing, it defaults to empty list."""
        pages = [{"url": "https://nvidia.com/test"}]

        results = extractor.extract_batch(pages)

        assert results[0].links == []

    def test_subcategory_optional_batch(self, extractor):
        """subcategory can be provided or omitted in batch input."""
        pages = [
            {"url": "https://nvidia.com/a", "subcategory": "foo"},
            {"url": "https://nvidia.com/b"},
        ]

        results = extractor.extract_batch(pages)

        assert results[0].subcategory == "foo"
        assert results[1].subcategory is None

    def test_partial_page_content_still_extracts(self, extractor):
        """Pages with minimal content still produce valid ExtractedPage objects."""
        pages = [
            {"url": "https://nvidia.com/blank", "title": "", "content": ""},
        ]

        results = extractor.extract_batch(pages)

        assert len(results) == 1
        assert results[0].products == []
        assert results[0].technologies == []
        assert results[0].keywords == []

    def test_batch_with_provided_links_preserved(self, extractor):
        """Links provided in batch input are correctly passed through."""
        pages = [
            {
                "url": "https://nvidia.com/test",
                "links": ["https://nvidia.com/link1", "https://nvidia.com/link2"],
            },
        ]

        results = extractor.extract_batch(pages)

        assert len(results[0].links) == 2
        assert "https://nvidia.com/link1" in results[0].links
        assert "https://nvidia.com/link2" in results[0].links
