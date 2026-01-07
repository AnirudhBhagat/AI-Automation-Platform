# orchestration/state.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class Event:
    """
    An execution event for observability/debugging.
    We'll show these in the Streamlit UI as a trace.
    """
    ts: str
    level: str          # INFO/WARN/ERROR
    step_id: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowState:
    """
    Shared state passed across all steps (the "blackboard").
    Everything agents produce should be stored here under stable keys.
    """
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_text: str = ""
    entities: Dict[str, str] = field(default_factory=dict)

    # facts are structured outputs of agents/tools
    facts: Dict[str, Any] = field(default_factory=dict)

    # final payload to send to Gemini later
    decision_packet: Optional[Dict[str, Any]] = None

    # execution trace
    events: List[Event] = field(default_factory=list)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log(self, level: str, step_id: str, message: str, **details: Any) -> None:
        self.events.append(
            Event(ts=self._now(), level=level, step_id=step_id, message=message, details=details or {})
        )

    def get(self, dotted_key: str) -> Optional[Any]:
        """
        Read state using dotted keys like:
          - "entities.customer_name"
          - "facts.finance.financial_summary"
        """
        parts = dotted_key.split(".")
        cur: Any = self.__dict__
        for p in parts:
            if isinstance(cur, dict):
                cur = cur.get(p)
            else:
                cur = getattr(cur, p, None)
            if cur is None:
                return None
        return cur

    def set(self, dotted_key: str, value: Any) -> None:
        """
        Write state using dotted keys.
        Creates intermediate dicts as needed for dict-based sections.
        """
        parts = dotted_key.split(".")
        # start from the object dict
        cur: Any = self.__dict__

        for i, p in enumerate(parts):
            is_last = (i == len(parts) - 1)
            if isinstance(cur, dict):
                if is_last:
                    cur[p] = value
                else:
                    if p not in cur or cur[p] is None:
                        cur[p] = {}
                    cur = cur[p]
            else:
                # attribute path (only top-level objects like entities, facts, decision_packet)
                if is_last:
                    setattr(self, p, value)
                else:
                    nxt = getattr(cur, p, None)
                    if nxt is None:
                        # if missing, create dict container
                        setattr(cur, p, {})
                        nxt = getattr(cur, p)
                    cur = nxt

