# mesh_scanner/port_scanner.py

from __future__ import annotations

import asyncio
from typing import Tuple


async def check_port(host: str, port: int, timeout: float) -> bool:
    """
    Versucht, einen TCP-Socket zu öffnen.
    Gibt True zurück, wenn Verbindung klappt, sonst False.
    """
    try:
        conn = asyncio.open_connection(host, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False


async def check_port_with_result(host: str, port: int, timeout: float) -> Tuple[str, int, bool]:
    is_open = await check_port(host, port, timeout)
    return host, port, is_open
