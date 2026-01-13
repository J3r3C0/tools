from typing import Dict, Any, List
from pathlib import Path

from .normalize import normalize_text

def extract_pdf_text(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    text_pages: List[str] = []
    used = None
    errors = []

    # Try PyPDF2 first
    try:
        import PyPDF2  # type: ignore
        used = "PyPDF2"
        with p.open("rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                t = page.extract_text() or ""
                text_pages.append(t)
    except Exception as e:
        errors.append(f"PyPDF2 failed: {e}")
        text_pages = []

    # Fallback: pdfplumber
    if not text_pages:
        try:
            import pdfplumber  # type: ignore
            used = "pdfplumber"
            with pdfplumber.open(str(p)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    text_pages.append(t)
        except Exception as e:
            errors.append(f"pdfplumber failed: {e}")

    combined = normalize_text("\n\n".join(text_pages))

    return {
        "type": "pdf",
        "path": str(p),
        "extractor": used,
        "errors": errors,
        "pages": len(text_pages),
        "text": combined
    }
