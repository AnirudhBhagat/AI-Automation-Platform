# planner/plan_templates.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from planner.classify import WorkflowType


class StepType(str, Enum):
    AGENT = "AGENT"          # run an agent step
    TOOL = "TOOL"            # (later) run a tool/mcp module step


@dataclass(frozen=True)
class PlanStep:
    """
    A single step in a workflow plan.
    For now we only execute AGENT steps. TOOL steps come in Step 3+.
    """
    step_id: str
    step_type: StepType
    owner: str               # e.g., "SalesAgent"
    action: str              # e.g., "collect_deal_context"
    requires: List[str]      # state keys required before running
    produces: List[str]      # state keys produced after running
    description: str


@dataclass(frozen=True)
class WorkflowPlan:
    workflow: WorkflowType
    steps: List[PlanStep]


def build_plan(workflow: WorkflowType) -> Optional[WorkflowPlan]:
    """
    Returns a static plan for the given workflow.
    Deterministic, no LLM.
    """
    if workflow == WorkflowType.DEAL_APPROVAL:
        steps = [
        PlanStep(
            step_id="sales_collect",
            step_type=StepType.AGENT,
            owner="SalesAgent",
            action="collect_deal_context",
            requires=["request_text", "entities.customer_name"],
            produces=["facts.sales"],
            description="Collect sales context (account + latest opportunity) via CRM tool.",
        ),
        PlanStep(
            step_id="finance_check",
            step_type=StepType.AGENT,
            owner="FinanceAgent",
            action="compute_financials",
            requires=["request_text", "entities.customer_name", "entities.deal_amount_usd", "entities.term_months"],
            produces=["facts.finance.computed_arr_usd", "facts.finance.risk_flags", "facts.finance.billing_profile"],
            description="Compute ARR and pull billing profile via billing tool.",
        ),
        PlanStep(
            step_id="data_signals",
            step_type=StepType.AGENT,
            owner="DataAgent",
            action="collect_usage_signals",
            requires=["entities.customer_name"],
            produces=["facts.data.usage_summary"],
            description="Collect usage signals from analytics store (DuckDB).",
        ),
        PlanStep(
            step_id="compliance_validate",
            step_type=StepType.AGENT,
            owner="ComplianceAgent",
            action="validate_policy",
            requires=["facts.finance.computed_arr_usd"],
            produces=["facts.compliance.policy"],
            description="Validate deal against policy rules (discount caps, ARR thresholds).",
        ),
        PlanStep(
            step_id="orchestrator_assemble",
            step_type=StepType.AGENT,
            owner="Orchestrator",
            action="assemble_decision_packet",
            requires=[
                "facts.sales",
                "facts.finance.computed_arr_usd",
                "facts.compliance.policy",
                "facts.data.usage_summary",
            ],
            produces=["decision_packet"],
            description="Assemble a structured decision packet for Gemini synthesis.",
        ),
    ]
    return WorkflowPlan(workflow=workflow, steps=steps)


    # (Optional stubs; we’ll implement later)
    if workflow == WorkflowType.REFUND_ESCALATION:
        return WorkflowPlan(workflow=workflow, steps=[])

    if workflow == WorkflowType.ACCESS_REQUEST:
        return WorkflowPlan(workflow=workflow, steps=[])

    return None
