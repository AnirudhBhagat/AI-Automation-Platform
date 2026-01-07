AI Automation Platform — Multi-Agent Internal Tooling System
Overview

This project implements a production-style AI automation platform designed for internal enterprise workflows such as deal approvals, finance checks, and compliance validation.

The system combines deterministic orchestration, multi-agent execution, and LLM-based synthesis to automate complex cross-functional processes while maintaining reliability, auditability, and cost control.

The architecture intentionally mirrors how internal AI tooling teams operate at modern SaaS companies.

Key Capabilities

Deterministic workflow classification and planning (no LLM dependency)

Multi-agent orchestration across Sales, Finance, Data, and Compliance

MCP-style modular tool interfaces with strict input/output contracts

Snowflake-like analytics using DuckDB (local, zero-cost)

Policy enforcement with explicit approval thresholds

Single-call LLM synthesis (Gemini) with response caching

End-to-end observability with execution traces and audit metadata

Streamlit-based internal tooling UI

Example Workflow: Deal Approval

Input:

“Approve $120k deal for Acme, 12 months, 15% discount, net-30”

Automated execution:

Classify request as DEAL_APPROVAL

Collect CRM account + opportunity context

Compute ARR and billing risk indicators

Aggregate usage analytics signals

Validate discount and ARR against policy rules

Assemble structured decision packet

Generate final decision memo via Gemini (1 API call)

System Components
Planner

Rule-based workflow classifier

Static workflow plan templates

Explicit preconditions and outputs per step

Orchestration Layer

Shared workflow state (“blackboard”)

Step-by-step execution engine

Failure detection and trace logging

Agents

SalesAgent: CRM context and opportunity metadata

FinanceAgent: ARR computation and billing risk signals

DataAgent: usage and engagement analytics

ComplianceAgent: policy validation and approval requirements

MCP-Style Tools

CRM reader (Salesforce-like)

Billing reader (Stripe-like)

Analytics queries (Snowflake-like via DuckDB)

Policy validation engine

LLM Layer

Gemini 2.5 Flash

Single synthesis call per workflow

Strict JSON schema enforcement

On-disk response caching

Reliability & Cost Controls

Deterministic execution for all business logic

LLM usage limited to final synthesis only

Request-level caching eliminates repeated API calls

Streamlit-friendly architecture avoids recomputation on reruns

Technology Stack

Python

Streamlit

DuckDB

Pydantic

Google Gemini API

Modular agent + tool architecture