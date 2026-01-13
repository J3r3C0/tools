# sheratan-journal

Separate, modular Sheratan Journal ingestion repo:
- Extract text from PDF/HTML
- Send to an LLM endpoint (LLM_ENDPOINT)
- Validate output against `weekly_intel_v1` JSON Schema
- Enrich entries using `journal_tagmap.json`
- Write outputs to `data/out/`

## Install
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Use

Put inputs into `data/in/` (pdf/html) and run:

```bash
python cli.py ingest --input "data/in/*.pdf" --week 2 --year 2026
python cli.py ingest --input "data/in/*.html" --week 2 --year 2026
python cli.py ingest --input "data/in/*" --week 2 --year 2026
```

Outputs:

* `data/out/extracted/KW{WW}_{YYYY}.raw.json`
* `data/out/structured/KW{WW}_{YYYY}.intel.json`

## LLM Endpoint Contract (minimal)

POST `${LLM_ENDPOINT}` with JSON:

```json
{
  "model": "any",
  "input": { "schema_version": "weekly_intel_v1", "week": 2, "year": 2026, "tagmap": {...}, "extracted_text": "..." },
  "instructions": "Return ONLY valid JSON matching weekly_intel_v1."
}
```

Response formats supported:

* `{ "ok": true, "output": { ...weekly_intel_v1... } }`
* Or directly the weekly_intel_v1 JSON object
