import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict


def atomic_write_text(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="ignore") as f:
            f.write(content)
        os.replace(tmp, str(p))
    finally:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


def atomic_write_json(path: str, obj: Dict[str, Any]) -> None:
    content = json.dumps(obj, ensure_ascii=False, indent=2)
    atomic_write_text(path, content)
