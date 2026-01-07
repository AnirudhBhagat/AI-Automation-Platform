# llm/gemini_client.py
from __future__ import annotations

import json
import os
from typing import Any, Dict

from llm.cache import get_cached_response, set_cached_response


PROMPT_VERSION = "v1"  # bump this whenever you change the prompt/schema


def _build_prompt(decision_packet: Dict[str, Any]) -> str:
    """
    We instruct Gemini to ONLY output JSON, no markdown.
    We also constrain it to cite evidence keys from the packet.
    """
    return f"""
You are an internal automation assistant for a software company.
You will be given a JSON object called DECISION_PACKET containing:
- request_text
- entities
- facts from internal systems (crm, billing, analytics)
- policy results
Your job: produce a decision memo in STRICT JSON ONLY.

Rules:
1) Do not invent data. Use ONLY values present in DECISION_PACKET.
2) Output MUST be valid JSON. No markdown. No backticks.
3) Every claim must reference an evidence_key that exists in DECISION_PACKET.
4) If required info is missing, set decision="NEEDS_INFO" and list missing_items.

Return JSON with this exact schema:
{{
  "decision": "APPROVE" | "REJECT" | "NEEDS_INFO",
  "summary": "string",
  "rationale": [
    {{"claim": "string", "evidence_key": "string"}}
  ],
  "risks": ["string"],
  "follow_ups": ["string"],
  "audit": {{
    "trace_id": "string",
    "workflow": "DEAL_APPROVAL",
    "model": "gemini-2.5-flash",
    "prompt_version": "{PROMPT_VERSION}"
  }},
  "missing_items": ["string"]
}}

DECISION_PACKET:
{json.dumps(decision_packet, ensure_ascii=False)}
""".strip()


def synthesize_decision(decision_packet: Dict[str, Any], model: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """
    Calls Gemini once and returns the parsed JSON response.
    Uses on-disk cache to avoid repeated calls.
    """
    cache_key = {"prompt_version": PROMPT_VERSION, "model": model, "decision_packet": decision_packet}
    cached = get_cached_response(cache_key)
    if cached is not None:
        return {"_cached": True, **cached}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fail fast with a clear error
        raise RuntimeError("Missing GEMINI_API_KEY env var")

    # Import here so the app can still run in deterministic mode without Gemini installed
    from google import genai  # type: ignore

    client = genai.Client(api_key=api_key)
    prompt = _build_prompt(decision_packet)

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
    )

    # Gemini usually returns text; we expect it to be JSON string.
    text = (resp.text or "").strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        # Save raw output for debugging
        parsed = {
            "decision": "NEEDS_INFO",
            "summary": "Model output was not valid JSON.",
            "rationale": [{"claim": "JSON parsing failed", "evidence_key": "N/A"}],
            "risks": ["MODEL_OUTPUT_NOT_JSON"],
            "follow_ups": ["Adjust prompt or enforce JSON mode if available in your SDK."],
            "audit": {
                "trace_id": decision_packet.get("trace_id", ""),
                "workflow": "DEAL_APPROVAL",
                "model": model,
                "prompt_version": PROMPT_VERSION,
            },
            "missing_items": [],
            "_raw_model_output": text,
            "_json_error": str(e),
        }

    set_cached_response(cache_key, parsed)
    return {"_cached": False, **parsed}
