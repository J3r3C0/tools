# mesh_scanner/banner_grabber.py

from __future__ import annotations

import asyncio
from typing import Optional


async def grab_http_banner(
    host: str,
    port: int,
    timeout: float,
    max_bytes: int,
) -> Optional[str]:
    """
    Minimaler HTTP-Bannner-Grab:
    - TCP-Connect
    - "GET / HTTP/1.0" senden
    - einige Bytes lesen
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except Exception:
        return None

    try:
        req = f"GET / HTTP/1.0\r\nHost: {host}\r\nUser-Agent: mesh-scanner/0.1\r\n\r\n"
        writer.write(req.encode("ascii", "ignore"))
        await writer.drain()

        data = await asyncio.wait_for(reader.read(max_bytes), timeout=timeout)
        if not data:
            return None
        try:
            text = data.decode("utf-8", "ignore")
        except UnicodeDecodeError:
            text = data.decode("latin-1", "ignore")
        return text
    except Exception:
        return None
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def grab_raw_banner(
    host: str,
    port: int,
    timeout: float,
    max_bytes: int,
) -> Optional[str]:
    """
    Versuch, einfach die ersten Bytes nach Verbindungsaufbau zu lesen.
    Gut für SSH, SMTP, etc., die beim Connect einen Banner schicken.
    """
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except Exception:
        return None

    try:
        data = await asyncio.wait_for(reader.read(max_bytes), timeout=timeout)
        if not data:
            return None
        try:
            text = data.decode("utf-8", "ignore")
        except UnicodeDecodeError:
            text = data.decode("latin-1", "ignore")
        return text
    except Exception:
        return None
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
