from typing import Dict, Any
from pathlib import Path

from bs4 import BeautifulSoup  # type: ignore
from .normalize import normalize_text

def extract_html_text(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)

    raw = p.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "lxml")

    # remove scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n")
    text = normalize_text(text)

    return {
        "type": "html",
        "path": str(p),
        "extractor": "beautifulsoup+lxml",
        "text": text
    }
