import json
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    llm_endpoint: str
    llm_model: str
    llm_timeout_seconds: int
    llm_headers: dict

    @staticmethod
    def from_env() -> "Config":
        endpoint = os.getenv("LLM_ENDPOINT", "").strip()
        if not endpoint:
            raise RuntimeError("LLM_ENDPOINT is required. Set it in .env")

        model = os.getenv("LLM_MODEL", "any").strip()
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "120").strip())

        headers_raw = os.getenv("LLM_HEADERS_JSON", "{}").strip()
        try:
            headers = json.loads(headers_raw) if headers_raw else {}
            if not isinstance(headers, dict):
                raise ValueError("LLM_HEADERS_JSON must be a JSON object")
        except Exception as e:
            raise RuntimeError(f"Invalid LLM_HEADERS_JSON: {e}")

        return Config(
            llm_endpoint=endpoint,
            llm_model=model,
            llm_timeout_seconds=timeout,
            llm_headers=headers,
        )
