# mesh_scanner/ip_range.py

from __future__ import annotations

import ipaddress
from typing import Iterable, List


def expand_cidr(cidr: str, max_hosts: int | None = None) -> List[str]:
    """
    Expand a CIDR notation like '192.168.0.0/24' into a list of IP strings.
    max_hosts begrenzt, wie viele Hosts maximal zurückgegeben werden.
    """
    network = ipaddress.ip_network(cidr, strict=False)
    hosts: Iterable[ipaddress._BaseAddress] = network.hosts()

    result: List[str] = []
    for idx, host in enumerate(hosts):
        if max_hosts is not None and idx >= max_hosts:
            break
        result.append(str(host))
    return result
