import json
from pathlib import Path
from typing import Any, Dict, List


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="ignore")


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def list_files(paths: List[str]) -> List[str]:
    return [str(Path(x)) for x in paths]
