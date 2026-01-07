from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class WorkflowType(str, Enum):
    DEAL_APPROVAL = "DEAL_APPROVAL"
    REFUND_ESCALATION = "REFUND_ESCALATION"
    ACCESS_REQUEST = "ACCESS_REQUEST"
    UNKNOWN = "UNKNOWN"

@dataclass
class ClassificationResult:
    workflow: WorkflowType
    confidence: float
    reasons: List[str] = field(default_factory = list)
    missing_fields: List[str] = field(default_factory = list)
    entities: Dict[str,str] = field(default_factory = dict)


# --- Simple regex helpers (cheap extraction; optional but useful) ---
_MONEY_RE = re.compile(r"\$?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(k|K|m|M)?")
_TERM_RE = re.compile(r"(\d{1,2})\s*(month|months|mo|mos|year|years|yr|yrs)\b", re.IGNORECASE)
_DISCOUNT_RE = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*%?\s*(discount|off)\b", re.IGNORECASE)


def _normalize_amount(amount_str: str, suffix: Optional[str]) -> Optional[str]:
    """
    
    Convert '$120' or '120000' into a normalized numeric string (e.g., '120000').
    Returns None if parsing fails.
    """
    try:
        raw = float(amount_str.replace(",", ""))
    except ValueError:
        return None
    
    if suffix:
        s = suffix.lower()
        if s == "k":
            raw *= 1_000
        elif s == "m":
            raw *= 1_000_000

    # store as an integer-like stream for clean downstream use
    return str(int(raw))


def extract_entities(text: str) -> Dict[str, str]:
    """
    
    Lightweight entity extraction from the user request.
    This is NOT ML-just regex-based extraction to support deterministic planning.
    """

    entities: Dict[str, str] = {}
    # Amount (e.g., $120k)
    m = _MONEY_RE.search(text)
    if m:
        normalized = _normalize_amount(m.group(1), m.group(2))
        if normalized:
            entities["deal_amount_usd"] = normalized
    
    # Term length (e.g., 12 months)
    t = _TERM_RE.search(text)
    if t:
        n = int(t.group(1))
        unit = t.group(2).lower()
        if unit.startswith(("year","yr")):
            n *= 12
        entities["term_months"] = str(n)

    # Discount (e.g., 15% discount)
    d = _DISCOUNT_RE.search(text)
    if d:
        entities["discount_pct"] = d.group(1)

    # Customer/company name heuristic: after "for <name>" (simple but useful)
    # Example: "Approve $120k deal for Acme"
    for_match = re.search(r"\bfor\s+([A-Za-z0-9][A-Za-z0-9 &\-_]{1,50})", text, re.IGNORECASE)
    if for_match:
        entities["customer_name"] = for_match.group(1).strip(" .,")

    return entities


def _score_rules(text: str) -> List[Tuple[WorkflowType, float, str]]:
    """
    
    Apply rule scoring. Each match adds score points.
    Returns a list of (workflow, score_increment, reason).
    """

    t = text.lower()
    hits: List[Tuple[WorkflowType, float, str]] = []

    # Deal approval signals
    if "approve" in t and any(w in t for w in ["deal", "discount", "opportunity", "quote", "pricing"]):
        hits.append((WorkflowType.DEAL_APPROVAL, 0.55, "Matched 'approve' + deal-related keyword"))
    if any (w in t for w in ["net-30", "net 30", "payment terms","invoice", "arr", "annual", "subscription"]):
        hits.append((WorkflowType.DEAL_APPROVAL, 0.20, "Matched finance/terms keyword for deal flow"))
    if _MONEY_RE.search(text):
        hits.append((WorkflowType.DEAL_APPROVAL, 0.10, "Detected monetary amount"))

    # Refund escalation signals
    if any(w in t for w in ["refund", "chargeback", "dispute"]):
        hits.append((WorkflowType.REFUND_ESCALATION, 0.70, "Matched refund/chargeback keyword"))
    if any(w in t for w in["invoice", "payment failed", "failed payment"]):
        hits.append((WorkflowType.REFUND_ESCALATION, 0.15, "Matched payment/billing signal"))

    # Access request signals
    if "access" in t and any(w in t for w in ["snowflake", "vpn", "github", "okta", "admin"]):
        hits.append((WorkflowType.ACCESS_REQUEST, 0.75, "Matched access + system keyword"))
    if any(w in t for w in["permission", "role", "rbac"]):
        hits.append((WorkflowType.ACCESS_REQUEST, 0.15, "Matched permission keyword"))

    return hits

def classify_request(text: str) -> ClassificationResult:
    """
    
    Deterministically classify a request into a workflow type.
    
    Strategy:
    - Apply a scoring rule set.
    - Choose workflow with highest score.
    - Compute a confidence (clipped to [0,1]).
    - Extract lightweight entities to help planning in later steps.
    - Identify missing fields for the chosen workflow.
    """

    entities = extract_entities(text)
    hits = _score_rules(text)

    # Aggregate scores per workflow
    scores: Dict[WorkflowType, float] = {w: 0.0 for w in WorkflowType}
    reasons_by_workflow: Dict[WorkflowType, List[str]] = {w:[] for w in WorkflowType}

    for wf, inc, reason in hits:
        scores[wf] += inc
        reasons_by_workflow[wf].append(reason)

    # Pick best workflow
    best_wf = max(scores.items(), key = lambda kv: kv[1])[0]
    best_score = scores[best_wf]

    # If nothing matched meaningfully, return UNKNOWN
    if best_score < 0.40:
        return ClassificationResult(
            workflow = WorkflowType.UNKNOWN,
            confidence = min(max(best_score, 0.0), 1.0),
            reasons = ["No strong rule matches; workflow unkown."],
            entities = entities,
        )
    
    # Confidence: clip score into [0,1]
    confidence = min(max(best_score, 0.0), 1.0)
    reasons = reasons_by_workflow[best_wf]

    missing_fields: List[str] = []
    if best_wf == WorkflowType.DEAL_APPROVAL:
        for field_name in ["deal_amount_usd", "term_months", "customer_name"]:
            if field_name not in entities:
                missing_fields.append(field_name)
    elif best_wf == WorkflowType.REFUND_ESCALATION:
        for field_name in ["customer_name"]:
            if field_name not in entities:
                missing_fields.append(field_name)
    elif best_wf == WorkflowType.ACCESS_REQUEST:
        for field_name in ["customer_name"]:
            if field_name not in entities:
                missing_fields.append(field_name)

    return ClassificationResult(
        workflow = best_wf,
        confidence = confidence,
        reasons = reasons,
        missing_fields = missing_fields,
        entities = entities,
    )
