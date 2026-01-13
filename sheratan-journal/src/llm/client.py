import json
from typing import Any, Dict, Optional, Tuple
import requests

from src.config import Config


def _try_parse_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        return None


def call_llm(cfg: Config, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns (raw_response_json, weekly_intel_obj)
    Supported responses:
      A) {"ok": true, "output": {...}}
      B) {...weekly_intel_v1...}
    """
    headers = {"Content-Type": "application/json"}
    headers.update(cfg.llm_headers or {})

    resp = requests.post(
        cfg.llm_endpoint,
        headers=headers,
        json=payload,
        timeout=cfg.llm_timeout_seconds,
    )
    resp.raise_for_status()

    data = resp.json() if "application/json" in resp.headers.get("Content-Type", "") else _try_parse_json(resp.text)
    if data is None:
        raise RuntimeError("LLM endpoint did not return JSON")

    if isinstance(data, dict) and data.get("ok") is True and isinstance(data.get("output"), dict):
        return data, data["output"]

    if isinstance(data, dict) and "issue" in data and "entries" in data:
        return {"ok": True, "passthrough": True}, data

    raise RuntimeError("Unexpected LLM response format")
