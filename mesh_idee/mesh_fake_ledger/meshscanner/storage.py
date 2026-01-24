# mesh_scanner/storage.py

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, List

from .models import ScanResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    port INTEGER NOT NULL,
    is_open INTEGER NOT NULL,
    service TEXT,
    banner TEXT,
    scanned_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_scans_ip ON scans (ip);
CREATE INDEX IF NOT EXISTS idx_scans_port ON scans (port);
CREATE INDEX IF NOT EXISTS idx_scans_ip_port ON scans (ip, port);
"""


def init_db(path: str | Path) -> None:
    path = Path(path)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_results(path: str | Path, results: Iterable[ScanResult]) -> None:
    path = Path(path)
    conn = sqlite3.connect(path)
    try:
        conn.execute("BEGIN")
        for r in results:
            rec = r.to_record()
            conn.execute(
                """
                INSERT INTO scans (ip, port, is_open, service, banner, scanned_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    rec["ip"],
                    rec["port"],
                    1 if rec["is_open"] else 0,
                    rec["service"],
                    rec["banner"],
                    rec["scanned_at"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


def get_last_n(path: str | Path, limit: int = 50) -> List[ScanResult]:
    path = Path(path)
    conn = sqlite3.connect(path)
    try:
        cur = conn.execute(
            """
            SELECT ip, port, is_open, service, banner, scanned_at
            FROM scans
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    results: List[ScanResult] = []
    for ip, port, is_open, service, banner, scanned_at in rows:
        from datetime import datetime

        ts = (
            datetime.fromisoformat(scanned_at)
            if isinstance(scanned_at, str)
            else None
        )
        results.append(
            ScanResult(
                ip=ip,
                port=port,
                is_open=bool(is_open),
                service=service,
                banner=banner,
                scanned_at=ts,
            )
        )
    return results
