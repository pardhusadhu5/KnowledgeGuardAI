import time
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.agents.investigator import knowledge_investigator_agent
from backend.database.crud import (
    create_investigation,
    add_evidence_to_investigation,
    get_investigation_by_id
)
from backend.models.schemas import InvestigationResponse
from backend.utils.logger import get_logger

logger = get_logger("investigation_service")


class InvestigationService:
    def investigate_claim(self, claim: str, db: Session) -> InvestigationResponse:
        logger.info(f"Starting agent investigation for claim: '{claim}'")
        start_time = time.perf_counter()

        # 1. Run LangGraph Knowledge Investigator Agent
        initial_state = {
            "claim": claim,
            "steps": [],
            "search_count": 1,
            "retrieved_documents": [],
            "evidence": []
        }
        
        agent_result = knowledge_investigator_agent.invoke(initial_state)
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        classification = agent_result.get("classification", "UNCERTAIN")
        explanation = agent_result.get("reasoning", "No explanation generated.")
        confidence = float(agent_result.get("confidence", 75.0))
        # Ensure confidence is formatted as percentage (0-100)
        confidence_pct = confidence * 100.0 if confidence <= 1.0 else confidence

        recommendation = agent_result.get("recommendation", "Review evidence manually.")
        human_verification_required = bool(agent_result.get("human_verification_required", True))
        comparison = agent_result.get("comparison", "")
        steps = agent_result.get("steps", [])
        evidence_items = agent_result.get("evidence", [])

        # Calculate agent metrics
        research_occurred = any(s.get("step_name") == "search_again" for s in steps) or (agent_result.get("search_count", 1) > 1)
        retrieval_attempts = 2 if research_occurred else 1
        unique_doc_ids = {ev.get("document_id") for ev in evidence_items if ev.get("document_id")}
        unique_docs_count = len(unique_doc_ids) if unique_doc_ids else len(set(ev.get("source", "") for ev in evidence_items)) or 1
        evidence_sufficient = agent_result.get("evidence_sufficient", True)

        # Build structured explanation object for UI transparency
        structured_explanation = self._build_structured_explanation(
            claim=claim,
            classification=classification,
            explanation=explanation,
            evidence_items=evidence_items,
            comparison=comparison
        )

        # 2. Persist investigation record to SQLite
        inv = create_investigation(
            db=db,
            claim=claim,
            classification=classification,
            explanation=explanation,
            confidence=round(confidence_pct, 1),
            recommendation=recommendation,
            human_verification_required=human_verification_required,
            steps=steps,
            comparison=comparison,
            human_review_status="Pending Review" if human_verification_required else "Reviewed",
            execution_time_ms=duration_ms,
            research_occurred=research_occurred,
            retrieval_attempts=retrieval_attempts,
            unique_documents=unique_docs_count,
            evidence_sufficient=evidence_sufficient,
            structured_explanation=structured_explanation
        )

        # 3. Persist evidence items associated with investigation
        for i, ev in enumerate(evidence_items):
            is_stored = (i == 0) or ("v2" in ev.get("version", "").lower() and classification == "OUTDATED")
            add_evidence_to_investigation(
                db=db,
                investigation_id=inv.id,
                evidence_text=ev.get("chunk_text", ""),
                relevance_score=float(ev.get("relevance_score", 0.0)),
                document_id=ev.get("document_id"),
                source=ev.get("source", "Document"),
                version=ev.get("version", "1.0"),
                date=ev.get("date", ""),
                page=int(ev.get("page", 1)) if ev.get("page") is not None else 1,
                is_stored_knowledge=is_stored
            )

        # 4. Fetch full enriched response
        enriched_response = get_investigation_by_id(db, inv.id)
        logger.info(f"Investigation #{inv.id} completed with classification [{classification}] in {duration_ms}ms")
        return enriched_response

    def _build_structured_explanation(
        self,
        claim: str,
        classification: str,
        explanation: str,
        evidence_items: List[Dict[str, Any]],
        comparison: str
    ) -> Dict[str, Any]:
        """Constructs an evidence-backed rationale breakdown."""
        if classification == "OUTDATED":
            return {
                "type": "TEMPORAL_SUPERSEDENCE",
                "older_evidence": evidence_items[1].get("source", "Legacy Baseline") if len(evidence_items) > 1 else "Prior Specification",
                "newer_evidence": evidence_items[0].get("source", "Recent Notice") if evidence_items else "Modern Standard",
                "temporal_relationship": "The newer authoritative publication supersedes the earlier version.",
                "final_assessment": "The claim relies on outdated information that is no longer active in the enterprise architecture."
            }
        elif classification == "CONFLICTING":
            return {
                "type": "POLICY_CONTRADICTION",
                "policy_a": evidence_items[0].get("source", "Policy A") if evidence_items else "Specification Alpha",
                "policy_b": evidence_items[1].get("source", "Policy B") if len(evidence_items) > 1 else "Specification Beta",
                "conflict_summary": "Two active governance standards provide mutually exclusive rules for the same architectural scope.",
                "final_assessment": "Contradictory requirements detected; automated reconciliation suspended pending engineering governance review."
            }
        elif classification == "UNCERTAIN":
            return {
                "type": "UNSUPPORTED_OR_MISSING",
                "retrieved_context": f"Inspected {len(evidence_items)} candidate chunk(s) from indexed documentation.",
                "missing_elements": "The knowledge base contains no authoritative citations verifying the specific parameters claimed.",
                "final_assessment": "Unverifiable from current knowledge base; flagged to prevent generative hallucination."
            }
        else: # CURRENT
            return {
                "type": "AUTHORITATIVE_ALIGNMENT",
                "corroborating_source": evidence_items[0].get("source", "Enterprise Documentation") if evidence_items else "Knowledge Base",
                "temporal_relationship": "The claim is substantiated by the most recent active guidelines.",
                "final_assessment": "Verified as current, active enterprise standard."
            }


investigation_service = InvestigationService()
