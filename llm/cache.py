# llm/cache.py
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_PATH = Path(".cache/gemini_cache.json")


def _stable_hash(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_cache() -> Dict[str, Any]:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(cache: Dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")


def get_cached_response(cache_key_obj: Any) -> Optional[Dict[str, Any]]:
    cache = load_cache()
    key = _stable_hash(cache_key_obj)
    return cache.get(key)


def set_cached_response(cache_key_obj: Any, response: Dict[str, Any]) -> None:
    cache = load_cache()
    key = _stable_hash(cache_key_obj)
    cache[key] = response
    save_cache(cache)
