import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from src.config import Config
from src.extract.pdf_extract import extract_pdf_text
from src.extract.html_extract import extract_html_text
from src.extract.normalize import clamp_chars
from src.io.load import read_json, ensure_dir
from src.io.write import atomic_write_json
from src.llm.client import call_llm
from src.llm.prompts import SYSTEM_PROMPT, build_instructions
from src.pipeline.validate import validate_weekly_intel
from src.pipeline.tag_enrich import enrich_domains


def _kw_label(week: int, year: int) -> str:
    return f"KW{week:02d}_{year}"


def _stable_entry_id(kw: str, idx: int, title: str) -> str:
    h = hashlib.sha1((title or "").encode("utf-8", errors="ignore")).hexdigest()[:8]
    return f"{kw}_{idx:03d}_{h}"


def ingest_one(input_path: str, week: int, year: int, out_root: str, dry_run: bool, max_chars: int) -> Dict[str, Any]:
    cfg = Config.from_env()
    kw = _kw_label(week, year)

    # paths
    out_root_p = Path(out_root)
    extracted_dir = out_root_p / "extracted"
    structured_dir = out_root_p / "structured"
    ensure_dir(str(extracted_dir))
    ensure_dir(str(structured_dir))

    schema_path = str(Path("schemas") / "weekly_intel_v1.json")
    tagmap_path = str(Path("journal_tagmap.json"))
    tagmap = read_json(tagmap_path)

    # extract
    ext = Path(input_path).suffix.lower()
    if ext == ".pdf":
        extracted = extract_pdf_text(input_path)
    elif ext in (".html", ".htm"):
        extracted = extract_html_text(input_path)
    else:
        # try html as fallback; else error
        extracted = extract_html_text(input_path) if "<html" in Path(input_path).read_text(encoding="utf-8", errors="ignore")[:2000].lower() else None
        if extracted is None:
            raise RuntimeError(f"Unsupported file type: {input_path}")

    extracted_text = clamp_chars(extracted.get("text", ""), max_chars=max_chars)

    raw_out_path = str(extracted_dir / f"{kw}.raw.json")
    atomic_write_json(raw_out_path, {"kw": kw, "input": input_path, "extracted": extracted})

    # llm payload
    payload = {
        "model": cfg.llm_model,
        "system": SYSTEM_PROMPT,
        "input": {
            "schema_version": "weekly_intel_v1",
            "week": week,
            "year": year,
            "tagmap": tagmap,
            "extracted_text": extracted_text,
            "source_inputs": [input_path],
        },
        "instructions": build_instructions("weekly_intel_v1"),
    }

    raw_resp, weekly = call_llm(cfg, payload)

    # normalize issue block
    weekly["issue"] = weekly.get("issue") or {}
    weekly["issue"]["week"] = week
    weekly["issue"]["year"] = year
    weekly["issue"]["schema_version"] = "weekly_intel_v1"
    weekly["issue"]["generated_at"] = weekly["issue"].get("generated_at") or datetime.now(timezone.utc).isoformat()
    weekly["issue"]["source_inputs"] = weekly["issue"].get("source_inputs") or [input_path]

    # enrich + stable ids
    entries = weekly.get("entries") or []
    new_entries: List[Dict[str, Any]] = []
    for i, e in enumerate(entries, start=1):
        if not isinstance(e, dict):
            continue
        if not e.get("id"):
            e["id"] = _stable_entry_id(kw, i, e.get("title", ""))
        enrich_domains(e, tagmap)
        new_entries.append(e)
    weekly["entries"] = new_entries

    # stats
    c_high = sum(1 for e in new_entries if e.get("relevance") == "HIGH")
    c_med = sum(1 for e in new_entries if e.get("relevance") == "MEDIUM")
    c_low = sum(1 for e in new_entries if e.get("relevance") == "LOW")
    weekly["stats"] = {
        "count_total": len(new_entries),
        "count_high": c_high,
        "count_medium": c_med,
        "count_low": c_low,
    }

    # validate
    validate_weekly_intel(weekly, schema_path)

    # write structured
    structured_path = str(structured_dir / f"{kw}.intel.json")
    if not dry_run:
        atomic_write_json(structured_path, weekly)

    return {
        "kw": kw,
        "input": input_path,
        "raw_extracted": raw_out_path,
        "structured": structured_path if not dry_run else None,
        "llm_raw": raw_resp,
        "counts": weekly["stats"],
    }


def ingest_many(input_files: List[str], week: int, year: int, out_root: str, dry_run: bool, max_chars: int) -> None:
    # If multiple files, we ingest them sequentially (simple & deterministic).
    for fp in input_files:
        result = ingest_one(fp, week, year, out_root, dry_run, max_chars)
        print(f"[OK] {result['kw']} :: {fp}")
        print(f"     extracted:  {result['raw_extracted']}")
        if result["structured"]:
            print(f"     structured: {result['structured']}")
        print(f"     counts:     {result['counts']}")
