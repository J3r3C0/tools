# mesh_scanner/models.py

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ScanResult:
    ip: str
    port: int
    is_open: bool
    service: Optional[str] = None
    banner: Optional[str] = None
    scanned_at: datetime | None = None

    def to_record(self) -> Dict[str, Any]:
        d = asdict(self)
        if d["scanned_at"] is None:
            d["scanned_at"] = datetime.utcnow().isoformat()
        else:
            # sicherstellen, dass es ein ISO-String ist
            if isinstance(d["scanned_at"], datetime):
                d["scanned_at"] = d["scanned_at"].isoformat()
        return d
