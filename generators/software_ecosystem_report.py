"""Generate NVIDIA Software Ecosystem report from aggregated crawl indices."""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

_LOCALE_PAIR = re.compile(r"^[A-Za-z]{2}\s+[A-Za-z]{2,3}$")
_EN_US_SLUG = re.compile(r"^En\s+Us\b", re.I)
_MISC_SLUG_PREFIX = re.compile(
    r"^(Es|Fr|De|It|Pt|Nl|Pl|Ro|Fi|Sv|Nb|Da|Cs|Tr)\s+[A-Za-z]{2,3}\b",
    re.I,
)
_JUNK = frozenset({
    "object", "l", "%20", "tag", "en", "hot", "images", "search", "categories",
    "kb", "shop", "help", "login", "account", "download", "join", "dashboard",
    "gtc", "catalog", "faq", "forums", "home", "nvidia.com", "c", "orgs",
})


def _noise_subcat(name: str) -> bool:
    s = (name or "").strip()
    if not s or s.lower() in _JUNK:
        return True
    if _LOCALE_PAIR.match(s) or _EN_US_SLUG.match(s) or _MISC_SLUG_PREFIX.match(s):
        return True
    return False


def _norm_tech_name(name: str) -> str:
    return " ".join((name or "").replace("\n", " ").split()).strip()


def _dedupe_tech_names(names: List[str], limit: int) -> List[str]:
    """Merge case/whitespace variants; keep a readable representative."""
    by_key: Dict[str, str] = {}
    for raw in names:
        n = _norm_tech_name(raw)
        if not n or len(n) > 120:
            continue
        key = n.lower()
        if key not in by_key or len(n) > len(by_key[key]):
            by_key[key] = n
    out = sorted(by_key.values(), key=lambda x: (-len(x), x.lower()))
    return out[:limit]


def _top_subcategories(sub: Dict[str, Any], n: int) -> List[Tuple[str, int]]:
    items = [(k, int(v)) for k, v in (sub or {}).items() if not _noise_subcat(str(k))]
    items.sort(key=lambda x: (-x[1], x[0].lower()))
    return items[:n]


def _flatten_tech_bucket(bucket: Dict[str, List[str]]) -> Counter:
    """Count mentions; use lowercase key internally via Counter on normalized display name."""
    c: Counter = Counter()
    for _cat, names in (bucket or {}).items():
        if not isinstance(names, list):
            continue
        for raw in names:
            n = _norm_tech_name(str(raw))
            if n:
                c[n] += 1
    return c


def build_software_ecosystem_markdown(
    ecosystem: Dict[str, Any],
    tech_catalog: Dict[str, Any],
) -> str:
    meta = ecosystem.get("metadata") or {}
    summary = ecosystem.get("summary") or {}
    dist = summary.get("ecosystem_distribution") or {}
    ecosystems = ecosystem.get("ecosystems") or {}

    sw = ecosystems.get("software") or {}
    dev = ecosystems.get("developer") or {}

    lines: List[str] = [
        "# NVIDIA Software Ecosystem Report",
        "",
        f"> Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"> Crawl window: `{meta.get('crawl_start', '')}` → `{meta.get('crawl_end', '')}`",
        f"> Pages in crawl aggregate: **{meta.get('total_pages', '—')}**",
        "",
        "## 1. Purpose and data sources",
        "",
        "This report synthesizes **software-relevant signals** from the crawler indices "
        "(not a replacement for official product documentation).",
        "",
        "| Source file | Role |",
        "|-------------|------|",
        "| `indices/nvidia_ecosystem.json` | Per-ecosystem page counts, subcategories, merged products/technologies on classified pages |",
        "| `indices/nvidia_technologies.json` | Global technology catalog grouped by **12** technology categories |",
        "| `raw/classified_pages.json` | Page-level evidence (large) |",
        "",
        "## 2. Classifier snapshot: Software vs Developer",
        "",
        "The pipeline assigns each page to one of five ecosystems. **Software** and **Developer** "
        "together cover most SDK, platform, and documentation surfaces.",
        "",
        f"- **Software ecosystem** pages: **{dist.get('software', 0)}**",
        f"- **Developer ecosystem** pages: **{dist.get('developer', 0)}**",
        f"- **All pages in this aggregate:** {meta.get('total_pages', '—')}",
        "",
        "### 2.1 Software ecosystem — thematic subcategories (noise filtered)",
        "",
    ]

    for name, cnt in _top_subcategories(sw.get("subcategories") or {}, 22):
        lines.append(f"- **{name}**: {cnt} pages")
    if not _top_subcategories(sw.get("subcategories") or {}, 1):
        lines.append("*(no subcategories after filter)*")
    lines.append("")

    lines.append("### 2.2 Developer ecosystem — top subcategories (noise filtered)")
    lines.append("")
    for name, cnt in _top_subcategories(dev.get("subcategories") or {}, 18):
        lines.append(f"- **{name}**: {cnt} pages")
    lines.append("")

    lines.append("## 3. Global software technology stack (`nvidia_technologies.json`)")
    lines.append("")
    lines.append(
        "The extractor assigns technologies into **twelve** categories. Counts below are **distinct "
        "technology names** per category (including near-duplicate spellings in raw crawl data)."
    )
    lines.append("")

    cats = (tech_catalog.get("categories") or {})
    rows = []
    for cat, payload in sorted(cats.items(), key=lambda x: -int((x[1] or {}).get("count", 0))):
        cnt = int((payload or {}).get("count", 0))
        rows.append((cat, cnt))
    lines.append("| Category | Distinct technologies |")
    lines.append("|----------|------------------------|")
    for cat, cnt in rows:
        lines.append(f"| {cat} | {cnt} |")
    lines.append("")

    for idx, (cat, payload) in enumerate(
        sorted(cats.items(), key=lambda x: -int((x[1] or {}).get("count", 0))),
        start=1,
    ):
        techs = (payload or {}).get("technologies") or []
        names = [t.get("name", "") for t in techs if isinstance(t, dict)]
        sample = _dedupe_tech_names(names, 28)
        lines.append(f"### 3.{idx} {cat}")
        lines.append("")
        lines.append(
            f"*{int((payload or {}).get('count', 0))} entries in index; showing up to "
            f"{len(sample)} deduplicated names.*"
        )
        lines.append("")
        for n in sample:
            lines.append(f"- {n}")
        lines.append("")

    lines.append("## 4. Technologies most associated with *Software*-classified pages")
    lines.append("")
    lines.append(
        "Aggregated from `ecosystems.software.technologies` in `nvidia_ecosystem.json` "
        "(counts reflect co-occurrence across pages classified as **software**)."
    )
    lines.append("")
    sw_tech = sw.get("technologies") or {}
    raw_flat = _flatten_tech_bucket(sw_tech)
    merged: Counter = Counter()
    display: Dict[str, str] = {}
    for name, cnt in raw_flat.items():
        k = name.lower()
        merged[k] += cnt
        if k not in display or len(name) > len(display[k]):
            display[k] = name
    for k, cnt in merged.most_common(35):
        lines.append(f"- {display.get(k, k)} — **{cnt}**")
    lines.append("")

    lines.append("## 5. Related reports in `reports/`")
    lines.append("")
    lines.append("- `nvidia_software_ecosystem_tree.md` — Mermaid mindmap of the software stack")
    lines.append("- `nvidia_software_detailed_analysis.md` — Long-form product writeups")
    lines.append("- `nvidia_software_license_analysis.md` — Open / proprietary / mixed license rollup")
    lines.append("- `nvidia_ecosystem_report.md` — Full five-ecosystem bilingual report")
    lines.append("- `nvidia_ecosystem_summary_clean.md` — Compact rollup with locale noise stripped")
    lines.append("")
    lines.append("PDF collateral lives under `pdf/` (`nvidia_pdf_catalog.json`, `nvidia_pdf_report.md`).")
    lines.append("")
    lines.append("## 6. Limitations")
    lines.append("")
    lines.append(
        "- Classification is **heuristic** (URL + keyword scoring); boundary between "
        "**Software** and **Developer** is fuzzy."
    )
    lines.append(
        "- Technology names inherit **HTML/marketing noise** (e.g. duplicated Merlin variants); "
        "deduplication here is lightweight."
    )
    lines.append(
        "- Crawl mix may include **non-English regional paths** from older runs; newer runs follow "
        "`config.py` locale policy."
    )
    lines.append("")

    return "\n".join(lines)


def write_software_ecosystem_report(indices_dir: Path, reports_dir: Path) -> Path:
    """Read indices, write `nvidia_software_ecosystem_report.md` into reports_dir."""
    eco_path = indices_dir / "nvidia_ecosystem.json"
    tech_path = indices_dir / "nvidia_technologies.json"
    if not eco_path.is_file():
        raise FileNotFoundError(f"Missing {eco_path}")
    if not tech_path.is_file():
        raise FileNotFoundError(f"Missing {tech_path}")

    ecosystem = json.loads(eco_path.read_text(encoding="utf-8"))
    tech_catalog = json.loads(tech_path.read_text(encoding="utf-8"))

    md = build_software_ecosystem_markdown(ecosystem, tech_catalog)
    reports_dir.mkdir(parents=True, exist_ok=True)
    out = reports_dir / "nvidia_software_ecosystem_report.md"
    out.write_text(md, encoding="utf-8")
    return out
