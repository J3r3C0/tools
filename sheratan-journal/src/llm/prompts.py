SYSTEM_PROMPT = """You are a strict JSON generator.
Return ONLY valid JSON.
No markdown, no commentary, no code fences.
"""

def build_instructions(schema_version: str) -> str:
    return (
        f"Return ONLY valid JSON matching schema_version='{schema_version}'. "
        "Ensure required fields exist and additionalProperties are not added. "
        "Use relevance strictly: HIGH, MEDIUM, LOW. confidence must be 0..1."
    )
