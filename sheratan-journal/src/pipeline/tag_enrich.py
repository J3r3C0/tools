from typing import Any, Dict, List, Set


def enrich_domains(entry: Dict[str, Any], tagmap: Dict[str, List[str]]) -> Dict[str, Any]:
    tags = entry.get("tags") or []
    domains: Set[str] = set(entry.get("domains") or [])

    for t in tags:
        for d in tagmap.get(t, []):
            domains.add(d)

    entry["domains"] = sorted(domains)
    return entry
