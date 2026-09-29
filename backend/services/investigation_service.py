from typing import Dict, Any
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
        
        # 1. Run LangGraph Knowledge Investigator Agent
        initial_state = {
            "claim": claim,
            "steps": [],
            "search_iteration": 1,
            "retrieved_documents": [],
            "evidence": []
        }
        
        agent_result = knowledge_investigator_agent.invoke(initial_state)

        classification = agent_result.get("classification", "UNCERTAIN")
        explanation = agent_result.get("reasoning", "No explanation generated.")
        confidence = float(agent_result.get("confidence", 75.0))
        recommendation = agent_result.get("recommendation", "Review evidence manually.")
        human_verification_required = bool(agent_result.get("human_verification_required", True))
        comparison = agent_result.get("comparison", "")
        steps = agent_result.get("steps", [])
        evidence_items = agent_result.get("evidence", [])

        # 2. Persist investigation record to SQLite
        inv = create_investigation(
            db=db,
            claim=claim,
            classification=classification,
            explanation=explanation,
            confidence=confidence,
            recommendation=recommendation,
            human_verification_required=human_verification_required,
            steps=steps,
            comparison=comparison
        )

        # 3. Persist evidence items associated with investigation
        for i, ev in enumerate(evidence_items):
            # First piece or items matching baseline can be marked as stored knowledge
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
                is_stored_knowledge=is_stored
            )

        # 4. Fetch full enriched response
        enriched_response = get_investigation_by_id(db, inv.id)
        logger.info(f"Investigation #{inv.id} completed with classification [{classification}] (confidence={confidence}%)")
        return enriched_response


investigation_service = InvestigationService()
