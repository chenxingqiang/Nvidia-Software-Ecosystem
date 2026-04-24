#!/usr/bin/env python3
"""Build a compact ecosystem summary from nvidia_ecosystem.json (locale/path noise filtered)."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Two-token locale codes mistaken as subcategories (e.g. path segment "en-gb" -> "En Gb").
_LOCALE_PAIR = re.compile(r"^[A-Za-z]{2}\s+[A-Za-z]{2,3}$")
# resources.nvidia.com style slugs surfaced as titles.
_EN_US_SLUG = re.compile(r"^En\s+Us\b", re.I)
_MISC_SLUG_PREFIX = re.compile(
    r"^(Es|Fr|De|It|Pt|Nl|Pl|Ro|Fi|Sv|Nb|Da|Cs|Tr)\s+[A-Za-z]{2,3}\b",
    re.I,
)

_JUNK_TOKENS = frozenset({
    "object",
    "l",
    "%20",
    "tag",
    "en",
    "hot",
    "images",
    "search",
    "categories",
    "kb",
    "shop",
    "help",
    "login",
    "account",
    "download",
    "join",
    "dashboard",
    "gtc",
    "catalog",
    "faq",
    "forums",
    "home",
    "nvidia.com",
})


def _is_noise_subcategory(name: str) -> bool:
    s = (name or "").strip()
    if not s:
        return True
    if s.lower() in _JUNK_TOKENS:
        return True
    if _LOCALE_PAIR.match(s):
        return True
    if _EN_US_SLUG.match(s):
        return True
    if _MISC_SLUG_PREFIX.match(s):
        return True
    return False


def _flatten_named_list_to_set(bucket: Dict[str, List[str]]) -> Set[str]:
    """Return unique names from an ecosystem products/technologies bucket."""
    result: Set[str] = set()
    for _cat, names in (bucket or {}).items():
        if not isinstance(names, list):
            continue
        for n in names:
            if isinstance(n, str) and n.strip():
                result.add(n.strip())
    return result


def _merge_counts(
    ecosystems_data: Dict[str, Any],
    eco_keys: List[str],
    field: str,
) -> Counter:
    """Count items by how many ecosystems they appear in.

    Each item is deduplicated within an ecosystem, then counted once
    per ecosystem that contains it (max 5). Case-insensitive dedup
    across ecosystems keeps the most common display form.
    """
    per_eco: List[Set[str]] = []
    all_items: Dict[str, int] = {}  # lower_name -> count across ecosystems
    best_form: Dict[str, str] = {}  # lower_name -> best display name

    for eco in eco_keys:
        info = ecosystems_data.get(eco) or {}
        items = _flatten_named_list_to_set(info.get(field) or {})
        per_eco.append(items)
        for name in items:
            key = name.lower()
            if key not in all_items:
                all_items[key] = 0
                best_form[key] = name
            all_items[key] += 1
            # Keep the title-case or UPPER case form as best display
            if name[0].isupper() and not best_form[key][0].isupper():
                best_form[key] = name

    result: Counter = Counter()
    for key, cnt in all_items.items():
        result[best_form[key]] = cnt
    return result


def _top(counter: Counter, n: int) -> List[Tuple[str, int]]:
    return counter.most_common(n)


def build_markdown(data: Dict[str, Any], top_n: int) -> str:
    meta = data.get("metadata") or {}
    summary = data.get("summary") or {}
    ecosystems = data.get("ecosystems") or {}

    lines: List[str] = [
        "# NVIDIA Ecosystem Summary (noise-filtered)",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"> Source crawl: {meta.get('crawl_start', '')} → {meta.get('crawl_end', '')}",
        f"> Pages in aggregate: **{meta.get('total_pages', '—')}**",
        "",
        "## Source of truth (recommended)",
        "",
        "| Role | File |",
        "|------|------|",
        "| Raw pages | `raw/crawl_data.json` (large; gitignored by default) |",
        "| Per-page classification | `raw/classified_pages.json` (large; gitignored) |",
        "| **Aggregated ecosystems** | **`indices/nvidia_ecosystem.json`** |",
        "| Product index | `indices/nvidia_products.json` |",
        "| Technology index | `indices/nvidia_technologies.json` |",
        "| PDF inventory | `pdf/nvidia_pdf_catalog.json` + `pdf/nvidia_pdf_urls.txt` |",
        "| Human narrative | `reports/*.md` (ecosystem, software trees, summaries) |",
        "",
        "## Five-ecosystem distribution",
        "",
    ]

    dist = (summary.get("ecosystem_distribution") or {})
    total = sum(dist.values()) or 1
    for eco in ("hardware", "software", "developer", "business", "technology"):
        cnt = int(dist.get(eco, 0))
        pct = 100.0 * cnt / total
        info = (ecosystems.get(eco) or {})
        name = info.get("name", eco)
        lines.append(f"- **{name}** (`{eco}`): {cnt} pages ({pct:.1f}%)")
    lines.append("")

    eco_keys = ("hardware", "software", "developer", "business", "technology")

    lines.append("## Clean subcategories (top per ecosystem)")
    lines.append("")
    lines.append(
        "*Subcategories matching locale-like tokens (`En Gb`, `Zh Cn`, `En Us …`) "
        "or generic junk (`Object`, `Tag`, …) are dropped.*"
    )
    lines.append("")

    for eco in eco_keys:
        info = ecosystems.get(eco) or {}
        name = info.get("name", eco)
        raw_sub = info.get("subcategories") or {}
        clean = [(k, v) for k, v in raw_sub.items() if not _is_noise_subcategory(str(k))]
        clean.sort(key=lambda x: (-x[1], x[0].lower()))
        top_sub = clean[:15]

        lines.append(f"### {name}")
        lines.append("")
        if not top_sub:
            lines.append("*(no clean subcategories after filter)*")
        else:
            for k, v in top_sub:
                lines.append(f"- **{k}**: {v} pages")
        lines.append("")

    # Count products/technologies across ecosystems (deduplicated per ecosystem)
    all_products = _merge_counts(ecosystems, eco_keys, "products")
    all_tech = _merge_counts(ecosystems, eco_keys, "technologies")

    lines.append(f"## Top products (mentions across pages, top {top_n})")
    lines.append("")
    for name, cnt in _top(all_products, top_n):
        lines.append(f"- {name} ({cnt}×)")
    lines.append("")

    lines.append(f"## Top technologies (mentions across pages, top {top_n})")
    lines.append("")
    for name, cnt in _top(all_tech, top_n):
        lines.append(f"- {name} ({cnt}×)")
    lines.append("")

    lines.append("## Regenerate")
    lines.append("")
    lines.append("```bash")
    lines.append("python scripts/summarize_ecosystem.py --input output/indices/nvidia_ecosystem.json")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--input",
        type=Path,
        default=root / "output" / "indices" / "nvidia_ecosystem.json",
        help="Path to nvidia_ecosystem.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "output" / "reports" / "nvidia_ecosystem_summary_clean.md",
        help="Markdown output path",
    )
    parser.add_argument("--top", type=int, default=40, help="Top N products/technologies")
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    md = build_markdown(data, args.top)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
