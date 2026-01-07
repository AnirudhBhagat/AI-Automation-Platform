# orchestration/runner.py
from __future__ import annotations

from typing import Any, Dict

from orchestration.state import WorkflowState
from planner.plan_templates import PlanStep, StepType, WorkflowPlan


class StepFailed(Exception):
    pass


def _check_requires(state: WorkflowState, step: PlanStep) -> None:
    missing = [k for k in step.requires if state.get(k) is None]
    if missing:
        state.log("ERROR", step.step_id, "Missing required inputs for step", missing=missing)
        raise StepFailed(f"Step {step.step_id} missing required keys: {missing}")


def _run_agent_step(state: WorkflowState, step: PlanStep) -> None:
    from agents.sales_agent import run as run_sales
    from agents.finance_agent import run as run_finance
    from agents.data_agent import run as run_data
    from agents.compliance_agent import run as run_compliance

    state.log("INFO", step.step_id, f"Running agent step: {step.owner}.{step.action}")

    if step.owner == "SalesAgent" and step.action == "collect_deal_context":
        customer = state.get("entities.customer_name")
        out = run_sales(customer_name=customer)
        state.set("facts.sales", out)

        # If CRM provides discount/payment terms, backfill entities deterministically
        opp = (out.get("opportunity") or {})
        if opp.get("requested_discount_pct") is not None:
            state.entities.setdefault("discount_pct", str(opp["requested_discount_pct"]))
        if opp.get("payment_terms") is not None:
            state.entities.setdefault("payment_terms", opp["payment_terms"])

    elif step.owner == "FinanceAgent" and step.action == "compute_financials":
        customer = state.get("entities.customer_name")
        amt = int(state.get("entities.deal_amount_usd"))
        term = int(state.get("entities.term_months"))
        out = run_finance(customer_name=customer, deal_amount_usd=amt, term_months=term)
        state.set("facts.finance", out)

    elif step.owner == "ComplianceAgent" and step.action == "validate_policy":
        discount = int(float(state.get("entities.discount_pct") or 0))
        arr = int(state.get("facts.finance.computed_arr_usd"))
        out = run_compliance(discount_pct=discount, computed_arr_usd=arr)
        state.set("facts.compliance", out)

    elif step.owner == "DataAgent" and step.action == "collect_usage_signals":
        customer = state.get("entities.customer_name")
        out = run_data(customer_name=customer)
        state.set("facts.data", out)

    elif step.owner == "Orchestrator" and step.action == "assemble_decision_packet":
        packet: Dict[str, Any] = {
            "trace_id": state.trace_id,
            "request_text": state.request_text,
            "entities": state.entities,
            "facts": state.facts,
            "generated_by": "deterministic_runner_step3",
        }
        state.decision_packet = packet

    else:
        state.log("WARN", step.step_id, "No implementation for agent step", owner=step.owner, action=step.action)

    state.log("INFO", step.step_id, "Step completed", produces=step.produces)



def run_plan(state: WorkflowState, plan: WorkflowPlan) -> WorkflowState:
    state.log("INFO", "runner", f"Starting plan execution: {plan.workflow.value}", steps=len(plan.steps))

    for step in plan.steps:
        if step.step_type != StepType.AGENT:
            state.log("WARN", step.step_id, "Skipping non-agent step in Step 2", step_type=step.step_type.value)
            continue

        _check_requires(state, step)
        _run_agent_step(state, step)

    state.log("INFO", "runner", "Plan execution finished")
    return state
