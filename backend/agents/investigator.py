import json
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
from backend.agents.state import InvestigationState
from backend.agents.tools import (
    analyze_claim,
    search_knowledge,
    retrieve_evidence,
    compare_evidence,
    generate_report
)
from backend.llm.client import llm_client
from backend.utils.logger import get_logger

logger = get_logger("investigator_agent")


# --- Node Definitions ---

def understand_claim_node(state: InvestigationState) -> Dict[str, Any]:
    claim = state.get("claim", "")
    analysis = analyze_claim(claim)
    
    steps = state.get("steps", [])
    steps.append({
        "step_name": "understand_claim",
        "description": "Analyzed claim intent, extracted key entities and retrieval keywords.",
        "status": "completed",
        "details": {
            "keywords": analysis["keywords"],
            "entities": analysis["entities"]
        }
    })

    return {
        "expanded_queries": analysis["alternative_queries"],
        "search_count": 1,
        "steps": steps
    }


def search_knowledge_base_node(state: InvestigationState) -> Dict[str, Any]:
    claim = state.get("claim", "")
    queries = state.get("expanded_queries", [])
    primary_query = queries[0] if queries else claim
    
    hits = search_knowledge(primary_query, n_results=5)
    
    steps = state.get("steps", [])
    steps.append({
        "step_name": "search_knowledge_base",
        "description": f"Queried vector database with semantic representation of: '{primary_query}'.",
        "status": "completed",
        "details": {
            "query_used": primary_query,
            "hits_count": len(hits)
        }
    })

    return {
        "retrieved_documents": hits,
        "steps": steps
    }


def retrieve_evidence_node(state: InvestigationState) -> Dict[str, Any]:
    hits = state.get("retrieved_documents", [])
    steps = state.get("steps", [])
    
    valid_evidence = []
    for hit in hits:
        valid_evidence.append(hit)
    
    steps.append({
        "step_name": "retrieve_evidence",
        "description": f"Retrieved and normalized {len(valid_evidence)} candidate evidence passage(s).",
        "status": "completed",
        "details": {
            "evidence_count": len(valid_evidence)
        }
    })

    return {
        "evidence": valid_evidence,
        "steps": steps
    }


def inspect_metadata_node(state: InvestigationState) -> Dict[str, Any]:
    evidence = state.get("evidence", [])
    steps = state.get("steps", [])

    metas = []
    for ev in evidence:
        metas.append({
            "source": ev.get("source", "Document"),
            "version": ev.get("version", "1.0"),
            "date": ev.get("date", ""),
            "topic": ev.get("topic", "General"),
            "document_id": ev.get("document_id"),
            "filename": ev.get("filename", ""),
            "relevance_score": ev.get("relevance_score", 0.0)
        })

    steps.append({
        "step_name": "inspect_metadata",
        "description": "Inspected document provenance: dates, versions, topics, and authors.",
        "status": "completed",
        "details": {
            "sources_inspected": list({m["source"] for m in metas}),
            "versions_found": list({m["version"] for m in metas})
        }
    })

    return {
        "source_metadata": metas,
        "steps": steps
    }


def evaluate_evidence_sufficiency_node(state: InvestigationState) -> Dict[str, Any]:
    evidence = state.get("evidence", [])
    search_count = state.get("search_count", 1)
    steps = state.get("steps", [])

    # Criteria: If fewer than 2 relevant pieces and search_count < 2, perform query expansion
    is_sufficient = not (len(evidence) < 2 and search_count < 2)

    steps.append({
        "step_name": "evaluate_evidence_sufficiency",
        "description": "Evaluated evidence completeness against investigative thresholds." if is_sufficient else "Initial evidence insufficient. Initiating secondary query expansion.",
        "status": "completed",
        "details": {
            "sufficient": is_sufficient,
            "search_count": search_count,
            "evidence_count": len(evidence)
        }
    })

    return {
        "evidence_sufficient": is_sufficient,
        "steps": steps
    }


def search_again_node(state: InvestigationState) -> Dict[str, Any]:
    """Secondary search node with fallback query expansion."""
    claim = state.get("claim", "")
    queries = state.get("expanded_queries", [])
    fallback = queries[1] if len(queries) > 1 else claim
    
    additional_hits = search_knowledge(fallback, n_results=4)
    existing_hits = state.get("retrieved_documents", [])
    
    # Merge
    existing_texts = {h["chunk_text"] for h in existing_hits}
    for ah in additional_hits:
        if ah["chunk_text"] not in existing_texts:
            existing_hits.append(ah)
            existing_texts.add(ah["chunk_text"])

    steps = state.get("steps", [])
    steps.append({
        "step_name": "search_again",
        "description": f"Executed secondary search iteration using fallback: '{fallback}'.",
        "status": "completed",
        "details": {
            "secondary_query": fallback,
            "total_accumulated_hits": len(existing_hits)
        }
    })

    return {
        "retrieved_documents": existing_hits,
        "evidence": existing_hits,
        "search_count": state.get("search_count", 1) + 1,
        "evidence_sufficient": True,
        "steps": steps
    }


def compare_relevant_evidence_node(state: InvestigationState) -> Dict[str, Any]:
    evidence = state.get("evidence", [])
    steps = state.get("steps", [])
    
    comp_result = compare_evidence(evidence)
    
    steps.append({
        "step_name": "compare_relevant_evidence",
        "description": "Correlated evidence passages across versions and chronological timeline.",
        "status": "completed",
        "details": {
            "summary": comp_result["comparison_summary"],
            "has_version_shift": comp_result["has_version_shift"]
        }
    })

    return {
        "comparison": comp_result["comparison_summary"],
        "steps": steps
    }


def send_structured_evidence_to_llm_node(state: InvestigationState) -> Dict[str, Any]:
    claim = state.get("claim", "")
    evidence = state.get("evidence", [])
    steps = state.get("steps", [])

    steps.append({
        "step_name": "send_structured_evidence_to_llm",
        "description": "Transmitted curated evidence dossier and strict verification prompt to reasoning LLM.",
        "status": "completed",
        "details": {
            "evidence_count_sent": len(evidence)
        }
    })

    # Call single generative LLM client
    llm_verdict = llm_client.reason_over_evidence(claim=claim, evidence_items=evidence)

    return {
        "classification": llm_verdict.get("classification", "UNCERTAIN"),
        "reasoning": llm_verdict.get("reasoning", llm_verdict.get("explanation", "")),
        "confidence": float(llm_verdict.get("confidence", 0.80)),
        "recommendation": llm_verdict.get("recommendation", "Review with domain experts."),
        "human_verification_required": bool(llm_verdict.get("human_verification_required", True)),
        "comparison": llm_verdict.get("comparison", state.get("comparison", "")),
        "steps": steps
    }


def classify_knowledge_node(state: InvestigationState) -> Dict[str, Any]:
    steps = state.get("steps", [])
    classification = state.get("classification", "UNCERTAIN")

    steps.append({
        "step_name": "classify_knowledge",
        "description": f"Assigned verified status classification: [{classification}].",
        "status": "completed",
        "details": {
            "classification": classification,
            "confidence": state.get("confidence", 0.0)
        }
    })

    return {"steps": steps}


def generate_explanation_node(state: InvestigationState) -> Dict[str, Any]:
    steps = state.get("steps", [])
    reasoning = state.get("reasoning", "")

    steps.append({
        "step_name": "generate_explanation",
        "description": "Synthesized evidence-backed rationale and temporal justification.",
        "status": "completed",
        "details": {
            "summary": reasoning[:120] + "..." if len(reasoning) > 120 else reasoning
        }
    })

    return {"steps": steps}


def generate_recommendation_node(state: InvestigationState) -> Dict[str, Any]:
    steps = state.get("steps", [])
    rec = state.get("recommendation", "")
    hvr = state.get("human_verification_required", True)

    steps.append({
        "step_name": "generate_recommendation",
        "description": f"Formulated remediation plan (Human Review Required: {hvr}).",
        "status": "completed",
        "details": {
            "recommendation": rec,
            "human_verification_required": hvr
        }
    })

    return {"steps": steps}


# --- Routing Condition ---
def sufficiency_router(state: InvestigationState) -> str:
    if not state.get("evidence_sufficient", True):
        return "search_again"
    return "compare_relevant_evidence"


# --- LangGraph Graph Assembly ---
def build_investigator_graph():
    builder = StateGraph(InvestigationState)

    builder.add_node("understand_claim", understand_claim_node)
    builder.add_node("search_knowledge_base", search_knowledge_base_node)
    builder.add_node("retrieve_evidence", retrieve_evidence_node)
    builder.add_node("inspect_metadata", inspect_metadata_node)
    builder.add_node("evaluate_evidence_sufficiency", evaluate_evidence_sufficiency_node)
    builder.add_node("search_again", search_again_node)
    builder.add_node("compare_relevant_evidence", compare_relevant_evidence_node)
    builder.add_node("send_structured_evidence_to_llm", send_structured_evidence_to_llm_node)
    builder.add_node("classify_knowledge", classify_knowledge_node)
    builder.add_node("generate_explanation", generate_explanation_node)
    builder.add_node("generate_recommendation", generate_recommendation_node)

    # Edge connections
    builder.add_edge(START, "understand_claim")
    builder.add_edge("understand_claim", "search_knowledge_base")
    builder.add_edge("search_knowledge_base", "retrieve_evidence")
    builder.add_edge("retrieve_evidence", "inspect_metadata")
    builder.add_edge("inspect_metadata", "evaluate_evidence_sufficiency")

    # Conditional branch
    builder.add_conditional_edges(
        "evaluate_evidence_sufficiency",
        sufficiency_router,
        {
            "search_again": "search_again",
            "compare_relevant_evidence": "compare_relevant_evidence"
        }
    )
    builder.add_edge("search_again", "compare_relevant_evidence")
    builder.add_edge("compare_relevant_evidence", "send_structured_evidence_to_llm")
    builder.add_edge("send_structured_evidence_to_llm", "classify_knowledge")
    builder.add_edge("classify_knowledge", "generate_explanation")
    builder.add_edge("generate_explanation", "generate_recommendation")
    builder.add_edge("generate_recommendation", END)

    return builder.compile()


# Compiled LangGraph Workflow instance
knowledge_investigator_agent = build_investigator_graph()
