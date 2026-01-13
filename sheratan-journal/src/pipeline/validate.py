from pathlib import Path
from typing import Any, Dict

from jsonschema import validate  # type: ignore
from jsonschema.exceptions import ValidationError  # type: ignore

from src.io.load import read_json


def validate_weekly_intel(obj: Dict[str, Any], schema_path: str) -> None:
    schema = read_json(schema_path)
    try:
        validate(instance=obj, schema=schema)
    except ValidationError as e:
        raise RuntimeError(f"Schema validation failed: {e.message}")
