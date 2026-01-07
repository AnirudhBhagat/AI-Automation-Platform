from __future__ import annotations

import json
from dataclasses import asdict

import streamlit as st
from planner.classify import classify_request, WorkflowType

st. set_page_config(page_title = "AI Automation Platform (MVP)", layout = "centered")

st.title("AI Automation Platform (MVP)")
st.caption("Deterministic planner + (later Gemini synthesis. Step 1: classify request -> workflow.)")

st.markdown("### Enter a request")
default_text = "Approve $120k deal for Acme, 12 months, 15% discount, net-30"
request_text = st.text_area("Request", value = default_text, height  = 120)

use_gemini = st.toggle("Use Gemini for final synthesis (1 call)", value=False)


col1, col2 = st.columns([1,1])
with col1:
    run_btn = st.button("Classify", type = "primary")
with col2:
    st.button("Clear", on_click = lambda: st.session_state.update({"request_text": ""}))

if run_btn:
    from orchestration.state import WorkflowState
    from orchestration.runner import run_plan
    from planner.plan_templates import build_plan

    result = classify_request(request_text)

    st.markdown("### Classification result")
    st.write(f"**Workflow:** `{result.workflow.value}`")
    st.write(f"**Confidence:** `{result.confidence:.2f}`")

    if result.missing_fields:
        st.info("Missing fields: " + ", ".join(f"`{f}`" for f in result.missing_fields))

    plan = build_plan(result.workflow)
    if plan is None:
        st.error("No plan found for this workflow yet.")
    else:
        st.markdown("### Plan steps")
        for s in plan.steps:
            st.write(f"- `{s.step_id}` — **{s.owner}.{s.action}**")

        # Build initial state and execute
        state = WorkflowState(request_text=request_text, entities=result.entities)
        state = run_plan(state, plan)

        st.markdown("### Execution trace")
        for e in state.events:
            st.write(f"`{e.ts}` **{e.level}** [{e.step_id}] — {e.message}")
            if e.details:
                st.json(e.details)

        st.markdown("### Decision packet (what we will send to Gemini later)")
        st.json(state.decision_packet or {})
        if use_gemini:
            st.markdown("### Gemini final synthesis")
        try:
            from llm.gemini_client import synthesize_decision

            output = synthesize_decision(state.decision_packet)
            if output.get("_cached"):
                st.success("Used cached Gemini response ✅")
            else:
                st.info("Called Gemini (1 request)")

            st.json(output)
        except Exception as e:
            st.error(f"Gemini synthesis failed: {e}")

