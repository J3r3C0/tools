# mesh_scanner/cli.py

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import List

from .config import ScannerConfig
from .scanner import run_scan
from .storage import init_db, save_results, get_last_n


def parse_ports(ports_str: str) -> List[int]:
    """
    Ports angaben z. B.:
    - "80"
    - "80,443,8080"
    - "20-25,80,443"
    """
    result: List[int] = []
    parts = [p.strip() for p in ports_str.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str)
            end = int(end_str)
            for port in range(start, end + 1):
                result.append(port)
        else:
            result.append(int(part))
    # Duplikate raus
    return sorted(set(result))


async def cmd_scan(args: argparse.Namespace) -> None:
    db_path = Path(args.db)
    cidr = args.cidr
    ports = parse_ports(args.ports)

    cfg = ScannerConfig(
        timeout=args.timeout,
        max_hosts=args.max_hosts,
        concurrency=args.concurrency,
        banner_max_bytes=args.banner_bytes,
    )

    print(f"[scanner] init db at {db_path}")
    init_db(db_path)

    print(f"[scanner] scanning {cidr} (max_hosts={cfg.max_hosts}) on ports {ports}")
    results = await run_scan(cidr, ports, cfg)

    print(f"[scanner] saving {len(results)} results")
    save_results(db_path, results)

    open_count = sum(1 for r in results if r.is_open)
    print(f"[scanner] done. open ports found: {open_count}")


def cmd_last(args: argparse.Namespace) -> None:
    db_path = Path(args.db)
    limit = args.limit
    results = get_last_n(db_path, limit=limit)
    for r in results:
        status = "open" if r.is_open else "closed"
        when = r.scanned_at.isoformat() if r.scanned_at else "n/a"
        print(f"{when} {r.ip}:{r.port} {status} service={r.service or '-'}")
        if r.banner:
            snippet = r.banner.strip().splitlines()
            if snippet:
                first_line = snippet[0]
                # etwas kürzen
                if len(first_line) > 120:
                    first_line = first_line[:117] + "..."
                print(f"    banner: {first_line}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mesh-scanner",
        description="Mini-Shodan Scanner-Core (CIDR + Ports → SQLite)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="Führe einen Scan durch")
    p_scan.add_argument("--cidr", required=True, help="z. B. 192.168.0.0/24")
    p_scan.add_argument(
        "--ports",
        required=True,
        help="Ports, z. B. 22,80,443 oder 20-25,80",
    )
    p_scan.add_argument(
        "--db",
        default="mesh_scanner.sqlite3",
        help="Pfad zur SQLite-Datei",
    )
    p_scan.add_argument(
        "--timeout",
        type=float,
        default=2.0,
        help="Timeout pro Port (Sekunden)",
    )
    p_scan.add_argument(
        "--max-hosts",
        type=int,
        default=256,
        help="Maximale Anzahl Hosts aus dem CIDR",
    )
    p_scan.add_argument(
        "--concurrency",
        type=int,
        default=200,
        help="Maximale gleichzeitige Verbindungen",
    )
    p_scan.add_argument(
        "--banner-bytes",
        type=int,
        default=2048,
        help="Maximal gelesene Banner-Bytes",
    )
    p_scan.set_defaults(func=lambda ns: asyncio.run(cmd_scan(ns)))

    # last
    p_last = sub.add_parser(
        "last",
        help="Zeige die letzten Scan-Ergebnisse aus der DB",
    )
    p_last.add_argument(
        "--db",
        default="mesh_scanner.sqlite3",
        help="Pfad zur SQLite-Datei",
    )
    p_last.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Wie viele Einträge anzeigen",
    )
    p_last.set_defaults(func=cmd_last)

    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
