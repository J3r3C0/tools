# mesh_scanner/scanner.py

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Iterable, List

from .config import ScannerConfig
from .ip_range import expand_cidr
from .models import ScanResult
from .port_scanner import check_port
from .banner_grabber import grab_http_banner, grab_raw_banner


async def _scan_host_port(
    host: str,
    port: int,
    cfg: ScannerConfig,
    sem: asyncio.Semaphore,
) -> ScanResult:
    async with sem:
        is_open = await check_port(host, port, cfg.timeout)

        banner = None
        service = None

        if is_open:
            # einfache Heuristik: HTTP-Banner für 80 / 443, sonst raw
            if port in (80, 8080, 8000, 443):
                service = "http"
                banner = await grab_http_banner(
                    host,
                    port,
                    timeout=cfg.timeout,
                    max_bytes=cfg.banner_max_bytes,
                )
            else:
                service = "unknown"
                banner = await grab_raw_banner(
                    host,
                    port,
                    timeout=cfg.timeout,
                    max_bytes=cfg.banner_max_bytes,
                )

        return ScanResult(
            ip=host,
            port=port,
            is_open=is_open,
            service=service,
            banner=banner,
            scanned_at=datetime.utcnow(),
        )


async def run_scan(
    cidr: str,
    ports: Iterable[int],
    cfg: ScannerConfig,
) -> List[ScanResult]:
    hosts = expand_cidr(cidr, max_hosts=cfg.max_hosts)
    sem = asyncio.Semaphore(cfg.concurrency)

    tasks: List[asyncio.Task] = []
    for host in hosts:
        for port in ports:
            tasks.append(asyncio.create_task(_scan_host_port(host, port, cfg, sem)))

    results: List[ScanResult] = []
    for coro in asyncio.as_completed(tasks):
        res = await coro
        results.append(res)
    return results
