# Output directory layout

| Subfolder | Contents |
|-----------|----------|
| **`raw/`** | `crawl_data.json`, `classified_pages.json` (large; regenerate with `main.py`) |
| **`indices/`** | `nvidia_ecosystem.json`, `nvidia_products.json`, `nvidia_technologies.json` |
| **`reports/`** | Markdown / Mermaid reports, including **`nvidia_software_ecosystem_report.md`** |
| **`pdf/`** | PDF crawler: `nvidia_pdf_catalog.json`, `nvidia_pdf_urls.txt`, `nvidia_pdf_report.md`, optional `pdfs/` |
| **(root)** | `crawl.log` only |

Regenerate the compact ecosystem summary:

```bash
python scripts/summarize_ecosystem.py
```

Regenerate the software ecosystem report (after indices exist):

```bash
python -c "from config import OUTPUT_DIR, output_subdirs; from generators.software_ecosystem_report import write_software_ecosystem_report; write_software_ecosystem_report(output_subdirs(OUTPUT_DIR)['indices'], output_subdirs(OUTPUT_DIR)['reports'])"
```

Full pipeline (creates subfolders, crawls, writes all artifacts):

```bash
python main.py --max-depth 3 --max-pages 100
```
